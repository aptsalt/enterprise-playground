export interface FeatureInfo {
  title: string;
  what: string;
  how: string[];
  example: {
    scenario: string;
    result: string;
  };
}

export const FEATURE_INFO: Record<string, FeatureInfo> = {
  "semantic-caching": {
    title: "Semantic Caching",
    what: "Instead of exact string matching, the cache checks if a new prompt means the same thing as a previous one using SequenceMatcher similarity scoring.",
    how: [
      "Every prompt you submit is compared against recent prompts using difflib.SequenceMatcher",
      "If similarity exceeds the threshold (~85%), the cached HTML is returned instantly",
      "Cache hits use 0 tokens and skip the GPU entirely",
      "Typical hit rate is ~35% during iterative UI refinement sessions",
    ],
    example: {
      scenario: "You ask \"Create a login form with email and password\" then later ask \"Build a login form with email and password fields\".",
      result: "The second prompt scores ~92% similarity, so the cached HTML is returned in <10ms with 0 tokens used instead of a full 8-12 second generation.",
    },
  },
  "smart-router": {
    title: "Smart Router",
    what: "A two-stage classifier that decides whether your prompt needs the full 14B code generator or can be handled by the smaller 3B model, saving GPU time on simple requests.",
    how: [
      "Stage 1: Keyword scan checks for code-specific terms (HTML, CSS, component, layout, etc.)",
      "Stage 2: The 3B model classifies ambiguous prompts as 'code' or 'text'",
      "Code prompts route to the 14B generator; text prompts go to the 3B model",
      "Achieves 95.8% routing accuracy across mixed workloads",
    ],
    example: {
      scenario: "You type \"What does flexbox do?\" — a text question, not a code request.",
      result: "The router detects no code keywords and classifies it as 'text', so the 3B model answers in ~1.5s instead of tying up the 14B generator for ~8s.",
    },
  },
  "rag-pipeline": {
    title: "RAG Pipeline",
    what: "Retrieval-Augmented Generation enriches your prompts with relevant UI patterns from a ChromaDB vector database, so the model generates code that matches your existing design system.",
    how: [
      "Your prompt is embedded using nomic-embed-text (runs on CPU to save GPU VRAM)",
      "ChromaDB performs similarity search across stored UI component chunks",
      "Top-matching chunks are injected into the generation prompt as context",
      "The 14B model generates code consistent with your existing patterns",
    ],
    example: {
      scenario: "You ask for a \"transaction history table\" and your ChromaDB has stored banking UI patterns with specific column layouts and color schemes.",
      result: "The model receives those patterns as context and generates a table matching your existing design — correct column headers, status badges, and currency formatting — instead of a generic table.",
    },
  },
  "context-compression": {
    title: "Context Compression",
    what: "The 3B model summarizes long RAG chunks before they're sent to the 14B generator, reducing input token count by 30-50% without losing essential design information.",
    how: [
      "RAG retrieves matching chunks from ChromaDB",
      "Long chunks are passed through the 3B model for summarization",
      "Compressed summaries retain component structure, class names, and layout patterns",
      "Fewer input tokens = faster generation and lower VRAM pressure",
    ],
    example: {
      scenario: "RAG retrieves a 2,000-token chunk containing a full banking dashboard component with verbose comments and repeated patterns.",
      result: "The 3B compressor distills it to ~900 tokens — key Tailwind classes, component hierarchy, and color variables — cutting generation time by ~25%.",
    },
  },
  "sse-streaming": {
    title: "SSE Streaming",
    what: "Server-Sent Events stream generated HTML token-by-token from the backend to your browser, so you see the UI being built in real time instead of waiting for the full response.",
    how: [
      "FastAPI opens an SSE connection when generation starts",
      "Each token from the 14B model is sent as an SSE event immediately",
      "The browser assembles tokens into a live HTML preview as they arrive",
      "Connection closes automatically when generation completes or on error",
    ],
    example: {
      scenario: "You request a complex dashboard card — the 14B model will produce ~3,000 tokens over ~10 seconds.",
      result: "Instead of a 10-second blank screen, you see the HTML structure appear within 500ms and watch the component fill in progressively, with a usable partial preview after ~3 seconds.",
    },
  },
  "dual-model": {
    title: "Dual-Model Architecture",
    what: "Two specialized models — a 14B code generator and a 3B utility model — run simultaneously on a single GPU within a 10.5GB VRAM budget.",
    how: [
      "The 14B Qwen2.5-Coder handles all HTML/CSS/JS code generation",
      "The 3B Qwen2.5 handles routing, classification, compression, and text tasks",
      "Both models stay loaded in VRAM with carefully tuned context windows",
      "Embeddings (nomic-embed-text) run on CPU to stay within the GPU budget",
    ],
    example: {
      scenario: "You submit a UI generation prompt while the system has both models loaded on an RTX 4090.",
      result: "The 3B model routes and compresses context in ~500ms, then the 14B model generates code — total VRAM stays at ~10.5GB, leaving headroom for model operations.",
    },
  },
  "qlora-fine-tuning": {
    title: "QLoRA Fine-Tuning",
    what: "Low-Rank Adaptation training lets you fine-tune the 14B generator on your own UI data without needing massive GPU memory — it trains adapter weights, not the full model.",
    how: [
      "Training data is collected from your generated UIs and corrections",
      "QLoRA (4-bit quantized LoRA with r=32) trains small adapter matrices",
      "Training runs on-device using your RTX 4090",
      "Trained adapters merge with the base model for improved generation quality",
    ],
    example: {
      scenario: "After generating 50+ banking UIs, you've manually corrected recurring issues with table alignment and button spacing.",
      result: "A QLoRA fine-tune session trains on your corrections, and subsequent generations produce correctly aligned tables and properly spaced buttons without needing those corrections in the prompt.",
    },
  },
  "umap-embeddings": {
    title: "UMAP Embedding Visualization",
    what: "UMAP reduces high-dimensional embedding vectors to 2D/3D coordinates so you can visually explore how your stored UI components cluster and relate to each other.",
    how: [
      "Component embeddings from ChromaDB are extracted (768-dimensional vectors)",
      "UMAP reduces them to 2D or 3D coordinates preserving neighborhood relationships",
      "Points are plotted as an interactive scatter visualization",
      "Clusters reveal which components are semantically similar",
    ],
    example: {
      scenario: "You've stored 200 UI component chunks and want to see how they're organized.",
      result: "The UMAP view shows distinct clusters: login forms grouped together, data tables in another cluster, navigation components in a third — letting you spot gaps or redundancies in your pattern library.",
    },
  },
  "vram-orchestration": {
    title: "VRAM Orchestration",
    what: "A memory budgeting system that manages GPU allocation across both models and embeddings, using CPU offloading to keep total VRAM within the 16GB limit of an RTX 4090.",
    how: [
      "Each model has a fixed VRAM budget (14B: ~8GB, 3B: ~2.5GB)",
      "Embedding model (nomic-embed-text) is offloaded to CPU entirely",
      "Context windows are sized to prevent VRAM spikes during generation",
      "Real-time monitoring tracks actual vs. budgeted VRAM per model",
    ],
    example: {
      scenario: "During a generation, the 14B model processes a long prompt with RAG context while the 3B model is idle.",
      result: "VRAM usage peaks at ~10.5GB — the 14B takes ~8GB for weights + KV cache, the 3B holds ~2.5GB idle, and embeddings run on CPU. The gauge stays comfortably under the 16GB ceiling.",
    },
  },
  "scraper": {
    title: "Playwright Scraper",
    what: "An automated browser scraper using Playwright and BeautifulSoup that captures real banking UIs — their HTML structure, styles, and layout — to build the training and RAG dataset.",
    how: [
      "Playwright launches a headless browser and navigates to target banking sites",
      "JavaScript is executed to render dynamic content (SPAs, lazy-loaded elements)",
      "BeautifulSoup parses and cleans the captured HTML",
      "Cleaned components are chunked and stored in ChromaDB with embeddings",
    ],
    example: {
      scenario: "You point the scraper at a banking dashboard page with account cards, transaction tables, and navigation menus.",
      result: "The scraper captures each component separately — 12 chunks covering cards, tables, nav items — each stored with its embedding vector for RAG retrieval during generation.",
    },
  },
  "agent-tracing": {
    title: "Agent Tracing",
    what: "Per-step observability that tracks latency, token usage, router confidence, and cache decisions across every stage of the pipeline for each request.",
    how: [
      "Each pipeline step (route, cache check, RAG, compress, generate) is instrumented",
      "Timestamps capture per-step and end-to-end latency",
      "Token counts are tracked for input and output at each model call",
      "Router confidence scores and cache similarity scores are logged",
    ],
    example: {
      scenario: "A generation request takes 12 seconds total and you want to know where the time went.",
      result: "The trace shows: route (0.3s, 95% confidence) → cache miss (0.1s, 72% similarity) → RAG (0.8s, 3 chunks) → compress (1.2s, 40% reduction) → generate (9.6s, 2,847 tokens). You can see the bottleneck is generation, not routing.",
    },
  },
  "chromadb-inspector": {
    title: "ChromaDB Inspector",
    what: "A built-in chunk browser that lets you explore, search, and inspect the vector database contents — see what's stored, how it's distributed, and test similarity queries.",
    how: [
      "Browse all stored chunks with their metadata and types",
      "Run similarity searches to see which chunks match a given query",
      "View type distributions (e.g., how many card vs. table vs. nav chunks)",
      "Inspect individual chunk content, embedding dimensions, and metadata",
    ],
    example: {
      scenario: "You want to check if the RAG database has enough 'data table' patterns before generating a new one.",
      result: "The inspector shows 18 table-type chunks, lets you search for \"transaction table\" and see the top-5 matches with similarity scores, and preview the actual HTML stored in each chunk.",
    },
  },
};

const PHASE_TO_FEATURE: Record<string, string> = {
  scrape: "scraper",
  map: "smart-router",
  store: "rag-pipeline",
  route: "smart-router",
  generate: "dual-model",
  cache: "semantic-caching",
  train: "qlora-fine-tuning",
};

export function getFeatureIdForPhase(phaseKey: string): string | undefined {
  return PHASE_TO_FEATURE[phaseKey];
}
