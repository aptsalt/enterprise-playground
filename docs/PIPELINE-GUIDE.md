# Enterprise Playground — ML Pipeline Guide

## Quick Start

```bash
pip install -r requirements.txt
python scripts/run.py
# Open http://localhost:8002
```

---

## The Big Picture

This app is a **complete local-first ML pipeline** that turns scraped banking websites into fine-tuned LLM adapters — with zero API costs. Everything runs on your RTX 4090.

```
 SCRAPE         MAP           STORE          ROUTE         GENERATE       CACHE          TRAIN
┌──────┐    ┌──────┐    ┌──────────┐    ┌──────┐    ┌──────────┐    ┌──────┐    ┌──────────┐
│ HTML │───>│ JSON │───>│ ChromaDB │───>│ 3B   │───>│ 14B      │───>│ SQLite│───>│ QLoRA    │
│ Pages│    │ Work-│    │ Vectors  │    │Router│    │ Generator │    │ Cache │    │ Fine-Tune│
│  +   │    │ flows│    │  +       │    │      │    │  + RAG    │    │       │    │          │
│ PNG  │    │      │    │ nomic-   │    │Key-  │    │  context  │    │Fuzzy  │    │ LoRA     │
│      │    │      │    │ embed    │    │word  │    │           │    │Match  │    │ Adapter  │
└──────┘    └──────┘    └──────────┘    └──────┘    └──────────┘    └──────┘    └──────────┘
 120 pages   63 flows    303 chunks     0 VRAM      8.5GB VRAM     7-day TTL   rank-32, 4bit
 Playwright  Pydantic    CPU-only       ~50 tok     ~6K tok out    0.85 sim    RTX 4090
```

---

## The 4 Dashboard Tabs Explained

---

### Tab 1: Pipeline (The Map)

**What it shows:** A visual overview of all 7 phases, with live counts.

**Why it matters:** This is your "system architecture at a glance." When presenting to an engineering lead, this tab answers: *"How does the whole thing work end-to-end?"*

```
┌─────────────────────────────────────────────────────────────────┐
│                        PIPELINE TAB                             │
├────────┬────────┬──────────┬────────┬──────────┬───────┬───────┤
│ 1.     │ 2.     │ 3.       │ 4.     │ 5.       │ 6.    │ 7.   │
│ Scrape │ Map    │ Store    │ Route  │ Generate │ Cache │ Train│
│ 120pg  │ 63wf   │ 303 emb  │ 0 req  │ 217 pg   │ 3 ent │ 2 fl│
└────────┴────────┴──────────┴────────┴──────────┴───────┴───────┘
```

**Each phase card shows:**
| Phase | Tool Stack | What Happens |
|-------|-----------|--------------|
| 1. Scrape | Playwright + BeautifulSoup | Headless browser captures TD Banking pages — HTML + screenshots |
| 2. Map | Pydantic + 3B LLM | Raw HTML → structured workflow JSONs with steps, forms, user actions |
| 3. Store (RAG) | ChromaDB + nomic-embed-text | Workflows embedded into vectors. CPU-only, zero VRAM cost |
| 4. Route | Keyword matcher + 3B LLM | Classifies request type. Keywords = 0 tokens, LLM fallback = ~50 tokens |
| 5. Generate | 14B Coder + RAG context | Generates full HTML/CSS/JS playground with injected RAG context |
| 6. Cache | SQLite + SequenceMatcher | Fuzzy matching (0.85 threshold). Skips re-generation for similar prompts |
| 7. Fine-Tune | QLoRA + PEFT | Generated playgrounds become training data → LoRA adapter |

**Implementation:**
- Endpoint: `GET /api/pipeline/status`
- Source: `webapp/app.py:253-274` — aggregates counts from all subsystems
- Each count is pulled live: `RAW_DIR.glob("*.html")`, `STRUCTURED_DIR.glob("workflow_*.json")`, etc.

---

### Tab 2: Data & RAG (The Engine Room)

**What it shows:** Two panels side-by-side — RAG pipeline controls (left) and training data + workflows (right).

**Why it matters:** This is the **operational control center.** You ingest data, test retrieval quality, prepare datasets, and trigger the training pipeline — all from this tab.

```
┌─────────────────────────────┬──────────────────────────────────┐
│     RAG PIPELINE            │   WORKFLOWS & TRAINING DATA      │
│                             │                                  │
│  ┌──────────────────────┐   │   ┌──────────────────────────┐   │
│  │ Vector Store         │   │   │ Training Dataset         │   │
│  │ ChromaDB (embedded)  │   │   │ 2 JSONL Files            │   │
│  │                      │   │   │ 203 Training Examples    │   │
│  │ 303 Embeddings       │   │   └──────────────────────────┘   │
│  │ nomic-embed-text     │   │                                  │
│  │ CPU (0 VRAM)         │   │   ┌──────────────────────────┐   │
│  │                      │   │   │ Workflows (63 total)     │   │
│  │ [Ingest] [Clear]     │   │   │ - Accounts Browse...     │   │
│  └──────────────────────┘   │   │ - Accounts Bundles...    │   │
│                             │   │ - Accounts CDIC...       │   │
│  ┌──────────────────────┐   │   │   [Generate Playground]  │   │
│  │ Full Pipeline Cycle  │   │   └──────────────────────────┘   │
│  │ [Prepare Dataset]    │   │                                  │
│  │ [Train LoRA]         │   │                                  │
│  └──────────────────────┘   │                                  │
│                             │                                  │
│  ┌──────────────────────┐   │                                  │
│  │ Test RAG Retrieval   │   │                                  │
│  │ [query input] [Query]│   │                                  │
│  │ Results: ...         │   │                                  │
│  └──────────────────────┘   │                                  │
└─────────────────────────────┴──────────────────────────────────┘
```

**Key Actions:**

| Button | What It Does | Endpoint |
|--------|-------------|----------|
| Ingest Workflows | Embeds all workflow JSONs + scraped pages into ChromaDB | `POST /api/rag/ingest` |
| Clear & Rebuild | Wipes ChromaDB collection and re-ingests from scratch | `POST /api/rag/clear` |
| Test RAG Query | Sends a natural language query, returns top-K similar chunks | `POST /api/rag/query` |
| Prepare Dataset | Collects generated playgrounds → filters by quality → exports JSONL | `POST /api/dataset/prepare` |
| Train LoRA | Shows the CLI command to run QLoRA fine-tuning | Display only |

**RAG Flow in Detail:**

```
Workflow JSON                                         User Prompt
      │                                                    │
      ▼                                                    ▼
┌─────────────┐                                    ┌──────────────┐
│ Chunk into  │                                    │ Embed query  │
│ sections    │                                    │ with nomic   │
│ (overview,  │                                    └──────┬───────┘
│  steps,     │                                           │
│  metadata)  │                                           ▼
└──────┬──────┘                                    ┌──────────────┐
       │                                           │ Cosine       │
       ▼                                           │ Similarity   │
┌─────────────┐                                    │ Search       │
│ Embed with  │───> ChromaDB Collection <──────────┤ (top-3)      │
│ nomic-embed │     303 vectors stored             └──────┬───────┘
│ (CPU only)  │                                           │
└─────────────┘                                           ▼
                                                   ┌──────────────┐
                                                   │ Inject into  │
                                                   │ 14B prompt   │
                                                   │ as context   │
                                                   └──────────────┘
```

**Implementation:**
- RAG store: `playground/rag.py` — ChromaDB embedded mode, nomic-embed-text via Ollama
- Dataset prep: `fine_tuning/prepare_dataset.py` — quality scoring 1-5, Alpaca format
- Endpoint: `POST /api/dataset/prepare` in `webapp/app.py:299-341`

---

### Tab 3: ML Metrics (The Dashboard)

**What it shows:** Model specs, performance metrics, VRAM usage, and fine-tuning configuration.

**Why it matters:** This answers *"What models are running, how fast are they, and what resources are they consuming?"* — the questions every ML lead asks.

```
┌──────────────────────────────┬──────────────────────────────────┐
│     GENERATOR (14B)          │          ROUTER (3B)             │
│                              │                                  │
│  qwen2.5-coder:14b           │  qwen2.5:3b                      │
│  Role: HTML/CSS/JS gen       │  Role: Classification, Routing   │
│  VRAM: ~8.5 GB (Q4_K_M)     │  VRAM: ~2 GB (Q4)               │
│  Context: 8,192 tokens       │  Context: 2,048 tokens           │
│  Max Output: 6,144 tokens    │  Max Output: 512 tokens          │
│  Temperature: 0.7            │  Temperature: 0.1                │
│  Avg Latency: --ms           │  Avg Latency: --ms               │
└──────────────────────────────┴──────────────────────────────────┘

┌──────────┬───────────┬───────────┬──────────────┐
│ Total    │ Cache Hit │ Avg       │ RAG          │
│ Gens     │ Rate      │ Latency   │ Generations  │
│ 217      │ 0%        │ --ms      │ 0            │
└──────────┴───────────┴───────────┴──────────────┘

┌──────────────────────────────┬──────────────────────────────────┐
│     VRAM USAGE               │     FINE-TUNING STATUS           │
│                              │                                  │
│     ┌────┐                   │  Base Model: Qwen2.5-Coder-14B  │
│     │ 3% │  RTX 4090         │  Method: QLoRA (4-bit, rank-32) │
│     │    │  556 / 16376 MB   │  Training Data: 203 examples    │
│     └────┘  53°C             │  LoRA Rank: 32                  │
│                              │  Batch Size: 2 (eff. 16)        │
│  Budget: 14B (8.5GB)        │  Learning Rate: 1e-4            │
│        + 3B (2GB)           │  Target: RTX 4090 / RunPod      │
│        = 10.5GB             │                                  │
│  Leaves 5.5GB for KV cache  │                                  │
└──────────────────────────────┴──────────────────────────────────┘
```

**Dual-Model Architecture — Why Two Models?**

```
User Request
      │
      ▼
┌─────────────┐     keyword match?     ┌─────────────────────┐
│ Smart Router │────── YES ──────────>  │ Classify instantly  │
│             │                        │ (0 tokens, 0 VRAM)  │
│  Keywords   │                        └──────────┬──────────┘
│  first,     │                                   │
│  LLM        │     no keyword?                   │
│  fallback   │────── THEN ──────>  ┌─────────────┴───────┐
└─────────────┘                     │ 3B Router Model     │
                                    │ ~50 tokens, 2GB     │
                                    │ Classifies: code?   │
                                    │ text? data? etc.    │
                                    └──────────┬──────────┘
                                               │
                              ┌────────────────┴────────────────┐
                              │                                 │
                        code/HTML task                    text/chat task
                              │                                 │
                              ▼                                 ▼
                     ┌────────────────┐                ┌────────────────┐
                     │ 14B Generator  │                │ 3B Router      │
                     │ 8.5GB VRAM     │                │ handles it     │
                     │ Full HTML out  │                │ directly       │
                     └────────────────┘                └────────────────┘
```

**Implementation:**
- Health check: `GET /api/health` in `webapp/app.py:168-199` — checks Ollama model availability
- Stats: `GET /api/stats` — aggregates VRAM (`nvidia-smi`), model info, cache stats
- VRAM: `_get_vram_info()` in `webapp/app.py:437-457` — calls `nvidia-smi --query-gpu`
- Metrics: `playground/metrics.py` — SQLite-backed generation metrics collector

---

### Tab 4: ML Observatory (The Deep Dive)

**What it shows:** Three sub-panels for deep inspection of the ML pipeline internals.

**Why it matters:** This is where you go from "it works" to "I understand exactly why it works." An ML lead will want to inspect chunk quality, training convergence, and adapter readiness.

#### Sub-Panel 1: RAG & Chunking

```
┌──────────┬──────────┬──────────┬──────────┬──────────┐
│ Total    │ Avg Size │ Min Size │ Max Size │ Sources  │
│ Chunks   │          │          │          │          │
│ 303      │ 866 chars│ 56       │ 2000     │ 2        │
└──────────┴──────────┴──────────┴──────────┴──────────┘

┌─────────────────────────────┬──────────────────────────────────┐
│  Chunk Size Distribution    │  Chunks per Workflow             │
│                             │                                  │
│  0-200   ████████████ 137   │  unknown        ██████████ 120   │
│  200-500 █████ 46           │  wf-segments... ██ 10            │
│  500-1K  0                  │  wf-investing.. █ 9              │
│  1K-1.5K 0                  │  wf-general...  █ 8              │
│  1.5K-2K 0                  │  wf-accounts..  █ 7              │
│  2K+     ██████████ 120     │  (more...)                       │
└─────────────────────────────┴──────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  Chunk Browser                              Prev | 1-50 | Next │
│                                                                │
│  #1  [overview] [accounts_browse] 242 chars   [Expand] [Similar]│
│  Workflow: Accounts Browse-All-Bank-Accounts...                │
│                                                                │
│  #2  [step] [accounts_browse] 56 chars        [Expand] [Similar]│
│  Step 1: URL: Action: Fill out form: Yes...                    │
│                                                                │
│  #3  [overview] [accounts_bundles] 174 chars   [Expand] [Similar]│
│  Workflow: Accounts Bundles Workflow Category...                │
└────────────────────────────────────────────────────────────────┘
```

**Key features:**
- **Histogram** shows if chunks are well-distributed or skewed (ideal: even spread)
- **Workflow breakdown** reveals which workflows contribute the most data
- **Expand** shows full chunk content
- **Similar** finds nearest neighbors by cosine distance — reveals duplicates and clusters

**Implementation:**
- Analytics: `GET /api/observatory/chunk-analytics` → `playground/rag.py:get_chunk_analytics()`
- Browse: `GET /api/observatory/chunks?offset=0&limit=50`
- Similar: `POST /api/observatory/similar-chunks` → cosine search within ChromaDB

#### Sub-Panel 2: Training Lifecycle

```
┌────────────────────────────────────────────────────────────────┐
│  ● Idle — No training runs detected                           │
│                                                                │
│  [Prepare Dataset]  [Show Train Command]  [Refresh]           │
└────────────────────────────────────────────────────────────────┘

┌─────────────────────────────┬──────────────────────────────────┐
│  Dataset Quality            │  Loss Curve                      │
│  Distribution               │                                  │
│                             │  (shows when training has run)   │
│  182 train / 21 val         │                                  │
│                             │     Loss                         │
│  Score 1  0                 │  3.0 ┤                           │
│  Score 2  0                 │      │╲                          │
│  Score 3  ██ 10             │  2.0 ┤  ╲                        │
│  Score 4  █ 5               │      │    ╲___                   │
│  Score 5  ██████████ 188    │  1.0 ┤        ╲___________       │
│                             │      └──────────────── Steps     │
│  Avg instruction: 115 chars │                                  │
│  Avg output: 4400 chars     │  ── Train Loss  --- Eval Loss    │
└─────────────────────────────┴──────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  Training Examples                    [train.jsonl ▾] Prev Next│
│                                                                │
│  #1  [Q5]  Instruction: US dollar account overview page...     │
│            Output: <nav class="td-nav">...                     │
│                                                                │
│  #2  [Q5]  Instruction: Trade-marks for TD Aeroplan...         │
│            Output: <section class="td-hero">...                │
└────────────────────────────────────────────────────────────────┘
```

**Training status detection:**
- `idle` — No adapter directories found
- `running` — Python process with `train_lora` detected
- `completed` — `final_adapter/` directory exists
- `interrupted` — Checkpoints exist but no final adapter

**Quality scoring (1-5):**
| Score | Criteria |
|-------|----------|
| 1 | Bare minimum — HTML exists |
| 2 | Some structure (nav, sections) |
| 3 | Uses 3+ TD CSS classes (td-nav, td-hero, product-card, etc.) |
| 4 | 5+ CSS classes + multiple semantic sections |
| 5 | Good size (1K-40K chars) + proper structure + no template leakage |

**Implementation:**
- Status: `GET /api/observatory/training/status` → `playground/observatory.py:get_training_status()`
- Logs: `GET /api/observatory/training/logs` → parses `trainer_state.json` for loss curves
- Analytics: `GET /api/observatory/dataset/analytics` → scans train.jsonl + val.jsonl
- Examples: `GET /api/observatory/training/examples?offset=0&limit=20&file=train`

#### Sub-Panel 3: Adapter Registry

```
┌──────────────────┬──────────────────┬──────────────────┐
│  adapter-v1      │  adapter-v2      │  (empty state)   │
│                  │                  │                  │
│  ● Completed     │  ● Interrupted   │  No adapters yet │
│                  │                  │  Run fine-tuning │
│  Size: 42.5 MB   │  Size: 28.1 MB   │  to create LoRA  │
│  Modified: 2026  │  Modified: 2026  │  adapters        │
│  Base: Qwen2.5   │  Base: Qwen2.5   │                  │
│  Rank: 32        │  Rank: 32        │  [Show Training  │
│  Checkpoints: 3  │  Checkpoints: 1  │   Command]       │
│                  │                  │                  │
│  [Deploy] [Det.] │  [Details]       │                  │
└──────────────────┴──────────────────┴──────────────────┘
```

**What adapters are:**
- LoRA adapters are small (30-50MB) weight matrices that modify the base 14B model's behavior
- They're produced by QLoRA fine-tuning on your generated playground data
- Once trained, they're merged into the base model and loaded via Ollama

**Implementation:**
- List: `GET /api/observatory/adapters` → scans `ADAPTERS_DIR` for directories
- Details: `GET /api/observatory/adapters/{name}` → file listing + trainer state
- Deploy: `POST /api/observatory/adapters/{name}/deploy` → returns merge command

---

## Recommended Build Order

This is the complete pipeline cycle — do this in order the first time, then repeat phases 3-7 as you iterate.

```
    ┌─────┐     ┌─────┐     ┌─────┐     ┌─────┐     ┌─────┐     ┌─────┐     ┌─────┐
    │  1  │────>│  2  │────>│  3  │────>│  4  │────>│  5  │────>│  6  │────>│  7  │
    │SCRAPE│     │ MAP │     │STORE│     │ROUTE│     │ GEN │     │PREP │     │TRAIN│
    └─────┘     └─────┘     └─────┘     └─────┘     └─────┘     └─────┘     └─────┘
       │           │           │           │           │           │           │
       │           │           │           │           │           │           │
       ▼           ▼           ▼           ▼           ▼           ▼           ▼
    120 HTML    63 workflow  303 vector   Classify   217 HTML   203 JSONL   LoRA
    pages       JSONs       embeddings   requests   playgrounds examples   adapter
                                                                    │
                                                                    │
                            ◄───────────── REPEAT ──────────────────┘
                            (re-ingest, generate more, retrain)
```

### Step-by-Step Walkthrough

#### Phase 1: Scrape (one-time setup)
```bash
python -m scraper.td_scraper
```
- Launches Playwright headless browser
- Captures TD Banking pages: HTML + screenshots
- Respects robots.txt and rate limits
- **Output:** `data/raw/*.html` (120 pages)
- **Tab to verify:** Pipeline → Scrape count

#### Phase 2: Map (one-time setup)
```bash
python -m scraper.workflow_mapper
```
- Converts raw HTML into structured workflow JSONs
- Extracts: steps, forms, user actions, categories
- Validates with Pydantic schemas
- **Output:** `data/structured/workflow_*.json` (63 workflows)
- **Tab to verify:** Pipeline → Map count

#### Phase 3: Store / Ingest RAG
**In the dashboard:** Data & RAG tab → click **"Ingest Workflows"**

```
What happens:
  1. Reads all workflow_*.json files
  2. Chunks each workflow into sections (overview, steps, metadata)
  3. Embeds each chunk with nomic-embed-text (CPU, ~137M params)
  4. Stores vectors in ChromaDB (local, embedded mode)

Result: 303 embeddings ready for retrieval
```

- **Tab to verify:** ML Observatory → RAG & Chunking (see histogram, chunk browser)
- **Test it:** Data & RAG → "Test RAG Retrieval" → try "credit card application"

#### Phase 4: Generate Playgrounds
**In the dashboard:** Generate tab → type a prompt → click **"Generate"**

```
What happens:
  1. Router classifies the request (keyword match or 3B fallback)
  2. If code task → RAG retrieves top-3 relevant chunks
  3. 14B model generates HTML/CSS/JS with RAG context injected
  4. Output is saved as a .html file + .meta.json
  5. Cache stores the result for similar future prompts

Result: A live interactive playground at /playground/{id}
```

- **Tab to verify:** Gallery → see iframe preview grid
- **Alternative:** Data & RAG → Workflows → click "Generate Playground" on any workflow

#### Phase 5: Prepare Dataset
**In the dashboard:** Data & RAG tab → **"Prepare Dataset"** button

```
What happens:
  1. Scans all generated playgrounds (*.meta.json + *.html)
  2. Extracts content fragments (not full HTML — just the LLM output)
  3. Scores quality 1-5 based on CSS class usage, structure, size
  4. Filters by minimum quality (default: 2)
  5. Splits into train.jsonl (90%) and val.jsonl (10%)
  6. Saves to data/ directory

Result: 182 train + 21 val examples in Alpaca format
```

- **Tab to verify:** ML Observatory → Training Lifecycle (quality distribution chart)
- **Inspect examples:** ML Observatory → Training Examples browser

#### Phase 6: Fine-Tune (CLI)
```bash
# Local (RTX 4090, ~12GB VRAM needed):
python -m fine_tuning.train_lora --local

# Cloud (RunPod, for full 14B):
python -m fine_tuning.train_lora
```

```
What happens:
  1. Loads base model (Qwen2.5-Coder-14B) in 4-bit quantization
  2. Applies LoRA config (rank-32, alpha-64, target: q_proj, v_proj)
  3. Trains on your playground data for 3 epochs
  4. Saves checkpoints + final adapter to adapters/ directory

Result: A LoRA adapter (~30-50MB) that specializes the model
```

- **Tab to verify:** ML Observatory → Training Lifecycle (loss curve, progress bar)
- **After training:** ML Observatory → Adapter Registry (shows the trained adapter)

#### Phase 7: Deploy Adapter
**In the dashboard:** ML Observatory → Adapter Registry → click **"Deploy"**

```bash
# The shown command:
python -m fine_tuning.merge_adapter --adapter adapters/{name}/final_adapter --create-ollama
```

```
What happens:
  1. Merges LoRA weights into the base model
  2. Converts to GGUF format for Ollama
  3. Creates an Ollama model tag you can use immediately

Result: Your fine-tuned model is now the default generator
```

### Repeat the Cycle

```
After deploying, the loop continues:

  Generate MORE playgrounds (now with your fine-tuned model)
       │
       ▼
  Quality improves → better training data
       │
       ▼
  Prepare new dataset (larger + higher quality)
       │
       ▼
  Fine-tune again (on expanded dataset)
       │
       ▼
  Deploy new adapter → even better generations
       │
       └────────── REPEAT ──────────┘
```

This is the **data flywheel**: better model → better data → better model.

---

## Tab-by-Tab Demo Script (3 minutes)

### For presenting to an engineering lead:

> "Let me walk you through the full ML pipeline — everything runs locally on a single GPU."

1. **Pipeline tab** (30s) — "Here's the architecture. 7 phases, left to right. We scraped 120 pages, mapped them into 63 structured workflows, embedded 303 chunks into a vector store, and generated 217 interactive playgrounds."

2. **Data & RAG tab** (45s) — "This is our RAG engine. ChromaDB with nomic-embed-text runs on CPU — zero VRAM cost. Watch me query it..." *[type 'mortgage pre-approval' → show results]* "...and these chunks get injected into the generator's prompt. Here's the training data pipeline — one click to prepare the dataset."

3. **ML Metrics tab** (30s) — "Two models running simultaneously on one RTX 4090. The 14B coder generates HTML, the 3B router handles classification. Total VRAM: 10.5GB, leaving 5.5GB for KV cache. Smart routing means most requests never hit the big model."

4. **ML Observatory tab** (75s) — "This is the deep dive."
   - *RAG & Chunking:* "303 chunks. The histogram shows size distribution — most are small step descriptions, with 120 larger overview chunks. Click 'Similar' to find near-duplicates."
   - *Training Lifecycle:* "203 examples, 92% scored quality 5. The loss curve shows convergence after training."
   - *Adapter Registry:* "Once trained, adapters appear here. One-click deploy merges them into Ollama."

5. **Close with:** "The whole pipeline is a data flywheel — better model makes better playgrounds, which become better training data, which makes a better model. Zero API costs, full local control."

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RTX 4090 (16GB VRAM)                        │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ Generator (14B)  │  │  Router (3B)     │  │  Embedder        │  │
│  │ qwen2.5-coder    │  │  qwen2.5         │  │  nomic-embed     │  │
│  │ ~8.5 GB Q4_K_M   │  │  ~2 GB Q4        │  │  CPU only        │  │
│  │                  │  │                  │  │  0 GB VRAM       │  │
│  │ HTML/CSS/JS gen  │  │ Classify/route   │  │ Vector embed     │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                     │
│  Total: ~10.5 GB loaded  |  Free: ~5.5 GB for KV cache            │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        Storage Layer                                │
│                                                                     │
│  ChromaDB (vectors)  │  SQLite (cache + metrics)  │  JSONL (train) │
│  data/chromadb/      │  data/cache.db             │  data/*.jsonl  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        Web Layer                                    │
│                                                                     │
│  FastAPI + Uvicorn   │  SSE Streaming   │  Single-page dashboard   │
│  Port 8000           │  Real-time gen   │  6 tabs, 0 JS framework  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference: All Endpoints

| Endpoint | Method | Tab | Purpose |
|----------|--------|-----|---------|
| `/api/pipeline/status` | GET | Pipeline | Phase counts for all 7 stages |
| `/api/rag/ingest` | POST | Data & RAG | Ingest workflows into ChromaDB |
| `/api/rag/clear` | POST | Data & RAG | Wipe and rebuild vector store |
| `/api/rag/query` | POST | Data & RAG | Test RAG retrieval |
| `/api/rag/stats` | GET | Data & RAG | Embedding counts and status |
| `/api/dataset/stats` | GET | Data & RAG | Training file counts |
| `/api/dataset/prepare` | POST | Data & RAG | Generate JSONL from playgrounds |
| `/api/metrics` | GET | ML Metrics | Generation stats and model breakdown |
| `/api/health` | GET | ML Metrics | Ollama model availability |
| `/api/stats` | GET | ML Metrics | VRAM, models, cache, playgrounds |
| `/api/observatory/chunk-analytics` | GET | Observatory | Chunk histogram and workflow breakdown |
| `/api/observatory/chunks` | GET | Observatory | Paginated chunk browser |
| `/api/observatory/similar-chunks` | POST | Observatory | Find similar chunks by ID |
| `/api/observatory/training/status` | GET | Observatory | Training state detection |
| `/api/observatory/training/logs` | GET | Observatory | Loss curve data from trainer_state.json |
| `/api/observatory/dataset/analytics` | GET | Observatory | Quality distribution analysis |
| `/api/observatory/training/examples` | GET | Observatory | Browse training examples |
| `/api/observatory/adapters` | GET | Observatory | List all LoRA adapters |
| `/api/observatory/adapters/{name}` | GET | Observatory | Adapter file details |
| `/api/observatory/adapters/{name}/deploy` | POST | Observatory | Get deploy/merge command |
