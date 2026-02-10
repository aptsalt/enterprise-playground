"""
Pipeline Orchestrator
======================
End-to-end pipeline: scrape → map → generate → dataset → train → deploy.

Usage:
    python scripts/pipeline.py full --target-examples 150 --train-local
    python scripts/pipeline.py scrape-only
    python scripts/pipeline.py generate-only
    python scripts/pipeline.py train-only --local
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

import click
from rich.console import Console

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    STRUCTURED_DIR, GENERATED_DIR, DATA_DIR,
    DISCOVER_MAX_PAGES,
)

console = Console()


def run_step(name: str, cmd: list[str], timeout: int = 600) -> bool:
    """Run a pipeline step and report status."""
    console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
    console.print(f"[bold cyan]  STEP: {name}[/bold cyan]")
    console.print(f"[bold cyan]{'='*60}[/bold cyan]")
    console.print(f"  Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd, timeout=timeout,
            cwd=str(Path(__file__).parent.parent),
        )
        if result.returncode == 0:
            console.print(f"  [green]PASSED[/green]")
            return True
        else:
            console.print(f"  [red]FAILED (exit code {result.returncode})[/red]")
            return False
    except subprocess.TimeoutExpired:
        console.print(f"  [red]TIMEOUT after {timeout}s[/red]")
        return False
    except Exception as e:
        console.print(f"  [red]ERROR: {e}[/red]")
        return False


def check_prerequisites() -> bool:
    """Verify required tools are available."""
    checks = [
        ("Python", [sys.executable, "--version"]),
        ("Playwright", [sys.executable, "-c", "from playwright.sync_api import sync_playwright; print('OK')"]),
        ("Ollama", [sys.executable, "-c", "import ollama; print('OK')"]),
    ]
    all_ok = True
    for name, cmd in checks:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                console.print(f"  [green]{name}: OK[/green]")
            else:
                console.print(f"  [red]{name}: FAILED[/red]")
                all_ok = False
        except Exception:
            console.print(f"  [red]{name}: NOT FOUND[/red]")
            all_ok = False
    return all_ok


@click.group()
def cli():
    """Enterprise Playground Pipeline"""
    pass


@cli.command()
@click.option("--max-pages", default=None, type=int)
def scrape_only(max_pages):
    """Run scraper only."""
    console.print("[bold]Pipeline: Scrape Only[/bold]")
    cmd = [sys.executable, "-m", "scraper.td_scraper", "--discover"]
    if max_pages:
        cmd.extend(["--max-pages", str(max_pages)])
    run_step("Scrape TD.com", cmd, timeout=3600)

    run_step("Map Workflows", [
        sys.executable, "-m", "scraper.workflow_mapper", "--use-llm"
    ], timeout=300)


@cli.command()
@click.option("--max-count", default=150, type=int)
@click.option("--source", default="all")
def generate_only(max_count, source):
    """Run batch generation only."""
    console.print("[bold]Pipeline: Generate Only[/bold]")
    run_step("Batch Generate", [
        sys.executable, "-m", "scripts.batch_generate",
        "--max-count", str(max_count),
        "--source", source,
    ], timeout=36000)

    run_step("Validate", [
        sys.executable, "-m", "scripts.validate_playgrounds",
    ], timeout=60)


@cli.command()
@click.option("--local", is_flag=True, help="Use local 7B profile")
def train_only(local):
    """Run training only."""
    console.print("[bold]Pipeline: Train Only[/bold]")

    run_step("Prepare Dataset", [
        sys.executable, "-m", "fine_tuning.prepare_dataset",
        "--min-quality", "3", "--format", "alpaca",
        "--split-ratio", "0.9", "--augment",
    ], timeout=120)

    train_cmd = [sys.executable, "-m", "fine_tuning.train_lora"]
    if local:
        train_cmd.append("--local")
    run_step("Train LoRA", train_cmd, timeout=36000)


@cli.command()
@click.option("--target-examples", default=150, type=int, help="Target number of playgrounds")
@click.option("--max-pages", default=None, type=int, help="Max pages to scrape")
@click.option("--train-local", is_flag=True, help="Use local 7B training profile")
@click.option("--skip-scrape", is_flag=True, help="Skip scraping if data exists")
@click.option("--skip-generate", is_flag=True, help="Skip generation if playgrounds exist")
def full(target_examples, max_pages, train_local, skip_scrape, skip_generate):
    """Run full pipeline: scrape → map → generate → dataset → train."""
    console.print("[bold]Pipeline: Full End-to-End[/bold]")
    console.print(f"  Target examples: {target_examples}")
    console.print(f"  Training profile: {'local_7b' if train_local else 'cloud_14b'}")

    start_time = datetime.now()

    # Prerequisites
    console.print("\n[bold]Checking prerequisites...[/bold]")
    if not check_prerequisites():
        console.print("[red]Prerequisites check failed. Fix issues above.[/red]")
        return

    # Phase 1-2: Scrape
    if not skip_scrape:
        scrape_cmd = [sys.executable, "-m", "scraper.td_scraper", "--discover"]
        if max_pages:
            scrape_cmd.extend(["--max-pages", str(max_pages)])
        if not run_step("Scrape TD.com", scrape_cmd, timeout=3600):
            console.print("[yellow]Scraping had issues, continuing with available data...[/yellow]")

        # Phase 3: Map workflows
        run_step("Map Workflows", [
            sys.executable, "-m", "scraper.workflow_mapper", "--use-llm"
        ], timeout=300)
    else:
        console.print("[dim]Skipping scrape (--skip-scrape)[/dim]")

    # Phase 4: Batch generate
    if not skip_generate:
        if not run_step("Batch Generate Playgrounds", [
            sys.executable, "-m", "scripts.batch_generate",
            "--max-count", str(target_examples),
        ], timeout=36000):
            console.print("[red]Generation failed[/red]")
            return
    else:
        console.print("[dim]Skipping generation (--skip-generate)[/dim]")

    # Validate
    run_step("Validate Playgrounds", [
        sys.executable, "-m", "scripts.validate_playgrounds",
    ], timeout=60)

    # Phase 5: Prepare dataset
    if not run_step("Prepare Dataset", [
        sys.executable, "-m", "fine_tuning.prepare_dataset",
        "--min-quality", "3", "--format", "alpaca",
        "--split-ratio", "0.9", "--augment",
    ], timeout=120):
        console.print("[red]Dataset preparation failed[/red]")
        return

    # Phase 6: Train
    train_cmd = [sys.executable, "-m", "fine_tuning.train_lora"]
    if train_local:
        train_cmd.append("--local")
    if not run_step("Train LoRA", train_cmd, timeout=36000):
        console.print("[red]Training failed[/red]")
        return

    # Summary
    elapsed = datetime.now() - start_time
    console.print(f"\n[bold green]{'='*60}[/bold green]")
    console.print(f"[bold green]  PIPELINE COMPLETE[/bold green]")
    console.print(f"[bold green]{'='*60}[/bold green]")
    console.print(f"  Duration: {elapsed}")

    # Print data stats
    _print_pipeline_stats()


def _print_pipeline_stats():
    """Print summary statistics from the pipeline run."""
    # Scraped pages
    scraped = list(STRUCTURED_DIR.glob("*.json"))
    scraped = [f for f in scraped if not f.name.startswith("_") and not f.name.startswith("workflow_")]
    console.print(f"  Scraped pages: {len(scraped)}")

    # Workflows
    workflows = list(STRUCTURED_DIR.glob("workflow_*.json"))
    console.print(f"  Workflows: {len(workflows)}")

    # Generated playgrounds
    playgrounds = list(GENERATED_DIR.glob("*.html"))
    console.print(f"  Playgrounds: {len(playgrounds)}")

    # Training data
    train_file = DATA_DIR / "train.jsonl"
    val_file = DATA_DIR / "val.jsonl"
    if train_file.exists():
        train_count = sum(1 for _ in open(train_file))
        val_count = sum(1 for _ in open(val_file)) if val_file.exists() else 0
        console.print(f"  Training examples: {train_count} train / {val_count} val")

    # Adapter
    from config import ADAPTERS_DIR
    adapter_path = ADAPTERS_DIR / "td-playground-lora" / "final_adapter"
    if adapter_path.exists():
        console.print(f"  Adapter: {adapter_path}")
    console.print()


if __name__ == "__main__":
    cli()
