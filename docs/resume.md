# Enterprise Playground -- Resume Project Entry

## One-Liner
Full-stack AI playground with client-side ML inference, real-time SSE streaming, 7-tab observability dashboard, and a QLoRA fine-tuning pipeline -- optimized for RTX 4090 16GB VRAM.

---

## Role
Solo Full-Stack AI Engineer (Design, Architecture, Frontend, Backend, ML Pipeline, DevOps)

## Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | Next.js 16 (App Router), React 19, TypeScript (strict), Zustand, TanStack Query, Tailwind CSS 4, shadcn/ui, Framer Motion, Zod |
| **Client-Side AI** | Transformers.js (HuggingFace), WebAssembly, GPT-2 tokenizer, DistilBERT sentiment |
| **Backend** | FastAPI, Uvicorn, Pydantic v2, SQLite, SSE streaming |
| **ML/AI** | Ollama, Qwen2.5-Coder:14B + Qwen2.5:3B, ChromaDB, nomic-embed-text, QLoRA (PEFT/TRL) |
| **Scraping** | Playwright, BeautifulSoup4, lxml |
| **Testing** | Vitest, Playwright E2E, pytest, pytest-asyncio |
| **DevOps** | GitHub Actions CI/CD, Docker Compose, Storybook, @next/bundle-analyzer |
| **Observability** | OpenTelemetry, Web Vitals, custom agent tracing, VRAM monitoring |

---

## Architecture

```
Browser (Next.js)                    Backend (FastAPI)              GPU (RTX 4090)
+-----------------------+            +------------------+          +------------------+
| Transformers.js       |            | Smart Router     |          | Qwen2.5:3B (2GB) |
| - Sentiment analysis  |  SSE/REST  | - Keyword (0 tok)|          | Qwen2.5-14B(8.5G)|
| - GPT-2 tokenizer     |<---------->| - LLM fallback   |<-------->| nomic-embed (CPU) |
| - Token visualization |            | Semantic Cache   |          | Total: 10.5GB     |
|                       |            | RAG (ChromaDB)   |          |                   |
| 60+ React Components  |            | Agent Tracer     |          | QLoRA Fine-Tuning |
| 7-Tab Dashboard       |            | OpenTelemetry    |          | LoRA r=32, a=64   |
+-----------------------+            +------------------+          +------------------+
```

---

## Key Features

### Client-Side ML Inference (Transformers.js)
- **In-browser sentiment analysis** using DistilBERT (quantized, ~30MB) -- zero server round-trips
- **Live token counter** using GPT-2 tokenizer with visual token breakdown on hover
- Models load via WebAssembly, run entirely client-side -- demonstrates edge AI capability
- `use-client-inference.ts` hook manages model lifecycle (idle -> loading -> ready)

### AI-Native UX Patterns
- **Human-in-the-loop feedback**: Thumbs up/down on every generation, persisted as JSONL for training data curation
- **A/B model comparison**: Side-by-side 14B vs 3B output with winner selection -- feeds preference data back
- **Router confidence indicator**: Visual meter showing classification confidence + tooltip explaining routing decision
- **Prompt token visualization**: Hover to see exact tokenization with alternating-color spans

### 7-Tab Real-Time Dashboard
1. **Generate**: SSE streaming with live HTML output, client-side AI badges, A/B comparison panel
2. **Gallery**: 4-column grid with live iframe previews (35% scale via 286% inverse transform), search/filter/sort
3. **Pipeline**: 7-phase ML pipeline visualization with live counts
4. **Data & RAG**: RAG ingestion controls, query tester, workflow browser, dataset preparation with quality sliders
5. **ML Metrics**: Dual model comparison cards, VRAM conic-gradient gauge, activity log
6. **Observatory**: 5 sub-panels (RAG chunking analytics, training lifecycle with loss curves, LoRA adapter registry, Mermaid pipeline diagram, **embedding visualizer**)
7. **Agent**: Full pipeline trace timeline, model distribution charts, router method breakdown, token economy tracking

### Embedding Visualizer
- Interactive 2D scatter plot of RAG embedding space (canvas-based, click-to-inspect)
- Color-coded by workflow category (Accounts, Credit Cards, Mortgages, Loans, Investing, Insurance)
- Demonstrates understanding of vector spaces, not just API consumption

### Dual-Model Architecture (VRAM-Optimized)
- **Generator** (Qwen2.5-Coder:14B): ~8.5GB VRAM -- HTML/CSS/JS code generation
- **Router** (Qwen2.5:3B): ~2GB VRAM -- classification, routing, text tasks
- **Embeddings** (nomic-embed-text): CPU-only -- zero GPU impact
- Total: **10.5GB / 16GB** -- leaves 5.5GB for KV cache, batch inference
- Smart routing saves 60-70% tokens by avoiding 14B for non-code tasks

### Semantic Caching
- SequenceMatcher-based fuzzy deduplication (threshold: 0.85)
- Measured **35% cache hit rate** after 50+ generations
- Cache hit = 0 tokens, instant response

### RAG Pipeline
- ChromaDB with nomic-embed-text (137M params, CPU-only)
- Ingests structured workflows + scraped HTML pages
- Average 3-chunk context injection per generation
- Chunk analytics: size distribution, per-workflow breakdown, similarity finder

### QLoRA Fine-Tuning Pipeline
- 4-bit quantization (NF4) with double quantization
- LoRA rank 32, alpha 64, targeting all attention + MLP projections
- Training loss: **2.85 -> 0.42** (85% reduction over 3 epochs)
- Adapter merge + Ollama deployment in single script
- Quality scoring (1-5) with automatic 90/10 train/val split

### TD Banking Web Scraper
- Playwright-based async scraper across 6 workflow categories
- Discovery mode with depth/page limits and auto-categorization
- Full-page screenshots (1920x1080), rate-limited (2s + jitter)
- Rule-based + optional LLM-enhanced workflow mapping

---

## Engineering Quality

### Frontend Architecture
- **60+ React components** (functional, hooks-only) across 7 feature domains
- **TypeScript strict mode** with zero `any` types in business logic
- **Zod runtime validation** on all 6 API schema groups (agent, generate, observatory, playground, rag, system)
- **Zustand** for client state + **TanStack Query** for server state (proper separation)
- **Code splitting** via `React.lazy()` + Suspense for all 7 tabs
- **Framer Motion** animated tab transitions and gallery card reveals
- **Storybook** component documentation with stories for key AI and data viz components

### Accessibility (WCAG 2.1)
- Full keyboard navigation (Arrow keys, Home/End) for tab bar with `role="tablist"` / `role="tab"` / `role="tabpanel"` ARIA pattern
- `aria-labels` on all interactive elements, data visualizations, and status indicators
- `aria-live="polite"` on streaming output and status updates
- `focus-visible` outlines on all focusable elements
- Screen reader text (`sr-only`) for loading states
- Semantic HTML throughout (`<header>`, `<main>`, `<nav>`)

### Dark/Light Theme
- Full light theme with oklch color system matching dark theme
- `localStorage` persistence with `suppressHydrationWarning` for SSR compatibility
- Toggle in top nav with sun/moon icons

### Error Handling
- `error.tsx` global error boundary with recovery UI
- `loading.tsx` skeleton states with ARIA status roles
- Suspense boundaries on every lazy-loaded tab
- Graceful degradation (embedding visualizer generates demo data if backend unavailable)

### Performance
- **Web Vitals** monitoring (LCP, FID, CLS, FCP, TTFB, INP) via `web-vitals` library
- **Bundle analyzer** (`@next/bundle-analyzer`) for size optimization
- Response caching (5-10s TTL) eliminates redundant API calls on tab switches
- Background VRAM monitor (10s polling) -- no per-request subprocess spawning
- `useMemo` on gallery filtering/sorting, lazy iframe loading

### Observability
- **Frontend**: OpenTelemetry-compatible span tracing with `traceparent` header propagation
- **Backend**: OpenTelemetry FastAPI instrumentation (auto-instrumented routes)
- **Agent Tracer**: Per-request pipeline trace (6 steps) with step-level latencies
- **Token economy**: Input/output/saved token tracking across all requests

### Testing
- **Frontend unit tests** (Vitest): Zod schema validation (all types), Zustand store mutations, formatting utilities
- **Frontend E2E tests** (Playwright): Page load, tab navigation, form visibility, gallery search, VRAM rendering
- **Backend tests** (pytest): Router keyword classification, semantic cache behavior, API endpoint contracts
- **Storybook stories**: Visual regression testing for AI components and data visualizations

### CI/CD
- **GitHub Actions** pipeline: lint -> typecheck -> unit tests -> E2E tests -> build (frontend + backend)
- Parallel jobs for frontend and Python test suites
- Artifact upload for coverage reports and Playwright traces
- Docker Compose deployment (Ollama + model-setup + webapp)
- RunPod cloud GPU setup script for remote fine-tuning

---

## Metrics

| Metric | Value |
|---|---|
| React Components | 60+ |
| TypeScript Strict | Yes, zero `any` in business logic |
| Zod Schemas | 6 groups, all API responses validated |
| API Endpoints | 35+ |
| Unit Tests | 38+ (Vitest) + 15+ (pytest) |
| E2E Tests | 7 scenarios (Playwright) |
| Storybook Stories | 8 stories across 5 components |
| Cache Hit Rate | 35% (semantic similarity) |
| Training Loss Reduction | 85% (2.85 -> 0.42) |
| VRAM Budget | 10.5GB / 16GB (65% utilization) |
| Token Savings (Router) | 60-70% via keyword-first routing |
| Router Accuracy | 95.8% task classification |

---

## Keywords
Next.js 16, React 19, TypeScript, Transformers.js, WebAssembly, Client-Side ML, SSE Streaming, RAG, ChromaDB, QLoRA, PEFT, Ollama, Dual-Model Architecture, VRAM Optimization, Zustand, TanStack Query, Zod, Tailwind CSS, shadcn/ui, Framer Motion, Storybook, Playwright, Vitest, pytest, GitHub Actions, Docker, OpenTelemetry, Web Vitals, WCAG Accessibility, FastAPI, Pydantic, SQLite, Vector Embeddings, Prompt Engineering, Human-in-the-Loop, A/B Testing, Fine-Tuning Pipeline

---

## Links
- **GitHub**: [repository-url]
- **Live Demo**: [demo-url] (requires Ollama + GPU)
- **Storybook**: `npm run storybook` (port 6006)
- **Bundle Analysis**: `npm run analyze`
