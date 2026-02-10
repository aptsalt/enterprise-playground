"""
Merge LoRA Adapter & Create Ollama Model
==========================================
Merges a LoRA adapter with the base model, then creates an Ollama
model file so you can run the fine-tuned model locally.

Usage:
    python -m fine_tuning.merge_adapter --adapter fine_tuning/adapters/td-playground-lora/final_adapter
    python -m fine_tuning.merge_adapter --adapter fine_tuning/adapters/td-playground-lora/final_adapter --create-ollama
"""

import json
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import BASE_MODEL, ADAPTERS_DIR
from playground.router import GENERATOR_SYSTEM

console = Console()


def merge_adapter(adapter_path: str, base_model: str = None, output_path: str = None) -> str:
    """Merge LoRA adapter weights into the base model."""
    console.print("[bold cyan]Merging LoRA adapter with base model...[/bold cyan]")

    adapter_dir = Path(adapter_path)
    if not adapter_dir.exists():
        console.print(f"[red]Adapter not found: {adapter_dir}[/red]")
        return None

    # Detect base model from adapter config
    if base_model is None:
        config_path = adapter_dir / "adapter_config.json"
        if config_path.exists():
            config = json.loads(config_path.read_text())
            base_model = config.get("base_model_name_or_path", "")
        if not base_model:
            base_model = BASE_MODEL
            console.print(f"  Using default base model: {base_model}")

    if output_path is None:
        output_path = str(ADAPTERS_DIR / "td-playground-merged")

    console.print(f"  Base model: {base_model}")
    console.print(f"  Adapter: {adapter_path}")
    console.print(f"  Output: {output_path}")

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    console.print("\n  Loading base model...")
    base = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)

    console.print("  Loading LoRA adapter...")
    model = PeftModel.from_pretrained(base, adapter_path)

    console.print("  Merging weights...")
    merged = model.merge_and_unload()

    console.print(f"  Saving merged model to {output_path}...")
    merged.save_pretrained(output_path)
    tokenizer.save_pretrained(output_path)

    total_size = sum(
        f.stat().st_size for f in Path(output_path).rglob("*") if f.is_file()
    ) / 1e9
    console.print(f"\n[bold green]Merged model saved: {output_path} ({total_size:.1f}GB)[/bold green]")
    return output_path


def create_ollama_model(merged_path: str, model_name: str = "td-playground") -> bool:
    """
    Create an Ollama model from the merged weights.
    This creates a Modelfile and registers it with Ollama.
    """
    console.print(f"\n[bold cyan]Creating Ollama model: {model_name}[/bold cyan]")

    merged_dir = Path(merged_path)
    if not merged_dir.exists():
        console.print(f"[red]Merged model not found: {merged_dir}[/red]")
        return False

    # Create Modelfile with the same system prompt used during training
    # Escape triple quotes for the Modelfile format
    system_prompt = GENERATOR_SYSTEM.replace('"', '\\"')
    modelfile_content = f'''FROM {merged_path}

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_predict 6144
PARAMETER stop "<|im_end|>"

SYSTEM """{system_prompt}"""
'''

    modelfile_path = merged_dir / "Modelfile"
    modelfile_path.write_text(modelfile_content, encoding="utf-8")
    console.print(f"  Modelfile saved: {modelfile_path}")

    # Register with Ollama
    try:
        result = subprocess.run(
            ["ollama", "create", model_name, "-f", str(modelfile_path)],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode == 0:
            console.print(f"[bold green]Ollama model created: {model_name}[/bold green]")
            console.print(f"  Run: ollama run {model_name}")
            return True
        else:
            console.print(f"[red]Ollama create failed: {result.stderr}[/red]")
            return False
    except FileNotFoundError:
        console.print("[yellow]Ollama CLI not found. Install Ollama first: https://ollama.com[/yellow]")
        console.print(f"  Modelfile saved at: {modelfile_path}")
        console.print(f"  After installing Ollama, run: ollama create {model_name} -f {modelfile_path}")
        return False
    except subprocess.TimeoutExpired:
        console.print("[yellow]Ollama create timed out (model may still be importing)[/yellow]")
        return False


def create_gguf_quantized(merged_path: str, quant_type: str = "q4_k_m") -> str:
    """
    Convert merged model to GGUF format for efficient Ollama serving.
    Requires llama.cpp's convert tool.
    """
    console.print(f"\n[bold cyan]Converting to GGUF ({quant_type})...[/bold cyan]")

    output_path = str(Path(merged_path).parent / f"td-playground-{quant_type}.gguf")

    # Try llama.cpp convert script (must be cloned separately)
    convert_script = Path("/opt/llama.cpp/convert_hf_to_gguf.py")
    quantize_bin = Path("/opt/llama.cpp/build/bin/llama-quantize")

    if not convert_script.exists():
        # Check common alternative locations
        for alt in [Path.home() / "llama.cpp/convert_hf_to_gguf.py", Path("llama.cpp/convert_hf_to_gguf.py")]:
            if alt.exists():
                convert_script = alt
                quantize_bin = alt.parent / "build/bin/llama-quantize"
                break

    if not convert_script.exists():
        console.print("[yellow]llama.cpp not found. To convert to GGUF:[/yellow]")
        console.print("  git clone https://github.com/ggerganov/llama.cpp /opt/llama.cpp")
        console.print("  cd /opt/llama.cpp && make -j")
        console.print(f"  python convert_hf_to_gguf.py {merged_path} --outfile {output_path}")
        if quant_type != "f16":
            console.print(f"  ./build/bin/llama-quantize {output_path} {output_path}.{quant_type} {quant_type}")
        return None

    try:
        # Step 1: Convert HF to GGUF (f16)
        f16_path = output_path.replace(quant_type, "f16") if quant_type != "f16" else output_path
        result = subprocess.run(
            ["python", str(convert_script), merged_path, "--outfile", f16_path],
            capture_output=True, text=True, timeout=1800,
        )
        if result.returncode != 0:
            console.print(f"[red]GGUF conversion failed: {result.stderr[:500]}[/red]")
            return None

        # Step 2: Quantize if not f16
        if quant_type != "f16" and quantize_bin.exists():
            result = subprocess.run(
                [str(quantize_bin), f16_path, output_path, quant_type],
                capture_output=True, text=True, timeout=1800,
            )
            if result.returncode != 0:
                console.print(f"[red]Quantization failed: {result.stderr[:500]}[/red]")
                return f16_path  # Return f16 as fallback
            # Clean up f16 intermediate
            if f16_path != output_path:
                Path(f16_path).unlink(missing_ok=True)
        else:
            output_path = f16_path

        size = Path(output_path).stat().st_size / 1e9
        console.print(f"[bold green]GGUF created: {output_path} ({size:.1f}GB)[/bold green]")
        return output_path
    except subprocess.TimeoutExpired:
        console.print("[yellow]GGUF conversion timed out (large model)[/yellow]")
        return None
    except Exception as e:
        console.print(f"[red]GGUF conversion error: {e}[/red]")
        return None


@click.command()
@click.option("--adapter", required=True, help="Path to LoRA adapter directory")
@click.option("--base-model", default=None, help="Base model (auto-detected from adapter)")
@click.option("--output", default=None, help="Output path for merged model")
@click.option("--create-ollama", is_flag=True, help="Create Ollama model after merging")
@click.option("--ollama-name", default="td-playground", help="Ollama model name")
@click.option("--quantize", default=None, help="GGUF quantization type (e.g., q4_k_m)")
def main(adapter, base_model, output, create_ollama, ollama_name, quantize):
    """Merge LoRA adapter and optionally create Ollama model."""
    merged_path = merge_adapter(adapter, base_model, output)
    if not merged_path:
        return

    if quantize:
        gguf_path = create_gguf_quantized(merged_path, quantize)
        if gguf_path and create_ollama:
            # Use GGUF for Ollama instead of raw weights
            create_ollama_model_from_gguf(gguf_path, ollama_name)
    elif create_ollama:
        create_ollama_model(merged_path, ollama_name)


def create_ollama_model_from_gguf(gguf_path: str, model_name: str = "td-playground"):
    """Create Ollama model from a GGUF file."""
    system_prompt = GENERATOR_SYSTEM.replace('"', '\\"')
    modelfile = f'''FROM {gguf_path}

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_predict 6144

SYSTEM """{system_prompt}"""
'''
    modelfile_path = Path(gguf_path).parent / "Modelfile"
    modelfile_path.write_text(modelfile, encoding="utf-8")

    try:
        subprocess.run(
            ["ollama", "create", model_name, "-f", str(modelfile_path)],
            check=True,
            timeout=600,
        )
        console.print(f"[bold green]Ollama model created from GGUF: {model_name}[/bold green]")
    except Exception as e:
        console.print(f"[yellow]Could not create Ollama model: {e}[/yellow]")


if __name__ == "__main__":
    main()
