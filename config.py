"""
Central configuration for the Enterprise Playground system.
Optimized for RTX 4090 16GB VRAM with dual-model architecture.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# === Paths ===
ROOT_DIR = Path(__file__).parent
WORKFLOWS_DIR = ROOT_DIR / "workflows"
RAW_DIR = WORKFLOWS_DIR / "raw"
STRUCTURED_DIR = WORKFLOWS_DIR / "structured"
SCREENSHOTS_DIR = WORKFLOWS_DIR / "screenshots"
PLAYGROUND_DIR = ROOT_DIR / "playground"
TEMPLATES_DIR = PLAYGROUND_DIR / "templates"
GENERATED_DIR = PLAYGROUND_DIR / "generated"
FINE_TUNING_DIR = ROOT_DIR / "fine_tuning"
ADAPTERS_DIR = FINE_TUNING_DIR / "adapters"
DATA_DIR = FINE_TUNING_DIR / "data"
CACHE_DIR = ROOT_DIR / ".cache"
CHROMA_DIR = ROOT_DIR / ".chroma"
METRICS_DB = CACHE_DIR / "metrics.db"

for d in [RAW_DIR, STRUCTURED_DIR, SCREENSHOTS_DIR, GENERATED_DIR, ADAPTERS_DIR, DATA_DIR, CACHE_DIR, CHROMA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# === Ollama ===
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# --- Dual-Model Architecture ---
# GENERATOR: 14B coder model for HTML/CSS/JS generation (~8.5GB VRAM at Q4_K_M)
# ROUTER: 3B model for classification, routing, chat, summaries (~2GB VRAM at Q4)
# Total: ~10.5GB VRAM on 4090, leaves ~5.5GB for KV cache
GENERATOR_MODEL = os.getenv("GENERATOR_MODEL", "qwen2.5-coder:14b")
ROUTER_MODEL = os.getenv("ROUTER_MODEL", "qwen2.5:3b")

# Legacy alias
OLLAMA_MODEL = GENERATOR_MODEL

# --- Model Parameters ---
GENERATOR_CTX_SIZE = int(os.getenv("GENERATOR_CTX_SIZE", "8192"))
GENERATOR_TEMPERATURE = float(os.getenv("GENERATOR_TEMPERATURE", "0.7"))
GENERATOR_MAX_TOKENS = int(os.getenv("GENERATOR_MAX_TOKENS", "6144"))

ROUTER_CTX_SIZE = int(os.getenv("ROUTER_CTX_SIZE", "2048"))
ROUTER_TEMPERATURE = float(os.getenv("ROUTER_TEMPERATURE", "0.1"))
ROUTER_MAX_TOKENS = int(os.getenv("ROUTER_MAX_TOKENS", "512"))

# === Caching ===
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_MAX_SIZE_MB = int(os.getenv("CACHE_MAX_SIZE_MB", "500"))
CACHE_SIMILARITY_THRESHOLD = float(os.getenv("CACHE_SIMILARITY_THRESHOLD", "0.85"))
CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "168"))  # 7 days

# === RAG ===
RAG_ENABLED = os.getenv("RAG_ENABLED", "true").lower() == "true"
RAG_EMBED_MODEL = os.getenv("RAG_EMBED_MODEL", "nomic-embed-text")
RAG_COLLECTION = os.getenv("RAG_COLLECTION", "td_workflows")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))

# === Metrics ===
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() == "true"

# === Application ===
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8002"))
APP_ENV = os.getenv("APP_ENV", "development")

# === Scraper ===
TD_BASE_URL = os.getenv("TD_BASE_URL", "https://www.td.com/ca/en/personal-banking")
SCRAPE_DELAY = float(os.getenv("SCRAPE_DELAY_SECONDS", "2"))
SCREENSHOT_WIDTH = int(os.getenv("SCREENSHOT_WIDTH", "1920"))
SCREENSHOT_HEIGHT = int(os.getenv("SCREENSHOT_HEIGHT", "1080"))
DISCOVER_MAX_DEPTH = int(os.getenv("DISCOVER_MAX_DEPTH", "2"))
DISCOVER_MAX_PAGES = int(os.getenv("DISCOVER_MAX_PAGES", "120"))

# === Fine-Tuning (targets 14B model for 4090) ===
BASE_MODEL = os.getenv("BASE_MODEL", "Qwen/Qwen2.5-Coder-14B-Instruct")
LORA_RANK = int(os.getenv("LORA_RANK", "32"))       # Lower rank = less VRAM
LORA_ALPHA = int(os.getenv("LORA_ALPHA", "64"))
LEARNING_RATE = float(os.getenv("LEARNING_RATE", "1e-4"))
NUM_EPOCHS = int(os.getenv("NUM_EPOCHS", "3"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "2"))        # Smaller batch for 16GB
GRADIENT_ACCUMULATION = int(os.getenv("GRADIENT_ACCUMULATION", "8"))

# === TD Banking Workflow Categories ===
# URLs are absolute paths from site root (used by scraper's _make_url)
WORKFLOW_CATEGORIES = {
    "accounts": {
        "name": "Bank Accounts",
        "urls": [
            "/ca/en/personal-banking/products/bank-accounts",
            "/ca/en/personal-banking/products/bank-accounts/chequing-accounts",
            "/ca/en/personal-banking/products/bank-accounts/savings-accounts",
            "/ca/en/personal-banking/products/bank-accounts/us-dollar-accounts",
            "/ca/en/personal-banking/products/bank-accounts/browse-all-bank-accounts",
        ],
    },
    "credit_cards": {
        "name": "Credit Cards",
        "urls": [
            "/ca/en/personal-banking/products/credit-cards",
            "/ca/en/personal-banking/products/credit-cards/cash-back",
            "/ca/en/personal-banking/products/credit-cards/travel-rewards",
            "/ca/en/personal-banking/products/credit-cards/aeroplan",
            "/ca/en/personal-banking/products/credit-cards/low-rate",
            "/ca/en/personal-banking/products/credit-cards/no-annual-fee",
            "/ca/en/personal-banking/products/credit-cards/student",
            "/ca/en/personal-banking/products/credit-cards/browse-all",
        ],
    },
    "mortgages": {
        "name": "Mortgages",
        "urls": [
            "/ca/en/personal-banking/products/mortgages",
            "/ca/en/personal-banking/products/mortgages/mortgage-rates",
            "/ca/en/personal-banking/products/mortgages/mortgage-payment-calculator",
            "/ca/en/personal-banking/products/mortgages/first-time-home-buyer",
            "/ca/en/personal-banking/products/mortgages/td-home-equity-flexline",
            "/ca/en/personal-banking/products/mortgages/renew-refinance/how-to-renew",
        ],
    },
    "loans": {
        "name": "Borrowing & Loans",
        "urls": [
            "/ca/en/personal-banking/products/borrowing",
            "/ca/en/personal-banking/products/borrowing/loans",
            "/ca/en/personal-banking/products/borrowing/lines-of-credit",
            "/ca/en/personal-banking/products/borrowing/lines-of-credit/personal-line-of-credit",
            "/ca/en/personal-banking/products/borrowing/lines-of-credit/student-line-of-credit",
        ],
    },
    "investing": {
        "name": "Investing",
        "urls": [
            "/ca/en/personal-banking/personal-investing",
            "/ca/en/personal-banking/personal-investing/products/investment-plans/tfsa",
            "/ca/en/personal-banking/personal-investing/products/registered-plans/rrsp",
            "/ca/en/personal-banking/personal-investing/products/registered-plans/fhsa",
            "/ca/en/personal-banking/personal-investing/products/gic",
            "/ca/en/personal-banking/personal-investing/products/mutual-funds",
        ],
    },
    "insurance": {
        "name": "Insurance",
        "urls": [
            "/ca/en/personal-banking/products/insurance",
            "/ca/en/personal-banking/products/insurance/travel-medical-insurance",
            "/ca/en/personal-banking/products/insurance/td-mortgage-protection",
            "/ca/en/personal-banking/products/insurance/td-loan-protection",
        ],
    },
    "tools": {
        "name": "Tools & Calculators",
        "urls": [
            "/ca/en/personal-banking/products/mortgages/mortgage-payment-calculator",
            "/ca/en/personal-banking/products/borrowing/personal-loan-line-of-credit-calculator",
            "/ca/en/personal-banking/personal-investing/compound-interest-calculator",
            "/ca/en/personal-banking/personal-investing/tfsa-calculator",
        ],
    },
    "segments": {
        "name": "Customer Segments",
        "urls": [
            "/ca/en/personal-banking/solutions/new-to-canada",
            "/ca/en/personal-banking/solutions/student-banking",
            "/ca/en/personal-banking/solutions/youth-and-parent",
        ],
    },
}

# === Training Profiles ===
TRAINING_PROFILES = {
    "local_7b": {
        "base_model": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "lora_rank": 16,
        "lora_alpha": 32,
        "batch_size": 2,
        "gradient_accumulation": 4,
        "max_seq_length": 4096,
        "learning_rate": 2e-4,
    },
    "cloud_14b": {
        "base_model": "Qwen/Qwen2.5-Coder-14B-Instruct",
        "lora_rank": 32,
        "lora_alpha": 64,
        "batch_size": 4,
        "gradient_accumulation": 4,
        "max_seq_length": 8192,
        "learning_rate": 1e-4,
    },
}
