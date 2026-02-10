# Enterprise Playground

## Project Overview
TD Banking workflow scraper, playground generator, and fine-tuning pipeline. Dual-model architecture optimized for RTX 4090 16GB VRAM.

## Tech Stack
- **Language**: Python 3.11+
- **Framework**: FastAPI + Uvicorn
- **Scraping**: Playwright + BeautifulSoup4 + lxml
- **LLM**: Ollama (Qwen2.5-Coder:14B generator + Qwen2.5:3b router)
- **RAG**: ChromaDB (embedded) + nomic-embed-text (Ollama, CPU-only)
- **Fine-tuning**: PyTorch + HuggingFace Transformers + PEFT/LoRA
- **Database**: SQLite (cache + metrics)
- **Deployment**: Docker + Docker Compose + RunPod (GPU)

## Architecture
```
scraper/          - TD Banking website scraper (Playwright-based)
  td_scraper.py   - Main scraper with screenshot capture
  workflow_mapper.py - Maps scraped data to workflow schemas
playground/       - Interactive playground generator
  router.py       - Request routing (3B model)
  generator.py    - HTML/CSS/JS generation (14B model) + RAG integration
  cache.py        - Response caching with similarity matching
  rag.py          - RAG pipeline (ChromaDB + nomic-embed-text)
  metrics.py      - Generation metrics collector (SQLite)
  templates/      - Jinja2 base templates
webapp/           - FastAPI web application
  app.py          - Main app entry point + RAG/metrics API endpoints
  dashboard.py    - 5-tab showcase dashboard renderer
workflows/        - Workflow definitions and schemas
  schema.py       - Pydantic models for workflow data
fine_tuning/      - LoRA fine-tuning pipeline
  prepare_dataset.py - Dataset preparation from scraped data
  train_lora.py   - LoRA training script
  merge_adapter.py - Adapter merging for deployment
deployment/       - Docker and RunPod configs
scripts/          - CLI entry points
config.py         - Central configuration (all env vars)
```

## Commands
- `python scripts/run.py` - Start the application
- `python scripts/quickstart.py` - Quick setup and launch
- `pip install -r requirements.txt` - Install dependencies
- `playwright install` - Install browser drivers
- `docker compose -f deployment/docker-compose.yml up` - Run via Docker

## Dual-Model Architecture
- **Generator** (qwen2.5-coder:14b): HTML/CSS/JS generation, ~8.5GB VRAM
- **Router** (qwen2.5:3b): Classification, routing, summaries, ~2GB VRAM
- Total: ~10.5GB VRAM, leaves ~5.5GB for KV cache on RTX 4090

## Rules
- MUST use async/await for all I/O operations
- MUST use Pydantic models for data validation
- MUST use environment variables for all configuration (see config.py)
- MUST respect SCRAPE_DELAY between requests to td.com
- MUST use the Router model for classification tasks, Generator model for code generation
- NEVER hardcode API keys or credentials
- NEVER commit .env files
- NEVER exceed 16GB VRAM budget in model loading
- NEVER scrape without respecting robots.txt and rate limits

## Testing
- Run tests with: `pytest`
- Use `httpx.AsyncClient` for API endpoint tests
- Use Playwright fixtures for scraper tests

## Environment Variables
All configuration is centralized in `config.py`. Copy `.env.example` to `.env` and customize. Key vars:
- `OLLAMA_HOST` - Ollama server URL
- `GENERATOR_MODEL` / `ROUTER_MODEL` - Model names
- `APP_PORT` - Web server port (default 8000)
- `TD_BASE_URL` - Scraping target base URL

## Dashboard Tabs (7-Tab Architecture)

### Tab 1: Generate
Primary UI for creating playgrounds with SSE streaming. User enters prompt + style, calls `/api/generate/stream`. Shows real-time chunk streaming, RAG context panel, recent playgrounds table, and stats cards.

### Tab 2: Gallery
Visual grid of all generated playgrounds (50 most recent). Each card shows live iframe preview (35% scale), prompt, model, file size, date, and badges (CACHE, RAG:N). Filterable by style.

### Tab 3: Pipeline Visualizer
6-phase ML pipeline flowchart (Scrape → Map → Store/RAG → Route → Generate → Cache → Fine-Tune). Fetches `/api/pipeline/status` for live phase counts.

### Tab 4: Data & RAG
Left: RAG pipeline controls (ingest, clear, rebuild, query tester). Right: Workflow browser + training dataset stats (JSONL). Prepare dataset button creates 90/10 train/val split.

### Tab 5: ML Metrics
Model comparison (14B vs 3B), metrics grid (generations, cache rate, latency), real-time VRAM gauge (nvidia-smi), fine-tuning status (QLoRA config), recent activity log (15 latest).

### Tab 6: ML Observatory (4 sub-panels)
- **6A RAG & Chunking**: Chunk analytics, size distribution, per-workflow breakdown, chunk browser with similarity finder
- **6B Training Lifecycle**: Status, progress bar, dataset quality distribution, loss curve (SVG), training examples browser
- **6C Adapter Registry**: LoRA adapter cards (status, size, rank, checkpoints, deploy button)
- **6D Pipeline Diagram**: Mermaid flowchart of full QLoRA pipeline with hover tooltips

### Tab 7: Agent (Observability)
Runtime pipeline observability showing how each request flows through the agent:
- **Top Stats**: Total traces, avg latency, cache hit rate, avg confidence, tokens saved, last 24h count
- **Latest Trace Timeline**: Visual step-by-step trace (route → cache_check → rag_query → compress → generate → cache_store) with per-step latency bars and expandable JSON metadata
- **Model Distribution**: Bar chart of 14B/3B/Cache usage percentages
- **Router Method**: Breakdown of keyword (0 tokens) vs LLM 3B (~50 tokens) vs force/stream
- **Step Latency Breakdown**: Per-step avg latencies as horizontal bar chart
- **Token Economy**: Input/output/saved token grid with efficiency breakdown
- **Trace History**: Sortable table of 30 recent traces (time, prompt, type, router, model, steps, latency, RAG, cache)

**Data flow**: Generator pipeline → Agent Tracer (`agent_tracer.py`) → SQLite (`cache/agent_traces.db`) → `/api/agent/stats` + `/api/agent/traces` → Tab 7 JS

## RAG & Embeddings Pipeline

### Files
- **RAG logic**: `playground/rag.py` — `RAGStore` class that handles ingestion, querying, and collection management
- **Vector store**: `.chroma/` — ChromaDB `PersistentClient` directory (SQLite + parquet HNSW index files)
- **Embedding model**: `nomic-embed-text` (137M params, CPU-only, zero VRAM) via Ollama
- **Collection name**: `td_workflows` (configurable via `RAG_COLLECTION` env var)

### Source Data
- **Raw HTML**: `workflows/raw/*.html` — scraped TD pages
- **Structured JSON**: `workflows/structured/workflow_*.json` — mapped by `workflow_mapper.py`

### How Ingestion Works (triggered by Tab 4 "Ingest" → `POST /api/rag/ingest`)
1. `ingest_workflows()` reads each `workflow_*.json`, creates an **overview chunk** (name, category, description, tags) + **per-step chunks** (title, URL, action, outcome, form fields), embeds via `ollama.embed(model="nomic-embed-text")`, upserts into ChromaDB with cosine similarity
2. `ingest_scraped_pages()` reads each `raw/*.html`, strips nav/footer/scripts via BeautifulSoup, creates a text summary (max 2000 chars), embeds and upserts

### How Querying Works (triggered on every generation request from Tab 1)
1. User prompt is embedded via the same `nomic-embed-text` model
2. ChromaDB cosine-similarity search returns `top_k` (default 3) nearest chunks
3. Chunks are injected as context into the 14B generator prompt

### RAGStore Methods
| Method | Trigger | Purpose |
|---|---|---|
| `ingest_workflows()` | `POST /api/rag/ingest` | Embed structured workflow JSONs |
| `ingest_scraped_pages()` | `POST /api/rag/ingest` | Embed raw scraped HTML |
| `query(prompt, top_k)` | Every `/api/generate/stream` call | Retrieve relevant context chunks |
| `clear()` | Tab 4 "Clear" button | Delete entire ChromaDB collection |
| `stats()` | Tab 4 + dashboard | Collection count, model info, chroma path |
| `get_all_chunks()` | Tab 6A chunk browser | Paginated chunk listing |
| `get_chunk_analytics()` | Tab 6A analytics | Size histogram, per-workflow breakdown |
| `find_similar_chunks()` | Tab 6A similarity finder | Near-duplicate detection via re-query |

### Data Flow
```
workflows/raw/*.html          ─┐
                                ├─→ rag.py (chunk + embed) ─→ .chroma/ (vectors + metadata)
workflows/structured/*.json   ─┘                                    │
                                                                    ▼
User prompt (Tab 1) ──→ rag.py.query() ──→ cosine search .chroma/ ──→ top-k chunks ──→ generator context
```

## Workflow Categories
Accounts, Credit Cards, Mortgages, Personal Loans, Investing, Insurance - each with dedicated URL mappings in config.py
