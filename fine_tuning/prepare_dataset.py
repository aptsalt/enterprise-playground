"""
Dataset Preparation for Fine-Tuning
=====================================
Converts captured workflows + generated playground examples into
a training dataset for LoRA fine-tuning.

The dataset format is "instruction → response" pairs where:
  - Instruction: User prompt requesting a playground
  - Response: The content fragment (NOT full HTML — just the inner page content)

Critical: Training data must match what the model should output.
The model outputs content fragments using pre-defined CSS classes.
The playground template wrapper is added by the application, not the model.

Usage:
    python -m fine_tuning.prepare_dataset
    python -m fine_tuning.prepare_dataset --min-quality 3
    python -m fine_tuning.prepare_dataset --augment
"""

import json
import re
import random
import sys
from pathlib import Path
from datetime import datetime

import click
from rich.console import Console

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import STRUCTURED_DIR, GENERATED_DIR, DATA_DIR
from playground.router import GENERATOR_SYSTEM

console = Console()


def extract_content_fragment(html: str) -> str:
    """
    Extract only the LLM-generated content from a wrapped playground HTML.
    The template wraps content inside <div id="variation-a">...</div>.
    Training data must contain only this content fragment, not the full template.
    """
    # Look for content between variation-a markers
    match = re.search(
        r'<div\s+id="variation-a"[^>]*>\s*(.*?)\s*</div>\s*<!--\s*/variation-a\s*-->',
        html, re.DOTALL
    )
    if match:
        return match.group(1).strip()

    # Fallback: if it's already a fragment (no DOCTYPE), return as-is
    if not html.strip().lower().startswith("<!doctype"):
        return html.strip()

    # Last resort: extract body content
    body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.IGNORECASE)
    if body_match:
        return body_match.group(1).strip()

    return html.strip()


def collect_examples() -> list[dict]:
    """
    Collect all prompt → content fragment pairs from generated playgrounds.
    Each generated playground has a .meta.json with the prompt
    and a .html file with the output.
    """
    examples = []
    for meta_file in sorted(GENERATED_DIR.glob("*.meta.json")):
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            html_file = meta_file.with_suffix("").with_suffix(".html")
            if not html_file.exists():
                continue

            html_content = html_file.read_text(encoding="utf-8")

            # Skip very small outputs (likely errors)
            if len(html_content) < 500:
                continue

            # Extract content fragment for training
            content_fragment = extract_content_fragment(html_content)

            # Skip if fragment is too small (extraction failed or empty content)
            if len(content_fragment) < 200:
                continue

            # Build the training example
            prompt = meta.get("prompt", "")
            if not prompt:
                continue

            # Include workflow context if it was used
            context = ""
            if meta.get("had_workflow_context") or meta.get("has_workflow_context"):
                for wf_file in STRUCTURED_DIR.glob("workflow_*.json"):
                    wf = json.loads(wf_file.read_text(encoding="utf-8"))
                    if wf.get("category") in prompt.lower():
                        context = _format_workflow_brief(wf)
                        break

            instruction = prompt
            if context:
                instruction = f"{prompt}\n\nWorkflow context:\n{context}"

            examples.append({
                "instruction": instruction,
                "input": "",
                "output": content_fragment,
                "playground_id": meta.get("playground_id", ""),
                "model": meta.get("model", ""),
                "style": meta.get("style", "default"),
                "html_size": len(content_fragment),
                "quality_score": _estimate_quality(content_fragment),
            })

        except Exception as e:
            console.print(f"[yellow]Skipping {meta_file.name}: {e}[/yellow]")

    return examples


def _format_workflow_brief(workflow: dict) -> str:
    """Create a brief workflow description for training context."""
    steps = workflow.get("steps", [])
    parts = [
        f"Workflow: {workflow.get('name', '')}",
        f"Category: {workflow.get('category', '')}",
        f"Steps: {len(steps)}",
    ]
    for step in steps[:5]:
        parts.append(f"  {step.get('step_number', '?')}. {step.get('title', '')} — {step.get('user_action', '')}")
    return "\n".join(parts)


def _estimate_quality(content: str) -> int:
    """
    Estimate content fragment quality on a 1-5 scale.
    Checks for proper use of template CSS classes and structure.
    """
    score = 1

    # Has expected TD playground CSS classes
    td_classes = ["td-nav", "td-hero", "product-card", "td-section", "td-footer",
                  "product-grid", "promo-card", "cta-strip", "hero-content"]
    class_hits = sum(1 for cls in td_classes if cls in content)
    if class_hits >= 3:
        score += 1
    if class_hits >= 5:
        score += 1

    # Has multiple semantic sections (not just a flat dump)
    section_tags = len(re.findall(r'<(?:nav|section|header|footer|div\s+class)', content))
    if section_tags >= 3:
        score += 1

    # Reasonable size for a content fragment (not too short, not bloated)
    if 1000 < len(content) < 40000:
        score += 1

    # Penalty: contains things that shouldn't be in a content fragment
    if "<!DOCTYPE" in content or "<style>" in content or "<script>" in content:
        score = max(1, score - 1)

    return min(score, 5)


def create_training_dataset(examples: list[dict], min_quality: int = 3) -> list[dict]:
    """
    Convert examples to the training format expected by LLaMA-Factory.
    Format: Alpaca-style with system/instruction/input/output.
    """
    dataset = []
    for ex in examples:
        if ex["quality_score"] < min_quality:
            continue

        entry = {
            "system": GENERATOR_SYSTEM,
            "instruction": ex["instruction"],
            "input": ex["input"],
            "output": ex["output"],
            "quality": ex["quality_score"],
        }
        dataset.append(entry)

    return dataset


def create_sharegpt_dataset(examples: list[dict], min_quality: int = 3) -> list[dict]:
    """
    Alternative format: ShareGPT (used by many fine-tuning frameworks).
    """
    dataset = []
    for ex in examples:
        if ex["quality_score"] < min_quality:
            continue

        entry = {
            "conversations": [
                {"from": "system", "value": GENERATOR_SYSTEM},
                {"from": "human", "value": ex["instruction"]},
                {"from": "gpt", "value": ex["output"]},
            ]
        }
        dataset.append(entry)

    return dataset


def augment_prompts(examples: list[dict], augment_ratio: float = 0.3) -> list[dict]:
    """
    Data augmentation by rephrasing prompts. Creates additional training
    examples with varied instruction wording but the same output.
    """
    verb_swaps = [
        ("Create", "Build"), ("Create", "Design"), ("Create", "Generate"),
        ("Build", "Create"), ("Design", "Build"), ("Generate", "Create"),
    ]
    noun_swaps = [
        ("page", "interface"), ("page", "view"), ("page", "screen"),
        ("landing page", "overview page"), ("dashboard", "control panel"),
        ("calculator", "computation tool"),
    ]

    augmented = []
    candidates = [ex for ex in examples if ex["quality_score"] >= 3]
    sample_size = int(len(candidates) * augment_ratio)

    for ex in random.sample(candidates, min(sample_size, len(candidates))):
        new_instruction = ex["instruction"]
        # Apply a random swap
        swaps = verb_swaps + noun_swaps
        old, new = random.choice(swaps)
        if old.lower() in new_instruction.lower():
            new_instruction = re.sub(re.escape(old), new, new_instruction, count=1, flags=re.IGNORECASE)
        else:
            # Prepend a verb if no swap matched
            new_instruction = f"{random.choice(['Create', 'Build', 'Design'])} a {new_instruction}"

        if new_instruction != ex["instruction"]:
            aug = ex.copy()
            aug["instruction"] = new_instruction
            aug["augmented"] = True
            augmented.append(aug)

    return augmented


@click.command()
@click.option("--min-quality", default=3, help="Minimum quality score (1-5)")
@click.option("--format", "fmt", default="alpaca", type=click.Choice(["alpaca", "sharegpt"]))
@click.option("--split-ratio", default=0.9, help="Train/val split ratio")
@click.option("--augment", is_flag=True, help="Enable prompt augmentation for more training data")
def main(min_quality: int, fmt: str, split_ratio: float, augment: bool):
    """Prepare fine-tuning dataset from generated playgrounds."""
    console.print("[bold]Collecting training examples...[/bold]")
    examples = collect_examples()

    if not examples:
        console.print("[red]No examples found. Generate some playgrounds first.[/red]")
        console.print("  Run: python -m webapp.app")
        console.print("  Then generate playgrounds via the web UI")
        return

    console.print(f"  Found {len(examples)} total examples")
    console.print(f"  Quality distribution: {_quality_distribution(examples)}")

    # Create dataset
    if fmt == "alpaca":
        dataset = create_training_dataset(examples, min_quality)
    else:
        dataset = create_sharegpt_dataset(examples, min_quality)

    if not dataset:
        console.print(f"[red]No examples passed quality filter (min={min_quality})[/red]")
        return

    console.print(f"  After quality filter: {len(dataset)} examples")

    # Augment if requested
    if augment:
        aug_examples = augment_prompts(examples)
        console.print(f"  Augmented examples: {len(aug_examples)}")
        if fmt == "alpaca":
            aug_dataset = create_training_dataset(aug_examples, min_quality)
        else:
            aug_dataset = create_sharegpt_dataset(aug_examples, min_quality)
        dataset.extend(aug_dataset)
        random.shuffle(dataset)
        console.print(f"  Total after augmentation: {len(dataset)} examples")

    # Split train/val
    split_idx = int(len(dataset) * split_ratio)
    train_data = dataset[:split_idx]
    val_data = dataset[split_idx:]

    # Save
    train_path = DATA_DIR / "train.jsonl"
    val_path = DATA_DIR / "val.jsonl"

    _save_jsonl(train_data, train_path)
    _save_jsonl(val_data, val_path)

    # Save dataset info
    info = {
        "total_examples": len(examples),
        "filtered_examples": len(dataset),
        "train_size": len(train_data),
        "val_size": len(val_data),
        "min_quality": min_quality,
        "format": fmt,
        "avg_output_tokens": sum(len(ex.get("output", "")) for ex in dataset) // max(len(dataset), 1) // 4,
        "created_at": datetime.now().isoformat(),
    }
    info_path = DATA_DIR / "dataset_info.json"
    info_path.write_text(json.dumps(info, indent=2), encoding="utf-8")

    console.print(f"\n[bold green]Dataset prepared![/bold green]")
    console.print(f"  Train: {train_path} ({len(train_data)} examples)")
    console.print(f"  Val: {val_path} ({len(val_data)} examples)")
    console.print(f"  Info: {info_path}")
    console.print(f"  Est. tokens per example: ~{info['avg_output_tokens']}")


def _save_jsonl(data: list[dict], path: Path):
    """Save data as JSONL."""
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def _quality_distribution(examples: list[dict]) -> str:
    """Show quality score distribution."""
    dist = {}
    for ex in examples:
        s = ex.get("quality_score", 0)
        dist[s] = dist.get(s, 0) + 1
    return " | ".join(f"Q{k}: {v}" for k, v in sorted(dist.items()))


if __name__ == "__main__":
    main()
