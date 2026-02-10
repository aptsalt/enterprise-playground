"""
Playground Generator v2
========================
Core engine with dual-model architecture, semantic caching,
SSE streaming, and token-optimized prompt engineering.

Architecture:
  Request → Router (3B, keyword or LLM) → Cache check →
    → HIT: instant return (0 tokens)
    → MISS: 3B compresses context → 14B generates HTML → cache store

Token budget per generation:
  - System prompt: ~150 tokens (down from ~600)
  - User prompt: ~200-400 tokens (3B compression)
  - Output: ~3000-5000 tokens (HTML)
  - Total: ~3500-5500 tokens vs old ~20,000+
"""

import asyncio
import json
import re
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, AsyncGenerator

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    OLLAMA_HOST, GENERATOR_MODEL, GENERATOR_TEMPERATURE,
    GENERATOR_MAX_TOKENS, GENERATOR_CTX_SIZE,
    GENERATED_DIR, STRUCTURED_DIR, RAG_ENABLED, METRICS_ENABLED,
)
from playground.router import RequestRouter, RoutedRequest, TaskType, GENERATOR_SYSTEM
from playground.cache import PlaygroundCache
from playground.template import wrap_in_playground
from playground.rag import RAGStore
from playground.metrics import MetricsCollector
from playground.agent_tracer import AgentTracer


class PlaygroundGenerator:
    def __init__(self, host: str = None):
        self.host = host or OLLAMA_HOST
        self.router = RequestRouter(host=self.host)
        self.cache = PlaygroundCache()
        self.rag = RAGStore()
        self.metrics = MetricsCollector()
        self.tracer = AgentTracer()
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import ollama
            self._client = ollama.Client(host=self.host)
        return self._client

    async def generate(
        self,
        prompt: str,
        workflow_context: Optional[dict] = None,
        style: str = "banking",
        force_generate: bool = False,
        bypass_cache: bool = False,
    ) -> dict:
        """
        Generate an interactive HTML playground. Full pipeline:
        1. Route request (keyword → 3B LLM fallback)
        2. Check cache (0 tokens if hit)
        3. Compress context with 3B (saves 30-50% on 14B input)
        4. Generate HTML with 14B
        5. Store in cache
        """
        trace_id = self.tracer.start_trace(prompt)
        step_order = 0

        # Step 1: Route
        t0 = time.monotonic()
        routed = self.router.route(prompt, force_type=TaskType.GENERATE if force_generate else None)
        route_ms = (time.monotonic() - t0) * 1000
        router_method = "keyword" if routed.confidence == 0.9 else ("forced" if routed.confidence == 1.0 else "llm_3b")
        step_order += 1
        self.tracer.add_step(
            trace_id, "route", step_order, route_ms,
            task_type=routed.task_type.value, model=routed.model,
            confidence=routed.confidence, method=router_method,
            needs_html=routed.needs_html,
        )

        # If router says this isn't a code task, handle with 3B
        if not routed.needs_html and not force_generate:
            t0 = time.monotonic()
            text_response = self.router.handle_light_task(routed)
            light_ms = (time.monotonic() - t0) * 1000
            step_order += 1
            self.tracer.add_step(
                trace_id, "light_task", step_order, light_ms,
                model=routed.model, response_len=len(text_response),
            )
            total_ms = route_ms + light_ms
            self.tracer.end_trace(
                trace_id, total_latency_ms=total_ms, total_steps=step_order,
                final_model=routed.model, task_type=routed.task_type.value,
                router_method=router_method, router_confidence=routed.confidence,
                tokens_output=len(text_response) // 4,
            )
            return {
                "html": None,
                "text": text_response,
                "task_type": routed.task_type.value,
                "model": routed.model,
                "playground_id": None,
                "metadata": {"routed_to": "3b", "task_type": routed.task_type.value},
            }

        start_time = time.monotonic()

        # Step 2: Cache check
        t0 = time.monotonic()
        cached = self.cache.get(prompt, style) if not bypass_cache else None
        cache_ms = (time.monotonic() - t0) * 1000
        step_order += 1
        self.tracer.add_step(
            trace_id, "cache_check", step_order, cache_ms,
            hit=cached is not None,
            similarity=cached["similarity"] if cached else 0,
        )

        if cached:
            total_ms = (time.monotonic() - start_time) * 1000
            self.tracer.end_trace(
                trace_id, total_latency_ms=total_ms, total_steps=step_order,
                final_model="cache", task_type="cache_hit", cache_hit=True,
                tokens_saved=4000, playground_id=cached["playground_id"],
                router_method=router_method, router_confidence=routed.confidence,
            )
            self.metrics.record_generation(
                prompt=prompt, model="cache", task_type="cache_hit",
                latency_ms=total_ms, cache_hit=True, style=style,
                playground_id=cached["playground_id"],
            )
            return {
                "html": cached["html"],
                "file_path": str(GENERATED_DIR / f"{cached['playground_id']}.html"),
                "playground_id": cached["playground_id"],
                "metadata": {
                    "cache_hit": True,
                    "similarity": cached["similarity"],
                    "tokens_saved": "~3000-5000",
                },
            }

        # Step 3: RAG context retrieval
        t0 = time.monotonic()
        rag_chunks = self.rag.query(prompt) if self.rag.enabled else []
        rag_ms = (time.monotonic() - t0) * 1000
        rag_context = ""
        if rag_chunks:
            rag_context = "\n\nRelevant context from TD workflows:\n"
            for chunk in rag_chunks:
                rag_context += f"---\n{chunk['content']}\n"
        step_order += 1
        self.tracer.add_step(
            trace_id, "rag_query", step_order, rag_ms,
            chunks_retrieved=len(rag_chunks), rag_enabled=self.rag.enabled,
            context_chars=len(rag_context),
        )

        # Step 4: Compress context with 3B router
        t0 = time.monotonic()
        enriched_prompt = self.router.enrich_prompt(prompt, workflow_context)
        compress_ms = (time.monotonic() - t0) * 1000
        step_order += 1
        compressed = workflow_context is not None
        self.tracer.add_step(
            trace_id, "compress", step_order, compress_ms,
            had_workflow=compressed,
            original_len=len(prompt),
            enriched_len=len(enriched_prompt),
            savings_pct=round((1 - len(enriched_prompt) / max(len(prompt), 1)) * 100, 1) if compressed else 0,
        )

        # Step 5: Build messages with token-optimized system prompt
        style_hint = self._style_hint(style)
        user_content = f"{style_hint}{enriched_prompt}"
        if rag_context:
            user_content += rag_context

        messages = [
            {"role": "system", "content": GENERATOR_SYSTEM},
            {"role": "user", "content": user_content},
        ]

        # Step 6: Generate with 14B
        t0 = time.monotonic()
        response = self.client.chat(
            model=GENERATOR_MODEL,
            messages=messages,
            options={
                "temperature": GENERATOR_TEMPERATURE,
                "num_predict": GENERATOR_MAX_TOKENS,
                "num_ctx": GENERATOR_CTX_SIZE,
                "top_p": 0.9,
                "repeat_penalty": 1.05,
            },
        )
        gen_ms = (time.monotonic() - t0) * 1000
        html_content = self._extract_content(response["message"]["content"])
        html_size = len(html_content.encode("utf-8"))
        input_tokens = len(user_content) // 4
        output_tokens = html_size // 4
        step_order += 1
        self.tracer.add_step(
            trace_id, "generate", step_order, gen_ms,
            model=GENERATOR_MODEL, input_tokens=input_tokens,
            output_tokens=output_tokens, html_size=html_size,
        )

        latency_ms = (time.monotonic() - start_time) * 1000

        # Save
        playground_id = self._generate_id(prompt)
        file_path = GENERATED_DIR / f"{playground_id}.html"
        file_path.write_text(html_content, encoding="utf-8")

        est_tokens = (html_size + len(user_content)) // 4
        metadata = {
            "playground_id": playground_id,
            "prompt": prompt,
            "model": GENERATOR_MODEL,
            "style": style,
            "routed_as": routed.task_type.value,
            "router_confidence": routed.confidence,
            "had_workflow_context": workflow_context is not None,
            "rag_chunks_used": len(rag_chunks),
            "html_size_bytes": html_size,
            "latency_ms": round(latency_ms, 1),
            "generated_at": datetime.now().isoformat(),
            "cache_hit": False,
        }
        meta_path = GENERATED_DIR / f"{playground_id}.meta.json"
        meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        # Step 7: Cache store
        t0 = time.monotonic()
        self.cache.put(prompt, style, playground_id, str(file_path), est_tokens)
        store_ms = (time.monotonic() - t0) * 1000
        step_order += 1
        self.tracer.add_step(
            trace_id, "cache_store", step_order, store_ms,
            playground_id=playground_id, est_tokens=est_tokens,
        )

        # Step 8: Record metrics
        self.metrics.record_generation(
            prompt=prompt, model=GENERATOR_MODEL,
            task_type=routed.task_type.value,
            latency_ms=latency_ms, cache_hit=False,
            rag_chunks_used=len(rag_chunks),
            rag_enabled=self.rag.enabled,
            playground_id=playground_id, style=style,
            html_size_bytes=html_size,
            output_tokens=output_tokens,
            input_tokens=input_tokens,
        )

        # Finalize trace
        self.tracer.end_trace(
            trace_id, total_latency_ms=latency_ms, total_steps=step_order,
            final_model=GENERATOR_MODEL, task_type=routed.task_type.value,
            rag_chunks=len(rag_chunks), tokens_input=input_tokens,
            tokens_output=output_tokens, playground_id=playground_id,
            router_method=router_method, router_confidence=routed.confidence,
        )

        return {
            "html": html_content,
            "file_path": str(file_path),
            "playground_id": playground_id,
            "metadata": metadata,
        }

    async def generate_stream(
        self,
        prompt: str,
        workflow_context: Optional[dict] = None,
        style: str = "banking",
    ) -> AsyncGenerator[str, None]:
        """
        Stream HTML generation via SSE. Yields chunks as they come from 14B.
        The webapp can push these to the client in real-time.
        """
        start_time = time.monotonic()
        trace_id = self.tracer.start_trace(prompt)
        step_order = 0

        # Step 1: Route (implicit — streaming always generates)
        step_order += 1
        self.tracer.add_step(trace_id, "route", step_order, 0.1, task_type="generate", method="stream", confidence=1.0)

        # Step 2: Cache check
        t0 = time.monotonic()
        cached = self.cache.get(prompt, style)
        cache_ms = (time.monotonic() - t0) * 1000
        step_order += 1
        self.tracer.add_step(trace_id, "cache_check", step_order, cache_ms, hit=cached is not None)

        if cached:
            total_ms = (time.monotonic() - start_time) * 1000
            self.tracer.end_trace(
                trace_id, total_latency_ms=total_ms, total_steps=step_order,
                final_model="cache", task_type="cache_hit", cache_hit=True,
                tokens_saved=4000, playground_id=cached["playground_id"],
                router_method="stream", router_confidence=1.0,
            )
            self.metrics.record_generation(
                prompt=prompt, model="cache", task_type="cache_hit",
                latency_ms=total_ms, cache_hit=True, style=style,
                playground_id=cached["playground_id"],
            )
            yield json.dumps({"type": "cache_hit", "playground_id": cached["playground_id"]})
            yield json.dumps({"type": "done", "html": cached["html"]})
            return

        # Step 3: RAG context retrieval
        t0 = time.monotonic()
        rag_chunks = self.rag.query(prompt) if self.rag.enabled else []
        rag_ms = (time.monotonic() - t0) * 1000
        rag_context = ""
        if rag_chunks:
            rag_context = "\n\nRelevant context from TD workflows:\n"
            for chunk in rag_chunks:
                rag_context += f"---\n{chunk['content']}\n"
            yield json.dumps({
                "type": "rag",
                "chunks": len(rag_chunks),
                "preview": [c["content"][:100] for c in rag_chunks],
            })
        step_order += 1
        self.tracer.add_step(
            trace_id, "rag_query", step_order, rag_ms,
            chunks_retrieved=len(rag_chunks), context_chars=len(rag_context),
        )

        # Step 4: Compress and prepare
        t0 = time.monotonic()
        enriched_prompt = self.router.enrich_prompt(prompt, workflow_context)
        compress_ms = (time.monotonic() - t0) * 1000
        step_order += 1
        self.tracer.add_step(trace_id, "compress", step_order, compress_ms, had_workflow=workflow_context is not None)

        style_hint = self._style_hint(style)
        user_content = f"{style_hint}{enriched_prompt}"
        if rag_context:
            user_content += rag_context

        messages = [
            {"role": "system", "content": GENERATOR_SYSTEM},
            {"role": "user", "content": user_content},
        ]

        yield json.dumps({"type": "status", "message": f"Generating with {GENERATOR_MODEL}..."})

        # Step 5: Stream from Ollama
        t0 = time.monotonic()
        full_content = ""
        chunk_buffer = ""

        stream = self.client.chat(
            model=GENERATOR_MODEL,
            messages=messages,
            stream=True,
            options={
                "temperature": GENERATOR_TEMPERATURE,
                "num_predict": GENERATOR_MAX_TOKENS,
                "num_ctx": GENERATOR_CTX_SIZE,
            },
        )

        for chunk in stream:
            token = chunk["message"]["content"]
            full_content += token
            chunk_buffer += token

            # Send chunks every 20 chars to reduce SSE overhead
            if len(chunk_buffer) >= 20:
                yield json.dumps({"type": "chunk", "content": chunk_buffer})
                chunk_buffer = ""

        # Flush remaining
        if chunk_buffer:
            yield json.dumps({"type": "chunk", "content": chunk_buffer})

        gen_ms = (time.monotonic() - t0) * 1000

        # Finalize
        html_content = self._extract_content(full_content)
        html_size = len(html_content.encode("utf-8"))
        input_tokens = len(user_content) // 4
        output_tokens = html_size // 4
        step_order += 1
        self.tracer.add_step(
            trace_id, "generate", step_order, gen_ms,
            model=GENERATOR_MODEL, input_tokens=input_tokens,
            output_tokens=output_tokens, html_size=html_size, streamed=True,
        )

        playground_id = self._generate_id(prompt)
        file_path = GENERATED_DIR / f"{playground_id}.html"
        file_path.write_text(html_content, encoding="utf-8")

        latency_ms = (time.monotonic() - start_time) * 1000
        metadata = {
            "playground_id": playground_id,
            "prompt": prompt,
            "model": GENERATOR_MODEL,
            "style": style,
            "rag_chunks_used": len(rag_chunks),
            "html_size_bytes": html_size,
            "latency_ms": round(latency_ms, 1),
            "generated_at": datetime.now().isoformat(),
        }
        meta_path = GENERATED_DIR / f"{playground_id}.meta.json"
        meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        est_tokens = (html_size + len(user_content)) // 4
        self.cache.put(prompt, style, playground_id, str(file_path), est_tokens)

        # Step 6: Cache store
        step_order += 1
        self.tracer.add_step(trace_id, "cache_store", step_order, 0.5, playground_id=playground_id)

        # Record metrics
        self.metrics.record_generation(
            prompt=prompt, model=GENERATOR_MODEL, task_type="generate",
            latency_ms=latency_ms, cache_hit=False,
            rag_chunks_used=len(rag_chunks), rag_enabled=self.rag.enabled,
            playground_id=playground_id, style=style,
            html_size_bytes=html_size,
            output_tokens=output_tokens,
            input_tokens=input_tokens,
        )

        # Finalize trace
        self.tracer.end_trace(
            trace_id, total_latency_ms=latency_ms, total_steps=step_order,
            final_model=GENERATOR_MODEL, task_type="generate",
            rag_chunks=len(rag_chunks), tokens_input=input_tokens,
            tokens_output=output_tokens, playground_id=playground_id,
            router_method="stream", router_confidence=1.0,
        )

        yield json.dumps({
            "type": "done", "playground_id": playground_id,
            "size": html_size, "latency_ms": round(latency_ms, 1),
            "rag_chunks": len(rag_chunks),
        })

    async def generate_from_workflow(self, workflow_id: str) -> dict:
        """Generate a playground from a saved workflow file."""
        workflow_file = None
        for f in STRUCTURED_DIR.glob("workflow_*.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("workflow_id") == workflow_id:
                workflow_file = f
                break

        if not workflow_file:
            raise FileNotFoundError(f"Workflow not found: {workflow_id}")

        workflow = json.loads(workflow_file.read_text(encoding="utf-8"))
        prompt = (
            f"Interactive playground: '{workflow['name']}' step-by-step. "
            f"Show each step with forms, CTAs, outcomes. Banking app demo style."
        )
        return await self.generate(prompt, workflow_context=workflow, style="banking")

    def _style_hint(self, style: str) -> str:
        """One-line style hint instead of verbose instructions. Token-efficient."""
        hints = {
            "banking": "Style: TD Green #008A4C, professional banking. ",
            "default": "Style: Blue/white, clean modern. ",
            "minimal": "Style: Minimalist, lots of whitespace. ",
            "dark": "Style: Dark theme #1a1a2e, accent #0f3460. ",
        }
        return hints.get(style, "")

    def _extract_content(self, content: str) -> str:
        """
        Extract the HTML content fragment from LLM response.
        The LLM should output raw HTML content (no DOCTYPE/html/head/body).
        We strip code fences and any wrapper tags, then wrap in the playground template.
        """
        c = content.strip()

        # Strip markdown code fences if present
        for pattern in [r'```html\s*(.*?)\s*```', r'```\s*(.*?)\s*```']:
            match = re.search(pattern, c, re.DOTALL)
            if match:
                c = match.group(1).strip()
                break

        # If the LLM output a full HTML page despite instructions, extract the body content
        if c.lower().startswith("<!doctype") or c.lower().startswith("<html"):
            body_match = re.search(r'<body[^>]*>(.*?)</body>', c, re.DOTALL | re.IGNORECASE)
            if body_match:
                c = body_match.group(1).strip()

        # Strip any stray <style> or <script> blocks the LLM may have added
        c = re.sub(r'<style[^>]*>.*?</style>', '', c, flags=re.DOTALL | re.IGNORECASE)

        # Wrap in playground template
        return wrap_in_playground(c)

    def _generate_id(self, prompt: str) -> str:
        hash_str = hashlib.md5(f"{prompt}{datetime.now().isoformat()}".encode()).hexdigest()[:8]
        slug = re.sub(r'[^a-z0-9]+', '-', prompt.lower())[:40].strip('-')
        return f"pg-{slug}-{hash_str}"

    def list_generated(self) -> list[dict]:
        results = []
        for meta_file in sorted(GENERATED_DIR.glob("*.meta.json")):
            try:
                data = json.loads(meta_file.read_text(encoding="utf-8"))
                data["exists"] = meta_file.with_suffix("").with_suffix(".html").exists()
                results.append(data)
            except Exception:
                pass
        return results

    def get_stats(self) -> dict:
        """Combined generator + cache + router stats."""
        playgrounds = self.list_generated()
        cache_stats = self.cache.stats()
        total_html_bytes = sum(p.get("html_size_bytes", 0) for p in playgrounds)
        return {
            "total_playgrounds": len(playgrounds),
            "total_html_size": f"{total_html_bytes / 1024:.0f} KB",
            "generator_model": GENERATOR_MODEL,
            "cache": cache_stats,
        }
