"""
Batch Playground Generator
============================
Generates a large number of diverse playgrounds for training data.
Three prompt sources: workflow-based, scraped-page, and synthetic.

Usage:
    python -m scripts.batch_generate
    python -m scripts.batch_generate --max-count 50 --dry-run
    python -m scripts.batch_generate --source synthetic
"""

import asyncio
import json
import random
import sys
from pathlib import Path
from datetime import datetime

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import STRUCTURED_DIR, GENERATED_DIR, WORKFLOW_CATEGORIES
from playground.generator import PlaygroundGenerator

console = Console()


def generate_workflow_prompts() -> list[dict]:
    """Generate prompts from workflow JSON files (2-3 per workflow)."""
    prompts = []
    for wf_file in sorted(STRUCTURED_DIR.glob("workflow_*.json")):
        try:
            wf = json.loads(wf_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        name = wf.get("name", "Unknown")
        category = wf.get("category", "banking")
        steps = wf.get("steps", [])
        step_count = len(steps)

        # Extract product names from step titles
        products = [s.get("title", "") for s in steps if s.get("title")][:5]
        product_list = ", ".join(products[:3]) if products else "various products"

        # Prompt 1: Landing page
        prompts.append({
            "prompt": f"TD Bank {name} landing page with product cards for {product_list}",
            "source": "workflow",
            "category": category,
            "workflow_file": str(wf_file),
        })

        # Prompt 2: Comparison table
        if step_count >= 2:
            prompts.append({
                "prompt": f"{name} comparison table showing features, fees, and rates for TD products",
                "source": "workflow",
                "category": category,
                "workflow_file": str(wf_file),
            })

        # Prompt 3: Application flow (if workflow has forms)
        has_forms = any(s.get("forms") or "form" in s.get("user_action", "").lower() for s in steps)
        if has_forms or step_count >= 3:
            prompts.append({
                "prompt": f"Interactive TD Bank {category.replace('_', ' ')} application flow with {min(step_count, 5)} steps",
                "source": "workflow",
                "category": category,
                "workflow_file": str(wf_file),
            })

    return prompts


def generate_scraped_page_prompts() -> list[dict]:
    """Generate prompts from scraped page structured data (1 per unique page)."""
    prompts = []
    seen_titles = set()

    for json_file in sorted(STRUCTURED_DIR.glob("*.json")):
        if json_file.name.startswith("_") or json_file.name.startswith("workflow_"):
            continue

        try:
            page = json.loads(json_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        title = page.get("title", "").strip()
        if not title or title in seen_titles or "404" in title:
            continue
        seen_titles.add(title)

        category = page.get("category", "general")
        cards = page.get("cards", [])
        forms = page.get("forms", [])
        headings = page.get("headings", [])

        # Build a descriptive prompt based on page content
        if cards:
            prompt_text = f"Product showcase page for {title} with {len(cards)} product cards and call-to-action buttons"
        elif forms:
            field_count = sum(len(f.get("fields", [])) for f in forms)
            prompt_text = f"Interactive form page for {title} with {field_count} input fields and validation"
        elif len(headings) > 3:
            prompt_text = f"{title} information page with FAQ accordion and key details sections"
        else:
            prompt_text = f"TD Bank {title} page with hero section, features, and call-to-action"

        prompts.append({
            "prompt": prompt_text,
            "source": "scraped",
            "category": category,
            "page_title": title,
        })

    return prompts


def generate_synthetic_prompts() -> list[dict]:
    """Generate diverse synthetic prompts for banking UI patterns."""
    templates = [
        # Calculators
        ("TD Bank mortgage payment calculator with amortization schedule and rate comparison", "tools"),
        ("Savings goal calculator showing compound interest over 1, 5, 10, and 25 years", "tools"),
        ("Credit card rewards calculator comparing cash back vs travel points value", "tools"),
        ("RRSP contribution calculator with tax refund estimate and retirement projection", "tools"),
        ("TFSA room calculator showing contribution limits and growth projections", "tools"),
        ("Car loan calculator with monthly payment breakdown and total interest", "tools"),
        ("Home affordability calculator based on income, debts, and down payment", "tools"),

        # Segment pages
        ("Student banking hub with chequing account, credit card, and study tools for university students", "segments"),
        ("New to Canada welcome page showing newcomer banking packages and documentation needed", "segments"),
        ("Senior banking page with accessibility features, investment options, and estate planning", "segments"),
        ("Family financial planning dashboard with joint accounts, kids savings, and education funds", "segments"),
        ("Small business owner banking page with business accounts, credit lines, and merchant services", "segments"),
        ("Post-graduation financial transition guide with loan repayment and first job banking", "segments"),

        # Account management
        ("Bank account comparison grid with monthly fees, transaction limits, and perks for all TD chequing accounts", "accounts"),
        ("Account opening wizard with 4 steps: choose account, personal info, ID verification, funding", "accounts"),
        ("Savings account landing page with interest rate tiers and automatic savings features", "accounts"),
        ("US dollar account overview page with cross-border features and exchange rates", "accounts"),

        # Credit cards
        ("Credit card rewards comparison dashboard with annual fee, earn rate, and welcome bonus for 6 cards", "credit_cards"),
        ("Aeroplan credit card showcase with tier benefits, lounge access, and travel insurance details", "credit_cards"),
        ("Student credit card application page with eligibility checker and card features", "credit_cards"),
        ("Cash back credit card landing page with spending category bonuses and redemption options", "credit_cards"),

        # Mortgages
        ("First-time home buyer guide with step-by-step process, pre-approval form, and FAQ", "mortgages"),
        ("Mortgage renewal comparison showing current vs new rate options with savings breakdown", "mortgages"),
        ("TD Home Equity FlexLine product page showing how the credit line works with diagrams", "mortgages"),
        ("Mortgage rates page with fixed vs variable comparison table and historical rate chart", "mortgages"),

        # Investing
        ("TFSA vs RRSP comparison page with side-by-side features, contribution limits, and use cases", "investing"),
        ("GIC rates page with term options, rate ladder strategy, and maturity calendar", "investing"),
        ("Investment portfolio overview dashboard showing asset allocation, returns, and rebalancing", "investing"),
        ("Mutual fund selector with risk assessment quiz and fund recommendations", "investing"),
        ("FHSA information page explaining the new first home savings account with eligibility and rules", "investing"),

        # Insurance
        ("Travel insurance comparison page with coverage levels, deductibles, and claim process", "insurance"),
        ("Mortgage protection insurance overview with coverage scenarios and premium calculator", "insurance"),
        ("TD insurance products landing page with credit protection, travel, and life insurance cards", "insurance"),

        # Dashboards and overviews
        ("Personal banking dashboard showing account balances, recent transactions, and quick actions", "accounts"),
        ("Financial health scorecard with spending insights, savings rate, and debt-to-income ratio", "tools"),
        ("TD personal banking homepage with hero banner, product categories, and featured promotions", "general"),
        ("Branch and ATM locator page with map, search by postal code, and branch details", "tools"),

        # Borrowing
        ("Personal line of credit product page with rates, features, and application CTA", "loans"),
        ("Student line of credit page with program-specific rates and repayment options", "loans"),
        ("Debt consolidation calculator showing potential savings from combining multiple debts", "loans"),
        ("Auto loan page with vehicle financing options, rates, and dealer partnership info", "loans"),
    ]

    prompts = []
    for prompt_text, category in templates:
        prompts.append({
            "prompt": prompt_text,
            "source": "synthetic",
            "category": category,
        })

    return prompts


async def run_batch(
    prompts: list[dict],
    max_count: int = 200,
    dry_run: bool = False,
) -> list[dict]:
    """Generate playgrounds for all prompts."""
    # Shuffle for diversity in case we hit max_count
    random.shuffle(prompts)
    prompts = prompts[:max_count]

    console.print(f"\n[bold]Batch generation: {len(prompts)} playgrounds[/bold]")
    console.print(f"  Sources: {_count_sources(prompts)}")

    if dry_run:
        console.print("\n[yellow]DRY RUN - prompts that would be generated:[/yellow]")
        for i, p in enumerate(prompts[:20]):
            console.print(f"  {i+1}. [{p['source']}] {p['prompt'][:80]}")
        if len(prompts) > 20:
            console.print(f"  ... and {len(prompts) - 20} more")
        return []

    generator = PlaygroundGenerator()
    results = []
    errors = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Generating", total=len(prompts))

        for i, p in enumerate(prompts):
            prompt_text = p["prompt"]
            short = prompt_text[:50]

            try:
                # Load workflow context if available
                workflow_context = None
                if p.get("workflow_file"):
                    try:
                        workflow_context = json.loads(Path(p["workflow_file"]).read_text(encoding="utf-8"))
                    except Exception:
                        pass

                result = await generator.generate(
                    prompt=prompt_text,
                    workflow_context=workflow_context,
                    style="banking",
                    force_generate=True,
                    bypass_cache=True,
                )

                if result.get("html"):
                    results.append({
                        "prompt": prompt_text,
                        "source": p["source"],
                        "category": p.get("category", "general"),
                        "playground_id": result.get("playground_id"),
                        "html_size": len(result["html"]),
                    })
                    progress.update(task, advance=1, description=f"[green]{short}...")
                else:
                    errors.append(f"No HTML: {short}")
                    progress.update(task, advance=1, description=f"[yellow]Skip: {short}...")

            except Exception as e:
                errors.append(f"{short}: {e}")
                progress.update(task, advance=1, description=f"[red]Error: {short}...")

    # Save batch report
    report = {
        "total_prompts": len(prompts),
        "successful": len(results),
        "errors": len(errors),
        "error_details": errors[:20],
        "sources": _count_sources(prompts),
        "generated_at": datetime.now().isoformat(),
    }
    report_path = GENERATED_DIR / "_batch_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    console.print(f"\n[bold green]Batch complete![/bold green]")
    console.print(f"  Generated: {len(results)}")
    console.print(f"  Errors: {len(errors)}")
    console.print(f"  Report: {report_path}")

    return results


def _count_sources(prompts: list[dict]) -> dict:
    counts = {}
    for p in prompts:
        s = p.get("source", "unknown")
        counts[s] = counts.get(s, 0) + 1
    return counts


@click.command()
@click.option("--max-count", default=200, help="Maximum playgrounds to generate")
@click.option("--source", default="all", type=click.Choice(["all", "workflow", "scraped", "synthetic"]))
@click.option("--dry-run", is_flag=True, help="Show prompts without generating")
def main(max_count: int, source: str, dry_run: bool):
    """Batch-generate playgrounds for training data."""
    all_prompts = []

    if source in ("all", "workflow"):
        wf_prompts = generate_workflow_prompts()
        console.print(f"  Workflow prompts: {len(wf_prompts)}")
        all_prompts.extend(wf_prompts)

    if source in ("all", "scraped"):
        scraped_prompts = generate_scraped_page_prompts()
        console.print(f"  Scraped page prompts: {len(scraped_prompts)}")
        all_prompts.extend(scraped_prompts)

    if source in ("all", "synthetic"):
        synth_prompts = generate_synthetic_prompts()
        console.print(f"  Synthetic prompts: {len(synth_prompts)}")
        all_prompts.extend(synth_prompts)

    console.print(f"\n[bold]Total prompts available: {len(all_prompts)}[/bold]")

    asyncio.run(run_batch(all_prompts, max_count=max_count, dry_run=dry_run))


if __name__ == "__main__":
    main()
