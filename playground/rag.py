"""
RAG Pipeline for Enterprise Playground
========================================
Embeds scraped TD workflows into ChromaDB using Ollama's nomic-embed-text.
Runs on CPU (137M params), zero VRAM impact on the RTX 4090.

Usage:
    rag = RAGStore()
    await rag.ingest_workflows()
    context = rag.query("credit card comparison", top_k=3)
"""

import json
import hashlib
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    OLLAMA_HOST, RAG_ENABLED, RAG_EMBED_MODEL, RAG_COLLECTION,
    RAG_TOP_K, CHROMA_DIR, STRUCTURED_DIR, RAW_DIR,
)


class RAGStore:
    def __init__(self):
        self._client = None
        self._collection = None
        self._embed_fn = None

    @property
    def enabled(self) -> bool:
        return RAG_ENABLED

    def _get_client(self):
        if self._client is None:
            import chromadb
            self._client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        return self._client

    def _get_embed_fn(self):
        if self._embed_fn is None:
            import ollama
            client = ollama.Client(host=OLLAMA_HOST)

            class OllamaEmbedding:
                def __call__(self, input: list[str]) -> list[list[float]]:
                    results = []
                    for text in input:
                        resp = client.embed(model=RAG_EMBED_MODEL, input=text)
                        if hasattr(resp, "embeddings"):
                            results.append(resp.embeddings[0])
                        else:
                            results.append(resp["embeddings"][0])
                    return results

            self._embed_fn = OllamaEmbedding()
        return self._embed_fn

    def _get_collection(self):
        if self._collection is None:
            client = self._get_client()
            embed_fn = self._get_embed_fn()

            class EmbedAdapter:
                """Adapter to match ChromaDB's EmbeddingFunction protocol."""
                def __init__(self, fn):
                    self._fn = fn

                def __call__(self, input: list[str]) -> list[list[float]]:
                    return self._fn(input)

            self._collection = client.get_or_create_collection(
                name=RAG_COLLECTION,
                embedding_function=EmbedAdapter(embed_fn),
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def ingest_workflows(self) -> dict:
        """Read all structured workflow JSONs, chunk them, embed into ChromaDB."""
        if not self.enabled:
            return {"status": "disabled"}

        collection = self._get_collection()
        files = list(STRUCTURED_DIR.glob("workflow_*.json"))
        ingested = 0
        chunks_added = 0

        for filepath in files:
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                workflow_id = data.get("workflow_id", filepath.stem)
                name = data.get("name", "")
                category = data.get("category", "")
                description = data.get("description", "")

                # Chunk 1: Overview
                overview = f"Workflow: {name}\nCategory: {category}\nDescription: {description}"
                if data.get("prerequisites"):
                    overview += f"\nPrerequisites: {', '.join(data['prerequisites'])}"
                if data.get("tags"):
                    overview += f"\nTags: {', '.join(data['tags'])}"

                doc_id = hashlib.md5(f"{workflow_id}_overview".encode()).hexdigest()
                collection.upsert(
                    ids=[doc_id],
                    documents=[overview],
                    metadatas=[{
                        "workflow_id": workflow_id,
                        "chunk_type": "overview",
                        "category": category,
                        "source": "workflow",
                    }],
                )
                chunks_added += 1

                # Chunk 2+: Individual steps
                for step in data.get("steps", []):
                    step_num = step.get("step_number", 0)
                    page = step.get("page_capture", {})
                    step_text = f"Step {step_num}: {page.get('title', '')}\n"
                    step_text += f"URL: {page.get('url', '')}\n"
                    step_text += f"Action: {step.get('user_action', '')}\n"
                    step_text += f"Outcome: {step.get('expected_outcome', '')}\n"

                    # Include section summaries
                    for section in page.get("sections", [])[:3]:
                        step_text += f"Section: {section.get('title', '')} - {section.get('content', '')[:200]}\n"

                    # Include form fields
                    for section in page.get("sections", []):
                        for form in section.get("forms", []):
                            fields = [f.get("label", f.get("name", "")) for f in form.get("fields", [])]
                            if fields:
                                step_text += f"Form fields: {', '.join(fields)}\n"

                    doc_id = hashlib.md5(f"{workflow_id}_step_{step_num}".encode()).hexdigest()
                    collection.upsert(
                        ids=[doc_id],
                        documents=[step_text[:2000]],
                        metadatas=[{
                            "workflow_id": workflow_id,
                            "chunk_type": "step",
                            "step_number": step_num,
                            "category": category,
                            "source": "workflow",
                        }],
                    )
                    chunks_added += 1

                ingested += 1
            except Exception as e:
                continue

        return {
            "status": "ok",
            "workflows_ingested": ingested,
            "chunks_added": chunks_added,
            "total_files": len(files),
        }

    def ingest_scraped_pages(self) -> dict:
        """Embed raw scraped HTML summaries from the raw directory."""
        if not self.enabled:
            return {"status": "disabled"}

        collection = self._get_collection()
        files = list(RAW_DIR.glob("*.html"))
        ingested = 0

        for filepath in files:
            try:
                from bs4 import BeautifulSoup
                html = filepath.read_text(encoding="utf-8", errors="ignore")
                soup = BeautifulSoup(html, "lxml")

                # Extract text content
                title = soup.title.string if soup.title else filepath.stem
                # Get main content, skip nav/footer
                for tag in soup.find_all(["nav", "footer", "script", "style"]):
                    tag.decompose()
                text = soup.get_text(separator="\n", strip=True)[:3000]

                summary = f"Page: {title}\nFile: {filepath.name}\n\n{text}"

                doc_id = hashlib.md5(f"page_{filepath.stem}".encode()).hexdigest()
                collection.upsert(
                    ids=[doc_id],
                    documents=[summary[:2000]],
                    metadatas=[{
                        "chunk_type": "scraped_page",
                        "filename": filepath.name,
                        "source": "scraper",
                    }],
                )
                ingested += 1
            except Exception:
                continue

        return {
            "status": "ok",
            "pages_ingested": ingested,
            "total_files": len(files),
        }

    def query(self, prompt: str, top_k: Optional[int] = None) -> list[dict]:
        """Query the RAG store for relevant context chunks."""
        if not self.enabled:
            return []

        try:
            collection = self._get_collection()
            if collection.count() == 0:
                return []

            k = min(top_k or RAG_TOP_K, collection.count())
            results = collection.query(
                query_texts=[prompt],
                n_results=k,
            )

            chunks = []
            for i in range(len(results["documents"][0])):
                chunks.append({
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                })
            return chunks
        except Exception:
            return []

    def stats(self) -> dict:
        """Return collection stats."""
        if not self.enabled:
            return {"enabled": False}

        try:
            collection = self._get_collection()
            count = collection.count()
            return {
                "enabled": True,
                "collection": RAG_COLLECTION,
                "embed_model": RAG_EMBED_MODEL,
                "total_chunks": count,
                "top_k": RAG_TOP_K,
                "chroma_dir": str(CHROMA_DIR),
            }
        except Exception as e:
            return {"enabled": True, "error": str(e)}

    def get_all_chunks(self, offset: int = 0, limit: int = 50) -> dict:
        """Paginated chunk listing from ChromaDB."""
        if not self.enabled:
            return {"chunks": [], "total": 0}

        try:
            collection = self._get_collection()
            total = collection.count()
            if total == 0:
                return {"chunks": [], "total": 0}

            result = collection.get(
                limit=limit,
                offset=offset,
                include=["documents", "metadatas"],
            )

            chunks = []
            ids = result.get("ids", [])
            docs = result.get("documents", [])
            metas = result.get("metadatas", [])

            for i in range(len(ids)):
                content = docs[i] if i < len(docs) else ""
                chunks.append({
                    "id": ids[i],
                    "content": content[:300],
                    "full_content": content,
                    "size": len(content),
                    "metadata": metas[i] if i < len(metas) else {},
                })

            return {"chunks": chunks, "total": total, "offset": offset, "limit": limit}
        except Exception as e:
            return {"chunks": [], "total": 0, "error": str(e)}

    def get_chunk_analytics(self) -> dict:
        """Size distribution histogram, per-workflow breakdown, source/type counts."""
        if not self.enabled:
            return {"total": 0}

        try:
            collection = self._get_collection()
            total = collection.count()
            if total == 0:
                return {"total": 0, "histogram": [], "workflows": {}, "sources": {}, "types": {}}

            # Fetch all chunks (metadata + documents for size)
            result = collection.get(include=["documents", "metadatas"])
            docs = result.get("documents", [])
            metas = result.get("metadatas", [])

            # Size histogram buckets
            buckets = [
                {"label": "0-200", "min": 0, "max": 200, "count": 0},
                {"label": "200-500", "min": 200, "max": 500, "count": 0},
                {"label": "500-1K", "min": 500, "max": 1000, "count": 0},
                {"label": "1K-1.5K", "min": 1000, "max": 1500, "count": 0},
                {"label": "1.5K-2K", "min": 1500, "max": 2000, "count": 0},
                {"label": "2K+", "min": 2000, "max": float("inf"), "count": 0},
            ]

            sizes = []
            workflows: dict[str, int] = {}
            sources: dict[str, int] = {}
            types: dict[str, int] = {}

            for i, doc in enumerate(docs):
                size = len(doc) if doc else 0
                sizes.append(size)

                for bucket in buckets:
                    if bucket["min"] <= size < bucket["max"]:
                        bucket["count"] += 1
                        break

                meta = metas[i] if i < len(metas) else {}
                wf_id = meta.get("workflow_id", "unknown")
                workflows[wf_id] = workflows.get(wf_id, 0) + 1
                source = meta.get("source", "unknown")
                sources[source] = sources.get(source, 0) + 1
                chunk_type = meta.get("chunk_type", "unknown")
                types[chunk_type] = types.get(chunk_type, 0) + 1

            histogram = [{"label": b["label"], "count": b["count"]} for b in buckets]

            avg_size = round(sum(sizes) / len(sizes)) if sizes else 0
            min_size = min(sizes) if sizes else 0
            max_size = max(sizes) if sizes else 0

            # Sort workflows by count descending
            sorted_workflows = dict(sorted(workflows.items(), key=lambda x: x[1], reverse=True))

            return {
                "total": total,
                "avg_size": avg_size,
                "min_size": min_size,
                "max_size": max_size,
                "histogram": histogram,
                "workflows": sorted_workflows,
                "sources": sources,
                "types": types,
            }
        except Exception as e:
            return {"total": 0, "error": str(e)}

    def find_similar_chunks(self, chunk_id: str, top_k: int = 5) -> dict:
        """Re-query ChromaDB with a chunk's own text to find near-duplicates."""
        if not self.enabled:
            return {"similar": [], "error": "RAG disabled"}

        try:
            collection = self._get_collection()

            # Get the source chunk's content
            source = collection.get(ids=[chunk_id], include=["documents", "metadatas"])
            if not source["documents"]:
                return {"similar": [], "error": "Chunk not found"}

            source_text = source["documents"][0]
            source_meta = source["metadatas"][0] if source["metadatas"] else {}

            # Query for similar (top_k+1 to exclude self)
            results = collection.query(
                query_texts=[source_text],
                n_results=min(top_k + 1, collection.count()),
            )

            similar = []
            for i in range(len(results["ids"][0])):
                rid = results["ids"][0][i]
                if rid == chunk_id:
                    continue
                similar.append({
                    "id": rid,
                    "content": results["documents"][0][i][:300],
                    "distance": round(results["distances"][0][i], 4) if results["distances"] else None,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                })
                if len(similar) >= top_k:
                    break

            return {
                "source_id": chunk_id,
                "source_preview": source_text[:200],
                "source_metadata": source_meta,
                "similar": similar,
            }
        except Exception as e:
            return {"similar": [], "error": str(e)}

    def clear(self) -> dict:
        """Wipe the collection and rebuild."""
        if not self.enabled:
            return {"status": "disabled"}

        try:
            client = self._get_client()
            client.delete_collection(RAG_COLLECTION)
            self._collection = None
            return {"status": "cleared"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
