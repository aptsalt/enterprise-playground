"""
Playground Quality Validator
==============================
Pre-training quality checks on generated playgrounds.
Ensures content fragments meet training data requirements.

Usage:
    python -m scripts.validate_playgrounds
    python -m scripts.validate_playgrounds --fix
"""

import json
import re
import sys
from pathlib import Path
from collections import Counter

import click
from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import GENERATED_DIR
from fine_tuning.prepare_dataset import extract_content_fragment

console = Console()

REQUIRED_CLASSES = ["td-nav", "td-hero", "product-card", "td-section", "td-footer"]
FRAGMENT_DISALLOWED = ["<!DOCTYPE", "<html", "</html>", "<head", "</head>", "<body", "</body>"]
MIN_SIZE = 500
MAX_SIZE = 50000


def validate_all(fix: bool = False) -> dict:
    """Validate all generated playgrounds."""
    html_files = sorted(GENERATED_DIR.glob("*.html"))
    if not html_files:
        console.print("[red]No playgrounds found in generated/[/red]")
        return {"total": 0}

    results = {
        "total": len(html_files),
        "valid": 0,
        "warnings": 0,
        "invalid": 0,
        "issues": Counter(),
        "details": [],
    }

    for html_file in html_files:
        html = html_file.read_text(encoding="utf-8")
        fragment = extract_content_fragment(html)
        issues = []

        # Check 1: Content fragment has expected CSS classes
        class_hits = sum(1 for cls in REQUIRED_CLASSES if cls in fragment)
        if class_hits < 2:
            issues.append(f"few_td_classes ({class_hits}/{len(REQUIRED_CLASSES)})")

        # Check 2: Fragment doesn't contain disallowed tags
        for tag in FRAGMENT_DISALLOWED:
            if tag.lower() in fragment.lower():
                issues.append(f"has_{tag.strip('</>').lower()}")

        # Check 3: Has <style> or <script> blocks (should be in template, not fragment)
        if re.search(r'<style[^>]*>', fragment, re.IGNORECASE):
            issues.append("has_style_block")
        if re.search(r'<script[^>]*>', fragment, re.IGNORECASE):
            issues.append("has_script_block")

        # Check 4: Size bounds
        frag_size = len(fragment)
        if frag_size < MIN_SIZE:
            issues.append(f"too_small ({frag_size}b)")
        elif frag_size > MAX_SIZE:
            issues.append(f"too_large ({frag_size}b)")

        # Check 5: Has meaningful content (not just wrapper divs)
        text_content = re.sub(r'<[^>]+>', '', fragment).strip()
        if len(text_content) < 100:
            issues.append("low_text_content")

        # Record results
        entry = {
            "file": html_file.name,
            "fragment_size": frag_size,
            "class_hits": class_hits,
            "issues": issues,
        }
        results["details"].append(entry)

        if not issues:
            results["valid"] += 1
        elif all("few_td_classes" in i or "has_script" in i for i in issues):
            results["warnings"] += 1
        else:
            results["invalid"] += 1

        for issue in issues:
            results["issues"][issue.split(" ")[0]] += 1

    # Print report
    _print_report(results)

    # Optionally remove invalid files
    if fix:
        removed = 0
        for detail in results["details"]:
            if any("too_small" in i for i in detail["issues"]):
                file_path = GENERATED_DIR / detail["file"]
                meta_path = file_path.with_suffix(".meta.json")
                file_path.unlink(missing_ok=True)
                meta_path.unlink(missing_ok=True)
                removed += 1
        if removed:
            console.print(f"\n[yellow]Removed {removed} invalid playgrounds[/yellow]")

    return results


def check_diversity(min_threshold: float = 0.8) -> dict:
    """Check that playgrounds are diverse enough (no near-duplicates)."""
    from difflib import SequenceMatcher

    html_files = sorted(GENERATED_DIR.glob("*.html"))
    fragments = []
    for f in html_files:
        html = f.read_text(encoding="utf-8")
        frag = extract_content_fragment(html)
        fragments.append((f.name, frag[:2000]))  # Compare first 2000 chars

    duplicates = []
    for i in range(len(fragments)):
        for j in range(i + 1, len(fragments)):
            ratio = SequenceMatcher(None, fragments[i][1], fragments[j][1]).ratio()
            if ratio > min_threshold:
                duplicates.append((fragments[i][0], fragments[j][0], ratio))

    if duplicates:
        console.print(f"\n[yellow]Found {len(duplicates)} near-duplicate pairs (>{min_threshold:.0%} similar):[/yellow]")
        for a, b, r in duplicates[:10]:
            console.print(f"  {r:.1%} similar: {a[:40]} <-> {b[:40]}")
    else:
        console.print(f"\n[green]No near-duplicates found (threshold: {min_threshold:.0%})[/green]")

    return {"duplicate_pairs": len(duplicates), "details": duplicates}


def _print_report(results: dict):
    table = Table(title="Playground Validation Report")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right")

    table.add_row("Total playgrounds", str(results["total"]))
    table.add_row("Valid", f"[green]{results['valid']}[/green]")
    table.add_row("Warnings", f"[yellow]{results['warnings']}[/yellow]")
    table.add_row("Invalid", f"[red]{results['invalid']}[/red]")

    console.print(table)

    if results["issues"]:
        console.print("\n[bold]Issue breakdown:[/bold]")
        for issue, count in results["issues"].most_common():
            console.print(f"  {issue}: {count}")


@click.command()
@click.option("--fix", is_flag=True, help="Remove invalid playgrounds")
@click.option("--diversity", is_flag=True, help="Run diversity check")
def main(fix: bool, diversity: bool):
    """Validate generated playgrounds for training data quality."""
    validate_all(fix=fix)
    if diversity:
        check_diversity()


if __name__ == "__main__":
    main()
