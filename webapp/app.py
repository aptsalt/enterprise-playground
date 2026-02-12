"""
Enterprise Playground Web Application v2
==========================================
Production-quality FastAPI app with:
- SSE streaming for real-time generation
- Dual-model status dashboard
- VRAM monitoring (nvidia-smi)
- Cache statistics panel
- Resource-efficient UI (single HTML, no framework bloat)

Run:
    uvicorn webapp.app:app --reload --host 0.0.0.0 --port 8000
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    APP_HOST, APP_PORT, APP_ENV,
    GENERATED_DIR, STRUCTURED_DIR, SCREENSHOTS_DIR, RAW_DIR,
    OLLAMA_HOST, GENERATOR_MODEL, ROUTER_MODEL, DATA_DIR,
    ROOT_DIR, ADAPTERS_DIR, CACHE_DIR, CHROMA_DIR,
)
from playground.generator import PlaygroundGenerator
from playground.rag import RAGStore
from playground.metrics import MetricsCollector
from playground.observatory import MLObservatory
from playground.agent_tracer import AgentTracer
from fine_tuning.prepare_dataset import collect_examples, create_training_dataset, _save_jsonl, _quality_distribution

app = FastAPI(title="Enterprise Playground", version="2.0.1")

# === OpenTelemetry Instrumentation ===
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
except ImportError:
    pass  # OpenTelemetry optional - works without it

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3004", "http://127.0.0.1:3004"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/generated", StaticFiles(directory=str(GENERATED_DIR)), name="generated")
app.mount("/screenshots", StaticFiles(directory=str(SCREENSHOTS_DIR)), name="screenshots")

generator = PlaygroundGenerator()
rag_store = generator.rag
metrics_collector = generator.metrics
observatory = MLObservatory()
agent_tracer = generator.tracer


# === Response Cache (TTL-based, eliminates redundant I/O on tab switch) ===

class ResponseCache:
    """Simple TTL cache for expensive API responses."""

    def __init__(self):
        self._store: dict[str, tuple[float, any]] = {}

    def get(self, key: str, ttl: float = 5.0):
        entry = self._store.get(key)
        if entry and (time.time() - entry[0]) < ttl:
            return entry[1]
        return None

    def set(self, key: str, value: any):
        self._store[key] = (time.time(), value)

    def invalidate(self, key: str):
        self._store.pop(key, None)


_rcache = ResponseCache()


# === Background VRAM Monitor ===

_vram_cache: dict = {"available": False}


async def _vram_monitor_loop():
    """Poll nvidia-smi every 10s in background instead of per-request."""
    global _vram_cache
    while True:
        try:
            proc = await asyncio.create_subprocess_exec(
                "nvidia-smi",
                "--query-gpu=memory.used,memory.total,memory.free,gpu_name,temperature.gpu,utilization.gpu",
                "--format=csv,noheader,nounits",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            if proc.returncode == 0:
                parts = [p.strip() for p in stdout.decode().strip().split(",")]
                if len(parts) >= 6:
                    used, total, free = int(parts[0]), int(parts[1]), int(parts[2])
                    _vram_cache = {
                        "used_mb": used, "total_mb": total, "free_mb": free,
                        "usage_pct": round(used / total * 100, 1),
                        "gpu_name": parts[3], "temp_c": int(parts[4]),
                        "utilization_pct": int(parts[5]),
                    }
        except Exception:
            pass
        await asyncio.sleep(10)


@app.on_event("startup")
async def _start_vram_monitor():
    asyncio.create_task(_vram_monitor_loop())


# === Request Models ===

class GenerateRequest(BaseModel):
    prompt: str
    workflow_id: Optional[str] = None
    style: str = "banking"
    force_generate: bool = False


class ChatRequest(BaseModel):
    message: str


# === Pages ===

@app.get("/", response_class=HTMLResponse)
async def home():
    return _render_dashboard()


@app.get("/playground/{playground_id}", response_class=HTMLResponse)
async def view_playground(playground_id: str):
    html_file = GENERATED_DIR / f"{playground_id}.html"
    if not html_file.exists():
        raise HTTPException(404, f"Playground not found: {playground_id}")
    return HTMLResponse(html_file.read_text(encoding="utf-8"))


# === API ===

@app.post("/api/generate")
async def api_generate(req: GenerateRequest):
    try:
        workflow_context = None
        if req.workflow_id:
            workflow_context = _load_workflow(req.workflow_id)

        result = await generator.generate(
            prompt=req.prompt,
            workflow_context=workflow_context,
            style=req.style,
            force_generate=req.force_generate,
        )
        # Invalidate caches so tabs show fresh data
        _rcache.invalidate("pipeline_status")
        _rcache.invalidate("metrics")
        _rcache.invalidate("agent_stats")
        _rcache.invalidate("agent_traces_30")
        return {
            "playground_id": result.get("playground_id"),
            "text": result.get("text"),
            "task_type": result.get("task_type"),
            "metadata": result.get("metadata"),
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/generate/stream")
async def api_generate_stream(req: GenerateRequest):
    """SSE streaming endpoint for real-time generation."""
    async def event_stream():
        try:
            workflow_context = None
            if req.workflow_id:
                workflow_context = _load_workflow(req.workflow_id)

            async for chunk in generator.generate_stream(
                prompt=req.prompt,
                workflow_context=workflow_context,
                style=req.style,
            ):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    """Route chat messages through the smart router. Uses 3B for non-code tasks."""
    try:
        result = await generator.generate(prompt=req.message)
        if result.get("html"):
            return {"type": "playground", "playground_id": result["playground_id"]}
        return {"type": "text", "response": result.get("text", "")}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/generate/workflow")
async def api_generate_from_workflow(req: dict):
    try:
        result = await generator.generate_from_workflow(req["workflow_id"])
        return {"playground_id": result["playground_id"], "metadata": result["metadata"]}
    except FileNotFoundError:
        raise HTTPException(404, f"Workflow not found: {req.get('workflow_id')}")
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/playgrounds")
async def api_list_playgrounds():
    return generator.list_generated()


@app.get("/api/workflows")
async def api_list_workflows():
    return _list_workflows()


@app.get("/api/stats")
async def api_stats():
    """Full system stats: models, cache, VRAM, playgrounds (cached 5s)."""
    cached = _rcache.get("stats", ttl=5.0)
    if cached:
        # Always inject fresh VRAM from background monitor
        cached["vram"] = _vram_cache if _vram_cache.get("used_mb") else cached.get("vram")
        return cached
    stats = generator.get_stats()
    stats["vram"] = _get_vram_info()
    stats["models"] = _get_model_info()
    stats["workflows_count"] = len(_list_workflows())
    _rcache.set("stats", stats)
    return stats


@app.get("/api/health")
async def health():
    ollama_ok = False
    models_loaded = []
    try:
        import ollama
        client = ollama.Client(host=OLLAMA_HOST)
        resp = client.list()
        # Ollama 0.4+ returns Pydantic models — use model_dump() for safe access
        models_loaded = []
        raw_models = resp.models if hasattr(resp, 'models') else resp.get("models", [])
        for m in raw_models:
            if hasattr(m, 'model_dump'):
                d = m.model_dump()
                models_loaded.append(d.get("model", ""))
            elif isinstance(m, dict):
                models_loaded.append(m.get("name", m.get("model", "")))
            else:
                models_loaded.append(str(m))
        ollama_ok = True
    except Exception:
        pass

    return {
        "status": "ok",
        "ollama_available": ollama_ok,
        "generator_model": GENERATOR_MODEL,
        "router_model": ROUTER_MODEL,
        "models_loaded": models_loaded,
        "generator_ready": any(GENERATOR_MODEL.split(":")[0] in m for m in models_loaded),
        "router_ready": any(ROUTER_MODEL.split(":")[0] in m for m in models_loaded),
    }


@app.post("/api/cache/clear")
async def clear_cache():
    generator.cache.clear()
    return {"status": "cleared"}


# === RAG Endpoints ===

@app.get("/api/rag/stats")
async def api_rag_stats():
    return rag_store.stats()


@app.post("/api/rag/ingest")
async def api_rag_ingest():
    """Trigger workflow + scraped page ingestion into ChromaDB."""
    wf_result = rag_store.ingest_workflows()
    page_result = rag_store.ingest_scraped_pages()
    return {"workflows": wf_result, "pages": page_result}


class PrepareDatasetRequest(BaseModel):
    min_quality: int = 2
    split_ratio: float = 0.9


class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 3


@app.post("/api/rag/query")
async def api_rag_query(req: RAGQueryRequest):
    chunks = rag_store.query(req.query, top_k=req.top_k)
    return {"query": req.query, "chunks": chunks, "count": len(chunks)}


@app.post("/api/rag/clear")
async def api_rag_clear():
    return rag_store.clear()


# === Metrics Endpoints ===

@app.get("/api/metrics")
async def api_metrics():
    cached = _rcache.get("metrics", ttl=5.0)
    if cached:
        return cached
    stats = metrics_collector.get_dashboard_stats()
    # Inject live VRAM from background monitor instead of per-request subprocess
    if isinstance(stats, dict):
        stats["vram"] = _vram_cache if _vram_cache.get("used_mb") else stats.get("vram")
    _rcache.set("metrics", stats)
    return stats


# === Pipeline Status ===

@app.get("/api/pipeline/status")
async def api_pipeline_status():
    """Pipeline phase counts for the visualizer (cached 5s)."""
    cached = _rcache.get("pipeline_status", ttl=5.0)
    if cached:
        return cached

    raw_pages = len(list(RAW_DIR.glob("*.html")))
    structured_workflows = len(list(STRUCTURED_DIR.glob("workflow_*.json")))
    rag_stats = rag_store.stats()
    embeddings = rag_stats.get("total_chunks", 0) if isinstance(rag_stats, dict) else 0
    playgrounds = len(generator.list_generated())
    cache_stats = generator.cache.stats()
    training_files = len(list(DATA_DIR.glob("*.jsonl")))

    result = {
        "phases": {
            "scrape": {"count": raw_pages, "label": "Scraped Pages"},
            "map": {"count": structured_workflows, "label": "Mapped Workflows"},
            "store": {"count": embeddings, "label": "RAG Embeddings"},
            "route": {"count": cache_stats.get("total_requests", 0), "label": "Requests Routed"},
            "generate": {"count": playgrounds, "label": "Playgrounds Generated"},
            "cache": {"count": cache_stats.get("entries", 0), "label": "Cache Entries"},
            "train": {"count": training_files, "label": "Training Files"},
        }
    }
    _rcache.set("pipeline_status", result)
    return result


# === Dataset Endpoints ===

@app.get("/api/dataset/stats")
async def api_dataset_stats():
    """Dataset stats for the Data & RAG tab (cached 10s)."""
    cached = _rcache.get("dataset_stats", ttl=10.0)
    if cached:
        return cached

    training_files = list(DATA_DIR.glob("*.jsonl"))
    total_examples = 0
    for f in training_files:
        try:
            total_examples += sum(1 for _ in f.open(encoding="utf-8"))
        except Exception:
            pass

    result = {
        "training_files": len(training_files),
        "total_examples": total_examples,
        "data_dir": str(DATA_DIR),
    }
    _rcache.set("dataset_stats", result)
    return result


# === Dataset Preparation Endpoint ===

@app.post("/api/dataset/prepare")
async def api_prepare_dataset(req: PrepareDatasetRequest = PrepareDatasetRequest()):
    """Prepare fine-tuning dataset from generated playgrounds."""
    min_quality = req.min_quality
    split_ratio = req.split_ratio

    examples = collect_examples()
    if not examples:
        return {"status": "error", "message": "No generated playgrounds found. Generate some first."}

    dataset = create_training_dataset(examples, min_quality=min_quality)
    if not dataset:
        return {"status": "error", "message": f"No examples passed quality filter (min={min_quality})"}

    split_idx = int(len(dataset) * split_ratio)
    train_data = dataset[:split_idx]
    val_data = dataset[split_idx:]

    train_path = DATA_DIR / "train.jsonl"
    val_path = DATA_DIR / "val.jsonl"
    _save_jsonl(train_data, train_path)
    _save_jsonl(val_data, val_path)

    info = {
        "total_examples": len(examples),
        "filtered_examples": len(dataset),
        "train_size": len(train_data),
        "val_size": len(val_data),
        "min_quality": min_quality,
        "format": "alpaca",
        "created_at": datetime.now().isoformat(),
    }
    info_path = DATA_DIR / "dataset_info.json"
    info_path.write_text(json.dumps(info, indent=2), encoding="utf-8")

    return {
        "status": "ok",
        "total_examples": len(examples),
        "filtered": len(dataset),
        "train_size": len(train_data),
        "val_size": len(val_data),
        "quality_distribution": _quality_distribution(examples),
    }


# === Observatory Endpoints ===

@app.get("/api/observatory/chunks")
async def api_observatory_chunks(offset: int = 0, limit: int = 50):
    return rag_store.get_all_chunks(offset=offset, limit=limit)


@app.get("/api/observatory/chunk-analytics")
async def api_observatory_chunk_analytics():
    cached = _rcache.get("chunk_analytics", ttl=10.0)
    if cached:
        return cached
    result = rag_store.get_chunk_analytics()
    _rcache.set("chunk_analytics", result)
    return result


class SimilarChunksRequest(BaseModel):
    chunk_id: str
    top_k: int = 5


@app.post("/api/observatory/similar-chunks")
async def api_observatory_similar_chunks(req: SimilarChunksRequest):
    return rag_store.find_similar_chunks(chunk_id=req.chunk_id, top_k=req.top_k)


@app.get("/api/observatory/training/status")
async def api_observatory_training_status():
    return observatory.get_training_status()


@app.get("/api/observatory/training/logs")
async def api_observatory_training_logs():
    return observatory.get_training_logs()


@app.get("/api/observatory/dataset/analytics")
async def api_observatory_dataset_analytics():
    return observatory.get_dataset_analytics()


@app.get("/api/observatory/training/examples")
async def api_observatory_training_examples(offset: int = 0, limit: int = 20, file: str = "train"):
    return observatory.get_training_examples(offset=offset, limit=limit, file=file)


@app.get("/api/observatory/adapters")
async def api_observatory_adapters():
    return observatory.list_adapters()


@app.get("/api/observatory/adapters/{name}")
async def api_observatory_adapter_details(name: str):
    details = observatory.get_adapter_details(name)
    if not details:
        raise HTTPException(404, f"Adapter not found: {name}")
    return details


@app.post("/api/observatory/adapters/{name}/deploy")
async def api_observatory_deploy_adapter(name: str):
    details = observatory.get_adapter_details(name)
    if not details:
        raise HTTPException(404, f"Adapter not found: {name}")
    return {
        "adapter": name,
        "command": details["deploy_command"],
        "message": "Run this command in your terminal to merge and deploy the adapter.",
    }


# === Feedback Endpoints (Human-in-the-loop) ===

class FeedbackRequest(BaseModel):
    playground_id: str
    rating: str  # "up" or "down"
    prompt: str = ""
    metadata: Optional[dict] = None


_feedback_log: list[dict] = []


@app.post("/api/feedback")
async def api_feedback(req: FeedbackRequest):
    """Record human feedback for fine-tuning data curation."""
    entry = {
        "playground_id": req.playground_id,
        "rating": req.rating,
        "prompt": req.prompt,
        "metadata": req.metadata,
        "timestamp": datetime.now().isoformat(),
    }
    _feedback_log.append(entry)

    # Persist to disk
    feedback_path = Path("cache/feedback.jsonl")
    feedback_path.parent.mkdir(exist_ok=True)
    with open(feedback_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return {"status": "recorded", "total_feedback": len(_feedback_log)}


@app.get("/api/feedback/stats")
async def api_feedback_stats():
    ups = sum(1 for f in _feedback_log if f["rating"] == "up")
    downs = sum(1 for f in _feedback_log if f["rating"] == "down")
    return {"total": len(_feedback_log), "positive": ups, "negative": downs}


# === Embedding Visualization Endpoints ===

@app.get("/api/observatory/embedding-coords")
async def api_embedding_coords(dims: int = 3):
    """Return UMAP-projected 2D/3D coordinates from real ChromaDB embeddings."""
    cache_key = f"embedding_coords_{dims}"
    cached = _rcache.get(cache_key, ttl=30.0)
    if cached:
        return cached

    try:
        import numpy as np
        import umap

        collection = rag_store._get_collection()
        total = collection.count()
        if total == 0:
            return []

        fetch_limit = min(total, 500)
        result = collection.get(
            limit=fetch_limit,
            include=["embeddings", "documents", "metadatas"],
        )

        ids = result.get("ids", [])
        raw_embeddings = result.get("embeddings", [])
        docs = result.get("documents", [])
        metas = result.get("metadatas", [])

        # ChromaDB may return numpy arrays — convert to np safely
        matrix = np.array(raw_embeddings, dtype=np.float32) if raw_embeddings is not None else np.array([])
        if matrix.ndim != 2 or matrix.shape[0] < 5:
            return []

        n_components = min(dims, 3)
        n_neighbors = min(15, matrix.shape[0] - 1)

        reducer = umap.UMAP(
            n_components=n_components,
            n_neighbors=n_neighbors,
            min_dist=0.1,
            metric="cosine",
            random_state=42,
        )
        projected = reducer.fit_transform(matrix)

        # Normalize to [0, 1] range
        mins = projected.min(axis=0)
        maxs = projected.max(axis=0)
        ranges = maxs - mins
        ranges[ranges == 0] = 1
        normalized = (projected - mins) / ranges

        results = []
        for i in range(len(ids)):
            meta = metas[i] if i < len(metas) else {}
            category = meta.get("category", meta.get("workflow_category", "default"))
            content = docs[i][:200] if i < len(docs) else ""
            point = {
                "id": ids[i],
                "category": category,
                "content": content,
                "chunk_type": meta.get("chunk_type", "unknown"),
                "source": meta.get("source", "unknown"),
                "x": round(float(normalized[i][0]), 4),
                "y": round(float(normalized[i][1]), 4),
            }
            if n_components >= 3:
                point["z"] = round(float(normalized[i][2]), 4)
            results.append(point)

        _rcache.set(cache_key, results)
        return results
    except Exception:
        return []


# === Agent Observability Endpoints ===

@app.get("/api/agent/stats")
async def api_agent_stats():
    cached = _rcache.get("agent_stats", ttl=3.0)
    if cached:
        return cached
    result = agent_tracer.get_agent_stats()
    _rcache.set("agent_stats", result)
    return result


@app.get("/api/agent/traces")
async def api_agent_traces(limit: int = 30):
    cached = _rcache.get(f"agent_traces_{limit}", ttl=3.0)
    if cached:
        return cached
    result = agent_tracer.get_recent_traces(limit=limit)
    _rcache.set(f"agent_traces_{limit}", result)
    return result


@app.get("/api/agent/trace/{trace_id}")
async def api_agent_trace(trace_id: str):
    trace = agent_tracer.get_trace(trace_id)
    if not trace:
        raise HTTPException(404, f"Trace not found: {trace_id}")
    return trace


# === Storage Overview Endpoint ===

@app.get("/api/storage/overview")
async def api_storage_overview():
    """Scan directory sizes, SQLite row counts, cache stats for the storage visualizer."""
    cached = _rcache.get("storage_overview", ttl=10.0)
    if cached:
        return cached

    import sqlite3

    def _dir_size(path: Path) -> int:
        if not path.exists():
            return 0
        total = 0
        for f in path.rglob("*"):
            if f.is_file():
                try:
                    total += f.stat().st_size
                except OSError:
                    pass
        return total

    def _sqlite_tables(db_path: Path) -> list[dict]:
        if not db_path.exists():
            return []
        tables = []
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            for (name,) in cursor.fetchall():
                try:
                    row_count = conn.execute(f"SELECT COUNT(*) FROM [{name}]").fetchone()[0]
                except Exception:
                    row_count = 0
                tables.append({"name": name, "rows": row_count})
            conn.close()
        except Exception:
            pass
        return tables

    dirs = {
        ".chroma": _dir_size(CHROMA_DIR),
        ".cache": _dir_size(CACHE_DIR),
        "generated": _dir_size(GENERATED_DIR),
        "workflows": _dir_size(ROOT_DIR / "workflows"),
        "adapters": _dir_size(ADAPTERS_DIR),
        "training_data": _dir_size(DATA_DIR),
    }
    total_size = sum(dirs.values())

    metrics_db = CACHE_DIR / "metrics.db"
    traces_db = CACHE_DIR / "agent_traces.db"

    cache_stats = generator.cache.stats()
    feedback_path = Path("cache/feedback.jsonl")
    feedback_count = 0
    if feedback_path.exists():
        try:
            feedback_count = sum(1 for _ in feedback_path.open(encoding="utf-8"))
        except Exception:
            pass

    result = {
        "total_size": total_size,
        "directories": dirs,
        "databases": {
            "metrics.db": {
                "path": str(metrics_db),
                "size": metrics_db.stat().st_size if metrics_db.exists() else 0,
                "tables": _sqlite_tables(metrics_db),
            },
            "agent_traces.db": {
                "path": str(traces_db),
                "size": traces_db.stat().st_size if traces_db.exists() else 0,
                "tables": _sqlite_tables(traces_db),
            },
        },
        "cache": {
            "entries": cache_stats.get("entries", 0),
            "hit_rate": cache_stats.get("hit_rate", "0%"),
            "tokens_saved": cache_stats.get("total_saved_tokens", 0),
        },
        "feedback_count": feedback_count,
    }
    _rcache.set("storage_overview", result)
    return result


# === Helpers ===

def _list_workflows() -> list[dict]:
    workflows = []
    for f in sorted(STRUCTURED_DIR.glob("workflow_*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            workflows.append({
                "workflow_id": data.get("workflow_id"),
                "name": data.get("name"),
                "category": data.get("category"),
                "total_pages": data.get("total_pages", len(data.get("steps", []))),
            })
        except Exception:
            pass
    return workflows


def _load_workflow(workflow_id: str) -> dict:
    for f in STRUCTURED_DIR.glob("workflow_*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        if data.get("workflow_id") == workflow_id:
            return data
    raise FileNotFoundError(f"Workflow not found: {workflow_id}")


def _get_vram_info() -> dict:
    """Get GPU VRAM usage from background monitor cache."""
    return _vram_cache


def _get_model_info() -> dict:
    """Get loaded model information from Ollama."""
    try:
        import ollama
        client = ollama.Client(host=OLLAMA_HOST)
        resp = client.list()
        models = {}
        raw_models = resp.models if hasattr(resp, 'models') else resp.get("models", [])
        for m in raw_models:
            d = m.model_dump() if hasattr(m, 'model_dump') else (m if isinstance(m, dict) else {})
            name = d.get("model", d.get("name", ""))
            size_gb = (d.get("size", 0) or 0) / 1e9
            models[name] = {"size_gb": round(size_gb, 1)}
        return models
    except Exception:
        return {}


def _render_dashboard() -> str:
    """Render the full 5-tab showcase dashboard."""
    from webapp.dashboard import render_dashboard
    playgrounds = generator.list_generated()
    workflows = _list_workflows()
    cache_stats = generator.cache.stats()
    rag_stats = rag_store.stats()
    return render_dashboard(
        playgrounds=playgrounds,
        workflows=workflows,
        cache_stats=cache_stats,
        rag_stats=rag_stats,
        generator_model=GENERATOR_MODEL,
        router_model=ROUTER_MODEL,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("webapp.app:app", host=APP_HOST, port=APP_PORT, reload=(APP_ENV == "development"))
