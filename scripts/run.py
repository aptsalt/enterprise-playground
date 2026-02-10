"""
Enterprise Playground CLI v2
==============================
Main entry point with dual-model management.

Usage:
    python scripts/run.py setup               # Pull both models via Ollama
    python scripts/run.py serve               # Start web app
    python scripts/run.py generate "prompt"   # Generate a playground
    python scripts/run.py chat "question"     # Ask the 3B router
    python scripts/run.py scrape              # Scrape TD.com
    python scripts/run.py map --use-llm       # Map to workflows
    python scripts/run.py prepare-data        # Prepare fine-tuning data
    python scripts/run.py train               # Fine-tune on GPU
    python scripts/run.py status              # System status + VRAM
    python scripts/run.py cache-stats         # Cache statistics
    python scripts/run.py cache-clear         # Clear cache
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    OLLAMA_HOST, GENERATOR_MODEL, ROUTER_MODEL,
    APP_HOST, APP_PORT,
    STRUCTURED_DIR, GENERATED_DIR, RAW_DIR, SCREENSHOTS_DIR, CACHE_DIR,
)

console = Console()


@click.group()
def cli():
    """Enterprise Playground — Dual-model interactive visualization system."""
    pass


@cli.command()
def setup():
    """Pull both models and verify Ollama is ready."""
    console.print("[bold]Setting up dual-model architecture...[/bold]")
    console.print(f"  Generator: {GENERATOR_MODEL} (~8.5GB)")
    console.print(f"  Router:    {ROUTER_MODEL} (~2GB)")
    console.print(f"  Total VRAM: ~10.5GB (fits in 16GB 4090)\n")

    for model in [ROUTER_MODEL, GENERATOR_MODEL]:
        console.print(f"[cyan]Pulling {model}...[/cyan]")
        try:
            result = subprocess.run(
                ["ollama", "pull", model],
                timeout=1800,
            )
            if result.returncode == 0:
                console.print(f"  [green]{model} ready[/green]")
            else:
                console.print(f"  [red]{model} failed[/red]")
        except FileNotFoundError:
            console.print("[red]Ollama not found. Install from: https://ollama.com[/red]")
            return
        except subprocess.TimeoutExpired:
            console.print(f"  [yellow]{model} still downloading (timeout)[/yellow]")

    console.print("\n[bold green]Setup complete![/bold green]")
    console.print("  Start with: python scripts/run.py serve")


@cli.command()
@click.option("--category", "-c", default=None, help="Scrape specific category")
@click.option("--url", "-u", default=None, help="Scrape specific URL path")
def scrape(category, url):
    """Scrape TD.com personal banking pages."""
    from scraper.td_scraper import TDScraper

    async def run():
        scraper = TDScraper()
        await scraper.start()
        try:
            if url:
                await scraper.capture_page(url, category or "custom")
            elif category:
                await scraper.scrape_category(category)
            else:
                await scraper.scrape_all()
        finally:
            await scraper.stop()

    asyncio.run(run())


@cli.command(name="map")
@click.option("--category", "-c", default=None)
@click.option("--use-llm", is_flag=True, help="Use 3B model for enhanced mapping")
def map_cmd(category, use_llm):
    """Convert scraped pages to structured workflows."""
    from scraper.workflow_mapper import load_captured_pages, group_pages_by_category
    from scraper.workflow_mapper import build_workflow_from_pages, build_workflow_with_llm

    pages = load_captured_pages(category)
    if not pages:
        console.print("[red]No captured pages found. Run scrape first.[/red]")
        return

    groups = group_pages_by_category(pages)
    for cat_key, cat_pages in groups.items():
        console.print(f"\n[cyan]{cat_key}: {len(cat_pages)} pages[/cyan]")
        if use_llm:
            workflow = build_workflow_with_llm(cat_key, cat_pages)
        else:
            workflow = build_workflow_from_pages(cat_key, cat_pages)
        if workflow:
            out_path = STRUCTURED_DIR / f"workflow_{cat_key}.json"
            out_path.write_text(json.dumps(workflow, indent=2, default=str))
            console.print(f"  [green]Saved: {out_path}[/green]")


@cli.command()
@click.argument("prompt")
@click.option("--style", "-s", default="banking", type=click.Choice(["banking", "default", "minimal", "dark"]))
@click.option("--force", is_flag=True, help="Force 14B generation even if router says otherwise")
def generate(prompt, style, force):
    """Generate an interactive playground from a prompt."""
    from playground.generator import PlaygroundGenerator

    async def run():
        gen = PlaygroundGenerator()
        result = await gen.generate(prompt=prompt, style=style, force_generate=force)

        if result.get("html"):
            console.print(f"\n[bold green]Playground ready:[/bold green] {result['file_path']}")
            meta = result.get("metadata", {})
            if meta.get("cache_hit"):
                console.print(f"  [cyan]Cache hit[/cyan] (similarity: {meta.get('similarity', 1.0):.0%})")
            else:
                console.print(f"  Model: {meta.get('model', 'unknown')}")
            console.print(f"  Open: python scripts/run.py serve")
        elif result.get("text"):
            console.print(f"\n[yellow]Routed to 3B ({result.get('task_type', 'chat')}):[/yellow]")
            console.print(result["text"])

    asyncio.run(run())


@cli.command()
@click.argument("message")
def chat(message):
    """Chat with the 3B router model (fast, for non-code tasks)."""
    from playground.router import RequestRouter

    router = RequestRouter()
    routed = router.route(message)
    console.print(f"[dim]Routed as: {routed.task_type.value} → {routed.model}[/dim]")

    if routed.needs_html:
        console.print("[yellow]This looks like a generation request. Use 'generate' instead.[/yellow]")
        return

    response = router.handle_light_task(routed)
    console.print(response)


@cli.command()
@click.option("--host", default=None)
@click.option("--port", default=None, type=int)
def serve(host, port):
    """Start the web application."""
    import uvicorn
    h = host or APP_HOST
    p = port or APP_PORT
    console.print(f"[bold green]Enterprise Playground v2[/bold green]")
    console.print(f"  URL: http://{h}:{p}")
    console.print(f"  Generator: {GENERATOR_MODEL}")
    console.print(f"  Router: {ROUTER_MODEL}")
    uvicorn.run("webapp.app:app", host=h, port=p, reload=True)


@cli.command("prepare-data")
@click.option("--min-quality", default=3)
@click.option("--format", "fmt", default="alpaca", type=click.Choice(["alpaca", "sharegpt"]))
def prepare_data(min_quality, fmt):
    """Prepare fine-tuning dataset from generated playgrounds."""
    from fine_tuning.prepare_dataset import collect_examples, create_training_dataset, create_sharegpt_dataset
    from config import DATA_DIR

    examples = collect_examples()
    if not examples:
        console.print("[red]No examples found. Generate playgrounds first.[/red]")
        return

    if fmt == "alpaca":
        dataset = create_training_dataset(examples, min_quality)
    else:
        dataset = create_sharegpt_dataset(examples, min_quality)

    split_idx = int(len(dataset) * 0.9)
    train_path = DATA_DIR / "train.jsonl"
    val_path = DATA_DIR / "val.jsonl"

    for path, data in [(train_path, dataset[:split_idx]), (val_path, dataset[split_idx:])]:
        with open(path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    console.print(f"[green]Dataset: {len(dataset)} examples (train: {split_idx}, val: {len(dataset) - split_idx})[/green]")


@cli.command()
@click.option("--base-model", default=None)
@click.option("--epochs", default=None, type=int)
@click.option("--use-llamafactory", is_flag=True)
def train(base_model, epochs, use_llamafactory):
    """Run LoRA fine-tuning (requires GPU)."""
    from fine_tuning.train_lora import main as train_main
    ctx = click.Context(train_main)
    ctx.invoke(train_main, base_model=base_model, epochs=epochs, use_llamafactory=use_llamafactory)


@cli.command("cache-stats")
def cache_stats():
    """Show cache statistics."""
    from playground.cache import PlaygroundCache
    cache = PlaygroundCache()
    stats = cache.stats()

    table = Table(title="Cache Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    for key, val in stats.items():
        table.add_row(key.replace("_", " ").title(), str(val))
    console.print(table)


@cli.command("cache-clear")
def cache_clear():
    """Clear the playground cache."""
    from playground.cache import PlaygroundCache
    cache = PlaygroundCache()
    cache.clear()
    console.print("[green]Cache cleared.[/green]")


@cli.command()
def status():
    """Show full system status including VRAM."""
    table = Table(title="Enterprise Playground Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")

    # Files
    raw_count = len(list(RAW_DIR.glob("*.html")))
    table.add_row("Scraped Pages", str(raw_count), str(RAW_DIR))

    screenshot_count = len(list(SCREENSHOTS_DIR.glob("*.png")))
    table.add_row("Screenshots", str(screenshot_count), "")

    workflow_count = len(list(STRUCTURED_DIR.glob("workflow_*.json")))
    table.add_row("Workflows", str(workflow_count), "")

    playground_count = len(list(GENERATED_DIR.glob("*.html")))
    table.add_row("Playgrounds", str(playground_count), str(GENERATED_DIR))

    # Cache
    from playground.cache import PlaygroundCache
    cache = PlaygroundCache()
    cs = cache.stats()
    table.add_row("Cache", f"{cs['entries']} entries, {cs['hit_rate']} rate", f"{cs['total_saved_tokens']:,} tokens saved")

    # Ollama models
    try:
        import ollama
        client = ollama.Client(host=OLLAMA_HOST)
        resp = client.list()
        raw_models = resp.models if hasattr(resp, 'models') else resp.get("models", [])
        model_names = []
        for m in raw_models:
            if hasattr(m, 'model_dump'):
                d = m.model_dump()
                model_names.append(d.get("model", ""))
            elif isinstance(m, dict):
                model_names.append(m.get("name", m.get("model", "")))
            else:
                model_names.append(str(m))
        gen_ok = any(GENERATOR_MODEL.split(":")[0] in m for m in model_names)
        rtr_ok = any(ROUTER_MODEL.split(":")[0] in m for m in model_names)
        table.add_row("Generator", "Ready" if gen_ok else "Not found", GENERATOR_MODEL)
        table.add_row("Router", "Ready" if rtr_ok else "Not found", ROUTER_MODEL)
    except Exception:
        table.add_row("Ollama", "Not available", OLLAMA_HOST)

    # VRAM
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total,gpu_name",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            parts = [p.strip() for p in result.stdout.strip().split(",")]
            used, total = int(parts[0]), int(parts[1])
            pct = round(used / total * 100, 1)
            table.add_row("GPU", parts[2], f"{used}/{total} MB ({pct}%)")
    except Exception:
        table.add_row("GPU", "nvidia-smi unavailable", "")

    # Training data
    from config import DATA_DIR
    train_file = DATA_DIR / "train.jsonl"
    if train_file.exists():
        count = sum(1 for _ in open(train_file))
        table.add_row("Training Data", f"{count} examples", str(train_file))
    else:
        table.add_row("Training Data", "Not prepared", "Run: prepare-data")

    console.print(table)


if __name__ == "__main__":
    cli()
