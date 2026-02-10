"""
Enterprise Playground — 8-Tab Showcase Dashboard
==================================================
Portfolio-grade UI demonstrating the full ML pipeline:
RAG, dual-model routing, semantic caching, fine-tuning, and agent observability.

Tabs:
  1. Generate — Enhanced prompt input with RAG context display
  2. Playgrounds Gallery — Grid of all generated playgrounds
  3. Pipeline Visualizer — Visual flowchart of the 6-phase pipeline
  4. Data & RAG — Dataset browser, RAG status, embedding management
  5. ML Metrics — Model comparison, latency, VRAM, fine-tuning status
  6. ML Observatory — Training lifecycle, adapters, pipeline diagram
  7. Agent — Runtime agent trace viewer, routing decisions, token economy
  8. Embeddings & Storage — Embedding space visualizer, ChromaDB inspector, storage map
"""

import html as html_lib


def render_dashboard(
    playgrounds: list[dict],
    workflows: list[dict],
    cache_stats: dict,
    rag_stats: dict,
    generator_model: str,
    router_model: str,
) -> str:
    """Render the complete 8-tab dashboard HTML."""

    # === Pre-compute data for templates ===
    pg_count = len(playgrounds)
    wf_count = len(workflows)
    cache_hits = cache_stats.get("hits", 0)
    cache_hit_rate = cache_stats.get("hit_rate", "0%")
    tokens_saved = cache_stats.get("total_saved_tokens", 0)
    rag_chunks = rag_stats.get("total_chunks", 0) if isinstance(rag_stats, dict) else 0
    rag_enabled = rag_stats.get("enabled", False) if isinstance(rag_stats, dict) else False
    rag_model = rag_stats.get("embed_model", "nomic-embed-text") if isinstance(rag_stats, dict) else "nomic-embed-text"

    # Playground rows for gallery
    gallery_cards = ""
    for pg in reversed(playgrounds[-50:]):
        prompt = html_lib.escape(pg.get("prompt", "")[:80])
        pid = pg.get("playground_id", "")
        size = pg.get("html_size_bytes", 0)
        size_str = f"{size/1024:.0f}KB" if size > 0 else "?"
        date = pg.get("generated_at", "")[:10]
        model = pg.get("model", "").split(":")[0]
        cache = pg.get("cache_hit", False)
        style = pg.get("style", "banking")
        rag_used = pg.get("rag_chunks_used", 0)
        latency = pg.get("latency_ms", 0)
        latency_str = f"{latency:.0f}ms" if latency else ""

        cache_badge = '<span class="px-1.5 py-0.5 text-[10px] bg-indigo-100 text-indigo-700 rounded">CACHE</span>' if cache else ""
        rag_badge = f'<span class="px-1.5 py-0.5 text-[10px] bg-blue-100 text-blue-700 rounded">RAG:{rag_used}</span>' if rag_used else ""

        gallery_cards += f"""<div class="gallery-card bg-gray-50 rounded-lg border border-gray-200 overflow-hidden hover:border-indigo-400 transition-colors cursor-pointer group"
            data-prompt="{prompt.lower()}" data-style="{style}" data-date="{date}" data-size="{size}" data-latency="{latency}" data-model="{model}" data-cache="{'1' if cache else '0'}" data-rag="{rag_used}"
            onclick="window.open('/playground/{pid}','_blank')">
            <div class="h-36 bg-gray-50 relative overflow-hidden">
                <iframe src="/playground/{pid}" class="w-full h-full pointer-events-none" style="transform:scale(0.35);transform-origin:top left;width:286%;height:286%" loading="lazy"></iframe>
                <div class="absolute inset-0 bg-gradient-to-t from-[#13161f]/90 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-2">
                    <span class="text-xs text-gray-900">Open</span>
                </div>
            </div>
            <div class="p-3">
                <div class="text-xs text-gray-600 truncate mb-1.5">{prompt}</div>
                <div class="flex items-center gap-1.5 flex-wrap">
                    <span class="text-[10px] text-gray-600">{model}</span>
                    <span class="text-[10px] text-gray-400">{size_str}</span>
                    <span class="text-[10px] text-gray-400">{date}</span>
                    {cache_badge}{rag_badge}
                    {"<span class='text-[10px] text-gray-600'>" + latency_str + "</span>" if latency_str else ""}
                </div>
            </div>
        </div>"""

    # Playground rows for table in Generate tab
    pg_rows = ""
    for pg in reversed(playgrounds[-15:]):
        prompt = html_lib.escape(pg.get("prompt", "")[:50])
        size = pg.get("html_size_bytes", 0)
        size_str = f"{size/1024:.0f}KB" if size > 0 else "?"
        date = pg.get("generated_at", "")[:16]
        cache = "HIT" if pg.get("cache_hit") else ""
        model = pg.get("model", "").split(":")[0]
        pid = pg.get("playground_id", "")
        rag_used = pg.get("rag_chunks_used", 0)
        rag_cell = f'<span class="text-blue-400">{rag_used}</span>' if rag_used else '<span class="text-gray-400">-</span>'
        pg_rows += f"""<tr class="border-b border-gray-200 hover:bg-gray-50 cursor-pointer" onclick="window.open('/playground/{pid}','_blank')">
            <td class="px-3 py-2 text-sm text-gray-600 max-w-[200px] truncate">{prompt}</td>
            <td class="px-3 py-2 text-xs text-gray-500">{model}</td>
            <td class="px-3 py-2 text-xs text-gray-500">{size_str}</td>
            <td class="px-3 py-2 text-xs">{f'<span class="text-indigo-600">{cache}</span>' if cache else '<span class="text-gray-400">GEN</span>'}</td>
            <td class="px-3 py-2 text-xs">{rag_cell}</td>
            <td class="px-3 py-2 text-xs text-gray-600">{date}</td>
        </tr>"""

    # Workflow cards for Data tab
    wf_cards = ""
    for wf in workflows:
        name = html_lib.escape(wf.get("name", ""))
        cat = wf.get("category", "")
        pages = wf.get("total_pages", 0)
        wfid = wf.get("workflow_id", "")
        wf_cards += f"""<div class="bg-gray-50 rounded-lg p-3 border border-gray-300">
            <div class="text-sm font-medium text-gray-800">{name}</div>
            <div class="text-xs text-gray-500 mt-1">{cat} | {pages} pages</div>
            <button onclick="generateFromWorkflow('{wfid}')"
                    class="mt-2 text-xs btn-primary px-3 py-1.5 rounded-lg">
                Generate Playground
            </button>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Enterprise Playground — Showcase</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
<script>
tailwind.config = {{
  theme: {{
    extend: {{
      colors: {{
        gray: {{
          50: '#212638',
          100: '#1a1d2b',
          200: '#2f3549',
          300: '#3a4158',
          400: '#6b7a94',
          500: '#9ba8c0',
          600: '#b8c3d6',
          700: '#d1dae8',
          800: '#e8ecf4',
          900: '#f3f5f9',
          950: '#fafbfd',
        }}
      }}
    }}
  }}
}}
</script>
<style>
body {{ background: #13161f; color: #e2e8f0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
.stat-card {{ background: linear-gradient(135deg, #212638 0%, #262b3f 100%); }}
.tab-btn {{ transition: all 0.2s; }}
.tab-btn.active {{ color: #818cf8; border-color: #818cf8; }}
.tab-btn:not(.active) {{ color: #64748b; border-color: transparent; }}
.tab-panel {{ display: none; }}
.tab-panel.active {{ display: block; }}
#stream-output {{ font-family: 'SF Mono', 'Fira Code', monospace; font-size: 12px; }}
.pipeline-node {{ transition: all 0.3s; }}
.pipeline-node:hover {{ transform: translateY(-2px); box-shadow: 0 4px 20px rgba(99,102,241,0.25); }}
.pipeline-arrow {{ color: #3a4158; }}
.glow {{ box-shadow: 0 0 30px rgba(99,102,241,0.12); }}
.metric-ring {{ background: conic-gradient(#818cf8 var(--pct), #2f3549 0); }}
.obs-panel {{ display: block; }}
.obs-panel.hidden {{ display: none; }}
.obs-panel-btn {{ color: #64748b; cursor: pointer; transition: color 0.2s; }}
.obs-panel-btn.active {{ color: #818cf8; }}
.obs-bar {{ transition: width 0.5s ease-out; }}
.chunk-expand {{ max-height: 0; overflow: hidden; transition: max-height 0.3s ease-out; }}
.chunk-expand.open {{ max-height: 600px; }}
/* === Embeddings Tab === */
.emb-panel {{ display: block; }}
.emb-panel.hidden {{ display: none; }}
.emb-panel-btn {{ color: #64748b; cursor: pointer; transition: color 0.2s; }}
.emb-panel-btn.active {{ color: #818cf8; }}
#emb-plotly .plotly .modebar {{ background: transparent !important; }}
#emb-plotly .plotly .modebar-btn path {{ fill: #64748b !important; }}
#emb-plotly .plotly .modebar-btn:hover path {{ fill: #818cf8 !important; }}
.storage-bar-seg {{ height: 24px; transition: width 0.5s ease-out; display: inline-block; }}
.storage-bar-seg:first-child {{ border-radius: 4px 0 0 4px; }}
.storage-bar-seg:last-child {{ border-radius: 0 4px 4px 0; }}
.status-dot {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; }}
.status-dot.running {{ background: #818cf8; animation: pulse-dot 1.5s infinite; }}
.status-dot.completed {{ background: #818cf8; }}
.status-dot.interrupted {{ background: #f59e0b; }}
.status-dot.idle {{ background: #64748b; }}
@keyframes pulse-dot {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.4; }} }}
/* === Pipeline Mermaid Diagram === */
.pipeline-mermaid {{ background: #1a1d2b; border-radius: 12px; border: 1px solid rgba(255,255,255,0.09); padding: 24px; }}
.pipeline-mermaid .node rect, .pipeline-mermaid .node polygon {{ fill: #262b3f !important; stroke: #4f46e5 !important; stroke-width: 1.5px; rx: 8; }}
.pipeline-mermaid .node .label {{ color: #e2e8f0 !important; }}
.pipeline-mermaid .edgePath .path {{ stroke: #4f46e5 !important; stroke-width: 1.5px; }}
.pipeline-mermaid .edgeLabel {{ background: #212638 !important; color: #94a3b8 !important; font-size: 11px; padding: 2px 6px; border-radius: 4px; }}
.pipeline-mermaid .cluster rect {{ fill: rgba(79,70,229,0.06) !important; stroke: rgba(99,102,241,0.2) !important; rx: 12; }}
.pipeline-mermaid .cluster text {{ fill: #818cf8 !important; }}
.pipeline-mermaid text {{ fill: #cbd5e1 !important; }}
.pipeline-mermaid .marker {{ fill: #4f46e5 !important; stroke: #4f46e5 !important; }}
.mermaid-tooltip {{ position: absolute; background: #262b3f; color: #e2e8f0; border: 1px solid #4f46e5; border-radius: 8px; padding: 10px 14px; font-size: 12px; max-width: 320px; pointer-events: none; opacity: 0; transition: opacity 0.2s; z-index: 100; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }}
.mermaid-tooltip.visible {{ opacity: 1; }}
.mermaid-tooltip .tt-title {{ font-weight: 600; color: #a5b4fc; margin-bottom: 4px; }}
.mermaid-tooltip .tt-body {{ color: #94a3b8; line-height: 1.4; }}
.pipeline-legend {{ display: flex; gap: 16px; flex-wrap: wrap; margin-top: 12px; }}
.pipeline-legend span {{ display: flex; align-items: center; gap: 6px; font-size: 11px; color: #64748b; }}
.pipeline-legend .dot {{ width: 8px; height: 8px; border-radius: 50%; }}
.diagram-node {{ cursor: pointer; transition: filter 0.2s; }}
.diagram-node:hover {{ filter: brightness(1.3); }}
/* === Premium Polish === */
.stat-card {{ transition: all 0.3s ease; border-color: rgba(255,255,255,0.09); }}
.stat-card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 25px rgba(99,102,241,0.15); }}
.tab-panel.active {{ animation: fadeUp 0.3s ease; }}
@keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: translateY(0); }} }}
.btn-primary {{ background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%); color: white; transition: all 0.2s ease; }}
.btn-primary:hover {{ box-shadow: 0 4px 16px rgba(99,102,241,0.4); transform: translateY(-1px); }}
.btn-primary:active {{ transform: translateY(0); }}
.btn-primary:disabled {{ opacity: 0.5; cursor: not-allowed; transform: none; box-shadow: none; }}
.card {{ background: rgba(33,38,56,0.9); backdrop-filter: blur(8px); border: 1px solid rgba(255,255,255,0.09); box-shadow: 0 1px 3px rgba(0,0,0,0.3); }}
.badge-indigo {{ background: linear-gradient(135deg, rgba(79,70,229,0.2), rgba(99,102,241,0.15)); color: #a5b4fc; font-weight: 600; }}
.badge-warm {{ background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.03)); color: #94a3b8; }}
::selection {{ background: rgba(99,102,241,0.3); }}
input, select {{ background: #1a1d2b !important; color: #e2e8f0 !important; border-color: #3a4158 !important; }}
input::placeholder {{ color: #64748b !important; }}
input:focus, select:focus {{ border-color: #6366f1 !important; box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important; }}
.bg-white {{ background: #212638 !important; }}
.pipeline-node {{ border: 1px solid rgba(255,255,255,0.09); box-shadow: 0 1px 3px rgba(0,0,0,0.3); }}
/* Dark theme overrides */
table {{ color: #cbd5e1; }}
code {{ background: #2f3549 !important; color: #a5b4fc; }}
.bg-indigo-100 {{ background: rgba(79,70,229,0.15) !important; }}
.bg-purple-100 {{ background: rgba(168,85,247,0.15) !important; }}
.bg-orange-100 {{ background: rgba(251,146,60,0.15) !important; }}
.bg-yellow-100 {{ background: rgba(250,204,21,0.15) !important; }}
.bg-blue-100 {{ background: rgba(59,130,246,0.15) !important; }}
.bg-red-100 {{ background: rgba(239,68,68,0.15) !important; }}
.bg-indigo-50 {{ background: rgba(79,70,229,0.1) !important; }}
.text-indigo-700 {{ color: #a5b4fc !important; }}
.text-blue-700 {{ color: #93c5fd !important; }}
.bg-indigo-100.text-indigo-700, .bg-blue-100.text-blue-700 {{ background: rgba(79,70,229,0.15) !important; }}
.bg-yellow-100.text-yellow-700 {{ background: rgba(250,204,21,0.12) !important; color: #fde047 !important; }}
.bg-red-100.text-red-700 {{ background: rgba(239,68,68,0.12) !important; color: #fca5a5 !important; }}
/* === Agent Trace Timeline === */
.trace-step {{ position: relative; padding-left: 28px; }}
.trace-step::before {{ content: ''; position: absolute; left: 9px; top: 0; bottom: 0; width: 2px; background: #2f3549; }}
.trace-step:last-child::before {{ display: none; }}
.trace-step-dot {{ position: absolute; left: 4px; top: 8px; width: 12px; height: 12px; border-radius: 50%; border: 2px solid #4f46e5; background: #212638; z-index: 1; }}
.trace-step-dot.cache-hit {{ border-color: #22c55e; background: rgba(34,197,94,0.2); }}
.trace-step-dot.cache-miss {{ border-color: #f59e0b; }}
.trace-step-dot.generate {{ border-color: #818cf8; background: rgba(129,140,248,0.2); }}
.trace-step-dot.rag {{ border-color: #06b6d4; }}
.trace-bar {{ height: 6px; border-radius: 3px; min-width: 2px; transition: width 0.5s ease-out; }}
.trace-expand {{ max-height: 0; overflow: hidden; transition: max-height 0.3s ease-out; }}
.trace-expand.open {{ max-height: 400px; }}
</style>
</head>
<body class="min-h-screen">

<!-- === TOP NAV === -->
<nav class="border-b border-gray-200/60 px-6 py-3.5 flex items-center justify-between sticky top-0 z-50 backdrop-blur-xl" style="background:rgba(19,22,31,0.85);box-shadow:0 1px 4px rgba(0,0,0,0.3)">
    <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl flex items-center justify-center text-white font-bold text-sm shadow-md" style="background:linear-gradient(135deg,#4f46e5 0%,#818cf8 100%);box-shadow:0 2px 10px rgba(79,70,229,0.3)">EP</div>
        <div>
            <span class="font-bold text-gray-900 tracking-tight text-[15px]">Enterprise Playground</span>
            <span class="text-[9px] text-indigo-300 ml-2 px-2 py-0.5 rounded-full font-semibold tracking-wider uppercase" style="background:rgba(99,102,241,0.15)">Showcase</span>
        </div>
    </div>
    <div class="flex items-center gap-4">
        <div id="vram-bar" class="flex items-center gap-2">
            <span class="text-xs text-gray-500">VRAM</span>
            <div class="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div id="vram-fill" class="h-full bg-indigo-500 rounded-full transition-all" style="width:0%"></div>
            </div>
            <span id="vram-text" class="text-xs text-gray-500">--</span>
        </div>
        <div class="flex items-center gap-1.5">
            <div id="gen-dot" class="w-2 h-2 rounded-full bg-gray-400"></div>
            <span class="text-xs text-gray-500">{generator_model}</span>
        </div>
        <div class="flex items-center gap-1.5">
            <div id="rtr-dot" class="w-2 h-2 rounded-full bg-gray-400"></div>
            <span class="text-xs text-gray-500">{router_model}</span>
        </div>
        <div class="flex items-center gap-1.5">
            <div class="w-2 h-2 rounded-full {"bg-indigo-500" if rag_enabled else "bg-gray-600"}"></div>
            <span class="text-xs text-gray-500">RAG</span>
        </div>
    </div>
</nav>

<!-- === TAB BAR === -->
<div class="border-b border-gray-200/60 backdrop-blur-sm sticky top-[56px] z-40" style="background:rgba(19,22,31,0.75)">
    <div class="max-w-7xl mx-auto px-6 flex gap-0">
        <button class="tab-btn active px-4 py-3 text-sm font-medium border-b-2" onclick="switchTab('generate')" data-tab="generate">Generate</button>
        <button class="tab-btn px-4 py-3 text-sm font-medium border-b-2" onclick="switchTab('gallery')" data-tab="gallery">Gallery <span class="text-xs text-gray-600 ml-1">{pg_count}</span></button>
        <button class="tab-btn px-4 py-3 text-sm font-medium border-b-2" onclick="switchTab('pipeline')" data-tab="pipeline">Pipeline</button>
        <button class="tab-btn px-4 py-3 text-sm font-medium border-b-2" onclick="switchTab('data')" data-tab="data">Data & RAG</button>
        <button class="tab-btn px-4 py-3 text-sm font-medium border-b-2" onclick="switchTab('metrics')" data-tab="metrics">ML Metrics</button>
        <button class="tab-btn px-4 py-3 text-sm font-medium border-b-2" onclick="switchTab('observatory')" data-tab="observatory">ML Observatory</button>
        <button class="tab-btn px-4 py-3 text-sm font-medium border-b-2" onclick="switchTab('agent')" data-tab="agent">Agent</button>
        <button class="tab-btn px-4 py-3 text-sm font-medium border-b-2" onclick="switchTab('embeddings')" data-tab="embeddings">Embeddings & Storage</button>
    </div>
</div>

<main class="max-w-7xl mx-auto px-6 py-6">

<!-- ============================================ -->
<!-- TAB 1: GENERATE -->
<!-- ============================================ -->
<div class="tab-panel active" id="tab-generate">
    <!-- Stats Row -->
    <div class="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
        <div class="stat-card rounded-lg p-4 border border-gray-200 glow">
            <div class="text-[10px] text-gray-500 uppercase tracking-wider">Playgrounds</div>
            <div class="text-2xl font-bold text-indigo-600 mt-1">{pg_count}</div>
        </div>
        <div class="stat-card rounded-lg p-4 border border-gray-200">
            <div class="text-[10px] text-gray-500 uppercase tracking-wider">Cache Hits</div>
            <div class="text-2xl font-bold text-blue-400 mt-1">{cache_hits}</div>
            <div class="text-[10px] text-gray-600">{cache_hit_rate}</div>
        </div>
        <div class="stat-card rounded-lg p-4 border border-gray-200">
            <div class="text-[10px] text-gray-500 uppercase tracking-wider">Tokens Saved</div>
            <div class="text-2xl font-bold text-amber-400 mt-1">{tokens_saved:,}</div>
        </div>
        <div class="stat-card rounded-lg p-4 border border-gray-200">
            <div class="text-[10px] text-gray-500 uppercase tracking-wider">RAG Chunks</div>
            <div class="text-2xl font-bold text-cyan-400 mt-1">{rag_chunks}</div>
            <div class="text-[10px] text-gray-600">{rag_model}</div>
        </div>
        <div class="stat-card rounded-lg p-4 border border-gray-200">
            <div class="text-[10px] text-gray-500 uppercase tracking-wider">Workflows</div>
            <div class="text-2xl font-bold text-purple-400 mt-1">{wf_count}</div>
        </div>
    </div>

    <!-- Generator Input -->
    <div class="bg-white rounded-xl border border-gray-200 p-5 mb-6">
        <div class="flex gap-3">
            <input type="text" id="prompt" placeholder="Describe what to visualize or ask anything..."
                   class="flex-1 bg-white border border-gray-300 rounded-lg px-4 py-3 text-sm text-gray-800
                          placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                   onkeydown="if(event.key==='Enter')generate()">
            <select id="style" class="bg-white border border-gray-300 rounded-lg px-3 text-sm text-gray-600">
                <option value="banking">Banking</option>
                <option value="default">Default</option>
                <option value="minimal">Minimal</option>
                <option value="dark">Dark</option>
            </select>
            <button onclick="generate()" id="gen-btn"
                    class="btn-primary px-6 py-3 rounded-xl font-medium text-sm whitespace-nowrap">
                Generate
            </button>
        </div>

        <!-- Stream output + RAG context side by side -->
        <div id="stream-panel" class="hidden mt-4">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <div class="lg:col-span-2">
                    <div class="flex items-center gap-2 mb-2">
                        <div id="stream-status" class="text-xs text-gray-500">Ready</div>
                        <div id="stream-spinner" class="hidden">
                            <svg class="animate-spin h-3 w-3 text-indigo-600" viewBox="0 0 24 24">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                            </svg>
                        </div>
                        <div id="gen-meta" class="text-xs text-gray-600 ml-auto"></div>
                    </div>
                    <div id="stream-output" class="bg-gray-50 rounded-lg p-3 max-h-48 overflow-y-auto text-gray-400 whitespace-pre-wrap border border-gray-200"></div>
                </div>
                <div>
                    <div class="text-xs text-gray-500 mb-2">RAG Context Injected</div>
                    <div id="rag-context" class="bg-gray-50 rounded-lg p-3 max-h-48 overflow-y-auto text-xs text-gray-500 border border-gray-200">
                        <span class="text-gray-400">Waiting for generation...</span>
                    </div>
                </div>
            </div>
        </div>

        <div id="chat-response" class="hidden mt-4 bg-white rounded-lg p-4 text-sm text-gray-600"></div>
    </div>

    <!-- Recent Playgrounds Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
            <h2 class="text-sm font-medium text-gray-400 uppercase tracking-wider">Recent Generations</h2>
            <span class="text-xs text-gray-600">{pg_count} total</span>
        </div>
        <table class="w-full">
            <thead><tr class="border-b border-gray-200 text-[10px] text-gray-500 uppercase">
                <th class="px-3 py-2 text-left">Prompt</th>
                <th class="px-3 py-2 text-left">Model</th>
                <th class="px-3 py-2 text-left">Size</th>
                <th class="px-3 py-2 text-left">Src</th>
                <th class="px-3 py-2 text-left">RAG</th>
                <th class="px-3 py-2 text-left">Date</th>
            </tr></thead>
            <tbody>{pg_rows or '<tr><td colspan="6" class="px-3 py-6 text-center text-gray-600 text-sm">No playgrounds yet</td></tr>'}</tbody>
        </table>
    </div>
</div>

<!-- ============================================ -->
<!-- TAB 2: GALLERY -->
<!-- ============================================ -->
<div class="tab-panel" id="tab-gallery">
    <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h2 class="text-lg font-semibold text-gray-800">Playgrounds Gallery</h2>
        <div class="flex items-center gap-2 flex-wrap">
            <div class="relative">
                <input id="gallery-search" type="text" placeholder="Search prompts..." oninput="applyGalleryFilters()"
                    class="bg-white border border-gray-300 rounded px-3 py-1 text-xs text-gray-700 w-52 pl-7 focus:outline-none focus:border-indigo-400 focus:ring-1 focus:ring-indigo-200">
                <svg class="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
            </div>
            <select id="gallery-filter" class="bg-white border border-gray-300 rounded px-2 py-1 text-xs text-gray-600" onchange="applyGalleryFilters()">
                <option value="all">All Styles</option>
                <option value="banking">Banking</option>
                <option value="default">Default</option>
                <option value="minimal">Minimal</option>
                <option value="dark">Dark</option>
            </select>
            <select id="gallery-sort" class="bg-white border border-gray-300 rounded px-2 py-1 text-xs text-gray-600" onchange="sortGallery()">
                <option value="newest">Newest First</option>
                <option value="oldest">Oldest First</option>
                <option value="largest">Largest Size</option>
                <option value="smallest">Smallest Size</option>
                <option value="fastest">Fastest</option>
                <option value="slowest">Slowest</option>
            </select>
            <span id="gallery-count" class="text-xs text-gray-600">{pg_count} playgrounds</span>
        </div>
    </div>
    <div id="gallery-grid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {gallery_cards or '<div class="col-span-full text-center py-16"><div class="text-5xl mb-4 opacity-15">&#x1F3A8;</div><div class="text-sm text-gray-500 font-medium mb-1">No Playgrounds Yet</div><div class="text-xs text-gray-400">Go to the Generate tab to create your first playground.</div></div>'}
    </div>
</div>

<!-- ============================================ -->
<!-- TAB 3: PIPELINE VISUALIZER -->
<!-- ============================================ -->
<div class="tab-panel" id="tab-pipeline">
    <h2 class="text-lg font-semibold text-gray-800 mb-2">Full ML Pipeline</h2>
    <p class="text-sm text-gray-500 mb-6">End-to-end: Scrape → Structure → Embed → Route → Generate → Cache → Train. All running locally, zero API costs.</p>

    <div class="flex flex-wrap items-center justify-center gap-2 mb-8" id="pipeline-flow">
        <!-- Nodes get populated by JS -->
    </div>

    <!-- Pipeline details -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" id="pipeline-details">
        <div class="bg-white rounded-xl border border-gray-200 p-4">
            <div class="flex items-center gap-2 mb-3">
                <div class="w-8 h-8 rounded-lg bg-orange-100 flex items-center justify-center text-orange-400 text-sm">1</div>
                <div><div class="text-sm font-medium text-gray-800">Scrape</div><div class="text-[10px] text-gray-500">Playwright + BeautifulSoup</div></div>
            </div>
            <div class="text-xs text-gray-400">Headless browser captures TD Banking pages: HTML, screenshots, structured data. Respects robots.txt and rate limits.</div>
            <div id="phase-scrape-count" class="text-lg font-bold text-orange-400 mt-2">--</div>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 p-4">
            <div class="flex items-center gap-2 mb-3">
                <div class="w-8 h-8 rounded-lg bg-yellow-100 flex items-center justify-center text-yellow-400 text-sm">2</div>
                <div><div class="text-sm font-medium text-gray-800">Map</div><div class="text-[10px] text-gray-500">Rule-based + 3B LLM</div></div>
            </div>
            <div class="text-xs text-gray-400">Converts raw HTML into structured workflow JSONs with steps, forms, and user actions. Pydantic-validated schemas.</div>
            <div id="phase-map-count" class="text-lg font-bold text-yellow-400 mt-2">--</div>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 p-4">
            <div class="flex items-center gap-2 mb-3">
                <div class="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center text-cyan-400 text-sm">3</div>
                <div><div class="text-sm font-medium text-gray-800">Store (RAG)</div><div class="text-[10px] text-gray-500">ChromaDB + nomic-embed-text</div></div>
            </div>
            <div class="text-xs text-gray-400">Embeds workflows into vector store using nomic-embed-text (137M params, CPU only, zero VRAM). Cosine similarity retrieval.</div>
            <div id="phase-store-count" class="text-lg font-bold text-cyan-400 mt-2">--</div>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 p-4">
            <div class="flex items-center gap-2 mb-3">
                <div class="w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center text-purple-400 text-sm">4</div>
                <div><div class="text-sm font-medium text-gray-800">Route</div><div class="text-[10px] text-gray-500">Keyword + 3B classifier</div></div>
            </div>
            <div class="text-xs text-gray-400">Smart router classifies requests: keyword matching (0 tokens) or 3B LLM fallback (~50 tokens). Routes to correct model.</div>
            <div id="phase-route-count" class="text-lg font-bold text-purple-400 mt-2">--</div>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 p-4">
            <div class="flex items-center gap-2 mb-3">
                <div class="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center text-indigo-600 text-sm">5</div>
                <div><div class="text-sm font-medium text-gray-800">Generate</div><div class="text-[10px] text-gray-500">14B Coder + RAG context</div></div>
            </div>
            <div class="text-xs text-gray-400">14B model generates HTML with injected RAG context. Token-optimized prompts. SSE streaming for real-time display.</div>
            <div id="phase-generate-count" class="text-lg font-bold text-indigo-600 mt-2">--</div>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 p-4">
            <div class="flex items-center gap-2 mb-3">
                <div class="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center text-blue-400 text-sm">6</div>
                <div><div class="text-sm font-medium text-gray-800">Cache</div><div class="text-[10px] text-gray-500">Semantic similarity matching</div></div>
            </div>
            <div class="text-xs text-gray-400">SequenceMatcher fuzzy matching (0.85 threshold). Avoids regeneration for similar prompts. 7-day TTL with LRU eviction.</div>
            <div id="phase-cache-count" class="text-lg font-bold text-blue-400 mt-2">--</div>
        </div>
    </div>

    <div class="mt-4 bg-white rounded-xl border border-gray-200 p-4">
        <div class="flex items-center gap-2 mb-3">
            <div class="w-8 h-8 rounded-lg bg-red-100 flex items-center justify-center text-red-400 text-sm">7</div>
            <div><div class="text-sm font-medium text-gray-800">Fine-Tune</div><div class="text-[10px] text-gray-500">QLoRA + PEFT on RTX 4090 / RunPod</div></div>
        </div>
        <div class="text-xs text-gray-400">Generated playgrounds become training data. QLoRA fine-tuning (rank-32, 4-bit quantization) produces domain-specific adapters. Merge into Ollama for deployment.</div>
        <div id="phase-train-count" class="text-lg font-bold text-red-400 mt-2">--</div>
    </div>
</div>

<!-- ============================================ -->
<!-- TAB 4: DATA & RAG -->
<!-- ============================================ -->
<div class="tab-panel" id="tab-data">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- RAG Status -->
        <div>
            <h2 class="text-lg font-semibold text-gray-800 mb-4">RAG Pipeline</h2>
            <div class="bg-white rounded-xl border border-gray-200 p-5 mb-4">
                <div class="flex items-center justify-between mb-4">
                    <div>
                        <div class="text-sm font-medium text-gray-800">Vector Store</div>
                        <div class="text-xs text-gray-500">ChromaDB (embedded mode)</div>
                    </div>
                    <div class="flex items-center gap-1.5">
                        <div class="w-2 h-2 rounded-full {"bg-indigo-500" if rag_enabled else "bg-red-400"}"></div>
                        <span class="text-xs text-gray-400">{"Active" if rag_enabled else "Disabled"}</span>
                    </div>
                </div>
                <div class="grid grid-cols-3 gap-3 mb-4">
                    <div class="bg-gray-50 rounded-lg p-3 text-center">
                        <div class="text-xl font-bold text-cyan-400" id="rag-chunk-count">{rag_chunks}</div>
                        <div class="text-[10px] text-gray-500">Embeddings</div>
                    </div>
                    <div class="bg-gray-50 rounded-lg p-3 text-center">
                        <div class="text-xl font-bold text-gray-600">{rag_model}</div>
                        <div class="text-[10px] text-gray-500">Embed Model</div>
                    </div>
                    <div class="bg-gray-50 rounded-lg p-3 text-center">
                        <div class="text-xl font-bold text-gray-600">CPU</div>
                        <div class="text-[10px] text-gray-500">VRAM Cost</div>
                    </div>
                </div>
                <div class="flex gap-2">
                    <button onclick="ingestRAG()" id="ingest-btn"
                            class="flex-1 btn-primary px-3 py-2 rounded-lg text-xs">
                        Ingest Workflows
                    </button>
                    <button onclick="clearRAG()"
                            class="bg-gray-200 text-gray-800 px-3 py-2 rounded-lg text-xs hover:bg-gray-300 transition-colors">
                        Clear & Rebuild
                    </button>
                </div>

                <!-- Pipeline Cycle Actions -->
                <div class="mt-4 p-3 rounded-lg border border-indigo-500/20" style="background:rgba(79,70,229,0.06)">
                    <div class="text-[10px] text-indigo-600 font-semibold uppercase tracking-wider mb-2">Full Pipeline Cycle</div>
                    <div class="flex gap-2">
                        <button onclick="prepareDataset()" id="prepare-btn"
                                class="flex-1 btn-primary px-3 py-2 rounded-lg text-xs">
                            Prepare Dataset
                        </button>
                        <button onclick="showTrainingCommand()"
                                class="flex-1 bg-gray-200 text-gray-800 px-3 py-2 rounded-lg text-xs hover:bg-gray-300 transition-colors">
                            Train LoRA
                        </button>
                    </div>
                    <div id="prepare-status" class="hidden mt-2 text-xs text-gray-500 bg-white/60 rounded p-2"></div>
                </div>
            </div>

            <!-- RAG Query Test -->
            <div class="bg-white rounded-xl border border-gray-200 p-5">
                <div class="text-sm font-medium text-gray-800 mb-3">Test RAG Retrieval</div>
                <div class="flex gap-2 mb-3">
                    <input type="text" id="rag-query" placeholder="e.g. credit card application process"
                           class="flex-1 bg-white border border-gray-300 rounded-lg px-3 py-2 text-xs text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                           onkeydown="if(event.key==='Enter')testRAG()">
                    <button onclick="testRAG()" class="btn-primary px-4 py-2 rounded-lg text-xs">Query</button>
                </div>
                <div id="rag-results" class="bg-gray-50 rounded-lg p-3 min-h-[100px] max-h-48 overflow-y-auto text-xs text-gray-500 border border-gray-200">
                    <span class="text-gray-400">Enter a query to test retrieval...</span>
                </div>
            </div>
        </div>

        <!-- Workflows & Dataset -->
        <div>
            <h2 class="text-lg font-semibold text-gray-800 mb-4">Workflows & Training Data</h2>

            <!-- Dataset stats -->
            <div class="bg-white rounded-xl border border-gray-200 p-5 mb-4">
                <div class="text-sm font-medium text-gray-800 mb-3">Training Dataset</div>
                <div class="grid grid-cols-2 gap-3 mb-3">
                    <div class="bg-gray-50 rounded-lg p-3 text-center">
                        <div class="text-xl font-bold text-amber-400" id="dataset-files">--</div>
                        <div class="text-[10px] text-gray-500">JSONL Files</div>
                    </div>
                    <div class="bg-gray-50 rounded-lg p-3 text-center">
                        <div class="text-xl font-bold text-amber-400" id="dataset-examples">--</div>
                        <div class="text-[10px] text-gray-500">Training Examples</div>
                    </div>
                </div>
                <div class="text-xs text-gray-500 bg-gray-50/50 rounded p-2">
                    Path: scrape → structure → embed → retrieve → generate → cache → export JSONL → QLoRA fine-tune
                </div>
            </div>

            <!-- Workflow browser -->
            <div class="bg-white rounded-xl border border-gray-200 p-5">
                <div class="flex items-center justify-between mb-3">
                    <div class="text-sm font-medium text-gray-800">Workflows</div>
                    <span class="text-xs text-gray-600">{wf_count} total</span>
                </div>
                <div class="space-y-2 max-h-64 overflow-y-auto">
                    {wf_cards or '<div class="text-xs text-gray-600 py-4 text-center">No workflows yet. Run the scraper first.</div>'}
                </div>
            </div>
        </div>
    </div>
</div>

<!-- ============================================ -->
<!-- TAB 5: ML METRICS -->
<!-- ============================================ -->
<div class="tab-panel" id="tab-metrics">
    <h2 class="text-lg font-semibold text-gray-800 mb-4">ML Metrics & Model Performance</h2>

    <!-- Model Comparison -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div class="bg-white rounded-xl border border-gray-200 p-5">
            <div class="flex items-center gap-3 mb-4">
                <div class="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-sm">14B</div>
                <div>
                    <div class="text-sm font-medium text-gray-800">Generator</div>
                    <div class="text-xs text-gray-500">{generator_model}</div>
                </div>
            </div>
            <div class="space-y-2 text-xs">
                <div class="flex justify-between"><span class="text-gray-500">Role</span><span class="text-gray-600">HTML/CSS/JS Generation</span></div>
                <div class="flex justify-between"><span class="text-gray-500">VRAM</span><span class="text-gray-600">~8.5 GB (Q4_K_M)</span></div>
                <div class="flex justify-between"><span class="text-gray-500">Context</span><span class="text-gray-600">8,192 tokens</span></div>
                <div class="flex justify-between"><span class="text-gray-500">Max Output</span><span class="text-gray-600">6,144 tokens</span></div>
                <div class="flex justify-between"><span class="text-gray-500">Temperature</span><span class="text-gray-600">0.7</span></div>
                <div class="flex justify-between"><span class="text-gray-500">Avg Latency</span><span class="text-indigo-600" id="gen-avg-latency">--</span></div>
                <div class="flex justify-between"><span class="text-gray-500">Generations</span><span class="text-gray-600" id="gen-count">--</span></div>
            </div>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 p-5">
            <div class="flex items-center gap-3 mb-4">
                <div class="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center text-purple-400 font-bold text-sm">3B</div>
                <div>
                    <div class="text-sm font-medium text-gray-800">Router</div>
                    <div class="text-xs text-gray-500">{router_model}</div>
                </div>
            </div>
            <div class="space-y-2 text-xs">
                <div class="flex justify-between"><span class="text-gray-500">Role</span><span class="text-gray-600">Classification, Routing, Chat</span></div>
                <div class="flex justify-between"><span class="text-gray-500">VRAM</span><span class="text-gray-600">~2 GB (Q4)</span></div>
                <div class="flex justify-between"><span class="text-gray-500">Context</span><span class="text-gray-600">2,048 tokens</span></div>
                <div class="flex justify-between"><span class="text-gray-500">Max Output</span><span class="text-gray-600">512 tokens</span></div>
                <div class="flex justify-between"><span class="text-gray-500">Temperature</span><span class="text-gray-600">0.1</span></div>
                <div class="flex justify-between"><span class="text-gray-500">Avg Latency</span><span class="text-purple-400" id="rtr-avg-latency">--</span></div>
                <div class="flex justify-between"><span class="text-gray-500">Requests</span><span class="text-gray-600" id="rtr-count">--</span></div>
            </div>
        </div>
    </div>

    <!-- Metrics Grid -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <div class="stat-card rounded-lg p-4 border border-gray-200">
            <div class="text-[10px] text-gray-500 uppercase tracking-wider">Total Generations</div>
            <div class="text-2xl font-bold text-gray-800 mt-1" id="m-total-gen">--</div>
        </div>
        <div class="stat-card rounded-lg p-4 border border-gray-200">
            <div class="text-[10px] text-gray-500 uppercase tracking-wider">Cache Hit Rate</div>
            <div class="text-2xl font-bold text-blue-400 mt-1" id="m-cache-rate">--</div>
        </div>
        <div class="stat-card rounded-lg p-4 border border-gray-200">
            <div class="text-[10px] text-gray-500 uppercase tracking-wider">Avg Latency</div>
            <div class="text-2xl font-bold text-amber-400 mt-1" id="m-avg-latency">--</div>
        </div>
        <div class="stat-card rounded-lg p-4 border border-gray-200">
            <div class="text-[10px] text-gray-500 uppercase tracking-wider">RAG Generations</div>
            <div class="text-2xl font-bold text-cyan-400 mt-1" id="m-rag-gen">--</div>
        </div>
    </div>

    <!-- VRAM Gauge + GPU Info -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div class="bg-white rounded-xl border border-gray-200 p-5">
            <div class="text-sm font-medium text-gray-800 mb-4">VRAM Usage</div>
            <div id="vram-gauge" class="flex items-center gap-4">
                <div class="relative w-24 h-24">
                    <div class="metric-ring w-full h-full rounded-full flex items-center justify-center" style="--pct:0%">
                        <div class="w-20 h-20 rounded-full bg-white flex items-center justify-center">
                            <span id="vram-gauge-pct" class="text-lg font-bold text-gray-900">--%</span>
                        </div>
                    </div>
                </div>
                <div class="space-y-1 text-xs">
                    <div class="flex justify-between gap-8"><span class="text-gray-500">GPU</span><span id="vram-gpu-name" class="text-gray-600">--</span></div>
                    <div class="flex justify-between gap-8"><span class="text-gray-500">Used</span><span id="vram-used" class="text-gray-600">-- MB</span></div>
                    <div class="flex justify-between gap-8"><span class="text-gray-500">Total</span><span id="vram-total" class="text-gray-600">-- MB</span></div>
                    <div class="flex justify-between gap-8"><span class="text-gray-500">Temp</span><span id="vram-temp" class="text-gray-600">--C</span></div>
                    <div class="flex justify-between gap-8"><span class="text-gray-500">Util</span><span id="vram-util" class="text-gray-600">--%</span></div>
                </div>
            </div>
            <div class="mt-4 text-[10px] text-gray-600">
                Budget: 14B (~8.5GB) + 3B (~2GB) = ~10.5GB | Leaves ~5.5GB for KV cache
            </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 p-5">
            <div class="text-sm font-medium text-gray-800 mb-4">Fine-Tuning Status</div>
            <div class="space-y-2 text-xs">
                <div class="flex justify-between"><span class="text-gray-500">Base Model</span><span class="text-gray-600">Qwen2.5-Coder-14B</span></div>
                <div class="flex justify-between"><span class="text-gray-500">Method</span><span class="text-gray-600">QLoRA (4-bit, rank-32)</span></div>
                <div class="flex justify-between"><span class="text-gray-500">Training Data</span><span class="text-gray-600" id="ft-data-size">--</span></div>
                <div class="flex justify-between"><span class="text-gray-500">LoRA Rank</span><span class="text-gray-600">32</span></div>
                <div class="flex justify-between"><span class="text-gray-500">Batch Size</span><span class="text-gray-600">2 (eff. 16)</span></div>
                <div class="flex justify-between"><span class="text-gray-500">Learning Rate</span><span class="text-gray-600">1e-4</span></div>
                <div class="flex justify-between"><span class="text-gray-500">Target</span><span class="text-gray-600">RTX 4090 / RunPod</span></div>
            </div>
            <div class="mt-3 bg-gray-50 rounded p-2 text-[10px] text-gray-500">
                Pipeline: Generated playgrounds → JSONL dataset → QLoRA fine-tune → LoRA adapter → Merge into Ollama
            </div>
        </div>
    </div>

    <!-- Recent Generations Log -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-200">
            <h3 class="text-sm font-medium text-gray-400">Recent Activity</h3>
        </div>
        <div id="metrics-log" class="max-h-48 overflow-y-auto">
            <div class="px-4 py-6 text-center text-xs text-gray-400">Loading metrics...</div>
        </div>
    </div>
</div>

<!-- ============================================ -->
<!-- TAB 6: ML OBSERVATORY -->
<!-- ============================================ -->
<div class="tab-panel" id="tab-observatory">
    <!-- Sub-panel navigation -->
    <div class="flex items-center gap-6 mb-6 border-b border-gray-200 pb-3">
        <h2 class="text-lg font-semibold text-gray-800">ML Observatory</h2>
        <div class="flex gap-4">
            <button class="obs-panel-btn active text-sm font-medium" onclick="switchObsPanel('rag')" id="obs-btn-rag">RAG & Chunking</button>
            <button class="obs-panel-btn text-sm font-medium" onclick="switchObsPanel('training')" id="obs-btn-training">Training Lifecycle</button>
            <button class="obs-panel-btn text-sm font-medium" onclick="switchObsPanel('adapters')" id="obs-btn-adapters">Adapter Registry</button>
            <button class="obs-panel-btn text-sm font-medium" onclick="switchObsPanel('pipeline-diagram')" id="obs-btn-pipeline-diagram">Pipeline Diagram</button>
        </div>
    </div>

    <!-- Sub-Panel 1: RAG & Chunking Visualizer -->
    <div class="obs-panel" id="obs-rag">
        <!-- Stats row -->
        <div class="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
            <div class="stat-card rounded-lg p-4 border border-gray-200">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider">Total Chunks</div>
                <div class="text-2xl font-bold text-cyan-400 mt-1" id="obs-chunk-total">--</div>
            </div>
            <div class="stat-card rounded-lg p-4 border border-gray-200">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider">Avg Size</div>
                <div class="text-2xl font-bold text-gray-600 mt-1" id="obs-chunk-avg">--</div>
            </div>
            <div class="stat-card rounded-lg p-4 border border-gray-200">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider">Min Size</div>
                <div class="text-2xl font-bold text-gray-600 mt-1" id="obs-chunk-min">--</div>
            </div>
            <div class="stat-card rounded-lg p-4 border border-gray-200">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider">Max Size</div>
                <div class="text-2xl font-bold text-gray-600 mt-1" id="obs-chunk-max">--</div>
            </div>
            <div class="stat-card rounded-lg p-4 border border-gray-200">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider">Sources</div>
                <div class="text-2xl font-bold text-purple-400 mt-1" id="obs-chunk-sources">--</div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <!-- Size Histogram -->
            <div class="bg-white rounded-xl border border-gray-200 p-5">
                <div class="text-sm font-medium text-gray-800 mb-4">Chunk Size Distribution</div>
                <div id="obs-histogram" class="space-y-2"></div>
            </div>

            <!-- Workflow Breakdown -->
            <div class="bg-white rounded-xl border border-gray-200 p-5">
                <div class="text-sm font-medium text-gray-800 mb-4">Chunks per Workflow</div>
                <div id="obs-workflows" class="space-y-2 max-h-64 overflow-y-auto"></div>
            </div>
        </div>

        <!-- Chunk Browser -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
            <div class="flex items-center justify-between mb-4">
                <div class="text-sm font-medium text-gray-800">Chunk Browser</div>
                <div class="flex items-center gap-2">
                    <button onclick="loadChunks(Math.max(0, obsChunkOffset - 50))" class="text-xs bg-gray-200 text-gray-600 px-2 py-1 rounded hover:bg-gray-200">Prev</button>
                    <span id="obs-chunk-page" class="text-xs text-gray-500">0-0</span>
                    <button onclick="loadChunks(obsChunkOffset + 50)" class="text-xs bg-gray-200 text-gray-600 px-2 py-1 rounded hover:bg-gray-200">Next</button>
                </div>
            </div>
            <div id="obs-chunk-list" class="space-y-2 max-h-96 overflow-y-auto">
                <div class="text-xs text-gray-600 py-4 text-center">Loading chunks...</div>
            </div>
        </div>
    </div>

    <!-- Sub-Panel 2: Training Lifecycle -->
    <div class="obs-panel hidden" id="obs-training">
        <!-- Status Card -->
        <div class="bg-white rounded-xl border border-gray-200 p-5 mb-6">
            <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                    <span class="status-dot idle" id="obs-train-dot"></span>
                    <div>
                        <div class="text-sm font-medium text-gray-800" id="obs-train-status">Checking...</div>
                        <div class="text-xs text-gray-500" id="obs-train-message"></div>
                    </div>
                </div>
                <div class="text-xs text-gray-500" id="obs-train-adapter"></div>
            </div>
            <!-- Progress bar (visible when running) -->
            <div id="obs-train-progress" class="hidden mb-4">
                <div class="flex justify-between text-xs text-gray-500 mb-1">
                    <span id="obs-train-step">Step 0/0</span>
                    <span id="obs-train-epoch">Epoch 0/0</span>
                </div>
                <div class="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div id="obs-train-progress-bar" class="h-full rounded-full transition-all" style="width:0%;background:linear-gradient(90deg,#4f46e5,#818cf8)"></div>
                </div>
            </div>
            <!-- Quick Actions -->
            <div class="flex gap-2 mt-3 pt-3 border-t border-gray-200/50">
                <button onclick="switchTab('data'); setTimeout(()=>document.getElementById('prepare-btn')?.scrollIntoView({{behavior:'smooth'}}),300)"
                        class="text-xs btn-primary px-3 py-1.5 rounded-lg">Prepare Dataset</button>
                <button onclick="showTrainingCommand()"
                        class="text-xs bg-gray-200 text-gray-800 px-3 py-1.5 rounded-lg hover:bg-gray-300 transition-colors">Show Train Command</button>
                <button onclick="loadTrainingStatus(); loadTrainingLogs(); loadDatasetAnalytics()"
                        class="text-xs bg-gray-200 text-gray-800 px-3 py-1.5 rounded-lg hover:bg-gray-300 transition-colors ml-auto">Refresh</button>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <!-- Quality Distribution -->
            <div class="bg-white rounded-xl border border-gray-200 p-5">
                <div class="text-sm font-medium text-gray-800 mb-2">Dataset Quality Distribution</div>
                <div class="flex items-center gap-3 mb-4">
                    <span class="text-xs text-gray-500" id="obs-dataset-counts">-- train / -- val examples</span>
                </div>
                <div id="obs-quality-chart" class="space-y-2"></div>
                <div class="flex items-center gap-4 mt-3 text-[10px] text-gray-600">
                    <span>Avg instruction: <span id="obs-avg-inst" class="text-gray-400">--</span> chars</span>
                    <span>Avg output: <span id="obs-avg-out" class="text-gray-400">--</span> chars</span>
                </div>
            </div>

            <!-- Loss Curve -->
            <div class="bg-white rounded-xl border border-gray-200 p-5">
                <div class="text-sm font-medium text-gray-800 mb-4">Loss Curve</div>
                <div id="obs-loss-chart" class="flex items-center justify-center" style="min-height:200px">
                    <span class="text-xs text-gray-600">No training logs available</span>
                </div>
                <div class="flex items-center gap-4 mt-2 text-[10px]">
                    <span class="flex items-center gap-1"><span class="w-3 h-0.5 bg-indigo-500 inline-block"></span> <span class="text-gray-500">Train Loss</span></span>
                    <span class="flex items-center gap-1"><span class="w-3 h-0.5 bg-amber-400 inline-block" style="border-top:1px dashed #f59e0b"></span> <span class="text-gray-500">Eval Loss</span></span>
                </div>
            </div>
        </div>

        <!-- Training Examples Browser -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
            <div class="flex items-center justify-between mb-4">
                <div class="text-sm font-medium text-gray-800">Training Examples</div>
                <div class="flex items-center gap-2">
                    <select id="obs-example-file" class="bg-white border border-gray-300 rounded px-2 py-1 text-xs text-gray-600" onchange="loadTrainingExamples(0)">
                        <option value="train">train.jsonl</option>
                        <option value="val">val.jsonl</option>
                    </select>
                    <button onclick="loadTrainingExamples(Math.max(0, obsExampleOffset - 20))" class="text-xs bg-gray-200 text-gray-600 px-2 py-1 rounded hover:bg-gray-200">Prev</button>
                    <span id="obs-example-page" class="text-xs text-gray-500">0-0</span>
                    <button onclick="loadTrainingExamples(obsExampleOffset + 20)" class="text-xs bg-gray-200 text-gray-600 px-2 py-1 rounded hover:bg-gray-200">Next</button>
                </div>
            </div>
            <div id="obs-example-list" class="space-y-2 max-h-96 overflow-y-auto">
                <div class="text-xs text-gray-600 py-4 text-center">Select a file to browse examples</div>
            </div>
        </div>
    </div>

    <!-- Sub-Panel 3: Adapter Registry -->
    <div class="obs-panel hidden" id="obs-adapters">
        <div id="obs-adapter-list" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div class="col-span-full text-center py-12">
                <div class="text-4xl mb-3 opacity-30">&#9881;</div>
                <div class="text-sm text-gray-500 font-medium">Loading adapters...</div>
            </div>
        </div>
    </div>

    <!-- Sub-Panel 4: Pipeline Diagram -->
    <div class="obs-panel hidden" id="obs-pipeline-diagram">
        <div class="bg-white rounded-xl border border-gray-200 p-5 mb-4">
            <div class="flex items-center justify-between mb-2">
                <div>
                    <h3 class="text-sm font-semibold text-gray-800">QLoRA Fine-Tuning Pipeline</h3>
                    <p class="text-xs text-gray-500 mt-1">End-to-end flow from raw scraped data to deployable LoRA adapter. Hover nodes for details.</p>
                </div>
                <div class="flex items-center gap-3">
                    <div class="text-xs text-gray-500">
                        <span class="text-indigo-400 font-medium">194</span> train &middot;
                        <span class="text-indigo-400 font-medium">22</span> val &middot;
                        <span class="text-indigo-400 font-medium">75</span> steps &middot;
                        <span class="text-indigo-400 font-medium">3</span> epochs
                    </div>
                </div>
            </div>
        </div>

        <div class="pipeline-mermaid relative" id="pipeline-mermaid-container">
            <div id="mermaid-diagram"></div>
            <div class="mermaid-tooltip" id="mermaid-tooltip">
                <div class="tt-title"></div>
                <div class="tt-body"></div>
            </div>
        </div>

        <!-- Metrics Summary Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 mt-4">
            <div class="stat-card rounded-lg p-3 border border-gray-200">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider">Base Model</div>
                <div class="text-sm font-bold text-cyan-400 mt-1">Qwen2.5-7B</div>
                <div class="text-[10px] text-gray-600">Instruct variant</div>
            </div>
            <div class="stat-card rounded-lg p-3 border border-gray-200">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider">Quantization</div>
                <div class="text-sm font-bold text-purple-400 mt-1">4-bit NF4</div>
                <div class="text-[10px] text-gray-600">QLoRA + bfloat16</div>
            </div>
            <div class="stat-card rounded-lg p-3 border border-gray-200">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider">LoRA Config</div>
                <div class="text-sm font-bold text-indigo-400 mt-1">r=16, a=32</div>
                <div class="text-[10px] text-gray-600">7 target modules</div>
            </div>
            <div class="stat-card rounded-lg p-3 border border-gray-200">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider">Final Loss</div>
                <div class="text-sm font-bold text-green-400 mt-1">0.164</div>
                <div class="text-[10px] text-gray-600">from 0.891 start</div>
            </div>
            <div class="stat-card rounded-lg p-3 border border-gray-200">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider">Token Accuracy</div>
                <div class="text-sm font-bold text-amber-400 mt-1">95.8%</div>
                <div class="text-[10px] text-gray-600">from 79.1% start</div>
            </div>
            <div class="stat-card rounded-lg p-3 border border-gray-200">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider">GPU</div>
                <div class="text-sm font-bold text-red-400 mt-1">RTX 4090</div>
                <div class="text-[10px] text-gray-600">16GB VRAM</div>
            </div>
        </div>

        <!-- Legend -->
        <div class="pipeline-legend mt-3">
            <span><span class="dot" style="background:#4f46e5"></span> Data Pipeline</span>
            <span><span class="dot" style="background:#818cf8"></span> Model & LoRA</span>
            <span><span class="dot" style="background:#22c55e"></span> Training Loop</span>
            <span><span class="dot" style="background:#f59e0b"></span> Output Artifacts</span>
            <span><span class="dot" style="background:#ef4444"></span> GPU Resources</span>
        </div>
    </div>
</div>

<!-- ============================================ -->
<!-- TAB 7: AGENT OBSERVABILITY -->
<!-- ============================================ -->
<div class="tab-panel" id="tab-agent">
    <!-- Stats Row -->
    <div class="grid grid-cols-2 md:grid-cols-6 gap-3 mb-6">
        <div class="stat-card rounded-lg p-4 border border-gray-200 glow">
            <div class="text-[10px] text-gray-500 uppercase tracking-wider">Total Traces</div>
            <div class="text-2xl font-bold text-indigo-600 mt-1" id="ag-total-traces">--</div>
        </div>
        <div class="stat-card rounded-lg p-4 border border-gray-200">
            <div class="text-[10px] text-gray-500 uppercase tracking-wider">Avg Latency</div>
            <div class="text-2xl font-bold text-amber-400 mt-1" id="ag-avg-latency">--</div>
        </div>
        <div class="stat-card rounded-lg p-4 border border-gray-200">
            <div class="text-[10px] text-gray-500 uppercase tracking-wider">Cache Hit Rate</div>
            <div class="text-2xl font-bold text-blue-400 mt-1" id="ag-cache-rate">--</div>
        </div>
        <div class="stat-card rounded-lg p-4 border border-gray-200">
            <div class="text-[10px] text-gray-500 uppercase tracking-wider">Avg Confidence</div>
            <div class="text-2xl font-bold text-green-400 mt-1" id="ag-avg-conf">--</div>
        </div>
        <div class="stat-card rounded-lg p-4 border border-gray-200">
            <div class="text-[10px] text-gray-500 uppercase tracking-wider">Tokens Saved</div>
            <div class="text-2xl font-bold text-cyan-400 mt-1" id="ag-tokens-saved">--</div>
        </div>
        <div class="stat-card rounded-lg p-4 border border-gray-200">
            <div class="text-[10px] text-gray-500 uppercase tracking-wider">Last 24h</div>
            <div class="text-2xl font-bold text-purple-400 mt-1" id="ag-24h">--</div>
        </div>
    </div>

    <!-- Main content: Latest Trace + Routing -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <!-- Latest Trace Timeline (2/3 width) -->
        <div class="lg:col-span-2 bg-white rounded-xl border border-gray-200 p-5">
            <div class="flex items-center justify-between mb-4">
                <div class="text-sm font-medium text-gray-800">Latest Agent Trace</div>
                <button onclick="loadAgentData()" class="text-xs bg-gray-200 text-gray-600 px-3 py-1 rounded hover:bg-gray-300 transition-colors">Refresh</button>
            </div>
            <div id="ag-latest-trace" class="space-y-1">
                <div class="text-xs text-gray-600 text-center py-8">No traces yet. Generate a playground to see the agent pipeline in action.</div>
            </div>
        </div>

        <!-- Right column: Model Distribution + Router -->
        <div class="space-y-6">
            <!-- Model Distribution -->
            <div class="bg-white rounded-xl border border-gray-200 p-5">
                <div class="text-sm font-medium text-gray-800 mb-4">Model Distribution</div>
                <div id="ag-model-dist" class="space-y-3">
                    <div class="text-xs text-gray-600 text-center py-4">No data</div>
                </div>
            </div>

            <!-- Router Method -->
            <div class="bg-white rounded-xl border border-gray-200 p-5">
                <div class="text-sm font-medium text-gray-800 mb-4">Router Method</div>
                <div id="ag-router-methods" class="space-y-3">
                    <div class="text-xs text-gray-600 text-center py-4">No data</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Step Latency Breakdown + Token Economy -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <!-- Per-Step Avg Latency -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
            <div class="text-sm font-medium text-gray-800 mb-4">Avg Latency per Pipeline Step</div>
            <div id="ag-step-latency" class="space-y-2">
                <div class="text-xs text-gray-600 text-center py-4">No data</div>
            </div>
        </div>

        <!-- Token Economy -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
            <div class="text-sm font-medium text-gray-800 mb-4">Token Economy</div>
            <div id="ag-token-economy" class="space-y-3">
                <div class="text-xs text-gray-600 text-center py-4">No data</div>
            </div>
        </div>
    </div>

    <!-- Trace History Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
            <h3 class="text-sm font-medium text-gray-400 uppercase tracking-wider">Agent Trace History</h3>
            <span class="text-xs text-gray-600" id="ag-trace-count">-- traces</span>
        </div>
        <div id="ag-trace-table" class="max-h-80 overflow-y-auto">
            <div class="px-4 py-6 text-center text-xs text-gray-600">Loading traces...</div>
        </div>
    </div>
</div>

<!-- ============================================ -->
<!-- TAB 8: EMBEDDINGS & STORAGE -->
<!-- ============================================ -->
<div class="tab-panel" id="tab-embeddings">
    <!-- Sub-panel navigation -->
    <div class="flex items-center gap-6 mb-6 border-b border-gray-200 pb-3">
        <h2 class="text-lg font-semibold text-gray-800">Embeddings & Storage</h2>
        <div class="flex gap-4">
            <button class="emb-panel-btn active text-sm font-medium" onclick="switchEmbPanel('space')" id="emb-btn-space">Embedding Space</button>
            <button class="emb-panel-btn text-sm font-medium" onclick="switchEmbPanel('chromadb')" id="emb-btn-chromadb">ChromaDB Inspector</button>
            <button class="emb-panel-btn text-sm font-medium" onclick="switchEmbPanel('storage')" id="emb-btn-storage">Storage Map</button>
        </div>
    </div>

    <!-- Sub-Panel A: Embedding Space -->
    <div class="emb-panel" id="emb-space">
        <!-- Stats row -->
        <div class="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
            <div class="stat-card rounded-lg p-4 border border-gray-200">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider">Total Embeddings</div>
                <div class="text-2xl font-bold text-cyan-400 mt-1" id="emb-total">--</div>
            </div>
            <div class="stat-card rounded-lg p-4 border border-gray-200">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider">Categories</div>
                <div class="text-2xl font-bold text-purple-400 mt-1" id="emb-categories">--</div>
            </div>
            <div class="stat-card rounded-lg p-4 border border-gray-200">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider">Embed Dims</div>
                <div class="text-2xl font-bold text-amber-400 mt-1" id="emb-dims">--</div>
            </div>
            <div class="stat-card rounded-lg p-4 border border-gray-200">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider">Collection</div>
                <div class="text-lg font-bold text-gray-600 mt-1" id="emb-collection">--</div>
            </div>
            <div class="stat-card rounded-lg p-4 border border-gray-200">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider">Projection</div>
                <div class="text-lg font-bold text-indigo-400 mt-1" id="emb-projection">UMAP</div>
            </div>
        </div>

        <!-- Controls + Plotly chart -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="lg:col-span-2">
                <div class="flex items-center gap-3 mb-3">
                    <div class="flex bg-gray-200 rounded-lg overflow-hidden">
                        <button id="emb-btn-3d" onclick="toggleEmbDims(3)" class="px-4 py-1.5 text-xs font-medium bg-indigo-500 text-white transition-colors">3D</button>
                        <button id="emb-btn-2d" onclick="toggleEmbDims(2)" class="px-4 py-1.5 text-xs font-medium text-gray-500 transition-colors">2D</button>
                    </div>
                    <span class="text-xs text-gray-500" id="emb-status">Loading UMAP projection...</span>
                </div>
                <div id="emb-plotly" style="width:100%;height:520px;background:#1a1d2b;border-radius:12px;border:1px solid rgba(255,255,255,0.09)"></div>
            </div>
            <div class="space-y-4">
                <div class="bg-white rounded-xl border border-gray-200 p-5">
                    <div class="text-sm font-medium text-gray-800 mb-3">Point Details</div>
                    <div id="emb-point-details" class="text-xs text-gray-600">
                        Click a point on the scatter plot to see chunk details here.
                    </div>
                </div>
                <div class="bg-white rounded-xl border border-gray-200 p-5">
                    <div class="text-sm font-medium text-gray-800 mb-3">Category Legend</div>
                    <div id="emb-legend" class="space-y-1.5 max-h-64 overflow-y-auto"></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Sub-Panel B: ChromaDB Inspector -->
    <div class="emb-panel hidden" id="emb-chromadb">
        <!-- Stats cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            <div class="stat-card rounded-lg p-4 border border-gray-200">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider">Total Chunks</div>
                <div class="text-2xl font-bold text-cyan-400 mt-1" id="cdb-total">--</div>
            </div>
            <div class="stat-card rounded-lg p-4 border border-gray-200">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider">Embed Model</div>
                <div class="text-lg font-bold text-gray-600 mt-1" id="cdb-model">--</div>
            </div>
            <div class="stat-card rounded-lg p-4 border border-gray-200">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider">Collection</div>
                <div class="text-lg font-bold text-gray-600 mt-1" id="cdb-collection">--</div>
            </div>
            <div class="stat-card rounded-lg p-4 border border-gray-200">
                <div class="text-[10px] text-gray-500 uppercase tracking-wider">DB Path</div>
                <div class="text-xs font-mono text-gray-600 mt-1 truncate" id="cdb-path">--</div>
            </div>
        </div>

        <!-- Charts row -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <!-- Chunk type distribution -->
            <div class="bg-white rounded-xl border border-gray-200 p-5">
                <div class="text-sm font-medium text-gray-800 mb-4">Chunk Type Distribution</div>
                <div id="cdb-type-dist" class="space-y-2">
                    <div class="text-xs text-gray-600 text-center py-4">Loading...</div>
                </div>
            </div>
            <!-- Per-workflow chunk counts -->
            <div class="bg-white rounded-xl border border-gray-200 p-5">
                <div class="text-sm font-medium text-gray-800 mb-4">Chunks per Workflow</div>
                <div id="cdb-workflow-dist" class="space-y-2 max-h-52 overflow-y-auto">
                    <div class="text-xs text-gray-600 text-center py-4">Loading...</div>
                </div>
            </div>
            <!-- Size histogram -->
            <div class="bg-white rounded-xl border border-gray-200 p-5">
                <div class="text-sm font-medium text-gray-800 mb-4">Size Distribution</div>
                <div id="cdb-size-hist" class="space-y-1">
                    <div class="text-xs text-gray-600 text-center py-4">Loading...</div>
                </div>
            </div>
        </div>

        <!-- Chunk Browser -->
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div class="px-4 py-3 border-b border-gray-200 flex items-center justify-between flex-wrap gap-2">
                <h3 class="text-sm font-medium text-gray-400 uppercase tracking-wider">Chunk Browser</h3>
                <div class="flex items-center gap-2">
                    <input id="cdb-search" type="text" placeholder="Search chunks..." oninput="filterCdbChunks()"
                        class="bg-white border border-gray-300 rounded px-3 py-1 text-xs text-gray-700 w-48 focus:outline-none focus:border-indigo-400">
                    <span class="text-xs text-gray-600" id="cdb-chunk-count">--</span>
                </div>
            </div>
            <div id="cdb-chunk-list" class="max-h-96 overflow-y-auto">
                <div class="px-4 py-6 text-center text-xs text-gray-600">Loading chunks...</div>
            </div>
            <div class="px-4 py-3 border-t border-gray-200 flex items-center justify-center gap-2" id="cdb-pagination"></div>
        </div>
    </div>

    <!-- Sub-Panel C: Storage Map -->
    <div class="emb-panel hidden" id="emb-storage">
        <!-- Total size header -->
        <div class="stat-card rounded-lg p-5 border border-gray-200 glow mb-6 flex items-center justify-between">
            <div>
                <div class="text-[10px] text-gray-500 uppercase tracking-wider">Total Storage Used</div>
                <div class="text-3xl font-bold text-indigo-600 mt-1" id="stor-total">--</div>
            </div>
            <button onclick="loadStorageOverview()" class="text-xs bg-gray-200 text-gray-600 px-3 py-1 rounded hover:bg-gray-300 transition-colors">Refresh</button>
        </div>

        <!-- Proportional bar -->
        <div class="bg-white rounded-xl border border-gray-200 p-5 mb-6">
            <div class="text-sm font-medium text-gray-800 mb-3">Storage Distribution</div>
            <div id="stor-bar" class="w-full rounded overflow-hidden flex" style="height:24px;background:#2f3549"></div>
            <div id="stor-bar-legend" class="flex gap-4 flex-wrap mt-3"></div>
        </div>

        <!-- Directory cards -->
        <div class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6" id="stor-dirs"></div>

        <!-- SQLite + Cache -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Databases -->
            <div class="bg-white rounded-xl border border-gray-200 p-5">
                <div class="text-sm font-medium text-gray-800 mb-4">SQLite Databases</div>
                <div id="stor-databases" class="space-y-4">
                    <div class="text-xs text-gray-600 text-center py-4">Loading...</div>
                </div>
            </div>
            <!-- Cache + Feedback -->
            <div class="bg-white rounded-xl border border-gray-200 p-5">
                <div class="text-sm font-medium text-gray-800 mb-4">Cache & Feedback</div>
                <div id="stor-cache" class="space-y-3">
                    <div class="text-xs text-gray-600 text-center py-4">Loading...</div>
                </div>
            </div>
        </div>
    </div>
</div>

</main>

<!-- ============================================ -->
<!-- JAVASCRIPT -->
<!-- ============================================ -->
<script>
// === Tab Switching ===
function switchTab(tabId) {{
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-' + tabId).classList.add('active');
    document.querySelector(`[data-tab="${{tabId}}"]`).classList.add('active');
    if (tabId === 'pipeline') loadPipeline();
    if (tabId === 'metrics') loadMetrics();
    if (tabId === 'data') loadDataStats();
    if (tabId === 'observatory') loadObservatory();
    if (tabId === 'agent') loadAgentData();
    if (tabId === 'embeddings') loadEmbeddings();
}}

// === Generate ===
let generating = false;
async function generate() {{
    if (generating) return;
    const prompt = document.getElementById('prompt').value.trim();
    if (!prompt) return;

    generating = true;
    const btn = document.getElementById('gen-btn');
    const panel = document.getElementById('stream-panel');
    const output = document.getElementById('stream-output');
    const status = document.getElementById('stream-status');
    const spinner = document.getElementById('stream-spinner');
    const chatResp = document.getElementById('chat-response');
    const ragCtx = document.getElementById('rag-context');
    const genMeta = document.getElementById('gen-meta');
    const style = document.getElementById('style').value;

    btn.disabled = true;
    btn.textContent = 'Generating...';
    panel.classList.remove('hidden');
    chatResp.classList.add('hidden');
    output.textContent = '';
    ragCtx.innerHTML = '<span class="text-gray-400">Querying RAG...</span>';
    genMeta.textContent = '';
    status.textContent = 'Routing request...';
    spinner.classList.remove('hidden');

    try {{
        const resp = await fetch('/api/generate/stream', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{ prompt, style, force_generate: false }})
        }});

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {{
            const {{ done, value }} = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, {{ stream: true }});
            const lines = buffer.split('\\n');
            buffer = lines.pop();

            for (const line of lines) {{
                if (!line.startsWith('data: ')) continue;
                try {{
                    const data = JSON.parse(line.slice(6));
                    if (data.type === 'status') {{
                        status.textContent = data.message;
                    }} else if (data.type === 'rag') {{
                        ragCtx.innerHTML = data.preview.map((p,i) =>
                            `<div class="mb-2 p-2 bg-gray-50 rounded border border-gray-200"><span class="text-cyan-500">Chunk ${{i+1}}:</span> ${{p}}</div>`
                        ).join('');
                        genMeta.textContent = `RAG: ${{data.chunks}} chunks`;
                    }} else if (data.type === 'chunk') {{
                        output.textContent += data.content;
                        output.scrollTop = output.scrollHeight;
                    }} else if (data.type === 'cache_hit') {{
                        status.textContent = 'Cache hit! Loading instantly...';
                        ragCtx.innerHTML = '<span class="text-indigo-600">Cache hit - no RAG needed</span>';
                    }} else if (data.type === 'done') {{
                        status.textContent = 'Done!';
                        spinner.classList.add('hidden');
                        if (data.latency_ms) genMeta.textContent += ` | ${{Math.round(data.latency_ms)}}ms`;
                        if (data.playground_id) {{
                            window.open('/playground/' + data.playground_id, '_blank');
                        }}
                    }} else if (data.type === 'error') {{
                        status.textContent = 'Error: ' + data.message;
                        output.textContent = data.message;
                    }}
                }} catch (e) {{}}
            }}
        }}
    }} catch (e) {{
        status.textContent = 'Error: ' + e.message;
    }} finally {{
        generating = false;
        btn.disabled = false;
        btn.textContent = 'Generate';
        spinner.classList.add('hidden');
        setTimeout(() => location.reload(), 3000);
    }}
}}

async function generateFromWorkflow(wfId) {{
    document.getElementById('stream-panel').classList.remove('hidden');
    document.getElementById('stream-status').textContent = 'Generating from workflow...';
    document.getElementById('stream-spinner').classList.remove('hidden');
    try {{
        const resp = await fetch('/api/generate/workflow', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{ workflow_id: wfId }})
        }});
        const data = await resp.json();
        if (data.playground_id) {{
            window.open('/playground/' + data.playground_id, '_blank');
            setTimeout(() => location.reload(), 1000);
        }}
    }} catch (e) {{
        document.getElementById('stream-status').textContent = 'Error: ' + e.message;
    }} finally {{
        document.getElementById('stream-spinner').classList.add('hidden');
    }}
}}

// === RAG ===
async function ingestRAG() {{
    const btn = document.getElementById('ingest-btn');
    btn.disabled = true;
    btn.textContent = 'Ingesting...';
    try {{
        const resp = await fetch('/api/rag/ingest', {{ method: 'POST' }});
        const data = await resp.json();
        const wf = data.workflows || {{}};
        const pg = data.pages || {{}};
        btn.textContent = `Done! ${{wf.chunks_added || 0}} wf + ${{pg.pages_ingested || 0}} pg chunks`;
        document.getElementById('rag-chunk-count').textContent = (wf.chunks_added || 0) + (pg.pages_ingested || 0);
        setTimeout(() => {{ btn.textContent = 'Ingest Workflows'; btn.disabled = false; }}, 3000);
    }} catch (e) {{
        btn.textContent = 'Error: ' + e.message;
        setTimeout(() => {{ btn.textContent = 'Ingest Workflows'; btn.disabled = false; }}, 3000);
    }}
}}

async function clearRAG() {{
    if (!confirm('Clear all RAG embeddings?')) return;
    await fetch('/api/rag/clear', {{ method: 'POST' }});
    document.getElementById('rag-chunk-count').textContent = '0';
}}

async function testRAG() {{
    const query = document.getElementById('rag-query').value.trim();
    if (!query) return;
    const el = document.getElementById('rag-results');
    el.innerHTML = '<span class="text-gray-600">Searching...</span>';
    try {{
        const resp = await fetch('/api/rag/query', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{ query, top_k: 5 }})
        }});
        const data = await resp.json();
        if (data.chunks && data.chunks.length > 0) {{
            el.innerHTML = data.chunks.map((c, i) => {{
                const dist = c.distance ? ` <span class="text-gray-600">(dist: ${{c.distance.toFixed(3)}})</span>` : '';
                const meta = c.metadata ? ` <span class="text-gray-400">[${{c.metadata.chunk_type || ''}}]</span>` : '';
                return `<div class="mb-2 p-2 bg-gray-50 rounded border border-gray-200">
                    <span class="text-cyan-500 font-medium">Result ${{i+1}}</span>${{dist}}${{meta}}
                    <div class="mt-1 text-gray-400">${{c.content.substring(0, 300)}}</div>
                </div>`;
            }}).join('');
        }} else {{
            el.innerHTML = '<span class="text-gray-600">No results. Try ingesting workflows first.</span>';
        }}
    }} catch (e) {{
        el.innerHTML = `<span class="text-red-400">Error: ${{e.message}}</span>`;
    }}
}}

// === Dataset Preparation ===
async function prepareDataset() {{
    const btn = document.getElementById('prepare-btn');
    const status = document.getElementById('prepare-status');
    btn.disabled = true;
    btn.textContent = 'Preparing...';
    status.classList.remove('hidden');
    status.innerHTML = '<span class="text-indigo-600">Collecting examples from generated playgrounds...</span>';
    try {{
        const resp = await fetch('/api/dataset/prepare', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{ min_quality: 2, split_ratio: 0.9 }})
        }});
        const data = await resp.json();
        if (data.status === 'ok') {{
            status.innerHTML = `<span class="text-indigo-600 font-medium">Dataset prepared!</span> ${{data.train_size}} train / ${{data.val_size}} val examples from ${{data.total_examples}} total. Quality: ${{data.quality_distribution}}`;
            loadDataStats();
        }} else {{
            status.innerHTML = `<span class="text-amber-600">${{data.message}}</span>`;
        }}
    }} catch (e) {{
        status.innerHTML = `<span class="text-red-500">Error: ${{e.message}}</span>`;
    }} finally {{
        btn.disabled = false;
        btn.textContent = 'Prepare Dataset';
    }}
}}

function showTrainingCommand() {{
    const cmd = 'python -m fine_tuning.train_lora --local';
    const status = document.getElementById('prepare-status');
    status.classList.remove('hidden');
    status.innerHTML = `<div class="space-y-1">
        <div class="text-indigo-600 font-medium">Training command:</div>
        <code class="block px-3 py-2 rounded text-[11px] font-mono select-all">${{cmd}}</code>
        <div class="text-gray-400 text-[10px]">Run this in your terminal. Requires torch, transformers, peft, trl, bitsandbytes.</div>
        <div class="text-gray-400 text-[10px]">For cloud training: <code class="text-gray-500">python -m fine_tuning.train_lora</code> (uses 14B model on RunPod)</div>
    </div>`;
}}

// === Pipeline ===
async function loadPipeline() {{
    try {{
        let data;
        if (window._preloadedPipeline) {{
            data = window._preloadedPipeline;
            delete window._preloadedPipeline;
        }} else {{
            const resp = await fetch('/api/pipeline/status');
            data = await resp.json();
        }}
        const phases = data.phases || {{}};
        for (const [key, phase] of Object.entries(phases)) {{
            const el = document.getElementById('phase-' + key + '-count');
            if (el) el.textContent = phase.count + ' ' + phase.label.toLowerCase();
        }}
    }} catch (e) {{}}
}}

// === Metrics ===
async function loadMetrics() {{
    try {{
        let data;
        if (window._preloadedMetrics) {{
            data = window._preloadedMetrics;
            delete window._preloadedMetrics;
        }} else {{
            const resp = await fetch('/api/metrics');
            data = await resp.json();
        }}
        if (!data.enabled) {{
            document.getElementById('metrics-log').innerHTML =
                '<div class="px-4 py-6 text-center text-xs text-gray-400">Metrics collection not enabled</div>';
            return;
        }}

        document.getElementById('m-total-gen').textContent = data.total_generations || 0;
        document.getElementById('m-cache-rate').textContent = data.cache_hit_rate || '0%';
        document.getElementById('m-avg-latency').textContent = (data.avg_latency_ms || 0) + 'ms';
        document.getElementById('m-rag-gen').textContent = data.rag_generations || 0;

        // Model breakdown
        const breakdown = data.model_breakdown || {{}};
        for (const [model, info] of Object.entries(breakdown)) {{
            if (model.includes('14b') || model.includes('coder')) {{
                document.getElementById('gen-avg-latency').textContent = info.avg_latency_ms + 'ms';
                document.getElementById('gen-count').textContent = info.count;
            }} else if (model.includes('3b') || model === 'cache') {{
                document.getElementById('rtr-avg-latency').textContent = info.avg_latency_ms + 'ms';
                document.getElementById('rtr-count').textContent = info.count;
            }}
        }}

        // VRAM gauge
        const vram = data.vram;
        if (vram) {{
            const pct = Math.round(vram.used_mb / vram.total_mb * 100);
            document.querySelector('.metric-ring').style.setProperty('--pct', pct + '%');
            document.getElementById('vram-gauge-pct').textContent = pct + '%';
            document.getElementById('vram-gpu-name').textContent = 'RTX 4090';
            document.getElementById('vram-used').textContent = vram.used_mb + ' MB';
            document.getElementById('vram-total').textContent = vram.total_mb + ' MB';
            document.getElementById('vram-temp').textContent = vram.temp_c + 'C';
            document.getElementById('vram-util').textContent = vram.utilization_pct + '%';
        }}

        // Recent activity log
        const recent = data.recent || [];
        if (recent.length > 0) {{
            document.getElementById('metrics-log').innerHTML = recent.map(r => {{
                const cacheTag = r.cache_hit ? '<span class="text-indigo-600 text-[10px]">CACHE</span>' : '';
                const ragTag = r.rag_chunks_used > 0 ? `<span class="text-cyan-500 text-[10px]">RAG:${{r.rag_chunks_used}}</span>` : '';
                return `<div class="px-4 py-2 border-b border-gray-200 flex items-center gap-3 text-xs">
                    <span class="text-gray-600 w-32 shrink-0">${{r.timestamp.substring(5, 16)}}</span>
                    <span class="text-gray-400 truncate flex-1">${{r.prompt?.substring(0, 60) || '-'}}</span>
                    <span class="text-gray-500 w-16">${{r.model?.split(':')[0] || ''}}</span>
                    <span class="text-amber-400 w-16">${{r.latency_ms}}ms</span>
                    ${{cacheTag}} ${{ragTag}}
                </div>`;
            }}).join('');
        }}
    }} catch (e) {{}}
}}

// === Data Stats ===
async function loadDataStats() {{
    try {{
        const resp = await fetch('/api/dataset/stats');
        const data = await resp.json();
        document.getElementById('dataset-files').textContent = data.training_files || 0;
        document.getElementById('dataset-examples').textContent = data.total_examples || 0;
        document.getElementById('ft-data-size').textContent = (data.total_examples || 0) + ' examples';
    }} catch (e) {{}}
}}

// === Observatory ===
let obsChunkOffset = 0;
let obsExampleOffset = 0;
let obsLoaded = {{ rag: false, training: false, adapters: false, 'pipeline-diagram': false }};

function loadObservatory() {{
    switchObsPanel('rag');
}}

function switchObsPanel(panel) {{
    document.querySelectorAll('.obs-panel').forEach(p => p.classList.add('hidden'));
    document.querySelectorAll('.obs-panel-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('obs-' + panel).classList.remove('hidden');
    document.getElementById('obs-btn-' + panel).classList.add('active');
    if (panel === 'rag' && !obsLoaded.rag) {{ Promise.all([loadChunkAnalytics(), loadChunks(0)]); obsLoaded.rag = true; }}
    if (panel === 'training' && !obsLoaded.training) {{ Promise.all([loadTrainingStatus(), loadTrainingLogs(), loadDatasetAnalytics(), loadTrainingExamples(0)]); obsLoaded.training = true; }}
    if (panel === 'adapters' && !obsLoaded.adapters) {{ loadAdapters(); obsLoaded.adapters = true; }}
    if (panel === 'pipeline-diagram' && !obsLoaded['pipeline-diagram']) {{ renderPipelineDiagram(); obsLoaded['pipeline-diagram'] = true; }}
}}

async function loadChunkAnalytics() {{
    try {{
        const resp = await fetch('/api/observatory/chunk-analytics');
        const data = await resp.json();
        document.getElementById('obs-chunk-total').textContent = data.total || 0;
        document.getElementById('obs-chunk-avg').textContent = (data.avg_size || 0) + ' chars';
        document.getElementById('obs-chunk-min').textContent = (data.min_size || 0);
        document.getElementById('obs-chunk-max').textContent = (data.max_size || 0);
        document.getElementById('obs-chunk-sources').textContent = Object.keys(data.sources || {{}}).length;

        // Histogram
        const histogram = data.histogram || [];
        const maxCount = Math.max(...histogram.map(h => h.count), 1);
        document.getElementById('obs-histogram').innerHTML = histogram.map(h => {{
            const pct = Math.round(h.count / maxCount * 100);
            return `<div class="flex items-center gap-2">
                <span class="text-xs text-gray-500 w-16 text-right">${{h.label}}</span>
                <div class="flex-1 h-5 bg-white rounded overflow-hidden">
                    <div class="obs-bar h-full bg-indigo-500/80 rounded" style="width:${{pct}}%"></div>
                </div>
                <span class="text-xs text-gray-400 w-8">${{h.count}}</span>
            </div>`;
        }}).join('');

        // Workflow breakdown
        const workflows = data.workflows || {{}};
        const wfEntries = Object.entries(workflows);
        const wfMax = Math.max(...wfEntries.map(([,c]) => c), 1);
        document.getElementById('obs-workflows').innerHTML = wfEntries.length > 0
            ? wfEntries.map(([id, count]) => {{
                const pct = Math.round(count / wfMax * 100);
                return `<div class="flex items-center gap-2">
                    <span class="text-xs text-gray-400 w-40 truncate" title="${{id}}">${{id}}</span>
                    <div class="flex-1 h-4 bg-white rounded overflow-hidden">
                        <div class="obs-bar h-full bg-purple-500/70 rounded" style="width:${{pct}}%"></div>
                    </div>
                    <span class="text-xs text-gray-500 w-8">${{count}}</span>
                </div>`;
            }}).join('')
            : '<div class="text-xs text-gray-600 text-center py-4">No workflow data</div>';
    }} catch (e) {{}}
}}

async function loadChunks(offset) {{
    obsChunkOffset = offset;
    try {{
        const resp = await fetch(`/api/observatory/chunks?offset=${{offset}}&limit=50`);
        const data = await resp.json();
        const chunks = data.chunks || [];
        const total = data.total || 0;
        document.getElementById('obs-chunk-page').textContent = `${{offset + 1}}-${{Math.min(offset + 50, total)}} of ${{total}}`;

        if (chunks.length === 0) {{
            document.getElementById('obs-chunk-list').innerHTML = `<div class="text-center py-8">
                <div class="text-4xl mb-3 opacity-20">&#x1F4E6;</div>
                <div class="text-sm text-gray-500 font-medium mb-1">No RAG Chunks</div>
                <div class="text-xs text-gray-400">Go to Data & RAG tab and click "Ingest Workflows" to populate the vector store.</div>
            </div>`;
            return;
        }}

        document.getElementById('obs-chunk-list').innerHTML = chunks.map((c, i) => {{
            const meta = c.metadata || {{}};
            const typeTag = meta.chunk_type ? `<span class="text-[10px] bg-gray-200 text-gray-400 px-1 rounded">${{meta.chunk_type}}</span>` : '';
            const catTag = meta.category ? `<span class="text-[10px] bg-gray-200 text-gray-400 px-1 rounded">${{meta.category}}</span>` : '';
            const idx = offset + i;
            return `<div class="bg-gray-50 rounded-lg border border-gray-300 p-3">
                <div class="flex items-center justify-between mb-1">
                    <div class="flex items-center gap-2">
                        <span class="text-xs text-gray-500">#${{idx + 1}}</span>
                        ${{typeTag}} ${{catTag}}
                        <span class="text-[10px] text-gray-600">${{c.size}} chars</span>
                    </div>
                    <div class="flex gap-1">
                        <button onclick="toggleChunkExpand('chunk-${{idx}}')" class="text-[10px] bg-gray-200 text-gray-600 px-2 py-0.5 rounded hover:bg-gray-200">Expand</button>
                        <button onclick="findSimilar('${{c.id}}', 'similar-${{idx}}')" class="text-[10px] bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded hover:bg-indigo-200">Similar</button>
                    </div>
                </div>
                <div class="text-xs text-gray-400 truncate">${{escapeHtml(c.content)}}</div>
                <div class="chunk-expand" id="chunk-${{idx}}">
                    <div class="mt-2 p-2 bg-gray-50 rounded text-xs text-gray-400 whitespace-pre-wrap">${{escapeHtml(c.full_content || c.content)}}</div>
                </div>
                <div id="similar-${{idx}}" class="mt-1"></div>
            </div>`;
        }}).join('');
    }} catch (e) {{}}
}}

function toggleChunkExpand(id) {{
    document.getElementById(id)?.classList.toggle('open');
}}

function escapeHtml(text) {{
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}}

async function findSimilar(chunkId, containerId) {{
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '<div class="text-[10px] text-gray-500 mt-1">Searching...</div>';
    try {{
        const resp = await fetch('/api/observatory/similar-chunks', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{ chunk_id: chunkId, top_k: 5 }})
        }});
        const data = await resp.json();
        const similar = data.similar || [];
        if (similar.length === 0) {{
            container.innerHTML = '<div class="text-[10px] text-gray-500 mt-1">No similar chunks found</div>';
            return;
        }}
        container.innerHTML = '<div class="mt-2 space-y-1">' + similar.map(s => {{
            const dist = s.distance || 0;
            const colorClass = dist < 0.1 ? 'text-red-400' : dist < 0.3 ? 'text-amber-400' : 'text-indigo-600';
            const label = dist < 0.1 ? 'Near-duplicate' : dist < 0.3 ? 'Similar' : 'Related';
            return `<div class="flex items-center gap-2 p-1.5 bg-gray-50 rounded text-[10px]">
                <span class="${{colorClass}} font-medium w-24">${{label}} (${{dist.toFixed(3)}})</span>
                <span class="text-gray-400 truncate flex-1">${{escapeHtml(s.content)}}</span>
            </div>`;
        }}).join('') + '</div>';
    }} catch (e) {{
        container.innerHTML = '<div class="text-[10px] text-red-400 mt-1">Error finding similar chunks</div>';
    }}
}}

async function loadTrainingStatus() {{
    try {{
        const resp = await fetch('/api/observatory/training/status');
        const data = await resp.json();
        const dot = document.getElementById('obs-train-dot');
        dot.className = 'status-dot ' + (data.status || 'idle');
        document.getElementById('obs-train-status').textContent = (data.status || 'idle').charAt(0).toUpperCase() + (data.status || 'idle').slice(1);
        document.getElementById('obs-train-message').textContent = data.message || '';
        document.getElementById('obs-train-adapter').textContent = data.adapter_dir || '';

        const progressEl = document.getElementById('obs-train-progress');
        if (data.status === 'running' || data.global_step > 0) {{
            progressEl.classList.remove('hidden');
            const step = data.global_step || 0;
            const maxSteps = data.max_steps || 1;
            const epoch = data.epoch || 0;
            const numEpochs = data.num_train_epochs || 0;
            const pct = Math.min(100, Math.round(step / maxSteps * 100));
            document.getElementById('obs-train-step').textContent = `Step ${{step}}/${{maxSteps}}`;
            document.getElementById('obs-train-epoch').textContent = `Epoch ${{Math.round(epoch * 10) / 10}}/${{numEpochs}}`;
            document.getElementById('obs-train-progress-bar').style.width = pct + '%';
        }} else {{
            progressEl.classList.add('hidden');
        }}
    }} catch (e) {{}}
}}

async function loadTrainingLogs() {{
    try {{
        const resp = await fetch('/api/observatory/training/logs');
        const data = await resp.json();
        const lossCurve = data.loss_curve || [];
        const evalLosses = data.eval_losses || [];

        if (lossCurve.length === 0) {{
            document.getElementById('obs-loss-chart').innerHTML = '<span class="text-xs text-gray-600">No training logs available</span>';
            return;
        }}

        // Build inline SVG loss chart
        const width = 500, height = 200, pad = 40;
        const allLosses = [...lossCurve.map(p => p.loss), ...evalLosses.map(p => p.eval_loss)];
        const minLoss = Math.min(...allLosses) * 0.9;
        const maxLoss = Math.max(...allLosses) * 1.1;
        const maxStep = Math.max(...lossCurve.map(p => p.step), ...evalLosses.map(p => p.step));

        function sx(step) {{ return pad + (step / maxStep) * (width - pad * 2); }}
        function sy(loss) {{ return pad + (1 - (loss - minLoss) / (maxLoss - minLoss)) * (height - pad * 2); }}

        // Grid lines
        let gridLines = '';
        for (let i = 0; i <= 4; i++) {{
            const y = pad + i * (height - pad * 2) / 4;
            const val = (maxLoss - (i / 4) * (maxLoss - minLoss)).toFixed(3);
            gridLines += `<line x1="${{pad}}" y1="${{y}}" x2="${{width - pad}}" y2="${{y}}" stroke="#2f3549" stroke-width="1"/>`;
            gridLines += `<text x="${{pad - 5}}" y="${{y + 3}}" text-anchor="end" fill="#94a3b8" font-size="9">${{val}}</text>`;
        }}

        // Axes
        const axes = `<line x1="${{pad}}" y1="${{pad}}" x2="${{pad}}" y2="${{height - pad}}" stroke="#3a4158" stroke-width="1"/>
            <line x1="${{pad}}" y1="${{height - pad}}" x2="${{width - pad}}" y2="${{height - pad}}" stroke="#3a4158" stroke-width="1"/>
            <text x="${{width / 2}}" y="${{height - 5}}" text-anchor="middle" fill="#94a3b8" font-size="10">Steps</text>`;

        // Train loss line
        const trainPath = lossCurve.map((p, i) => `${{i === 0 ? 'M' : 'L'}}${{sx(p.step).toFixed(1)}},${{sy(p.loss).toFixed(1)}}`).join(' ');

        // Eval loss line
        const evalPath = evalLosses.length > 0
            ? evalLosses.map((p, i) => `${{i === 0 ? 'M' : 'L'}}${{sx(p.step).toFixed(1)}},${{sy(p.eval_loss).toFixed(1)}}`).join(' ')
            : '';

        document.getElementById('obs-loss-chart').innerHTML = `
            <svg viewBox="0 0 ${{width}} ${{height}}" class="w-full" style="max-height:220px">
                ${{gridLines}}
                ${{axes}}
                <path d="${{trainPath}}" fill="none" stroke="#6366f1" stroke-width="2"/>
                ${{evalPath ? `<path d="${{evalPath}}" fill="none" stroke="#f59e0b" stroke-width="2" stroke-dasharray="4,3"/>` : ''}}
            </svg>`;
    }} catch (e) {{}}
}}

async function loadDatasetAnalytics() {{
    try {{
        const resp = await fetch('/api/observatory/dataset/analytics');
        const data = await resp.json();
        document.getElementById('obs-dataset-counts').textContent = `${{data.train_count}} train / ${{data.val_count}} val examples`;
        document.getElementById('obs-avg-inst').textContent = data.avg_instruction_len || '--';
        document.getElementById('obs-avg-out').textContent = data.avg_output_len || '--';

        const dist = data.quality_distribution || {{}};
        const maxQ = Math.max(...Object.values(dist), 1);
        const colors = {{ 1: '#ef4444', 2: '#f97316', 3: '#eab308', 4: '#22c55e', 5: '#10b981' }};
        document.getElementById('obs-quality-chart').innerHTML = [1,2,3,4,5].map(q => {{
            const count = dist[q] || 0;
            const pct = Math.round(count / maxQ * 100);
            return `<div class="flex items-center gap-2">
                <span class="text-xs text-gray-400 w-16">Score ${{q}}</span>
                <div class="flex-1 h-5 bg-white rounded overflow-hidden">
                    <div class="obs-bar h-full rounded" style="width:${{pct}}%;background:${{colors[q]}}"></div>
                </div>
                <span class="text-xs text-gray-400 w-8">${{count}}</span>
            </div>`;
        }}).join('');
    }} catch (e) {{}}
}}

async function loadTrainingExamples(offset) {{
    obsExampleOffset = offset;
    const file = document.getElementById('obs-example-file').value;
    try {{
        const resp = await fetch(`/api/observatory/training/examples?offset=${{offset}}&limit=20&file=${{file}}`);
        const data = await resp.json();
        const examples = data.examples || [];
        const total = data.total || 0;
        document.getElementById('obs-example-page').textContent = `${{offset + 1}}-${{Math.min(offset + 20, total)}} of ${{total}}`;

        if (examples.length === 0) {{
            document.getElementById('obs-example-list').innerHTML = `<div class="text-center py-8">
                <div class="text-4xl mb-3 opacity-20">&#x1F4DD;</div>
                <div class="text-sm text-gray-500 font-medium mb-1">No Training Examples</div>
                <div class="text-xs text-gray-400">Go to Data & RAG tab and click "Prepare Dataset" to create training JSONL files from generated playgrounds.</div>
            </div>`;
            return;
        }}

        document.getElementById('obs-example-list').innerHTML = examples.map(ex => {{
            const qualityBadge = ex.quality ? `<span class="text-[10px] px-1 rounded ${{
                ex.quality >= 4 ? 'bg-indigo-100 text-indigo-700' : ex.quality >= 3 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'
            }}">Q${{ex.quality}}</span>` : '';
            return `<div class="bg-gray-50 rounded-lg border border-gray-300 p-3 cursor-pointer" onclick="this.querySelector('.chunk-expand')?.classList.toggle('open')">
                <div class="flex items-center gap-2 mb-1">
                    <span class="text-xs text-gray-500">#${{ex.index + 1}}</span>
                    ${{qualityBadge}}
                </div>
                <div class="text-xs text-cyan-400 truncate">Instruction: ${{escapeHtml(ex.instruction)}}</div>
                <div class="chunk-expand">
                    ${{ex.input ? `<div class="mt-1 text-xs text-gray-500">Input: ${{escapeHtml(ex.input)}}</div>` : ''}}
                    <div class="mt-1 p-2 bg-gray-50 rounded text-xs text-gray-400 whitespace-pre-wrap max-h-48 overflow-y-auto">Output: ${{escapeHtml(ex.output)}}</div>
                </div>
            </div>`;
        }}).join('');
    }} catch (e) {{}}
}}

async function loadAdapters() {{
    try {{
        const resp = await fetch('/api/observatory/adapters');
        const adapters = await resp.json();

        if (adapters.length === 0) {{
            document.getElementById('obs-adapter-list').innerHTML = `<div class="col-span-full text-center py-12">
                <div class="text-5xl mb-4 opacity-20">&#x1F9E9;</div>
                <div class="text-sm text-gray-500 font-medium mb-1">No Adapters Yet</div>
                <div class="text-xs text-gray-400 max-w-sm mx-auto">Run fine-tuning to create LoRA adapters. Adapters specialize the 14B model on your generated playground data.</div>
                <button onclick="showTrainingCommand()" class="mt-3 text-xs btn-primary px-4 py-1.5 rounded-lg">Show Training Command</button>
            </div>`;
            return;
        }}

        document.getElementById('obs-adapter-list').innerHTML = adapters.map(a => {{
            const statusColor = a.status === 'completed' ? 'completed' : a.status === 'interrupted' ? 'interrupted' : 'idle';
            const modules = (a.target_modules || []).join(', ');
            return `<div class="bg-white rounded-xl border border-gray-200 p-5">
                <div class="flex items-center gap-2 mb-3">
                    <span class="status-dot ${{statusColor}}"></span>
                    <div class="text-sm font-medium text-gray-800">${{escapeHtml(a.name)}}</div>
                </div>
                <div class="space-y-1.5 text-xs mb-3">
                    <div class="flex justify-between"><span class="text-gray-500">Status</span><span class="text-gray-600">${{a.status}}</span></div>
                    <div class="flex justify-between"><span class="text-gray-500">Size</span><span class="text-gray-600">${{a.size_mb}} MB</span></div>
                    <div class="flex justify-between"><span class="text-gray-500">Modified</span><span class="text-gray-600">${{(a.modified || '').substring(0, 10)}}</span></div>
                    <div class="flex justify-between"><span class="text-gray-500">Base Model</span><span class="text-gray-600 truncate max-w-[150px]" title="${{escapeHtml(a.base_model)}}">${{escapeHtml((a.base_model || '').split('/').pop())}}</span></div>
                    ${{a.lora_rank ? `<div class="flex justify-between"><span class="text-gray-500">LoRA Rank</span><span class="text-gray-600">${{a.lora_rank}}</span></div>` : ''}}
                    <div class="flex justify-between"><span class="text-gray-500">Checkpoints</span><span class="text-gray-600">${{a.checkpoint_count}}</span></div>
                    ${{modules ? `<div class="flex justify-between"><span class="text-gray-500">Targets</span><span class="text-gray-600 text-[10px] truncate max-w-[150px]" title="${{modules}}">${{modules}}</span></div>` : ''}}
                </div>
                <div class="flex gap-2">
                    ${{a.has_final ? `<button onclick="deployAdapter('${{a.name}}')" class="flex-1 text-xs btn-primary px-2 py-1.5 rounded-lg">Deploy</button>` : ''}}
                    <button onclick="viewAdapterDetails('${{a.name}}')" class="flex-1 text-xs bg-gray-200 text-gray-600 px-2 py-1.5 rounded hover:bg-gray-200 transition-colors">Details</button>
                </div>
            </div>`;
        }}).join('');
    }} catch (e) {{}}
}}

async function deployAdapter(name) {{
    try {{
        const resp = await fetch(`/api/observatory/adapters/${{name}}/deploy`, {{ method: 'POST' }});
        const data = await resp.json();
        alert('Run this command to deploy:\\n\\n' + data.command);
    }} catch (e) {{
        alert('Error: ' + e.message);
    }}
}}

async function viewAdapterDetails(name) {{
    try {{
        const resp = await fetch(`/api/observatory/adapters/${{name}}`);
        const data = await resp.json();
        const fileList = (data.files || []).map(f => `${{f.path}} (${{f.size_str}})`).join('\\n');
        alert(`Adapter: ${{name}}\\nFiles (${{data.file_count}}):\\n\\n${{fileList}}\\n\\nDeploy command:\\n${{data.deploy_command}}`);
    }} catch (e) {{
        alert('Error: ' + e.message);
    }}
}}

// === Pipeline Diagram (Mermaid) ===
const PIPELINE_TOOLTIPS = {{
    'scraper': {{
        title: 'TD Banking Scraper',
        body: 'Playwright-based scraper collects page structure, forms, CTAs, navigation patterns, and screenshots from 40+ TD Banking URLs across 8 categories (accounts, credit cards, mortgages, etc.).'
    }},
    'raw_data': {{
        title: 'Raw Scraped Data',
        body: 'JSON files containing extracted page elements: headings, paragraphs, forms, buttons, links, metadata. Stored in workflows/raw/ with full page structure preserved.'
    }},
    'workflow_mapper': {{
        title: 'Workflow Mapper',
        body: 'Maps raw scraped data into structured workflow schemas using Pydantic models. Extracts interaction patterns, form fields, navigation flows, and component hierarchies.'
    }},
    'structured': {{
        title: 'Structured Workflows',
        body: 'Clean workflow definitions with typed schemas: WorkflowStep, FormField, NavigationFlow. Each workflow has category, components, and interaction patterns defined.'
    }},
    'prepare_dataset': {{
        title: 'Dataset Preparation',
        body: 'Converts structured workflows into Alpaca-format training examples. Generates instruction/input/output triplets with system prompts. Applies quality scoring and 90/10 train/val split.'
    }},
    'train_jsonl': {{
        title: 'Training Data (194 examples)',
        body: 'train.jsonl — 194 Alpaca-format examples. Each contains: system prompt (TD Banking context), instruction (user request), input (optional context), output (HTML/CSS/JS playground code).'
    }},
    'val_jsonl': {{
        title: 'Validation Data (22 examples)',
        body: 'val.jsonl — 22 held-out examples for eval loss tracking. Same format as training data. Used for early stopping and overfitting detection during training.'
    }},
    'tokenizer': {{
        title: 'Qwen2.5 Tokenizer',
        body: 'AutoTokenizer from Qwen/Qwen2.5-Coder-7B-Instruct. ChatML format with <|im_start|>/<|im_end|> special tokens. Pad token set to EOS token.'
    }},
    'base_model': {{
        title: 'Base Model (4-bit Quantized)',
        body: 'Qwen/Qwen2.5-Coder-7B-Instruct loaded with BitsAndBytes NF4 quantization. Double quantization enabled, bfloat16 compute dtype. ~4.5GB VRAM footprint.'
    }},
    'bnb_config': {{
        title: 'BitsAndBytes 4-bit Config',
        body: 'NF4 quantization type (normalized float 4-bit), double quantization for extra compression, bfloat16 compute dtype for forward pass precision. Reduces 7B model from ~14GB to ~4.5GB.'
    }},
    'lora_config': {{
        title: 'LoRA Configuration',
        body: 'Rank=16, Alpha=32 (scaling factor 2x). Targets all attention + MLP projections: q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj. Dropout=0.05. ~0.5% trainable parameters.'
    }},
    'peft_model': {{
        title: 'PEFT Model (LoRA Applied)',
        body: 'Base model wrapped with LoRA adapters via get_peft_model(). Only adapter weights are trainable. Gradient checkpointing enabled to trade compute for memory savings.'
    }},
    'chatml_format': {{
        title: 'ChatML Formatting',
        body: 'Each example formatted as: <|im_start|>system\\n{{system}}<|im_end|>\\n<|im_start|>user\\n{{instruction}}<|im_end|>\\n<|im_start|>assistant\\n{{output}}<|im_end|>. Max length: 2048 tokens.'
    }},
    'sft_config': {{
        title: 'SFT Training Config',
        body: 'SFTConfig: batch_size=1, grad_accum=4 (effective batch=4), lr=2e-4, cosine scheduler, warmup=3%, weight_decay=0.01, bf16=True, paged_adamw_32bit optimizer, max_grad_norm=0.3.'
    }},
    'sft_trainer': {{
        title: 'SFT Trainer (TRL v0.27)',
        body: 'HuggingFace TRL SFTTrainer handles the training loop. 75 steps over 3 epochs. Eval every 50 steps, checkpoint every 100 steps. Reports train loss, eval loss, and token-level accuracy.'
    }},
    'training_loop': {{
        title: 'Training Loop (75 steps)',
        body: 'Epoch 1: loss 0.891 → 0.298. Epoch 2: loss 0.298 → 0.194. Epoch 3: loss 0.194 → 0.164. Token accuracy: 79.1% → 95.8%. Eval loss: 0.223, eval accuracy: 93.7%.'
    }},
    'gpu_vram': {{
        title: 'RTX 4090 VRAM Usage',
        body: 'Peak VRAM ~14.5GB/16GB during training. Model: ~4.5GB (quantized), LoRA adapters: ~200MB, Optimizer states: ~1.5GB (paged), Activations + KV cache: ~8GB with gradient checkpointing.'
    }},
    'loss_curve': {{
        title: 'Loss Curve & Metrics',
        body: 'Train loss: 0.891 → 0.164 (81.6% reduction). Eval loss: 0.223 (no overfitting). Token accuracy: 79.1% → 95.8%. Smooth convergence with cosine LR schedule.'
    }},
    'checkpoints': {{
        title: 'Training Checkpoints',
        body: 'Saved every 100 steps with save_total_limit=3. Contains adapter weights, optimizer states, and trainer_state.json with full loss history for resuming interrupted training.'
    }},
    'final_adapter': {{
        title: 'Final LoRA Adapter',
        body: 'Saved to adapters/td-playground-lora/final_adapter/. Contains adapter_model.safetensors (~50MB), adapter_config.json, tokenizer files. Ready for merging or direct inference.'
    }},
    'merge': {{
        title: 'Adapter Merge (Optional)',
        body: 'merge_adapter.py merges LoRA weights into base model creating a standalone model. Can then create Ollama Modelfile for local deployment with: ollama create td-playground -f Modelfile'
    }},
    'deploy': {{
        title: 'Deployment to Ollama',
        body: 'Merged model exported to GGUF format, then loaded into Ollama as td-playground model. Replaces qwen2.5-coder:14b as the generator in the dual-model architecture.'
    }}
}};

function renderPipelineDiagram() {{
    // Load mermaid from CDN
    if (!window.mermaid) {{
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js';
        script.onload = () => {{
            window.mermaid.initialize({{
                startOnLoad: false,
                theme: 'dark',
                themeVariables: {{
                    primaryColor: '#262b3f',
                    primaryTextColor: '#e2e8f0',
                    primaryBorderColor: '#4f46e5',
                    lineColor: '#4f46e5',
                    secondaryColor: '#2f3549',
                    tertiaryColor: '#1a1d2b',
                    edgeLabelBackground: '#212638',
                    clusterBkg: 'rgba(79,70,229,0.06)',
                    clusterBorder: 'rgba(99,102,241,0.2)',
                    fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif',
                    fontSize: '12px',
                }},
                flowchart: {{
                    curve: 'basis',
                    padding: 20,
                    htmlLabels: true,
                    useMaxWidth: true,
                }},
                securityLevel: 'loose',
            }});
            drawDiagram();
        }};
        document.head.appendChild(script);
    }} else {{
        drawDiagram();
    }}
}}

async function drawDiagram() {{
    const graphDef = `flowchart TB
        subgraph DATA["Data Pipeline"]
            scraper["Playwright Scraper\\n40+ TD Banking URLs"]
            raw_data["Raw JSON Data\\nworkflows/raw/"]
            workflow_mapper["Workflow Mapper\\nPydantic Schemas"]
            structured["Structured Workflows\\nworkflows/structured/"]
            prepare_dataset["prepare_dataset.py\\nAlpaca Format + Quality Scoring"]
            train_jsonl["train.jsonl\\n194 examples"]
            val_jsonl["val.jsonl\\n22 examples"]
        end

        subgraph MODEL["Model & LoRA Setup"]
            tokenizer["Qwen2.5 Tokenizer\\nChatML Format"]
            bnb_config["BitsAndBytes Config\\nNF4 4-bit Quantization"]
            base_model["Qwen2.5-Coder-7B-Instruct\\n4-bit Quantized ~4.5GB"]
            lora_config["LoRA Config\\nr=16, alpha=32, 7 modules"]
            peft_model["PEFT Model\\nTrainable: ~0.5%"]
        end

        subgraph TRAIN["Training Loop"]
            chatml_format["ChatML Formatting\\nmax_length=2048"]
            sft_config["SFTConfig\\nlr=2e-4, cosine, bf16"]
            sft_trainer["SFTTrainer\\nTRL v0.27"]
            training_loop["Training\\n75 steps x 3 epochs"]
        end

        subgraph GPU["GPU Resources"]
            gpu_vram["RTX 4090\\n16GB VRAM"]
            loss_curve["Loss: 0.891 to 0.164\\nAccuracy: 95.8%"]
        end

        subgraph OUTPUT["Output Artifacts"]
            checkpoints["Checkpoints\\nevery 100 steps"]
            final_adapter["Final LoRA Adapter\\n~50MB safetensors"]
            merge["merge_adapter.py\\nMerge into Base"]
            deploy["Ollama Deployment\\ntd-playground model"]
        end

        scraper -->|"extract pages"| raw_data
        raw_data -->|"map to schemas"| workflow_mapper
        workflow_mapper -->|"validate & structure"| structured
        structured -->|"generate examples"| prepare_dataset
        prepare_dataset -->|"90/10 split"| train_jsonl
        prepare_dataset -->|"90/10 split"| val_jsonl

        tokenizer -->|"encode tokens"| chatml_format
        bnb_config -->|"quantize weights"| base_model
        base_model -->|"inject adapters"| peft_model
        lora_config -->|"configure rank"| peft_model

        train_jsonl -->|"feed batches"| chatml_format
        val_jsonl -->|"eval every 50 steps"| sft_trainer
        chatml_format -->|"formatted dataset"| sft_trainer
        peft_model -->|"trainable model"| sft_trainer
        sft_config -->|"hyperparameters"| sft_trainer
        sft_trainer -->|"forward + backward"| training_loop

        gpu_vram -.->|"~14.5GB peak"| training_loop
        training_loop -->|"log metrics"| loss_curve
        training_loop -->|"save periodically"| checkpoints
        training_loop -->|"save final"| final_adapter
        final_adapter -->|"merge weights"| merge
        merge -->|"create GGUF"| deploy
    `;

    try {{
        const {{ svg }} = await window.mermaid.render('pipeline-svg', graphDef);
        document.getElementById('mermaid-diagram').innerHTML = svg;

        // Attach hover tooltips to nodes
        const tooltip = document.getElementById('mermaid-tooltip');
        const container = document.getElementById('pipeline-mermaid-container');

        document.querySelectorAll('#mermaid-diagram .node').forEach(node => {{
            const nodeId = node.id?.replace(/^flowchart-/, '').replace(/-\\d+$/, '') || '';
            const info = PIPELINE_TOOLTIPS[nodeId];
            if (!info) return;

            node.classList.add('diagram-node');
            node.addEventListener('mouseenter', (e) => {{
                tooltip.querySelector('.tt-title').textContent = info.title;
                tooltip.querySelector('.tt-body').textContent = info.body;
                tooltip.classList.add('visible');
            }});
            node.addEventListener('mousemove', (e) => {{
                const rect = container.getBoundingClientRect();
                let x = e.clientX - rect.left + 12;
                let y = e.clientY - rect.top + 12;
                if (x + 320 > rect.width) x = e.clientX - rect.left - 330;
                if (y + 150 > rect.height) y = e.clientY - rect.top - 100;
                tooltip.style.left = x + 'px';
                tooltip.style.top = y + 'px';
            }});
            node.addEventListener('mouseleave', () => {{
                tooltip.classList.remove('visible');
            }});
        }});

        // Also try to attach to edge labels
        document.querySelectorAll('#mermaid-diagram .edgeLabel').forEach(label => {{
            label.style.cursor = 'default';
        }});
    }} catch (e) {{
        document.getElementById('mermaid-diagram').innerHTML = '<div class="text-center py-12"><div class="text-sm text-red-400">Failed to render diagram: ' + e.message + '</div></div>';
    }}
}}

// === Agent Observability ===
let agentLoaded = false;
const STEP_COLORS = {{
    'route': '#a78bfa', 'cache_check': '#60a5fa', 'rag_query': '#22d3ee',
    'compress': '#fbbf24', 'generate': '#818cf8', 'cache_store': '#34d399',
    'light_task': '#f472b6', 'metrics': '#94a3b8',
}};
const STEP_ICONS = {{
    'route': '&#x2192;', 'cache_check': '&#x1F50D;', 'rag_query': '&#x1F4DA;',
    'compress': '&#x1F4E6;', 'generate': '&#x2728;', 'cache_store': '&#x1F4BE;',
    'light_task': '&#x1F4AC;', 'metrics': '&#x1F4CA;',
}};

async function loadAgentData() {{
    try {{
        let stats, traces;
        if (window._preloadedAgentStats && window._preloadedAgentTraces) {{
            stats = window._preloadedAgentStats;
            traces = window._preloadedAgentTraces;
            delete window._preloadedAgentStats;
            delete window._preloadedAgentTraces;
        }} else {{
            const [statsResp, tracesResp] = await Promise.all([
                fetch('/api/agent/stats'), fetch('/api/agent/traces?limit=30')
            ]);
            stats = await statsResp.json();
            traces = await tracesResp.json();
        }}

        if (!stats.enabled) {{
            document.getElementById('ag-latest-trace').innerHTML = '<div class="text-xs text-gray-600 text-center py-8">Agent tracing not enabled</div>';
            return;
        }}

        // Stats row
        document.getElementById('ag-total-traces').textContent = stats.total_traces || 0;
        document.getElementById('ag-avg-latency').textContent = (stats.avg_latency_ms || 0).toFixed(0) + 'ms';
        document.getElementById('ag-cache-rate').textContent = stats.cache_hit_rate || '0%';
        document.getElementById('ag-avg-conf').textContent = ((stats.avg_confidence || 0) * 100).toFixed(0) + '%';
        document.getElementById('ag-tokens-saved').textContent = (stats.token_economy?.total_saved || 0).toLocaleString();
        document.getElementById('ag-24h').textContent = stats.last_24h_traces || 0;

        // Latest trace timeline
        if (traces.length > 0) {{
            renderTraceTimeline(traces[0]);
        }}

        // Model distribution
        renderModelDist(stats.model_distribution || {{}});

        // Router methods
        renderRouterMethods(stats.router_methods || {{}});

        // Step latencies
        renderStepLatencies(stats.step_avg_latencies || {{}});

        // Token economy
        renderTokenEconomy(stats.token_economy || {{}}, stats);

        // Trace history table
        renderTraceTable(traces);

        agentLoaded = true;
    }} catch (e) {{}}
}}

function renderTraceTimeline(trace) {{
    const steps = trace.steps || [];
    const maxMs = Math.max(...steps.map(s => s.latency_ms), 1);
    const prompt = escapeHtml((trace.prompt || '').substring(0, 100));

    let html = `<div class="mb-4 p-3 rounded-lg" style="background:rgba(79,70,229,0.06);border:1px solid rgba(99,102,241,0.15)">
        <div class="flex items-center justify-between mb-1">
            <span class="text-xs text-indigo-400 font-medium">${{trace.id}}</span>
            <span class="text-[10px] text-gray-500">${{(trace.started_at || '').substring(0, 19)}}</span>
        </div>
        <div class="text-xs text-gray-400 mb-2 truncate">"${{prompt}}"</div>
        <div class="flex items-center gap-3 text-[10px]">
            <span class="text-amber-400">${{(trace.total_latency_ms || 0).toFixed(0)}}ms total</span>
            <span class="text-gray-500">|</span>
            <span class="text-gray-400">${{trace.total_steps}} steps</span>
            <span class="text-gray-500">|</span>
            <span class="${{trace.cache_hit ? 'text-green-400' : 'text-gray-400'}}">${{trace.cache_hit ? 'CACHE HIT' : trace.final_model || ''}}</span>
            ${{trace.rag_chunks > 0 ? `<span class="text-gray-500">|</span><span class="text-cyan-400">RAG:${{trace.rag_chunks}}</span>` : ''}}
        </div>
    </div>`;

    html += '<div class="space-y-0.5">';
    for (const step of steps) {{
        const pct = Math.max(2, (step.latency_ms / maxMs) * 100);
        const color = STEP_COLORS[step.step_name] || '#64748b';
        const icon = STEP_ICONS[step.step_name] || '&#x25CF;';
        const meta = step.metadata || {{}};
        const stepId = `step-detail-${{trace.id}}-${{step.step_order}}`;

        let detail = '';
        if (step.step_name === 'route') {{
            detail = `${{meta.method || ''}} &#x2192; ${{meta.task_type || ''}} (conf: ${{((meta.confidence || 0) * 100).toFixed(0)}}%)`;
        }} else if (step.step_name === 'cache_check') {{
            detail = meta.hit ? `<span class="text-green-400">HIT</span> (sim: ${{(meta.similarity || 0).toFixed(2)}})` : '<span class="text-gray-500">MISS</span>';
        }} else if (step.step_name === 'rag_query') {{
            detail = `${{meta.chunks_retrieved || 0}} chunks, ${{meta.context_chars || 0}} chars`;
        }} else if (step.step_name === 'compress') {{
            detail = meta.had_workflow ? `compressed (${{meta.savings_pct || 0}}% saved)` : 'no workflow context';
        }} else if (step.step_name === 'generate') {{
            detail = `${{meta.input_tokens || 0}} in / ${{meta.output_tokens || 0}} out tokens, ${{((meta.html_size || 0) / 1024).toFixed(1)}}KB`;
        }} else if (step.step_name === 'cache_store') {{
            detail = `stored ${{meta.playground_id || ''}}`;
        }} else if (step.step_name === 'light_task') {{
            detail = `${{meta.model || '3B'}}, ${{meta.response_len || 0}} chars`;
        }}

        html += `<div class="trace-step py-2 cursor-pointer" onclick="document.getElementById('${{stepId}}')?.classList.toggle('open')">
            <div class="trace-step-dot ${{step.step_name}}"></div>
            <div class="flex items-center gap-2 mb-1">
                <span class="text-xs font-medium" style="color:${{color}}">${{icon}} ${{step.step_name}}</span>
                <span class="text-[10px] text-amber-400 font-mono">${{step.latency_ms.toFixed(1)}}ms</span>
                <span class="text-[10px] text-gray-500 truncate flex-1">${{detail}}</span>
            </div>
            <div class="flex items-center gap-2">
                <div class="flex-1 h-1.5 rounded-full overflow-hidden" style="background:#212638">
                    <div class="trace-bar" style="width:${{pct}}%;background:${{color}}"></div>
                </div>
            </div>
            <div class="trace-expand" id="${{stepId}}">
                <div class="mt-2 p-2 rounded text-[10px] text-gray-400 font-mono" style="background:#1a1d2b">${{escapeHtml(JSON.stringify(meta, null, 2))}}</div>
            </div>
        </div>`;
    }}
    html += '</div>';

    document.getElementById('ag-latest-trace').innerHTML = html;
}}

function renderModelDist(dist) {{
    const total = Object.values(dist).reduce((a, b) => a + b, 0) || 1;
    const colors = {{ 'cache': '#34d399' }};

    let html = '';
    for (const [model, count] of Object.entries(dist).sort((a, b) => b[1] - a[1])) {{
        const pct = (count / total * 100).toFixed(1);
        const label = model.includes('14b') || model.includes('coder') ? '14B Generator' : model === 'cache' ? 'Cache' : model.includes('3b') ? '3B Router' : model.split(':').pop() || model;
        const color = model.includes('14b') || model.includes('coder') ? '#818cf8' : model === 'cache' ? '#34d399' : '#a78bfa';
        html += `<div>
            <div class="flex justify-between text-xs mb-1"><span class="text-gray-400">${{label}}</span><span style="color:${{color}}" class="font-medium">${{count}} (${{pct}}%)</span></div>
            <div class="h-2 rounded-full overflow-hidden" style="background:#212638">
                <div class="obs-bar h-full rounded-full" style="width:${{pct}}%;background:${{color}}"></div>
            </div>
        </div>`;
    }}
    document.getElementById('ag-model-dist').innerHTML = html || '<div class="text-xs text-gray-600 text-center py-4">No data</div>';
}}

function renderRouterMethods(methods) {{
    const total = Object.values(methods).reduce((a, b) => a + b, 0) || 1;
    const colors = {{ 'keyword': '#34d399', 'llm_3b': '#818cf8', 'forced': '#f59e0b', 'stream': '#06b6d4' }};
    const labels = {{ 'keyword': 'Keyword (0 tokens)', 'llm_3b': 'LLM 3B (~50 tokens)', 'forced': 'Force Generate', 'stream': 'Stream Mode' }};

    let html = '';
    for (const [method, count] of Object.entries(methods).sort((a, b) => b[1] - a[1])) {{
        const pct = (count / total * 100).toFixed(1);
        const color = colors[method] || '#64748b';
        html += `<div>
            <div class="flex justify-between text-xs mb-1"><span class="text-gray-400">${{labels[method] || method}}</span><span style="color:${{color}}" class="font-medium">${{count}} (${{pct}}%)</span></div>
            <div class="h-2 rounded-full overflow-hidden" style="background:#212638">
                <div class="obs-bar h-full rounded-full" style="width:${{pct}}%;background:${{color}}"></div>
            </div>
        </div>`;
    }}
    document.getElementById('ag-router-methods').innerHTML = html || '<div class="text-xs text-gray-600 text-center py-4">No data</div>';
}}

function renderStepLatencies(stepData) {{
    const entries = Object.entries(stepData).sort((a, b) => b[1].avg_ms - a[1].avg_ms);
    const maxMs = entries.length > 0 ? entries[0][1].avg_ms : 1;

    let html = '';
    for (const [step, data] of entries) {{
        const pct = Math.max(2, (data.avg_ms / maxMs) * 100);
        const color = STEP_COLORS[step] || '#64748b';
        html += `<div class="flex items-center gap-2">
            <span class="text-xs text-gray-400 w-24 truncate">${{step}}</span>
            <div class="flex-1 h-5 rounded overflow-hidden" style="background:#212638">
                <div class="obs-bar h-full rounded flex items-center px-2" style="width:${{pct}}%;background:${{color}}40">
                    <span class="text-[10px] font-mono text-gray-300">${{data.avg_ms.toFixed(0)}}ms</span>
                </div>
            </div>
            <span class="text-[10px] text-gray-500 w-12 text-right">x${{data.count}}</span>
        </div>`;
    }}
    document.getElementById('ag-step-latency').innerHTML = html || '<div class="text-xs text-gray-600 text-center py-4">No data</div>';
}}

function renderTokenEconomy(economy, stats) {{
    const totalInput = economy.total_input || 0;
    const totalOutput = economy.total_output || 0;
    const totalSaved = economy.total_saved || 0;
    const totalUsed = totalInput + totalOutput;
    const efficiency = totalUsed > 0 ? ((totalSaved / (totalUsed + totalSaved)) * 100).toFixed(1) : 0;

    const html = `
        <div class="grid grid-cols-3 gap-3 mb-4">
            <div class="rounded-lg p-3 text-center" style="background:#1a1d2b">
                <div class="text-lg font-bold text-indigo-400">${{totalInput.toLocaleString()}}</div>
                <div class="text-[10px] text-gray-500">Input Tokens</div>
            </div>
            <div class="rounded-lg p-3 text-center" style="background:#1a1d2b">
                <div class="text-lg font-bold text-amber-400">${{totalOutput.toLocaleString()}}</div>
                <div class="text-[10px] text-gray-500">Output Tokens</div>
            </div>
            <div class="rounded-lg p-3 text-center" style="background:#1a1d2b">
                <div class="text-lg font-bold text-green-400">${{totalSaved.toLocaleString()}}</div>
                <div class="text-[10px] text-gray-500">Tokens Saved</div>
            </div>
        </div>
        <div class="mb-3">
            <div class="flex justify-between text-xs mb-1">
                <span class="text-gray-400">Efficiency (tokens saved vs total)</span>
                <span class="text-green-400 font-medium">${{efficiency}}%</span>
            </div>
            <div class="h-3 rounded-full overflow-hidden" style="background:#212638">
                <div class="obs-bar h-full rounded-full" style="width:${{efficiency}}%;background:linear-gradient(90deg,#22c55e,#34d399)"></div>
            </div>
        </div>
        <div class="space-y-2 text-xs">
            <div class="flex justify-between"><span class="text-gray-500">Cache hits saved ~4000 tokens each</span><span class="text-green-400">${{stats.cache_hits || 0}} hits</span></div>
            <div class="flex justify-between"><span class="text-gray-500">Keyword routing saved ~50 tokens each</span><span class="text-green-400">${{(stats.router_methods || {{}}).keyword || 0}} routes</span></div>
            <div class="flex justify-between"><span class="text-gray-500">3B router (vs 14B) saves ~4x latency</span><span class="text-purple-400">${{Object.values(stats.routing_breakdown || {{}}).reduce((a,b) => a+b, 0) - ((stats.routing_breakdown || {{}}).generate || 0)}} light tasks</span></div>
        </div>`;

    document.getElementById('ag-token-economy').innerHTML = html;
}}

function renderTraceTable(traces) {{
    document.getElementById('ag-trace-count').textContent = traces.length + ' traces';
    if (traces.length === 0) {{
        document.getElementById('ag-trace-table').innerHTML = '<div class="px-4 py-6 text-center text-xs text-gray-600">No traces recorded yet</div>';
        return;
    }}

    let html = '<table class="w-full"><thead><tr class="border-b border-gray-200 text-[10px] text-gray-500 uppercase">' +
        '<th class="px-3 py-2 text-left">Time</th>' +
        '<th class="px-3 py-2 text-left">Prompt</th>' +
        '<th class="px-3 py-2 text-left">Type</th>' +
        '<th class="px-3 py-2 text-left">Router</th>' +
        '<th class="px-3 py-2 text-left">Model</th>' +
        '<th class="px-3 py-2 text-left">Steps</th>' +
        '<th class="px-3 py-2 text-left">Latency</th>' +
        '<th class="px-3 py-2 text-left">RAG</th>' +
        '<th class="px-3 py-2 text-left">Cache</th>' +
        '</tr></thead><tbody>';

    for (const t of traces) {{
        const time = (t.started_at || '').substring(11, 19);
        const prompt = escapeHtml((t.prompt || '').substring(0, 40));
        const taskBadge = t.task_type === 'cache_hit' ? '<span class="text-green-400">cache</span>' :
            `<span class="text-gray-400">${{t.task_type || '-'}}</span>`;
        const routerBadge = t.router_method === 'keyword' ? '<span class="text-green-400">keyword</span>' :
            t.router_method === 'llm_3b' ? '<span class="text-indigo-400">LLM</span>' :
            `<span class="text-gray-500">${{t.router_method || '-'}}</span>`;
        const model = (t.final_model || '').split(':').pop() || '-';
        const cacheBadge = t.cache_hit ? '<span class="text-green-400">HIT</span>' : '<span class="text-gray-500">miss</span>';
        const ragBadge = t.rag_chunks > 0 ? `<span class="text-cyan-400">${{t.rag_chunks}}</span>` : '<span class="text-gray-500">-</span>';

        html += `<tr class="border-b border-gray-200/50 hover:bg-gray-50/50 cursor-pointer" onclick="loadSingleTrace('${{t.id}}')">
            <td class="px-3 py-2 text-xs text-gray-500 font-mono">${{time}}</td>
            <td class="px-3 py-2 text-xs text-gray-400 truncate max-w-[180px]">${{prompt}}</td>
            <td class="px-3 py-2 text-xs">${{taskBadge}}</td>
            <td class="px-3 py-2 text-xs">${{routerBadge}}</td>
            <td class="px-3 py-2 text-xs text-gray-500">${{model}}</td>
            <td class="px-3 py-2 text-xs text-gray-400">${{t.total_steps}}</td>
            <td class="px-3 py-2 text-xs text-amber-400 font-mono">${{(t.total_latency_ms || 0).toFixed(0)}}ms</td>
            <td class="px-3 py-2 text-xs">${{ragBadge}}</td>
            <td class="px-3 py-2 text-xs">${{cacheBadge}}</td>
        </tr>`;
    }}
    html += '</tbody></table>';
    document.getElementById('ag-trace-table').innerHTML = html;
}}

async function loadSingleTrace(traceId) {{
    try {{
        const resp = await fetch('/api/agent/trace/' + traceId);
        const trace = await resp.json();
        renderTraceTimeline(trace);
        document.getElementById('ag-latest-trace').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }} catch (e) {{}}
}}

// === Health Polling ===
async function pollHealth() {{
    try {{
        const [health, stats] = await Promise.all([
            fetch('/api/health').then(r => r.json()),
            fetch('/api/stats').then(r => r.json())
        ]);

        document.getElementById('gen-dot').className = 'w-2 h-2 rounded-full ' +
            (health.generator_ready ? 'bg-indigo-500' : 'bg-red-400');
        document.getElementById('rtr-dot').className = 'w-2 h-2 rounded-full ' +
            (health.router_ready ? 'bg-indigo-500' : 'bg-red-400');

        const vram = stats.vram;
        if (vram && vram.total_mb) {{
            const pct = vram.usage_pct;
            document.getElementById('vram-fill').style.width = pct + '%';
            document.getElementById('vram-fill').className = 'h-full rounded-full transition-all ' +
                (pct > 85 ? 'bg-red-500' : pct > 60 ? 'bg-amber-500' : 'bg-indigo-500');
            document.getElementById('vram-text').textContent = `${{vram.used_mb}}/${{vram.total_mb}}MB`;

            // Update metrics tab VRAM
            const gaugePct = Math.round(pct);
            document.querySelector('.metric-ring')?.style.setProperty('--pct', gaugePct + '%');
            const gaugeEl = document.getElementById('vram-gauge-pct');
            if (gaugeEl) gaugeEl.textContent = gaugePct + '%';
            const gpuEl = document.getElementById('vram-gpu-name');
            if (gpuEl) gpuEl.textContent = vram.gpu_name || 'GPU';
            const usedEl = document.getElementById('vram-used');
            if (usedEl) usedEl.textContent = vram.used_mb + ' MB';
            const totalEl = document.getElementById('vram-total');
            if (totalEl) totalEl.textContent = vram.total_mb + ' MB';
            const tempEl = document.getElementById('vram-temp');
            if (tempEl) tempEl.textContent = (vram.temp_c || '--') + 'C';
            const utilEl = document.getElementById('vram-util');
            if (utilEl) utilEl.textContent = (vram.utilization_pct || '--') + '%';
        }}
    }} catch (e) {{}}
}}

// === Gallery Search + Filter + Sort ===
function applyGalleryFilters() {{
    const search = (document.getElementById('gallery-search').value || '').toLowerCase().trim();
    const style = document.getElementById('gallery-filter').value;
    let visible = 0;
    document.querySelectorAll('#gallery-grid .gallery-card').forEach(card => {{
        const matchSearch = !search || card.dataset.prompt.includes(search);
        const matchStyle = style === 'all' || card.dataset.style === style;
        const show = matchSearch && matchStyle;
        card.style.display = show ? '' : 'none';
        if (show) visible++;
    }});
    document.getElementById('gallery-count').textContent = visible + ' playgrounds';
}}

function sortGallery() {{
    const sortBy = document.getElementById('gallery-sort').value;
    const grid = document.getElementById('gallery-grid');
    const cards = Array.from(grid.querySelectorAll('.gallery-card'));

    cards.sort((a, b) => {{
        switch (sortBy) {{
            case 'newest': return (b.dataset.date || '').localeCompare(a.dataset.date || '');
            case 'oldest': return (a.dataset.date || '').localeCompare(b.dataset.date || '');
            case 'largest': return Number(b.dataset.size || 0) - Number(a.dataset.size || 0);
            case 'smallest': return Number(a.dataset.size || 0) - Number(b.dataset.size || 0);
            case 'fastest': {{
                const la = Number(a.dataset.latency || 999999);
                const lb = Number(b.dataset.latency || 999999);
                return la - lb;
            }}
            case 'slowest': return Number(b.dataset.latency || 0) - Number(a.dataset.latency || 0);
            default: return 0;
        }}
    }});

    cards.forEach(card => grid.appendChild(card));
    applyGalleryFilters();
}}

// === Tab 8: Embeddings & Storage ===
let embLoaded = {{ space: false, chromadb: false, storage: false }};
let embCoords = [];
let cdbChunksAll = [];
let cdbChunksPage = 0;

function loadEmbeddings() {{
    switchEmbPanel('space');
}}

function switchEmbPanel(panel) {{
    document.querySelectorAll('.emb-panel').forEach(p => p.classList.add('hidden'));
    document.querySelectorAll('.emb-panel-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('emb-' + panel).classList.remove('hidden');
    document.getElementById('emb-btn-' + panel).classList.add('active');
    if (panel === 'space' && !embLoaded.space) {{ loadEmbeddingCoords(); embLoaded.space = true; }}
    if (panel === 'chromadb' && !embLoaded.chromadb) {{ loadChromaDBInspector(); embLoaded.chromadb = true; }}
    if (panel === 'storage' && !embLoaded.storage) {{ loadStorageOverview(); embLoaded.storage = true; }}
}}

// --- Sub-panel A: Embedding Space (Plotly + UMAP) ---
const EMB_COLORS = ['#818cf8','#f472b6','#34d399','#fbbf24','#60a5fa','#a78bfa','#fb923c','#22d3ee','#e879f9','#4ade80',
    '#f87171','#38bdf8','#a3e635','#fb7185','#2dd4bf','#c084fc','#fdba74','#67e8f9','#d946ef','#86efac'];
let embCurrentDims = 3;
let embData3D = null;
let embData2D = null;
let embStats = null;

async function loadEmbeddingCoords() {{
    document.getElementById('emb-status').textContent = 'Loading UMAP projection...';
    try {{
        const [resp3d, resp2d, statsResp] = await Promise.all([
            fetch('/api/observatory/embedding-coords?dims=3'),
            fetch('/api/observatory/embedding-coords?dims=2'),
            fetch('/api/rag/stats'),
        ]);
        embData3D = await resp3d.json();
        embData2D = await resp2d.json();
        embStats = await statsResp.json();

        const data = embCurrentDims === 3 ? embData3D : embData2D;
        document.getElementById('emb-total').textContent = data.length;
        const cats = [...new Set(data.map(c => c.category))];
        document.getElementById('emb-categories').textContent = cats.length;
        document.getElementById('emb-collection').textContent = embStats.collection || '--';
        document.getElementById('emb-dims').textContent = embStats.embed_model || '--';

        renderEmbLegend(data);
        renderEmbPlotly(data, embCurrentDims);
        document.getElementById('emb-status').textContent = `UMAP ${{embCurrentDims}}D | ${{data.length}} points | ${{cats.length}} categories`;
    }} catch (e) {{
        document.getElementById('emb-status').textContent = 'Failed to load embeddings';
        document.getElementById('emb-total').textContent = '0';
    }}
}}

function toggleEmbDims(dims) {{
    embCurrentDims = dims;
    document.getElementById('emb-btn-3d').className = 'px-4 py-1.5 text-xs font-medium transition-colors ' + (dims === 3 ? 'bg-indigo-500 text-white' : 'text-gray-500');
    document.getElementById('emb-btn-2d').className = 'px-4 py-1.5 text-xs font-medium transition-colors ' + (dims === 2 ? 'bg-indigo-500 text-white' : 'text-gray-500');
    const data = dims === 3 ? embData3D : embData2D;
    if (data) {{
        renderEmbPlotly(data, dims);
        document.getElementById('emb-status').textContent = `UMAP ${{dims}}D | ${{data.length}} points`;
    }}
}}

function renderEmbLegend(data) {{
    const catCounts = {{}};
    data.forEach(c => {{ catCounts[c.category] = (catCounts[c.category] || 0) + 1; }});
    const sorted = Object.entries(catCounts).sort((a, b) => b[1] - a[1]);
    const cats = sorted.map(s => s[0]);
    document.getElementById('emb-legend').innerHTML = sorted.map(([cat, count], i) =>
        `<div class="flex items-center gap-2 text-xs text-gray-500">
            <span class="w-2.5 h-2.5 rounded-full flex-shrink-0" style="background:${{EMB_COLORS[cats.indexOf(cat) % EMB_COLORS.length]}}"></span>
            <span class="truncate" title="${{cat}}">${{cat}}</span>
            <span class="text-gray-600 ml-auto">${{count}}</span>
        </div>`
    ).join('');
}}

function renderEmbPlotly(data, dims) {{
    if (!data || !data.length) return;

    const cats = [...new Set(data.map(c => c.category))];
    const traces = cats.map((cat, catIdx) => {{
        const pts = data.filter(p => p.category === cat);
        const color = EMB_COLORS[catIdx % EMB_COLORS.length];
        const hoverText = pts.map(p => `<b>${{cat}}</b><br>${{p.chunk_type || ''}}<br>${{(p.content || '').substring(0, 80)}}...`);

        if (dims === 3) {{
            return {{
                type: 'scatter3d',
                mode: 'markers',
                name: cat,
                x: pts.map(p => p.x),
                y: pts.map(p => p.y),
                z: pts.map(p => p.z),
                text: hoverText,
                hoverinfo: 'text',
                customdata: pts,
                marker: {{
                    size: 4,
                    color: color,
                    opacity: 0.85,
                    line: {{ width: 0.5, color: 'rgba(255,255,255,0.15)' }},
                }},
            }};
        }} else {{
            return {{
                type: 'scattergl',
                mode: 'markers',
                name: cat,
                x: pts.map(p => p.x),
                y: pts.map(p => p.y),
                text: hoverText,
                hoverinfo: 'text',
                customdata: pts,
                marker: {{
                    size: 6,
                    color: color,
                    opacity: 0.85,
                    line: {{ width: 0.5, color: 'rgba(255,255,255,0.15)' }},
                }},
            }};
        }}
    }});

    const darkAxis = {{
        backgroundcolor: '#1a1d2b',
        gridcolor: 'rgba(255,255,255,0.09)',
        zerolinecolor: 'rgba(255,255,255,0.1)',
        tickfont: {{ color: '#64748b', size: 10 }},
        title: {{ font: {{ color: '#94a3b8', size: 11 }} }},
    }};

    const layout3d = {{
        paper_bgcolor: '#1a1d2b',
        plot_bgcolor: '#1a1d2b',
        font: {{ color: '#94a3b8' }},
        margin: {{ l: 0, r: 0, t: 30, b: 0 }},
        showlegend: false,
        scene: {{
            xaxis: {{ ...darkAxis, title: 'UMAP-1' }},
            yaxis: {{ ...darkAxis, title: 'UMAP-2' }},
            zaxis: {{ ...darkAxis, title: 'UMAP-3' }},
            camera: {{ eye: {{ x: 1.5, y: 1.5, z: 1.2 }} }},
        }},
    }};

    const layout2d = {{
        paper_bgcolor: '#1a1d2b',
        plot_bgcolor: '#1a1d2b',
        font: {{ color: '#94a3b8' }},
        margin: {{ l: 50, r: 20, t: 30, b: 50 }},
        showlegend: false,
        xaxis: {{ gridcolor: 'rgba(255,255,255,0.09)', zerolinecolor: 'rgba(255,255,255,0.1)', tickfont: {{ color: '#64748b' }}, title: {{ text: 'UMAP-1', font: {{ color: '#94a3b8' }} }} }},
        yaxis: {{ gridcolor: 'rgba(255,255,255,0.09)', zerolinecolor: 'rgba(255,255,255,0.1)', tickfont: {{ color: '#64748b' }}, title: {{ text: 'UMAP-2', font: {{ color: '#94a3b8' }} }} }},
    }};

    const config = {{ responsive: true, displayModeBar: true, modeBarButtonsToRemove: ['lasso2d','select2d'], displaylogo: false }};
    Plotly.newPlot('emb-plotly', traces, dims === 3 ? layout3d : layout2d, config);

    // Click handler for point details
    const plotDiv = document.getElementById('emb-plotly');
    plotDiv.on('plotly_click', function(eventData) {{
        if (eventData.points && eventData.points[0]) {{
            const pt = eventData.points[0].customdata;
            if (pt) {{
                const details = document.getElementById('emb-point-details');
                details.innerHTML = `
                    <div class="mb-2"><span class="text-gray-400">ID:</span> <span class="text-gray-800 font-mono text-[11px]">${{pt.id}}</span></div>
                    <div class="mb-2"><span class="text-gray-400">Category:</span> <span class="text-indigo-400 font-medium">${{pt.category}}</span></div>
                    <div class="mb-2"><span class="text-gray-400">Type:</span> <span class="text-gray-700">${{pt.chunk_type || '--'}}</span></div>
                    <div class="mb-2"><span class="text-gray-400">Source:</span> <span class="text-gray-700">${{pt.source || '--'}}</span></div>
                    <div class="mb-2"><span class="text-gray-400">UMAP:</span> <span class="text-gray-600">(${{pt.x}}, ${{pt.y}}${{pt.z != null ? ', ' + pt.z : ''}})</span></div>
                    <div class="mt-3 p-2 bg-gray-50 rounded border border-gray-200 text-[11px] text-gray-600 max-h-48 overflow-y-auto">${{pt.content}}</div>
                `;
            }}
        }}
    }});
}}

// --- Sub-panel B: ChromaDB Inspector ---
async function loadChromaDBInspector() {{
    try {{
        const [statsResp, analyticsResp] = await Promise.all([
            fetch('/api/rag/stats'),
            fetch('/api/observatory/chunk-analytics'),
        ]);
        const stats = await statsResp.json();
        const analytics = await analyticsResp.json();

        document.getElementById('cdb-total').textContent = stats.total_chunks || 0;
        document.getElementById('cdb-model').textContent = stats.embed_model || '--';
        document.getElementById('cdb-collection').textContent = stats.collection || '--';
        document.getElementById('cdb-path').textContent = stats.persist_directory || '--';

        // Chunk type distribution
        const sources = analytics.sources || {{}};
        const srcEntries = Object.entries(sources).sort((a, b) => b[1] - a[1]);
        const maxSrc = Math.max(...srcEntries.map(s => s[1]), 1);
        document.getElementById('cdb-type-dist').innerHTML = srcEntries.length ? srcEntries.map(([name, count]) =>
            `<div class="flex items-center gap-2">
                <span class="text-xs text-gray-500 w-24 truncate">${{name}}</span>
                <div class="flex-1 bg-gray-200 rounded-full h-4 overflow-hidden">
                    <div class="h-full rounded-full obs-bar" style="width:${{(count/maxSrc*100).toFixed(1)}}%;background:linear-gradient(90deg,#4f46e5,#818cf8)"></div>
                </div>
                <span class="text-xs text-gray-600 w-8 text-right">${{count}}</span>
            </div>`
        ).join('') : '<div class="text-xs text-gray-600 text-center py-4">No data</div>';

        // Per-workflow chunk counts
        const workflows = analytics.workflows || {{}};
        const wfEntries = Object.entries(workflows).sort((a, b) => b[1] - a[1]);
        const maxWf = Math.max(...wfEntries.map(w => w[1]), 1);
        document.getElementById('cdb-workflow-dist').innerHTML = wfEntries.length ? wfEntries.map(([name, count]) =>
            `<div class="flex items-center gap-2">
                <span class="text-xs text-gray-500 w-32 truncate" title="${{name}}">${{name}}</span>
                <div class="flex-1 bg-gray-200 rounded-full h-3 overflow-hidden">
                    <div class="h-full rounded-full obs-bar" style="width:${{(count/maxWf*100).toFixed(1)}}%;background:linear-gradient(90deg,#7c3aed,#a78bfa)"></div>
                </div>
                <span class="text-xs text-gray-600 w-6 text-right">${{count}}</span>
            </div>`
        ).join('') : '<div class="text-xs text-gray-600 text-center py-4">No data</div>';

        // Size histogram
        const histogram = analytics.histogram || [];
        const maxHist = Math.max(...histogram.map(h => h.count), 1);
        document.getElementById('cdb-size-hist').innerHTML = histogram.length ? histogram.map(h =>
            `<div class="flex items-center gap-2">
                <span class="text-[10px] text-gray-500 w-20 truncate">${{h.range}}</span>
                <div class="flex-1 bg-gray-200 rounded-full h-3 overflow-hidden">
                    <div class="h-full rounded-full obs-bar" style="width:${{(h.count/maxHist*100).toFixed(1)}}%;background:linear-gradient(90deg,#0891b2,#22d3ee)"></div>
                </div>
                <span class="text-[10px] text-gray-600 w-6 text-right">${{h.count}}</span>
            </div>`
        ).join('') : '<div class="text-xs text-gray-600 text-center py-4">No data</div>';

        // Load chunks
        loadCdbChunks(0);
    }} catch (e) {{
        document.getElementById('cdb-total').textContent = 'Error';
    }}
}}

async function loadCdbChunks(page) {{
    cdbChunksPage = page;
    const limit = 20;
    const offset = page * limit;
    try {{
        const resp = await fetch(`/api/observatory/chunks?offset=${{offset}}&limit=${{limit}}`);
        cdbChunksAll = await resp.json();

        renderCdbChunks(cdbChunksAll);
        document.getElementById('cdb-chunk-count').textContent = `${{cdbChunksAll.length}} loaded (page ${{page + 1}})`;

        // Pagination
        const pag = document.getElementById('cdb-pagination');
        pag.innerHTML = `
            <button onclick="loadCdbChunks(${{Math.max(0, page - 1)}})" class="text-xs px-3 py-1 rounded bg-gray-200 text-gray-600 hover:bg-gray-300 ${{page === 0 ? 'opacity-50' : ''}}" ${{page === 0 ? 'disabled' : ''}}>Prev</button>
            <span class="text-xs text-gray-500">Page ${{page + 1}}</span>
            <button onclick="loadCdbChunks(${{page + 1}})" class="text-xs px-3 py-1 rounded bg-gray-200 text-gray-600 hover:bg-gray-300 ${{cdbChunksAll.length < limit ? 'opacity-50' : ''}}" ${{cdbChunksAll.length < limit ? 'disabled' : ''}}>Next</button>
        `;
    }} catch (e) {{
        document.getElementById('cdb-chunk-list').innerHTML = '<div class="px-4 py-6 text-center text-xs text-red-400">Failed to load chunks</div>';
    }}
}}

function renderCdbChunks(chunks) {{
    const list = document.getElementById('cdb-chunk-list');
    if (!chunks.length) {{
        list.innerHTML = '<div class="px-4 py-6 text-center text-xs text-gray-600">No chunks found</div>';
        return;
    }}
    list.innerHTML = chunks.map((c, i) => {{
        const id = c.id || `chunk-${{i}}`;
        const meta = c.metadata || {{}};
        const content = (c.content || '').substring(0, 200);
        const source = meta.source || meta.workflow_id || '--';
        const category = meta.category || meta.workflow_category || '--';
        return `<div class="px-4 py-3 border-b border-gray-200 hover:bg-gray-50 transition-colors">
            <div class="flex items-center justify-between mb-1">
                <span class="font-mono text-[10px] text-gray-500 truncate max-w-[200px]">${{id}}</span>
                <div class="flex items-center gap-2">
                    <span class="text-[10px] px-1.5 py-0.5 bg-indigo-100 text-indigo-700 rounded">${{category}}</span>
                    <button onclick="findSimilarCdb('${{id}}')" class="text-[10px] px-2 py-0.5 bg-gray-200 text-gray-600 rounded hover:bg-gray-300">Find Similar</button>
                </div>
            </div>
            <div class="text-xs text-gray-600 truncate">${{content}}</div>
            <div class="text-[10px] text-gray-500 mt-1">Source: ${{source}}</div>
        </div>`;
    }}).join('');
}}

function filterCdbChunks() {{
    const query = (document.getElementById('cdb-search').value || '').toLowerCase();
    const filtered = cdbChunksAll.filter(c => {{
        const content = (c.content || '').toLowerCase();
        const id = (c.id || '').toLowerCase();
        return content.includes(query) || id.includes(query);
    }});
    renderCdbChunks(filtered);
}}

async function findSimilarCdb(chunkId) {{
    try {{
        const resp = await fetch('/api/observatory/similar-chunks', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ chunk_id: chunkId, top_k: 5 }}),
        }});
        const data = await resp.json();
        const similar = data.similar || data || [];
        const list = document.getElementById('cdb-chunk-list');
        if (Array.isArray(similar) && similar.length) {{
            list.innerHTML = `<div class="px-4 py-2 bg-indigo-100 text-xs text-indigo-700 font-medium">Similar to: ${{chunkId}} <button onclick="loadCdbChunks(${{cdbChunksPage}})" class="ml-3 underline">Back to all</button></div>` +
                similar.map((c, i) => {{
                    const content = (c.content || c.document || '').substring(0, 200);
                    const dist = c.distance != null ? c.distance.toFixed(4) : '--';
                    return `<div class="px-4 py-3 border-b border-gray-200">
                        <div class="flex items-center justify-between mb-1">
                            <span class="font-mono text-[10px] text-gray-500">${{c.id || 'chunk-' + i}}</span>
                            <span class="text-[10px] text-amber-400">dist: ${{dist}}</span>
                        </div>
                        <div class="text-xs text-gray-600">${{content}}</div>
                    </div>`;
                }}).join('');
        }}
    }} catch (e) {{
        // silently fail
    }}
}}

// --- Sub-panel C: Storage Map ---
function _fmtBytes(bytes) {{
    if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(2) + ' GB';
    if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + ' MB';
    if (bytes >= 1024) return (bytes / 1024).toFixed(0) + ' KB';
    return bytes + ' B';
}}

const STOR_COLORS = ['#4f46e5','#7c3aed','#0891b2','#059669','#d97706','#e11d48'];

async function loadStorageOverview() {{
    try {{
        const resp = await fetch('/api/storage/overview');
        const data = await resp.json();

        document.getElementById('stor-total').textContent = _fmtBytes(data.total_size || 0);

        // Directory cards
        const dirs = data.directories || {{}};
        const dirEntries = Object.entries(dirs).sort((a, b) => b[1] - a[1]);
        document.getElementById('stor-dirs').innerHTML = dirEntries.map(([name, size], i) =>
            `<div class="stat-card rounded-lg p-4 border border-gray-200">
                <div class="flex items-center gap-2 mb-1">
                    <span class="w-3 h-3 rounded" style="background:${{STOR_COLORS[i % STOR_COLORS.length]}}"></span>
                    <span class="text-sm font-medium text-gray-800">${{name}}</span>
                </div>
                <div class="text-xl font-bold text-gray-700">${{_fmtBytes(size)}}</div>
                <div class="text-[10px] text-gray-500 mt-1">${{data.total_size ? ((size / data.total_size) * 100).toFixed(1) : 0}}% of total</div>
            </div>`
        ).join('');

        // Proportional bar
        const total = data.total_size || 1;
        document.getElementById('stor-bar').innerHTML = dirEntries.map(([name, size], i) => {{
            const pct = (size / total * 100).toFixed(1);
            return size > 0 ? `<div class="storage-bar-seg" style="width:${{pct}}%;background:${{STOR_COLORS[i % STOR_COLORS.length]}}" title="${{name}}: ${{_fmtBytes(size)}}"></div>` : '';
        }}).join('');

        document.getElementById('stor-bar-legend').innerHTML = dirEntries.map(([name, size], i) =>
            `<span class="flex items-center gap-1.5 text-xs text-gray-500"><span class="w-3 h-3 rounded" style="background:${{STOR_COLORS[i % STOR_COLORS.length]}}"></span>${{name}}</span>`
        ).join('');

        // SQLite databases
        const dbs = data.databases || {{}};
        document.getElementById('stor-databases').innerHTML = Object.entries(dbs).map(([name, info]) => {{
            const tables = info.tables || [];
            return `<div>
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-medium text-gray-800">${{name}}</span>
                    <span class="text-xs text-gray-500">${{_fmtBytes(info.size || 0)}}</span>
                </div>
                ${{tables.length ? `<div class="space-y-1">` + tables.map(t =>
                    `<div class="flex items-center justify-between text-xs">
                        <span class="text-gray-500 font-mono">${{t.name}}</span>
                        <span class="text-gray-600">${{t.rows.toLocaleString()}} rows</span>
                    </div>`
                ).join('') + '</div>' : '<div class="text-xs text-gray-600">No tables</div>'}}
            </div>`;
        }}).join('');

        // Cache + Feedback
        const cache = data.cache || {{}};
        document.getElementById('stor-cache').innerHTML = `
            <div class="grid grid-cols-3 gap-3">
                <div class="text-center">
                    <div class="text-lg font-bold text-indigo-400">${{cache.entries || 0}}</div>
                    <div class="text-[10px] text-gray-500">Cache Entries</div>
                </div>
                <div class="text-center">
                    <div class="text-lg font-bold text-green-400">${{cache.hit_rate || '0%'}}</div>
                    <div class="text-[10px] text-gray-500">Hit Rate</div>
                </div>
                <div class="text-center">
                    <div class="text-lg font-bold text-amber-400">${{(cache.tokens_saved || 0).toLocaleString()}}</div>
                    <div class="text-[10px] text-gray-500">Tokens Saved</div>
                </div>
            </div>
            <div class="mt-3 pt-3 border-t border-gray-200 flex items-center justify-between">
                <span class="text-xs text-gray-500">Feedback Log Entries</span>
                <span class="text-sm font-bold text-purple-400">${{data.feedback_count || 0}}</span>
            </div>
        `;
    }} catch (e) {{
        document.getElementById('stor-total').textContent = 'Error';
    }}
}}

// === Init ===
pollHealth();
setInterval(pollHealth, 30000);

// Preload all tab data in background so first tab switch is instant
Promise.all([
    loadDataStats(),
    fetch('/api/pipeline/status').then(r => r.json()).then(data => {{ window._preloadedPipeline = data; }}).catch(() => {{}}),
    fetch('/api/metrics').then(r => r.json()).then(data => {{ window._preloadedMetrics = data; }}).catch(() => {{}}),
    fetch('/api/agent/stats').then(r => r.json()).then(data => {{ window._preloadedAgentStats = data; }}).catch(() => {{}}),
    fetch('/api/agent/traces?limit=30').then(r => r.json()).then(data => {{ window._preloadedAgentTraces = data; }}).catch(() => {{}}),
]).catch(() => {{}});
</script>
</body></html>"""
