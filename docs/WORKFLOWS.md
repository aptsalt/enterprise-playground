# Enterprise Playground — Complete Workflow Reference

Every user action mapped end-to-end: **UI interaction → API route → processing pipeline → data store → output**.

---

## Table of Contents

- [System Flow Overview](#system-flow-overview)
- [1. Generate Playground (Prompt → HTML)](#1-generate-playground-prompt--html)
- [2. Generate Playground (SSE Streaming)](#2-generate-playground-sse-streaming)
- [3. Generate from Workflow](#3-generate-from-workflow)
- [4. Chat / Ask a Question](#4-chat--ask-a-question)
- [5. View Playground](#5-view-playground)
- [6. Browse Gallery](#6-browse-gallery)
- [7. Scrape TD.com Pages](#7-scrape-tdcom-pages)
- [8. Map Scraped Pages to Workflows](#8-map-scraped-pages-to-workflows)
- [9. RAG Ingest (Embed Workflows)](#9-rag-ingest-embed-workflows)
- [10. RAG Query (Test Retrieval)](#10-rag-query-test-retrieval)
- [11. RAG Clear & Rebuild](#11-rag-clear--rebuild)
- [12. Cache Management](#12-cache-management)
- [13. Prepare Fine-Tuning Dataset](#13-prepare-fine-tuning-dataset)
- [14. Train LoRA Adapter (Fine-Tune)](#14-train-lora-adapter-fine-tune)
- [15. Merge & Deploy Fine-Tuned Model](#15-merge--deploy-fine-tuned-model)
- [16. Pipeline Visualizer](#16-pipeline-visualizer)
- [17. ML Metrics Dashboard](#17-ml-metrics-dashboard)
- [18. Health Monitoring & VRAM](#18-health-monitoring--vram)
- [19. Customize Playground (Control Panel)](#19-customize-playground-control-panel)
- [20. Export CSS](#20-export-css)
- [Data Store Reference](#data-store-reference)
- [Complete API Endpoint Map](#complete-api-endpoint-map)

---

## System Flow Overview

```
User Action (Browser / CLI)
        |
        v
   FastAPI Server (webapp/app.py)
        |
        +-------> Smart Router (playground/router.py)
        |              |
        |         Keyword match? ─── Yes ──> Route decision (0 tokens)
        |              |
        |              No
        |              |
        |         3B LLM classify (~50 tokens)
        |              |
        |         +----+----+
        |         |         |
        |     Code task   Text task
        |         |         |
        |         v         v
        |    Cache check   3B direct response
        |     (cache.py)    (router.py)
        |      |     |
        |     HIT   MISS
        |      |     |
        |      |     v
        |      |   RAG query (rag.py → ChromaDB)
        |      |     |
        |      |     v
        |      |   3B compress context (router.py)
        |      |     |
        |      |     v
        |      |   14B generate HTML (generator.py → Ollama)
        |      |     |
        |      v     v
        |   Return HTML
        |      |
        |      v
        +-- Save to disk (playground/generated/*.html)
        +-- Store in cache (.cache/index.json)
        +-- Record metrics (SQLite: .metrics/metrics.db)
        +-- SSE stream to browser
```

---

## 1. Generate Playground (Prompt → HTML)

**What**: User types a prompt, clicks Generate, receives a self-contained HTML playground.

### UI Action
- **Tab**: Generate (Tab 1)
- **Input**: Text prompt in `#prompt-input`, style dropdown (`banking`, `default`, `minimal`, `dark`)
- **Button**: "Generate" button triggers `generate()` JS function

### Data Flow

```
Browser                           Server                              Data Stores
───────                           ──────                              ───────────
Click "Generate"
    |
    ├─ POST /api/generate ──────> app.py:api_generate()
    |                                 |
    |                                 ├─ generator.generate()
    |                                 |       |
    |                                 |       ├─ router.route(prompt)
    |                                 |       |       |
    |                                 |       |       ├─ _keyword_classify()     ─── 0 tokens
    |                                 |       |       └─ OR _llm_classify()      ─── 3B: ~50 tokens
    |                                 |       |
    |                                 |       ├─ [If GENERATE/MODIFY]:
    |                                 |       |       |
    |                                 |       |       ├─ cache.get(prompt, style)
    |                                 |       |       |       |
    |                                 |       |       |       ├─ HIT ────────────── .cache/index.json (read)
    |                                 |       |       |       └─ MISS
    |                                 |       |       |
    |                                 |       |       ├─ rag.query(prompt)       ─── ChromaDB (.chroma/)
    |                                 |       |       |
    |                                 |       |       ├─ router.enrich_prompt()  ─── 3B: ~150 tokens
    |                                 |       |       |
    |                                 |       |       ├─ ollama.chat(14B)        ─── 14B: ~4000 tokens
    |                                 |       |       |
    |                                 |       |       ├─ _extract_content()
    |                                 |       |       |
    |                                 |       |       ├─ SAVE ──────────────────── playground/generated/{id}.html
    |                                 |       |       ├─ SAVE ──────────────────── playground/generated/{id}.meta.json
    |                                 |       |       ├─ cache.put() ───────────── .cache/index.json (write)
    |                                 |       |       └─ metrics.record() ──────── .metrics/metrics.db (SQLite)
    |                                 |       |
    |                                 |       ├─ [If EXPLAIN/CHAT/SUMMARIZE]:
    |                                 |       |       └─ router.handle_light_task() ── 3B: ~300 tokens
    |                                 |       |
    |                                 |       └─ Return result
    |                                 |
    |  <── JSON: {playground_id, text, task_type, metadata}
    |
    ├─ window.open('/playground/{id}')
    └─ Reload dashboard
```

### Files Touched
| File | Role |
|------|------|
| `webapp/app.py:78-98` | API handler |
| `playground/router.py` | Classify + compress |
| `playground/generator.py` | Generate + extract HTML |
| `playground/cache.py` | Cache lookup/store |
| `playground/rag.py` | Vector search |
| `playground/metrics.py` | Record stats |
| `playground/template.py` | Wrap HTML in control panel framework |

### Data Written
| Store | Path | Format |
|-------|------|--------|
| Playground HTML | `playground/generated/pg-{slug}-{hash}.html` | Self-contained HTML |
| Playground Metadata | `playground/generated/pg-{slug}-{hash}.meta.json` | JSON |
| Cache Index | `.cache/index.json` | JSON (entries array) |
| Metrics DB | `.metrics/metrics.db` | SQLite row in `generation_metrics` |

---

## 2. Generate Playground (SSE Streaming)

**What**: Same as Generate, but with real-time token streaming visible in the browser.

### UI Action
- **Tab**: Generate (Tab 1)
- **Same input as above**, but triggers `generate()` which uses the streaming endpoint
- **Stream panel** (`#stream-output`) shows tokens arriving in real-time

### Data Flow

```
Browser                           Server                              Ollama
───────                           ──────                              ──────
POST /api/generate/stream ──────> app.py:api_generate_stream()
    |                                 |
    |                                 ├─ generator.generate_stream()
    |                                 |       |
    |                                 |       ├─ route() → classify
    |                                 |       ├─ cache.get() → check
    |                                 |       ├─ rag.query() → context
    |                                 |       |
    |  <── SSE: {"type":"status","message":"Routing..."}
    |  <── SSE: {"type":"status","message":"Generating with 14B..."}
    |  <── SSE: {"type":"rag","chunks":3,"preview":[...]}
    |                                 |
    |                                 ├─ ollama.chat(stream=True)
    |                                 |       |
    |  <── SSE: {"type":"chunk","content":"<!DOCTYPE..."} ◄── Token by token
    |  <── SSE: {"type":"chunk","content":"<div class..."} ◄── from Ollama
    |  ...  (repeats for each token batch)
    |                                 |
    |                                 ├─ _extract_content() + save
    |                                 |
    |  <── SSE: {"type":"done","playground_id":"pg-...","size":24567,"latency_ms":8234}
    |
    ├─ window.open('/playground/{id}')
    └─ setTimeout(reload, 2000)
```

### SSE Event Types
| Event | Payload | When |
|-------|---------|------|
| `status` | `{message: "..."}` | Routing, cache check, RAG query |
| `rag` | `{chunks: N, preview: [...]}` | After RAG retrieval |
| `cache_hit` | `{playground_id, similarity}` | Cache hit found |
| `chunk` | `{content: "..."}` | Each token batch from 14B |
| `done` | `{playground_id, size, latency_ms}` | Generation complete |
| `error` | `{message: "..."}` | On failure |

---

## 3. Generate from Workflow

**What**: One-click playground generation from a saved workflow definition.

### UI Action
- **Tab**: Data & RAG (Tab 4)
- **Element**: Workflow card → "Generate" button
- **Trigger**: `generateFromWorkflow(workflow_id)` JS function

### Data Flow

```
Browser                           Server                              Data Stores
───────                           ──────                              ───────────
Click workflow "Generate"
    |
    ├─ POST /api/generate/workflow
    |   body: {"workflow_id": "wf-accounts-20260208"}
    |                                 |
    |                                 ├─ app.py:api_generate_from_workflow()
    |                                 |       |
    |                                 |       ├─ _load_workflow(id)  ─────── workflows/structured/workflow_*.json
    |                                 |       |
    |                                 |       ├─ generator.generate_from_workflow()
    |                                 |       |       |
    |                                 |       |       ├─ Build prompt from workflow steps
    |                                 |       |       ├─ Inject workflow context
    |                                 |       |       ├─ Route → GENERATE (forced)
    |                                 |       |       ├─ 14B generation
    |                                 |       |       └─ Save + cache + metrics
    |                                 |       |
    |  <── JSON: {playground_id, metadata}
    |
    └─ window.open('/playground/{id}')
```

### Files Read
| Store | Path |
|-------|------|
| Workflow Definition | `workflows/structured/workflow_{category}_{date}.json` |

### Files Written
Same as Generate (playground HTML, metadata, cache, metrics).

---

## 4. Chat / Ask a Question

**What**: User sends a text message, 3B model responds directly (no HTML generation).

### UI Action
- **Tab**: Generate (Tab 1) — prompt input can also trigger chat
- **Trigger**: `POST /api/chat` when router classifies as EXPLAIN/CHAT/SUMMARIZE

### Data Flow

```
Browser                           Server                              Model
───────                           ──────                              ─────
POST /api/chat
  body: {"message": "What is a TFSA?"}
    |
    |  ──────────────────────────> app.py:api_chat()
    |                                 |
    |                                 ├─ generator.generate(prompt=message)
    |                                 |       |
    |                                 |       ├─ router.route() → EXPLAIN (3B)
    |                                 |       |
    |                                 |       └─ router.handle_light_task()
    |                                 |               |
    |                                 |               └─ ollama.chat(3B)  ─── ~300 tokens
    |                                 |
    |  <── JSON: {"type":"text","response":"A TFSA is..."}
    |
    └─ Display in chat area
```

### Data Written
| Store | What |
|-------|------|
| Metrics DB | Row with `task_type=EXPLAIN`, `model=qwen2.5:3b` |

No HTML is generated. No cache entry is created.

---

## 5. View Playground

**What**: User opens a previously generated playground in a new tab.

### UI Action
- **Tab**: Generate (click table row) or Gallery (click card)
- **Trigger**: `window.open('/playground/{id}', '_blank')`

### Data Flow

```
Browser                           Server                              File System
───────                           ──────                              ───────────
GET /playground/pg-mortgage-a1b2c3d4
    |
    |  ──────────────────────────> app.py:view_playground()
    |                                 |
    |                                 ├─ Read file ──────── playground/generated/pg-mortgage-a1b2c3d4.html
    |                                 |
    |  <── HTMLResponse (full playground with control panel)
    |
    └─ Render interactive playground
        ├─ Control Panel (left sidebar)
        ├─ Preview area (main content)
        ├─ Device switcher (desktop/tablet/mobile)
        └─ Health polling (every 10s → /api/health, /api/stats)
```

---

## 6. Browse Gallery

**What**: User browses grid of all generated playgrounds with thumbnail previews.

### UI Action
- **Tab**: Gallery (Tab 2)
- **Filter buttons**: All, Banking, Default, Minimal, Dark
- **Trigger**: `filterGallery(style)` JS function

### Data Flow

```
Browser                           Server
───────                           ──────
Page Load (GET /)
    |
    |  ──────────────────────────> app.py:home() → _render_dashboard()
    |                                 |
    |                                 ├─ generator.list_generated()
    |                                 |       |
    |                                 |       └─ Read all *.meta.json ── playground/generated/*.meta.json
    |                                 |
    |  <── HTML with gallery cards (last 50 playgrounds)
    |
    ├─ Each card renders <iframe> thumbnail (scaled 0.35x)
    └─ Click card → window.open('/playground/{id}')

Filter (client-side only):
    ├─ filterGallery('banking')
    └─ Show/hide cards by data-style attribute (no API call)
```

---

## 7. Scrape TD.com Pages

**What**: Capture HTML, screenshots, and structured data from TD.com banking pages.

### UI/CLI Action
- **CLI**: `python scripts/run.py scrape [--category accounts] [--url /path]`
- No web UI trigger (CLI only)

### Data Flow

```
CLI                               Scraper                             File System
───                               ───────                             ───────────
run.py scrape --category accounts
    |
    ├─ TDScraper.start()
    |       |
    |       └─ Launch headless Chromium (Playwright)
    |
    ├─ For each URL in config.WORKFLOW_CATEGORIES[category]:
    |       |
    |       ├─ scraper.capture_page(url)
    |       |       |
    |       |       ├─ Navigate to td.com page
    |       |       ├─ Wait for networkidle
    |       |       ├─ _dismiss_overlays()  (cookie banners, modals)
    |       |       ├─ _extract_structured_data()
    |       |       |       |
    |       |       |       ├─ Parse: title, meta, headings, breadcrumbs
    |       |       |       ├─ Parse: links (CTAs), buttons, forms, fields
    |       |       |       ├─ Parse: sections, cards, navigation
    |       |       |       └─ Return structured JSON
    |       |       |
    |       |       ├─ Take screenshot ──────────── workflows/screenshots/{slug}.png
    |       |       ├─ Save raw HTML ────────────── workflows/raw/{slug}.html
    |       |       └─ Save structured JSON ─────── workflows/structured/{slug}.json
    |       |
    |       └─ Sleep(SCRAPE_DELAY_SECONDS)
    |
    └─ TDScraper.stop()  (close browser)
```

### Data Written
| Store | Path | Format | Contents |
|-------|------|--------|----------|
| Raw HTML | `workflows/raw/{slug}.html` | HTML | Full page source |
| Screenshot | `workflows/screenshots/{slug}.png` | PNG | Full-page capture |
| Structured Data | `workflows/structured/{slug}.json` | JSON | title, forms, cards, CTAs, sections |

### Category URL Map (from config.py)
| Category | Example URLs |
|----------|-------------|
| Accounts | `/banking/accounts/chequing`, `/banking/accounts/savings` |
| Credit Cards | `/banking/credit-cards/view-all`, `/banking/credit-cards/cash-back` |
| Mortgages | `/banking/mortgages`, `/banking/mortgages/mortgage-rates` |
| Loans | `/banking/personal-loans/personal-line-of-credit` |
| Investing | `/investing/direct-investing`, `/investing/tfsa` |
| Insurance | `/insurance/home-insurance`, `/insurance/auto-insurance` |

---

## 8. Map Scraped Pages to Workflows

**What**: Convert raw scraped page JSONs into structured workflow definitions with steps.

### CLI Action
- **CLI**: `python scripts/run.py map [--category accounts] [--use-llm]`

### Data Flow

```
CLI                               Mapper                              Data Stores
───                               ──────                              ───────────
run.py map --use-llm
    |
    ├─ workflow_mapper.load_captured_pages()
    |       └─ Read all *.json ──────────── workflows/structured/*.json
    |
    ├─ workflow_mapper.group_pages_by_category()
    |       └─ Group pages: {accounts: [...], mortgages: [...], ...}
    |
    ├─ For each category:
    |       |
    |       ├─ [Without --use-llm]:
    |       |       └─ build_workflow_from_pages()
    |       |               |
    |       |               ├─ Sort pages by URL depth
    |       |               ├─ Infer user actions:
    |       |               |   ├─ Has forms? → "Fill out application form"
    |       |               |   ├─ Has cards? → "Browse and compare products"
    |       |               |   ├─ Has CTAs? → "Click to proceed"
    |       |               |   └─ Default → "Navigate and explore"
    |       |               └─ Build step sequence
    |       |
    |       ├─ [With --use-llm]:
    |       |       └─ build_workflow_with_llm()
    |       |               |
    |       |               ├─ Summarize pages for 3B context
    |       |               ├─ Prompt 3B: "Create workflow JSON" ──── 3B: ~500 tokens
    |       |               └─ Parse JSON from response
    |       |
    |       └─ Save workflow ────────────── workflows/structured/workflow_{cat}_{date}.json
```

### Workflow JSON Output
```json
{
    "workflow_id": "wf-accounts-20260208",
    "name": "Bank Accounts Workflow",
    "category": "accounts",
    "description": "User journey through TD bank accounts",
    "entry_point": "https://www.td.com/.../bank-accounts",
    "steps": [
        {
            "step_number": 1,
            "page_capture": { "url": "...", "title": "...", "sections": [...] },
            "user_action": "Browse and compare account types",
            "expected_outcome": "User selects account type",
            "next_step_trigger": "Click 'Learn More'"
        }
    ],
    "tags": ["accounts", "td-bank"],
    "created_at": "2026-02-08T..."
}
```

---

## 9. RAG Ingest (Embed Workflows)

**What**: Embed all workflow definitions and scraped pages into ChromaDB for semantic retrieval.

### UI Action
- **Tab**: Data & RAG (Tab 4)
- **Button**: "Ingest Workflows" button
- **Trigger**: `ingestRAG()` JS function

### Data Flow

```
Browser                           Server                              Data Stores
───────                           ──────                              ───────────
Click "Ingest Workflows"
    |
    ├─ POST /api/rag/ingest ────> app.py:api_rag_ingest()
    |                                 |
    |                                 ├─ rag_store.ingest_workflows()
    |                                 |       |
    |                                 |       ├─ For each workflow JSON:        ── workflows/structured/workflow_*.json
    |                                 |       |       |
    |                                 |       |       ├─ Chunk 1: Overview
    |                                 |       |       |   "Workflow: Bank Accounts\n
    |                                 |       |       |    Category: accounts\n
    |                                 |       |       |    Description: ...\n
    |                                 |       |       |    Tags: accounts, td-bank"
    |                                 |       |       |
    |                                 |       |       ├─ Chunk 2+: Each step
    |                                 |       |       |   "Step 1: Bank Accounts page\n
    |                                 |       |       |    URL: ...\n
    |                                 |       |       |    Action: Browse products\n
    |                                 |       |       |    Form fields: name, email..."
    |                                 |       |       |
    |                                 |       |       └─ Embed via nomic-embed-text ─── Ollama (CPU)
    |                                 |       |               |
    |                                 |       |               └─ Upsert to ChromaDB ── .chroma/ (persistent)
    |                                 |       |
    |                                 |       └─ Return {workflows_ingested, chunks_added}
    |                                 |
    |                                 ├─ rag_store.ingest_scraped_pages()
    |                                 |       |
    |                                 |       ├─ For each raw HTML file:        ── workflows/raw/*.html
    |                                 |       |       |
    |                                 |       |       ├─ BeautifulSoup parse
    |                                 |       |       ├─ Remove nav/footer/script/style
    |                                 |       |       ├─ Extract text (max 3000 chars)
    |                                 |       |       └─ Embed + upsert to ChromaDB
    |                                 |       |
    |                                 |       └─ Return {pages_ingested}
    |                                 |
    |  <── JSON: {workflows: {...}, pages: {...}}
    |
    └─ Update RAG stats display
```

### Embedding Details
| Component | Value |
|-----------|-------|
| Model | `nomic-embed-text` (137M params) |
| Compute | CPU only (zero VRAM) |
| Vector DB | ChromaDB (persistent, cosine similarity) |
| Storage | `.chroma/` directory |
| Chunk size | Max 2000 chars per chunk |
| Metadata | workflow_id, chunk_type, category, source |

---

## 10. RAG Query (Test Retrieval)

**What**: Test the RAG pipeline by querying ChromaDB and viewing retrieved chunks.

### UI Action
- **Tab**: Data & RAG (Tab 4)
- **Input**: RAG Query Tester text input
- **Button**: "Test" button
- **Trigger**: `testRAG()` JS function

### Data Flow

```
Browser                           Server                              ChromaDB
───────                           ──────                              ────────
Enter "credit card comparison"
Click "Test"
    |
    ├─ POST /api/rag/query
    |   body: {"query": "credit card comparison", "top_k": 5}
    |
    |  ──────────────────────────> app.py:api_rag_query()
    |                                 |
    |                                 ├─ rag_store.query(query, top_k=5)
    |                                 |       |
    |                                 |       ├─ Embed query via nomic-embed-text
    |                                 |       ├─ ChromaDB cosine similarity search ── .chroma/
    |                                 |       └─ Return top-k chunks with distances
    |                                 |
    |  <── JSON: {
    |         query: "credit card comparison",
    |         chunks: [
    |           {content: "Workflow: Credit Cards...", metadata: {...}, distance: 0.12},
    |           {content: "Step 1: View all cards...", metadata: {...}, distance: 0.18},
    |           ...
    |         ],
    |         count: 5
    |       }
    |
    └─ Display chunks in results panel
```

---

## 11. RAG Clear & Rebuild

**What**: Wipe the ChromaDB collection and re-embed from scratch.

### UI Action
- **Tab**: Data & RAG (Tab 4)
- **Button**: "Clear & Rebuild"
- **Trigger**: `clearRAG()` JS function

### Data Flow

```
Browser                           Server                              ChromaDB
───────                           ──────                              ────────
Click "Clear & Rebuild"
    |
    ├─ POST /api/rag/clear ─────> app.py:api_rag_clear()
    |                                 |
    |                                 ├─ rag_store.clear()
    |                                 |       |
    |                                 |       ├─ client.delete_collection("td_workflows")
    |                                 |       └─ Reset _collection = None
    |                                 |
    |  <── JSON: {"status": "cleared"}
    |
    └─ User should then click "Ingest Workflows" to rebuild
```

### Storage Impact
| Before | After |
|--------|-------|
| `.chroma/` has embedded vectors | `.chroma/` collection deleted |
| N chunks in memory | 0 chunks, collection auto-recreated on next query |

---

## 12. Cache Management

**What**: View cache statistics or clear the semantic cache.

### UI Actions

#### View Stats
- **Tab**: Generate (Tab 1) — stats cards show cache hits, tokens saved
- **CLI**: `python scripts/run.py cache-stats`
- **API**: Cache stats included in `GET /api/stats`

#### Clear Cache
- **Tab**: No direct UI button (API only or CLI)
- **CLI**: `python scripts/run.py cache-clear`
- **API**: `POST /api/cache/clear`

### Data Flow (Clear)

```
CLI / API                         Server                              File System
─────────                         ──────                              ───────────
POST /api/cache/clear ──────────> app.py:clear_cache()
    |                                 |
    |                                 ├─ generator.cache.clear()
    |                                 |       |
    |                                 |       ├─ Delete .cache/index.json
    |                                 |       └─ Reset in-memory entries
    |                                 |
    |  <── JSON: {"status": "cleared"}
```

### Cache Internals
| Property | Value |
|----------|-------|
| Storage | `.cache/index.json` |
| Matching | MD5 hash (exact) + SequenceMatcher (fuzzy, threshold 0.85) |
| Normalization | Lowercase, remove filler words, append style |
| Eviction | LRU by `last_hit` + TTL (168 hours / 7 days) |
| Size limit | 500 MB (configurable) |
| Stats tracked | hits, misses, hit_rate, total_saved_tokens |

---

## 13. Prepare Fine-Tuning Dataset

**What**: Convert generated playgrounds into a JSONL training dataset with quality scoring.

### CLI Action
- **CLI**: `python scripts/run.py prepare-data [--min-quality 3] [--format alpaca]`

### Data Flow

```
CLI                               Prepare Script                      File System
───                               ──────────────                      ───────────
run.py prepare-data --min-quality 3
    |
    ├─ prepare_dataset.py
    |       |
    |       ├─ Scan playground/generated/*.meta.json
    |       |
    |       ├─ For each playground:
    |       |       |
    |       |       ├─ Read meta.json ────────── playground/generated/{id}.meta.json
    |       |       ├─ Read HTML ─────────────── playground/generated/{id}.html
    |       |       |
    |       |       ├─ Quality Score (1-5):
    |       |       |   ├─ +1: Base score
    |       |       |   ├─ +1: Valid HTML (has <!DOCTYPE> and </html>)
    |       |       |   ├─ +1: Interactive (onclick, addEventListener, 2+ matches)
    |       |       |   ├─ +1: Styling (Tailwind CDN or <style> block)
    |       |       |   └─ +1: Reasonable size (2KB-50KB)
    |       |       |
    |       |       ├─ [If score >= min_quality]:
    |       |       |       └─ Add to dataset (Alpaca format)
    |       |       |           {
    |       |       |               "instruction": system_prompt,
    |       |       |               "input": original_prompt,
    |       |       |               "output": html_content
    |       |       |           }
    |       |       |
    |       |       └─ [If score < min_quality]: Skip
    |       |
    |       ├─ Shuffle + split (90/10)
    |       ├─ Write train.jsonl ─────────── fine_tuning/data/train.jsonl
    |       └─ Write val.jsonl ───────────── fine_tuning/data/val.jsonl
```

### Output Files
| File | Format | Contents |
|------|--------|----------|
| `fine_tuning/data/train.jsonl` | JSONL (Alpaca) | 90% of quality-filtered examples |
| `fine_tuning/data/val.jsonl` | JSONL (Alpaca) | 10% validation split |

---

## 14. Train LoRA Adapter (Fine-Tune)

**What**: Fine-tune the 14B model on your generated playgrounds using QLoRA.

### CLI Action
- **CLI**: `python scripts/run.py train [--epochs 3] [--use-llamafactory]`
- **Recommended**: Run on cloud GPU (A100 80GB)

### Data Flow

```
Cloud GPU                         Train Script                        File System
─────────                         ────────────                        ───────────
run.py train
    |
    ├─ train_lora.py
    |       |
    |       ├─ Load base model ──────── HuggingFace: Qwen2.5-Coder-14B-Instruct
    |       |       |
    |       |       ├─ 4-bit NF4 quantization (BitsAndBytesConfig)
    |       |       └─ bfloat16 compute type
    |       |
    |       ├─ Apply LoRA adapters:
    |       |       |
    |       |       ├─ Rank: 32
    |       |       ├─ Alpha: 64
    |       |       ├─ Target: q_proj, k_proj, v_proj, o_proj,
    |       |       |          gate_proj, up_proj, down_proj
    |       |       └─ Trainable params: ~200 MB
    |       |
    |       ├─ Load dataset ─────────── fine_tuning/data/train.jsonl
    |       |                           fine_tuning/data/val.jsonl
    |       |
    |       ├─ Train:
    |       |       ├─ Batch size: 2
    |       |       ├─ Gradient accumulation: 8 (effective batch: 16)
    |       |       ├─ Epochs: 3
    |       |       ├─ Learning rate: 1e-4 (cosine scheduler)
    |       |       ├─ Warmup: 3% of steps
    |       |       └─ Optimizer: paged_adamw_32bit
    |       |
    |       ├─ Save checkpoints ────── fine_tuning/adapters/td-playground-lora/checkpoint-*/
    |       └─ Save final adapter ──── fine_tuning/adapters/td-playground-lora/final_adapter/
```

### VRAM Requirements
| Phase | VRAM Needed | Hardware |
|-------|-------------|----------|
| QLoRA training (14B, 4-bit) | ~24 GB | A100 40GB+ |
| Full fine-tune (not recommended) | ~80 GB | A100 80GB |
| Local inference only | ~10.5 GB | RTX 4090 16GB |

---

## 15. Merge & Deploy Fine-Tuned Model

**What**: Merge the LoRA adapter back into the base model and create an Ollama model.

### CLI Action
- **CLI**: `python fine_tuning/merge_adapter.py --adapter <path> --create-ollama`

### Data Flow

```
Local Machine                     Merge Script                        Ollama
─────────────                     ────────────                        ──────
merge_adapter.py --adapter final_adapter --create-ollama
    |
    ├─ Load base model (FP16)
    |       └─ HuggingFace: Qwen2.5-Coder-14B-Instruct
    |
    ├─ Load LoRA adapter ────────── fine_tuning/adapters/td-playground-lora/final_adapter/
    |
    ├─ Merge weights
    |       └─ model.merge_and_unload()
    |
    ├─ Save merged model ────────── fine_tuning/merged/td-playground/
    |
    ├─ [If --create-ollama]:
    |       |
    |       ├─ Create Modelfile:
    |       |   FROM ./fine_tuning/merged/td-playground
    |       |   PARAMETER temperature 0.7
    |       |   SYSTEM "..."
    |       |
    |       └─ ollama create td-playground ─── Register in Ollama
    |
    └─ Update .env:
        GENERATOR_MODEL=td-playground
        |
        └─ Restart: python scripts/run.py serve
```

### Post-Deploy Verification
```
python scripts/run.py status
# Should show: Generator model: td-playground (fine-tuned)
```

---

## 16. Pipeline Visualizer

**What**: Visual flowchart showing all 7 pipeline phases with live counts.

### UI Action
- **Tab**: Pipeline (Tab 3)
- **Auto-refresh**: JS polls `/api/pipeline/status` periodically

### Data Flow

```
Browser                           Server                              Data Stores
───────                           ──────                              ───────────
Tab 3 loaded
    |
    ├─ loadPipeline() JS function
    |       |
    |       └─ GET /api/pipeline/status ─> app.py:api_pipeline_status()
    |                                         |
    |                                         ├─ Count raw HTML files ──── workflows/raw/*.html
    |                                         ├─ Count workflow JSONs ──── workflows/structured/workflow_*.json
    |                                         ├─ RAG chunk count ──────── .chroma/ (ChromaDB)
    |                                         ├─ Total requests routed ── .cache/index.json
    |                                         ├─ Playground count ─────── playground/generated/*.meta.json
    |                                         ├─ Cache entry count ────── .cache/index.json
    |                                         └─ Training file count ──── fine_tuning/data/*.jsonl
    |                                         |
    |  <── JSON: {phases: {
    |         scrape:   {count: 25,  label: "Scraped Pages"},
    |         map:      {count: 6,   label: "Mapped Workflows"},
    |         store:    {count: 42,  label: "RAG Embeddings"},
    |         route:    {count: 150, label: "Requests Routed"},
    |         generate: {count: 87,  label: "Playgrounds Generated"},
    |         cache:    {count: 45,  label: "Cache Entries"},
    |         train:    {count: 2,   label: "Training Files"}
    |       }}
    |
    └─ Update phase count badges in flowchart
```

### 7 Pipeline Phases Displayed
| Phase | Source | Technology |
|-------|--------|------------|
| 1. Scrape | Playwright + BeautifulSoup | Headless Chromium |
| 2. Map | Rule-based + 3B LLM | workflow_mapper.py |
| 3. Store (RAG) | ChromaDB + nomic-embed-text | Vector embeddings |
| 4. Route | Keyword + 3B classifier | router.py |
| 5. Generate | 14B Coder + RAG context | generator.py |
| 6. Cache | Semantic similarity | SequenceMatcher |
| 7. Fine-Tune | QLoRA + PEFT | train_lora.py |

---

## 17. ML Metrics Dashboard

**What**: View model performance, latency, VRAM, and generation activity.

### UI Action
- **Tab**: ML Metrics (Tab 5)
- **Auto-refresh**: JS polls `/api/metrics` and `/api/stats`

### Data Flow

```
Browser                           Server                              SQLite
───────                           ──────                              ──────
Tab 5 loaded → loadMetrics()
    |
    ├─ GET /api/metrics ─────────> app.py:api_metrics()
    |                                 |
    |                                 └─ metrics_collector.get_dashboard_stats()
    |                                         |
    |                                         ├─ SELECT COUNT(*) ──── Total generations
    |                                         ├─ SELECT ... cache_hit ── Cache hit rate
    |                                         ├─ SELECT AVG(latency) ── Avg latency
    |                                         ├─ SELECT SUM(tokens) ── Token totals
    |                                         ├─ SELECT ... GROUP BY model ── Model breakdown
    |                                         ├─ SELECT ... last 24h ── Recent count
    |                                         ├─ SELECT ... vram_snapshots ── Latest VRAM
    |                                         └─ SELECT ... LIMIT 50 ── Recent activity
    |
    |  <── JSON: {
    |         total_generations: 150,
    |         cache_hit_rate: "23.4%",
    |         avg_latency_ms: 8500,
    |         model_breakdown: {
    |             "qwen2.5-coder:14b": {count: 55, avg_latency_ms: 9200},
    |             "qwen2.5:3b": {count: 95, avg_latency_ms: 450}
    |         },
    |         rag_generations: 30,
    |         recent: [{timestamp, prompt, model, latency_ms, cache_hit, ...}, ...]
    |       }
    |
    └─ Render:
        ├─ Model comparison cards (14B vs 3B)
        ├─ Metrics grid (generations, cache rate, latency, RAG)
        ├─ VRAM gauge (conic-gradient ring)
        ├─ Fine-tuning status card
        └─ Recent activity log (scrollable)
```

### SQLite Tables
| Table | Columns | Purpose |
|-------|---------|---------|
| `generation_metrics` | timestamp, prompt, model, task_type, latency_ms, tokens, cache_hit, rag_chunks, playground_id, style, html_size | Per-generation tracking |
| `vram_snapshots` | timestamp, used_mb, total_mb, temp_c, utilization_pct | GPU monitoring |

---

## 18. Health Monitoring & VRAM

**What**: Live model status indicators and GPU memory monitoring.

### UI Action
- **Location**: Top navbar (all tabs)
- **Auto-refresh**: `pollHealth()` every 10 seconds
- **Indicators**: Green/red dots for Generator and Router models, VRAM usage bar

### Data Flow

```
Browser (every 10s)               Server                              System
───────────────────               ──────                              ──────
pollHealth()
    |
    ├─ GET /api/health ──────────> app.py:health()
    |                                 |
    |                                 ├─ ollama.Client.list()
    |                                 |       └─ Check loaded models
    |                                 |
    |  <── JSON: {
    |         generator_ready: true,
    |         router_ready: true,
    |         models_loaded: ["qwen2.5-coder:14b", "qwen2.5:3b"]
    |       }
    |
    ├─ GET /api/stats ───────────> app.py:api_stats()
    |                                 |
    |                                 ├─ _get_vram_info()
    |                                 |       └─ nvidia-smi subprocess
    |                                 |
    |  <── JSON: {
    |         vram: {used_mb: 10500, total_mb: 16384, usage_pct: 64.1, temp_c: 62}
    |       }
    |
    └─ Update UI:
        ├─ Generator dot: green/red
        ├─ Router dot: green/red
        ├─ VRAM bar: width = usage_pct%
        └─ VRAM text: "10.5 / 16.0 GB"
```

---

## 19. Customize Playground (Control Panel)

**What**: Real-time visual customization of generated playgrounds via the left sidebar.

### UI Action
- **Location**: Inside any opened playground (`/playground/{id}`)
- **Panel**: 320px left sidebar with controls
- **All changes are client-side** (CSS variables, no API calls)

### Control Panel Features

```
Control Panel (320px left sidebar)
    |
    ├─ Quick Presets
    |   ├─ Current TD    → --td-primary: #008A4C, --td-accent: #34A853
    |   ├─ Modern        → --td-primary: #2563eb, flat design
    |   ├─ Minimal       → --td-primary: #374151, reduced borders
    |   ├─ Bold          → --td-primary: #dc2626, large typography
    |   ├─ Dark Mode     → --td-bg: #111827, inverted colors
    |   └─ Corporate     → --td-primary: #1e3a5f, serif fonts
    |
    ├─ Brand Colors (color pickers)
    |   ├─ Primary → CSS var --td-primary
    |   ├─ Accent  → CSS var --td-accent
    |   ├─ Background → CSS var --td-bg
    |   └─ Text    → CSS var --td-text
    |
    ├─ Hero Layout
    |   ├─ Default    → .layout-default
    |   ├─ Centered   → .layout-centered
    |   ├─ Split      → .layout-split
    |   └─ Minimal    → .layout-minimal
    |
    ├─ Card Style
    |   ├─ Elevated   → .card-elevated (shadow)
    |   ├─ Bordered   → .card-bordered (border)
    |   ├─ Filled     → .card-filled (background)
    |   └─ Horizontal → .card-horizontal (flex-row)
    |
    ├─ Typography
    |   ├─ System     → system-ui, -apple-system
    |   ├─ Modern     → Inter, Roboto
    |   └─ Classic    → Georgia, serif
    |
    ├─ CTA Style
    |   ├─ Rounded    → border-radius: 8px
    |   ├─ Square     → border-radius: 0
    |   └─ Pill       → border-radius: 9999px
    |
    ├─ Spacing
    |   ├─ Compact    → .spacing-compact (reduced padding)
    |   ├─ Default    → .spacing-default
    |   └─ Spacious   → .spacing-spacious (extra padding)
    |
    ├─ Device Preview
    |   ├─ Desktop    → iframe width: 1280px
    |   ├─ Tablet     → iframe width: 768px
    |   └─ Mobile     → iframe width: 375px
    |
    ├─ Zoom
    |   └─ Slider: 50% - 100%
    |
    └─ Tools
        ├─ Annotations → Toggle element labels overlay
        ├─ A/B Compare → Split view with variation
        ├─ Export CSS  → Modal with custom CSS variables
        └─ Reset       → Revert all customizations
```

### Implementation (No API Calls)
All customization happens via CSS custom properties on the document root:
```javascript
document.documentElement.style.setProperty('--td-primary', '#2563eb');
```

---

## 20. Export CSS

**What**: Export the current customization as a CSS snippet.

### UI Action
- **Location**: Inside playground → Tools → Export CSS
- **Output**: Modal with copyable CSS code

### Data Flow (Client-Side Only)

```
Click "Export CSS"
    |
    ├─ Read current CSS custom properties
    |       getComputedStyle(document.documentElement)
    |
    ├─ Build CSS string:
    |   :root {
    |       --td-primary: #2563eb;
    |       --td-accent: #34a853;
    |       --td-bg: #ffffff;
    |       --td-text: #1f2937;
    |   }
    |
    └─ Display in modal with copy button
```

---

## Data Store Reference

All persistent storage locations:

| Store | Path | Format | Written By | Read By |
|-------|------|--------|------------|---------|
| Raw HTML | `workflows/raw/*.html` | HTML files | Scraper | RAG ingestion |
| Screenshots | `workflows/screenshots/*.png` | PNG images | Scraper | Dashboard (static files) |
| Structured Pages | `workflows/structured/*.json` | JSON | Scraper | Mapper, RAG |
| Workflow Defs | `workflows/structured/workflow_*.json` | JSON | Mapper | Generator, RAG, Dashboard |
| Generated HTML | `playground/generated/*.html` | HTML | Generator | View endpoint, Gallery |
| Playground Meta | `playground/generated/*.meta.json` | JSON | Generator | Dashboard, Stats |
| Cache Index | `.cache/index.json` | JSON | Cache | Cache |
| ChromaDB Vectors | `.chroma/` | Binary (ChromaDB) | RAG ingest | RAG query |
| Metrics DB | `.metrics/metrics.db` | SQLite | MetricsCollector | Metrics API |
| Training Data | `fine_tuning/data/*.jsonl` | JSONL | prepare_dataset.py | train_lora.py |
| LoRA Adapters | `fine_tuning/adapters/` | PyTorch | train_lora.py | merge_adapter.py |
| Merged Model | `fine_tuning/merged/` | HF format | merge_adapter.py | Ollama |

---

## Complete API Endpoint Map

| Method | Path | Tab/Source | Action |
|--------|------|------------|--------|
| `GET` | `/` | — | Render 5-tab dashboard |
| `GET` | `/playground/{id}` | Gallery/Generate | View playground |
| `POST` | `/api/generate` | Generate (Tab 1) | Generate playground (JSON) |
| `POST` | `/api/generate/stream` | Generate (Tab 1) | Generate with SSE streaming |
| `POST` | `/api/generate/workflow` | Data & RAG (Tab 4) | Generate from workflow |
| `POST` | `/api/chat` | Generate (Tab 1) | Chat with 3B router |
| `GET` | `/api/playgrounds` | Gallery (Tab 2) | List all playgrounds |
| `GET` | `/api/workflows` | Data & RAG (Tab 4) | List all workflows |
| `GET` | `/api/stats` | All tabs (navbar) | System stats + VRAM |
| `GET` | `/api/health` | All tabs (navbar) | Model availability |
| `POST` | `/api/cache/clear` | CLI / API | Clear cache |
| `GET` | `/api/rag/stats` | Data & RAG (Tab 4) | ChromaDB stats |
| `POST` | `/api/rag/ingest` | Data & RAG (Tab 4) | Ingest workflows |
| `POST` | `/api/rag/query` | Data & RAG (Tab 4) | Test RAG retrieval |
| `POST` | `/api/rag/clear` | Data & RAG (Tab 4) | Clear ChromaDB |
| `GET` | `/api/metrics` | ML Metrics (Tab 5) | Aggregated metrics |
| `GET` | `/api/pipeline/status` | Pipeline (Tab 3) | Phase counts |
| `GET` | `/api/dataset/stats` | Data & RAG (Tab 4) | Training data stats |

---

## End-to-End Pipeline Summary

```
1. SCRAPE       td.com pages → raw HTML + screenshots + structured JSON
                                    ↓
2. MAP          structured JSON → workflow definitions (step sequences)
                                    ↓
3. EMBED (RAG)  workflows + pages → ChromaDB vectors (nomic-embed-text, CPU)
                                    ↓
4. ROUTE        user prompt → keyword match OR 3B LLM classify → task type
                                    ↓
5. GENERATE     14B model + RAG context → self-contained HTML playground
                                    ↓
6. CACHE        store result → semantic match for future similar prompts
                                    ↓
7. METRICS      log to SQLite → latency, tokens, cache hits, VRAM snapshots
                                    ↓
8. FINE-TUNE    200+ playgrounds → quality score → JSONL → QLoRA → LoRA adapter
                                    ↓
9. DEPLOY       merge adapter → create Ollama model → update config → serve
```
