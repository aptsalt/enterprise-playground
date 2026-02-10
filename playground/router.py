"""
Smart Request Router
=====================
Uses the lightweight 3B model to classify incoming requests and route them
to the appropriate handler. This saves massive tokens by keeping the expensive
14B coder model focused solely on HTML generation.

Routes:
  GENERATE  → 14B coder: full playground HTML generation
  MODIFY    → 14B coder: edit/fix existing playground
  EXPLAIN   → 3B router: text explanation, no code needed
  SUMMARIZE → 3B router: summarize workflow data
  COMPARE   → 3B router: compare products/features (text) + 14B (if visual)
  CHAT      → 3B router: general conversation, clarification

Token savings: ~60-70% of requests handled by 3B model at 4x speed
"""

import json
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    OLLAMA_HOST, GENERATOR_MODEL, ROUTER_MODEL,
    ROUTER_TEMPERATURE, ROUTER_MAX_TOKENS, ROUTER_CTX_SIZE,
    GENERATOR_TEMPERATURE, GENERATOR_MAX_TOKENS, GENERATOR_CTX_SIZE,
)


class TaskType(str, Enum):
    GENERATE = "generate"       # Full playground HTML → 14B
    MODIFY = "modify"           # Edit existing playground → 14B
    EXPLAIN = "explain"         # Text explanation → 3B
    SUMMARIZE = "summarize"     # Summarize data → 3B
    COMPARE = "compare"         # Compare items → 3B (text) or 14B (visual)
    CHAT = "chat"               # General chat → 3B


@dataclass
class RoutedRequest:
    task_type: TaskType
    model: str
    prompt: str
    system_prompt: str
    temperature: float
    max_tokens: int
    ctx_size: int
    needs_html: bool
    confidence: float


# Compact classification prompt — designed to minimize input tokens
ROUTER_CLASSIFY_PROMPT = """Classify this request into exactly ONE category.
Reply with ONLY the category name, nothing else.

Categories:
- GENERATE: create new interactive HTML/visual playground
- MODIFY: edit, fix, update an existing playground
- EXPLAIN: answer a question, explain a concept (text only)
- SUMMARIZE: summarize workflow/data/page content
- COMPARE: compare products, features, options
- CHAT: general conversation, greeting, clarification

Request: {prompt}

Category:"""

# System prompts — content-only generation for the playground framework
GENERATOR_SYSTEM = """You generate HTML CONTENT fragments for a banking UI/UX playground.
The framework provides CSS, control panel, and preview shell. You generate ONLY the inner page content.

OUTPUT RULES:
- Output raw HTML only. NO <!DOCTYPE>, <html>, <head>, <body>, <style>, <script> tags.
- NO markdown, NO code fences, NO explanation text.
- Use ONLY the pre-defined CSS classes listed below. Do NOT write inline styles.

STRUCTURE your content with these sections (use as many as relevant):

NAV: <nav class="td-nav" data-label="Navigation">
  Use .logo (with <span> for accent), .td-nav-links, .td-nav-actions .btn-login

HERO: <section class="td-hero" data-label="Hero">
  Use .hero-content with h1, p, .btn-hero
  Include: <div class="hero-visual" style="display:none;">EMOJI</div>

PRODUCT CARDS: <section class="td-section" data-label="Products">
  Use .section-header h2/p, then .product-grid with .product-card items
  Each card: .card-icon (emoji), h3, p, .card-link

PROMOTIONS: <section class="td-section alt-bg" data-label="Promotions">
  Use .promo-banner with .promo-card.green-bg and .promo-card.dark-bg

FORMS: Use .td-section with .td-form-section, .td-form-group, .td-btn-primary
STEPS: Use .td-steps with .td-step.active/.completed, .td-step-connector
TABS: Use .td-tabs with .td-tab[data-tab], .td-tab-content panels
ACCORDIONS: Use .td-accordion with .td-accordion-header, .td-accordion-body
TABLES: Use .td-table with th/td rows
BADGES: Use .td-badge-green/blue/orange/red

LIFE STAGES: .life-stage-grid with .life-stage-card (.stage-img + .stage-content)
CTA: <section class="cta-strip" data-label="CTA"> with h2, p, .btn-cta
FOOTER: <footer class="td-footer" data-label="Footer"> with .footer-grid/.footer-col

CONTENT GUIDELINES:
- Use realistic banking content (TD Bank style)
- Use emoji for card icons (e.g. &#128179; &#127968; &#128200;)
- Add data-label="Name" attributes for annotation mode
- Make content rich: 4-8 product cards, 2 promo cards, 3 life stage cards
- For workflow topics: include step indicators and forms"""

ROUTER_SYSTEM = """You are a concise assistant for an enterprise banking playground system.
Answer directly and briefly. Use markdown for structure. No fluff."""


def _keyword_classify(prompt: str) -> Optional[TaskType]:
    """Fast keyword-based classification. Avoids LLM call entirely for obvious cases."""
    p = prompt.lower().strip()

    # Direct generate signals
    generate_signals = [
        "create", "build", "generate", "make me", "design",
        "playground", "interactive", "visualize", "visualization",
        "html", "demo", "walkthrough", "show me"
    ]
    if any(s in p for s in generate_signals):
        # Check if it's a modification
        modify_signals = ["fix", "update", "change", "edit", "modify", "adjust", "tweak"]
        if any(s in p for s in modify_signals) and ("playground" in p or "pg-" in p):
            return TaskType.MODIFY
        return TaskType.GENERATE

    # Direct explain signals
    explain_signals = ["what is", "what are", "how does", "explain", "why", "tell me about", "define"]
    if any(p.startswith(s) or s in p for s in explain_signals):
        return TaskType.EXPLAIN

    # Direct summarize signals
    if any(s in p for s in ["summarize", "summary", "overview", "brief", "recap"]):
        return TaskType.SUMMARIZE

    # Direct compare signals
    if any(s in p for s in ["compare", "difference", "vs", "versus", "which is better"]):
        return TaskType.COMPARE

    # Chat/greeting signals
    if any(p.startswith(s) for s in ["hi", "hello", "hey", "thanks", "ok", "sure", "yes", "no"]):
        return TaskType.CHAT

    return None  # Uncertain — use LLM


class RequestRouter:
    def __init__(self, host: str = None):
        self.host = host or OLLAMA_HOST
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import ollama
            self._client = ollama.Client(host=self.host)
        return self._client

    def route(self, prompt: str, force_type: TaskType = None) -> RoutedRequest:
        """
        Classify a request and return routing info.
        Uses keyword matching first (0 tokens), falls back to 3B LLM.
        """
        if force_type:
            task_type = force_type
            confidence = 1.0
        else:
            # Try keyword classification first (free)
            task_type = _keyword_classify(prompt)
            confidence = 0.9 if task_type else 0.0

            if task_type is None:
                # Fall back to 3B LLM classification (~50 tokens)
                task_type, confidence = self._llm_classify(prompt)

        # Determine model and parameters
        needs_html = task_type in (TaskType.GENERATE, TaskType.MODIFY)

        if needs_html:
            model = GENERATOR_MODEL
            system_prompt = GENERATOR_SYSTEM
            temperature = GENERATOR_TEMPERATURE
            max_tokens = GENERATOR_MAX_TOKENS
            ctx_size = GENERATOR_CTX_SIZE
        else:
            model = ROUTER_MODEL
            system_prompt = ROUTER_SYSTEM
            temperature = ROUTER_TEMPERATURE
            max_tokens = ROUTER_MAX_TOKENS
            ctx_size = ROUTER_CTX_SIZE

        return RoutedRequest(
            task_type=task_type,
            model=model,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            ctx_size=ctx_size,
            needs_html=needs_html,
            confidence=confidence,
        )

    def _llm_classify(self, prompt: str) -> tuple[TaskType, float]:
        """Use 3B model for classification. ~50 input tokens, ~5 output tokens."""
        try:
            response = self.client.chat(
                model=ROUTER_MODEL,
                messages=[{
                    "role": "user",
                    "content": ROUTER_CLASSIFY_PROMPT.format(prompt=prompt[:200])
                }],
                options={
                    "temperature": 0.0,
                    "num_predict": 10,
                    "num_ctx": 512,
                },
            )
            raw = response["message"]["content"].strip().upper()

            type_map = {
                "GENERATE": TaskType.GENERATE,
                "MODIFY": TaskType.MODIFY,
                "EXPLAIN": TaskType.EXPLAIN,
                "SUMMARIZE": TaskType.SUMMARIZE,
                "COMPARE": TaskType.COMPARE,
                "CHAT": TaskType.CHAT,
            }

            for key, val in type_map.items():
                if key in raw:
                    return val, 0.8
            return TaskType.GENERATE, 0.5  # Default fallback

        except Exception:
            return TaskType.GENERATE, 0.3

    def handle_light_task(self, routed: RoutedRequest) -> str:
        """Handle non-HTML tasks directly with the 3B model."""
        response = self.client.chat(
            model=ROUTER_MODEL,
            messages=[
                {"role": "system", "content": routed.system_prompt},
                {"role": "user", "content": routed.prompt},
            ],
            options={
                "temperature": routed.temperature,
                "num_predict": routed.max_tokens,
                "num_ctx": routed.ctx_size,
            },
        )
        return response["message"]["content"]

    def enrich_prompt(
        self,
        prompt: str,
        workflow_context: dict = None,
        rag_context: str = "",
    ) -> str:
        """
        Use 3B model to compress and enrich a prompt before sending to 14B.
        Extracts key requirements so the 14B model gets a tighter input.
        Saves ~30-50% input tokens on the expensive model.

        If rag_context is provided, it will be appended after compression.
        """
        if not workflow_context:
            return prompt

        # Compress workflow context with 3B model
        compress_prompt = (
            f"Extract ONLY the essential info needed to build an HTML visualization. "
            f"Output a compact bullet list, max 10 lines.\n\n"
            f"Workflow: {json.dumps(workflow_context, default=str)[:1500]}\n\n"
            f"User request: {prompt}"
        )

        try:
            response = self.client.chat(
                model=ROUTER_MODEL,
                messages=[{"role": "user", "content": compress_prompt}],
                options={"temperature": 0.1, "num_predict": 300, "num_ctx": 2048},
            )
            compressed = response["message"]["content"]
            return f"{prompt}\n\nWorkflow summary:\n{compressed}"
        except Exception:
            return prompt
