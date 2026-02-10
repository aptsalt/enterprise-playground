"""
LoRA Fine-Tuning Script
========================
Fine-tunes a base model (Qwen2.5-Coder) with QLoRA on the prepared
playground dataset. Designed to run on a cloud GPU (RunPod, vast.ai).

Requirements (install on GPU machine):
    pip install torch transformers peft datasets bitsandbytes trl accelerate

Usage:
    python -m fine_tuning.train_lora
    python -m fine_tuning.train_lora --base-model Qwen/Qwen2.5-Coder-7B-Instruct --epochs 5
    python -m fine_tuning.train_lora --use-llamafactory  # Use LLaMA-Factory instead
"""

import json
import sys
from pathlib import Path

import click
from rich.console import Console

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import BASE_MODEL, LORA_RANK, LORA_ALPHA, LEARNING_RATE, NUM_EPOCHS, BATCH_SIZE, GRADIENT_ACCUMULATION, DATA_DIR, ADAPTERS_DIR

console = Console()


def train_with_trl(
    base_model: str,
    train_file: Path,
    val_file: Path,
    output_dir: Path,
    lora_rank: int,
    lora_alpha: int,
    lr: float,
    epochs: int,
    batch_size: int,
):
    """Fine-tune using HuggingFace TRL + PEFT (QLoRA)."""
    console.print("[bold cyan]Starting QLoRA fine-tuning with TRL...[/bold cyan]")
    console.print(f"  Base model: {base_model}")
    console.print(f"  LoRA rank: {lora_rank}, alpha: {lora_alpha}")
    console.print(f"  Learning rate: {lr}")
    console.print(f"  Epochs: {epochs}, Batch size: {batch_size}")

    import torch
    from datasets import load_dataset
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer, SFTConfig

    # === Load tokenizer ===
    console.print("\n[cyan]Loading tokenizer...[/cyan]")
    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # === Quantization config (4-bit QLoRA) ===
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # === Load base model ===
    console.print("[cyan]Loading base model (4-bit quantized)...[/cyan]")
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )
    model = prepare_model_for_kbit_training(model)

    # === LoRA config ===
    lora_config = LoraConfig(
        r=lora_rank,
        lora_alpha=lora_alpha,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = get_peft_model(model, lora_config)
    trainable_params, total_params = model.get_nb_trainable_parameters()
    console.print(f"  Trainable: {trainable_params:,} / {total_params:,} ({100 * trainable_params / total_params:.2f}%)")

    # === Load dataset ===
    console.print("[cyan]Loading dataset...[/cyan]")
    dataset = load_dataset("json", data_files={
        "train": str(train_file),
        "validation": str(val_file),
    })

    def format_example(example):
        """Format Alpaca-style example into a single text string."""
        system = example.get("system", "")
        instruction = example.get("instruction", "")
        inp = example.get("input", "")
        output = example.get("output", "")

        parts = []
        if system:
            parts.append(f"<|im_start|>system\n{system}<|im_end|>")
        user_msg = instruction
        if inp:
            user_msg += f"\n\n{inp}"
        parts.append(f"<|im_start|>user\n{user_msg}<|im_end|>")
        parts.append(f"<|im_start|>assistant\n{output}<|im_end|>")
        return {"text": "\n".join(parts)}

    dataset = dataset.map(format_example)
    console.print(f"  Train: {len(dataset['train'])} examples")
    console.print(f"  Val: {len(dataset['validation'])} examples")

    # === Training arguments (SFTConfig absorbs packing + max_seq_length) ===
    training_args = SFTConfig(
        output_dir=str(output_dir),
        num_train_epochs=epochs,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        learning_rate=lr,
        weight_decay=0.01,
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=50,
        save_strategy="steps",
        save_steps=100,
        save_total_limit=3,
        bf16=True,
        gradient_checkpointing=True,
        max_grad_norm=0.3,
        report_to="none",
        optim="paged_adamw_32bit",
        packing=False,
        max_length=2048,
    )

    # === Train ===
    console.print("\n[bold green]Starting training...[/bold green]")
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        processing_class=tokenizer,
    )

    trainer.train()

    # Save adapter
    adapter_path = output_dir / "final_adapter"
    model.save_pretrained(str(adapter_path))
    tokenizer.save_pretrained(str(adapter_path))

    console.print(f"\n[bold green]Training complete![/bold green]")
    console.print(f"  Adapter saved to: {adapter_path}")
    console.print(f"  To merge: python -m fine_tuning.merge_adapter --adapter {adapter_path}")

    return str(adapter_path)


def generate_llamafactory_config(
    base_model: str,
    train_file: Path,
    val_file: Path,
    output_dir: Path,
    lora_rank: int,
    lora_alpha: int,
    lr: float,
    epochs: int,
    batch_size: int,
) -> Path:
    """
    Generate a LLaMA-Factory YAML config for fine-tuning.
    LLaMA-Factory provides a web UI and more polished training pipeline.
    """
    config = {
        "model_name_or_path": base_model,
        "stage": "sft",
        "do_train": True,
        "finetuning_type": "lora",
        "lora_rank": lora_rank,
        "lora_alpha": lora_alpha,
        "lora_target": "all",
        "lora_dropout": 0.05,
        "dataset_dir": str(DATA_DIR),
        "dataset": "train",
        "template": "qwen",
        "cutoff_len": 4096,
        "max_samples": 1000,
        "overwrite_cache": True,
        "preprocessing_num_workers": 4,
        "output_dir": str(output_dir),
        "logging_steps": 10,
        "save_steps": 100,
        "eval_steps": 50,
        "plot_loss": True,
        "overwrite_output_dir": True,
        "per_device_train_batch_size": batch_size,
        "gradient_accumulation_steps": 4,
        "learning_rate": lr,
        "num_train_epochs": epochs,
        "lr_scheduler_type": "cosine",
        "warmup_ratio": 0.03,
        "bf16": True,
        "quantization_bit": 4,
        "quantization_method": "bitsandbytes",
        "val_size": 0.1,
    }

    config_path = DATA_DIR / "llamafactory_config.yaml"
    import yaml
    config_path.write_text(yaml.dump(config, default_flow_style=False), encoding="utf-8")

    # Also create the dataset_info.json that LLaMA-Factory expects
    dataset_info = {
        "train": {
            "file_name": str(train_file),
            "formatting": "alpaca",
            "columns": {
                "system": "system",
                "prompt": "instruction",
                "query": "input",
                "response": "output",
            }
        }
    }
    di_path = DATA_DIR / "dataset_info.json"
    di_path.write_text(json.dumps(dataset_info, indent=2), encoding="utf-8")

    console.print(f"[green]LLaMA-Factory config saved: {config_path}[/green]")
    console.print(f"  Run: llamafactory-cli train {config_path}")
    console.print(f"  Or:  llamafactory-cli webui  (for the web interface)")

    return config_path


@click.command()
@click.option("--base-model", default=None, help="Base model to fine-tune")
@click.option("--epochs", default=None, type=int, help="Number of training epochs")
@click.option("--batch-size", default=None, type=int, help="Batch size")
@click.option("--lr", default=None, type=float, help="Learning rate")
@click.option("--lora-rank", default=None, type=int, help="LoRA rank")
@click.option("--local", is_flag=True, help="Use local 7B profile optimized for RTX 4090 16GB")
@click.option("--use-llamafactory", is_flag=True, help="Generate LLaMA-Factory config instead")
def main(base_model, epochs, batch_size, lr, lora_rank, local, use_llamafactory):
    """Run LoRA fine-tuning on the prepared dataset."""
    from config import TRAINING_PROFILES

    # Apply profile defaults, then CLI overrides
    if local:
        profile = TRAINING_PROFILES["local_7b"]
        console.print("[bold cyan]Using local_7b profile (RTX 4090 optimized)[/bold cyan]")
    else:
        profile = TRAINING_PROFILES.get("cloud_14b", {})

    model = base_model or profile.get("base_model", BASE_MODEL)
    ep = epochs or NUM_EPOCHS
    bs = batch_size or profile.get("batch_size", BATCH_SIZE)
    learning_rate = lr or profile.get("learning_rate", LEARNING_RATE)
    rank = lora_rank or profile.get("lora_rank", LORA_RANK)
    alpha = profile.get("lora_alpha", LORA_ALPHA)

    train_file = DATA_DIR / "train.jsonl"
    val_file = DATA_DIR / "val.jsonl"

    if not train_file.exists():
        console.print("[red]Training data not found. Run prepare_dataset first.[/red]")
        console.print("  python -m fine_tuning.prepare_dataset")
        return

    output_dir = ADAPTERS_DIR / "td-playground-lora"
    output_dir.mkdir(parents=True, exist_ok=True)

    if use_llamafactory:
        generate_llamafactory_config(model, train_file, val_file, output_dir, rank, alpha, learning_rate, ep, bs)
    else:
        train_with_trl(model, train_file, val_file, output_dir, rank, alpha, learning_rate, ep, bs)


if __name__ == "__main__":
    main()
