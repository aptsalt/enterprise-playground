"""
Quickstart Script v2
=====================
Sets up the dual-model Enterprise Playground on a 4090 16GB system.

Usage:
    python scripts/quickstart.py
"""

import subprocess
import sys
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def run(cmd: str, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    print(f"  $ {cmd}")
    return subprocess.run(cmd, shell=True, check=check, capture_output=capture, text=True)


def main():
    print("=" * 60)
    print("Enterprise Playground v2 — Quickstart")
    print("Optimized for RTX 4090 16GB VRAM")
    print("=" * 60)

    # 1. Python check
    print("\n[1/5] Checking Python...")
    v = sys.version_info
    print(f"  Python {v.major}.{v.minor}.{v.micro}")
    if v.major < 3 or (v.major == 3 and v.minor < 10):
        print("  ERROR: Python 3.10+ required")
        sys.exit(1)

    # 2. Install deps
    print("\n[2/5] Installing dependencies...")
    run(f"{sys.executable} -m pip install -r requirements.txt -q")

    # 3. Playwright
    print("\n[3/5] Installing Playwright browsers...")
    run(f"{sys.executable} -m playwright install chromium")

    # 4. Config
    print("\n[4/5] Configuration...")
    env_file = Path(__file__).parent.parent / ".env"
    env_example = Path(__file__).parent.parent / ".env.example"
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print(f"  Created .env from .env.example")
    else:
        print(f"  .env already exists")

    # 5. Ollama + models
    print("\n[5/5] Checking Ollama + models...")
    from config import GENERATOR_MODEL, ROUTER_MODEL

    result = run("ollama --version", check=False, capture=True)
    if result.returncode == 0:
        print(f"  Ollama: {result.stdout.strip()}")

        list_result = run("ollama list", check=False, capture=True)
        models_output = list_result.stdout or ""

        for model in [ROUTER_MODEL, GENERATOR_MODEL]:
            model_base = model.split(":")[0]
            if model_base in models_output:
                print(f"  {model}: ready")
            else:
                print(f"  {model}: not found")
                print(f"    Run: ollama pull {model}")

        print(f"\n  VRAM budget:")
        print(f"    {ROUTER_MODEL} (~2GB) + {GENERATOR_MODEL} (~8.5GB) = ~10.5GB")
        print(f"    Remaining for KV cache: ~5.5GB")
    else:
        print("  Ollama not installed: https://ollama.com")

    print("\n" + "=" * 60)
    print("Commands:")
    print("=" * 60)
    print()
    print("  Setup models:     python scripts/run.py setup")
    print("  Start web app:    python scripts/run.py serve")
    print("  Scrape TD.com:    python scripts/run.py scrape")
    print("  Generate:         python scripts/run.py generate \"mortgage application flow\"")
    print("  Chat (3B):        python scripts/run.py chat \"what is a TFSA?\"")
    print("  System status:    python scripts/run.py status")
    print("  Cache stats:      python scripts/run.py cache-stats")
    print()
    print("  Full pipeline:")
    print("    1. python scripts/run.py setup")
    print("    2. python scripts/run.py scrape")
    print("    3. python scripts/run.py map --use-llm")
    print("    4. python scripts/run.py serve")
    print("    5. Generate playgrounds via http://localhost:8000")
    print("    6. python scripts/run.py prepare-data")
    print("    7. Upload to GPU & run: python -m fine_tuning.train_lora")
    print()


if __name__ == "__main__":
    main()
