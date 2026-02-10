"""
Workflow Mapper
================
Converts raw scraped data into structured workflow definitions.
Uses the local LLM (via Ollama) to intelligently map page captures
into coherent user journeys.

Usage:
    python -m scraper.workflow_mapper                # Process all captured data
    python -m scraper.workflow_mapper --category accounts
"""

import json
import sys
from pathlib import Path
from datetime import datetime

import click
from rich.console import Console

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import STRUCTURED_DIR, OLLAMA_HOST, ROUTER_MODEL

console = Console()


def load_captured_pages(category: str = None) -> list[dict]:
    """Load all captured page JSONs."""
    pages = []
    for json_file in sorted(STRUCTURED_DIR.glob("*.json")):
        if json_file.name.startswith("_"):
            continue
        if category and not json_file.name.startswith(category):
            continue
        data = json.loads(json_file.read_text(encoding="utf-8"))
        pages.append(data)
    return pages


def group_pages_by_category(pages: list[dict]) -> dict[str, list[dict]]:
    """Group captured pages by their category."""
    groups = {}
    for page in pages:
        cat = page.get("category", "unknown")
        groups.setdefault(cat, []).append(page)
    return groups


def build_workflow_from_pages(category: str, pages: list[dict]) -> dict:
    """
    Build a workflow definition from a set of related pages.
    This creates a basic workflow without LLM assistance.
    For LLM-enhanced workflows, use build_workflow_with_llm().
    """
    if not pages:
        return None

    # Sort by URL depth (shallow pages first)
    pages.sort(key=lambda p: p.get("url", "").count("/"))

    steps = []
    for i, page in enumerate(pages):
        step = {
            "step_number": i + 1,
            "url": page.get("url", ""),
            "title": page.get("title", ""),
            "content_summary": _summarize_page(page),
            "interactive_elements": _extract_interactions(page),
            "forms": page.get("forms", []),
            "user_action": _infer_user_action(page, i),
            "screenshot_path": page.get("screenshot_path"),
        }
        steps.append(step)

    entry = pages[0]
    workflow = {
        "workflow_id": f"wf-{category}-{datetime.now().strftime('%Y%m%d')}",
        "name": f"{category.replace('_', ' ').title()} Workflow",
        "category": category,
        "description": f"User journey through TD {category.replace('_', ' ')} section",
        "entry_point": entry.get("url", ""),
        "steps": steps,
        "total_pages": len(pages),
        "tags": [category, "td-bank", "personal-banking"],
        "created_at": datetime.now().isoformat(),
    }
    return workflow


def _summarize_page(page: dict) -> str:
    """Create a brief content summary from page data."""
    parts = []
    if page.get("meta_description"):
        parts.append(page["meta_description"])
    headings = page.get("headings", [])
    for h in headings[:5]:
        parts.append(h.get("text", ""))
    cards = page.get("cards", [])
    if cards:
        parts.append(f"{len(cards)} product/feature cards")
    forms = page.get("forms", [])
    if forms:
        total_fields = sum(len(f.get("fields", [])) for f in forms)
        parts.append(f"{len(forms)} form(s) with {total_fields} fields")
    return " | ".join(parts)[:500]


def _extract_interactions(page: dict) -> list[dict]:
    """Extract key interactive elements."""
    interactions = []
    for btn in page.get("buttons", [])[:10]:
        if btn.get("label"):
            interactions.append({"type": "button", "label": btn["label"]})
    for link in page.get("links", [])[:10]:
        if link.get("is_cta") and link.get("label"):
            interactions.append({"type": "cta_link", "label": link["label"], "url": link.get("url")})
    return interactions


def _infer_user_action(page: dict, step_index: int) -> str:
    """Infer what the user does on this page."""
    forms = page.get("forms", [])
    cards = page.get("cards", [])
    ctas = [l for l in page.get("links", []) if l.get("is_cta")]

    if forms:
        field_names = [f.get("label") or f.get("name") for form in forms for f in form.get("fields", [])]
        return f"Fill out form: {', '.join(field_names[:5])}"
    elif cards:
        return f"Browse and compare {len(cards)} options, select one to proceed"
    elif ctas:
        return f"Review information and click CTA: {ctas[0].get('label', 'Continue')}"
    elif step_index == 0:
        return "Landing page - review overview and choose a path"
    else:
        return "Review information and navigate to next step"


def build_workflow_with_llm(category: str, pages: list[dict]) -> dict:
    """
    Use local LLM to create a more intelligent workflow mapping.
    Requires Ollama running with configured model.
    """
    try:
        import ollama
    except ImportError:
        console.print("[yellow]ollama package not installed, falling back to rule-based mapping[/yellow]")
        return build_workflow_from_pages(category, pages)

    # Build context from pages
    page_summaries = []
    for i, page in enumerate(pages):
        summary = {
            "page_index": i,
            "url": page.get("url"),
            "title": page.get("title"),
            "headings": [h["text"] for h in page.get("headings", [])[:5]],
            "cards_count": len(page.get("cards", [])),
            "forms_count": len(page.get("forms", [])),
            "cta_buttons": [l["label"] for l in page.get("links", []) if l.get("is_cta")][:5],
        }
        page_summaries.append(summary)

    prompt = f"""Analyze these {len(pages)} captured web pages from TD Bank's {category} section
and create a structured user workflow. Each page represents a step in the customer journey.

Pages captured:
{json.dumps(page_summaries, indent=2)}

Create a JSON workflow with:
1. A clear workflow name and description
2. Ordered steps showing the user journey
3. For each step: what the user sees, what action they take, what triggers the next step

Return ONLY valid JSON in this format:
{{
    "name": "...",
    "description": "...",
    "steps": [
        {{
            "step_number": 1,
            "page_index": 0,
            "title": "...",
            "user_action": "...",
            "expected_outcome": "...",
            "next_step_trigger": "..."
        }}
    ]
}}"""

    try:
        client = ollama.Client(host=OLLAMA_HOST)
        response = client.chat(
            model=ROUTER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.3},
        )
        llm_output = response["message"]["content"]

        # Extract JSON from response
        json_match = llm_output
        if "```json" in llm_output:
            json_match = llm_output.split("```json")[1].split("```")[0]
        elif "```" in llm_output:
            json_match = llm_output.split("```")[1].split("```")[0]

        llm_workflow = json.loads(json_match.strip())

        # Merge LLM analysis with original page data
        base_workflow = build_workflow_from_pages(category, pages)
        base_workflow["name"] = llm_workflow.get("name", base_workflow["name"])
        base_workflow["description"] = llm_workflow.get("description", base_workflow["description"])

        for llm_step in llm_workflow.get("steps", []):
            idx = llm_step.get("page_index", llm_step.get("step_number", 1) - 1)
            if 0 <= idx < len(base_workflow["steps"]):
                base_workflow["steps"][idx]["user_action"] = llm_step.get("user_action", base_workflow["steps"][idx]["user_action"])
                base_workflow["steps"][idx]["expected_outcome"] = llm_step.get("expected_outcome", "")
                base_workflow["steps"][idx]["next_step_trigger"] = llm_step.get("next_step_trigger", "")

        base_workflow["llm_enhanced"] = True
        return base_workflow

    except Exception as e:
        console.print(f"[yellow]LLM mapping failed ({e}), using rule-based mapping[/yellow]")
        return build_workflow_from_pages(category, pages)


def split_category_into_sub_workflows(category: str, pages: list[dict], max_per_workflow: int = 8) -> list[tuple[str, list[dict]]]:
    """
    Break large categories (10+ pages) into logical sub-workflows
    based on URL path structure. Returns list of (sub_key, pages) pairs.
    """
    if len(pages) <= max_per_workflow:
        return [(category, pages)]

    # Group by URL sub-path (3rd level under category)
    sub_groups = {}
    for page in pages:
        url = page.get("url", "") or page.get("url_path", "")
        # Extract sub-path: e.g. /ca/en/personal-banking/products/credit-cards/cash-back → cash-back
        parts = url.rstrip("/").split("/")
        # Find the part after the category identifier
        sub_key = "overview"
        for i, part in enumerate(parts):
            if part in ("products", "personal-investing", "solutions"):
                # Get the next 1-2 path components
                remaining = parts[i+1:]
                if len(remaining) >= 2:
                    sub_key = remaining[1]  # e.g. "cash-back" under "credit-cards"
                break

        sub_groups.setdefault(sub_key, []).append(page)

    # If splitting didn't help much (all pages in one sub-group), chunk by count
    if len(sub_groups) <= 1:
        chunks = []
        for i in range(0, len(pages), max_per_workflow):
            chunk = pages[i:i+max_per_workflow]
            suffix = f"part{i // max_per_workflow + 1}"
            chunks.append((f"{category}_{suffix}", chunk))
        return chunks

    return [(f"{category}_{sub_key}", sub_pages) for sub_key, sub_pages in sub_groups.items()]


@click.command()
@click.option("--category", "-c", default=None, help="Process a specific category")
@click.option("--use-llm/--no-llm", default=False, help="Use LLM for enhanced mapping")
@click.option("--split/--no-split", default=True, help="Split large categories into sub-workflows")
def main(category: str, use_llm: bool, split: bool):
    """Convert captured pages into structured workflows."""
    pages = load_captured_pages(category)
    if not pages:
        console.print("[red]No captured pages found. Run the scraper first.[/red]")
        return

    console.print(f"[bold]Processing {len(pages)} captured pages[/bold]")
    groups = group_pages_by_category(pages)

    all_workflows = []
    for cat_key, cat_pages in groups.items():
        console.print(f"\n[cyan]Category: {cat_key} ({len(cat_pages)} pages)[/cyan]")

        # Split large categories into sub-workflows
        if split:
            sub_groups = split_category_into_sub_workflows(cat_key, cat_pages)
        else:
            sub_groups = [(cat_key, cat_pages)]

        for sub_key, sub_pages in sub_groups:
            if split and len(sub_groups) > 1:
                console.print(f"  [dim]Sub-workflow: {sub_key} ({len(sub_pages)} pages)[/dim]")

            if use_llm:
                workflow = build_workflow_with_llm(sub_key, sub_pages)
            else:
                workflow = build_workflow_from_pages(sub_key, sub_pages)

            if workflow:
                out_path = STRUCTURED_DIR / f"workflow_{sub_key}.json"
                out_path.write_text(json.dumps(workflow, indent=2, default=str), encoding="utf-8")
                console.print(f"  [green]Saved:[/green] {out_path}")
                all_workflows.append(workflow)

    # Save master workflow collection
    collection = {
        "source": "TD Canada Trust - Personal Banking",
        "total_workflows": len(all_workflows),
        "workflow_ids": [w["workflow_id"] for w in all_workflows],
        "generated_at": datetime.now().isoformat(),
    }
    master_path = STRUCTURED_DIR / "_workflows_index.json"
    master_path.write_text(json.dumps(collection, indent=2), encoding="utf-8")
    console.print(f"\n[bold green]Generated {len(all_workflows)} workflows[/bold green]")


if __name__ == "__main__":
    main()
