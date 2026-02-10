#!/bin/bash
# =============================================================================
# RunPod / Vast.ai GPU Setup Script
# =============================================================================
# Sets up the fine-tuning environment on a cloud GPU instance.
#
# Recommended GPU: NVIDIA A100 80GB or H100
# Minimum GPU: RTX 4090 24GB (use local_7b profile) or A10G
# Recommended image: RunPod PyTorch 2.x template
#
# Usage:
#   bash deployment/runpod_setup.sh
#
# After setup, upload your project and training data, then run:
#   python -m fine_tuning.train_lora
# =============================================================================

set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/workspace/enterprise-playground}"

echo "========================================="
echo "Enterprise Playground - GPU Setup"
echo "========================================="
echo ""

# === System packages ===
echo "[1/7] Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq git curl wget unzip rsync > /dev/null

# === Python packages ===
echo "[2/7] Installing Python packages..."
pip install -q --upgrade pip

if [ -f "$PROJECT_DIR/requirements-gpu.txt" ]; then
    echo "  Found requirements-gpu.txt, installing..."
    pip install -q -r "$PROJECT_DIR/requirements-gpu.txt"
else
    echo "  Installing GPU deps directly..."
    pip install -q \
        torch \
        "transformers>=4.47.0" \
        "peft>=0.14.0" \
        "datasets>=3.2.0" \
        "bitsandbytes>=0.45.0" \
        "trl>=0.13.0" \
        "accelerate>=1.2.0" \
        pyyaml \
        rich \
        click
fi

# === Optional: LLaMA-Factory (web UI for fine-tuning) ===
echo "[3/7] Installing LLaMA-Factory..."
pip install -q llamafactory 2>/dev/null || {
    echo "  LLaMA-Factory pip install failed, trying git..."
    git clone --depth 1 https://github.com/hiyouga/LLaMA-Factory.git /opt/LLaMA-Factory 2>/dev/null || true
    if [ -d "/opt/LLaMA-Factory" ]; then
        cd /opt/LLaMA-Factory && pip install -q -e . && cd -
    fi
}

# === Ollama (for testing the fine-tuned model) ===
echo "[4/7] Installing Ollama..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
fi
# Start Ollama in background if not running
if ! pgrep -x ollama > /dev/null; then
    nohup ollama serve > /tmp/ollama.log 2>&1 &
    sleep 5
fi

# === Project directory ===
echo "[5/7] Setting up project directory..."
mkdir -p "$PROJECT_DIR"
mkdir -p "$PROJECT_DIR/fine_tuning/data"
mkdir -p "$PROJECT_DIR/fine_tuning/adapters"

# === Verify GPU ===
echo "[6/7] Verifying GPU..."
python3 -c "
import torch
if torch.cuda.is_available():
    gpu_name = torch.cuda.get_device_name(0)
    gpu_mem = torch.cuda.get_device_properties(0).total_mem / 1e9
    print(f'  GPU: {gpu_name} ({gpu_mem:.0f}GB)')
    print(f'  CUDA: {torch.version.cuda}')
    print(f'  PyTorch: {torch.__version__}')
    if gpu_mem < 16:
        print(f'  WARNING: {gpu_mem:.0f}GB VRAM detected. Use local_7b profile.')
        print(f'  Run: python -m fine_tuning.train_lora --local')
    elif gpu_mem < 40:
        print(f'  OK for 14B with QLoRA (4-bit quantization)')
    else:
        print(f'  OK for full 14B fine-tuning')
else:
    print('  ERROR: No GPU detected! Fine-tuning requires a GPU.')
    exit(1)
"

# === Validate setup ===
echo "[7/7] Validating Python imports..."
python3 -c "
import transformers, peft, datasets, trl, accelerate, bitsandbytes
print(f'  transformers: {transformers.__version__}')
print(f'  peft: {peft.__version__}')
print(f'  trl: {trl.__version__}')
print(f'  accelerate: {accelerate.__version__}')
print('  All imports OK')
" || {
    echo "  ERROR: Some packages failed to import. Check errors above."
    exit 1
}

echo ""
echo "========================================="
echo "Setup complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo ""
echo "  1. Upload your project:"
echo "     rsync -avz --exclude '.git' --exclude 'playground/generated' \\"
echo "       --exclude 'workflows/raw' --exclude 'workflows/screenshots' \\"
echo "       . runpod:$PROJECT_DIR/"
echo ""
echo "  2. Upload training data (if already prepared locally):"
echo "     scp fine_tuning/data/train.jsonl runpod:$PROJECT_DIR/fine_tuning/data/"
echo "     scp fine_tuning/data/val.jsonl runpod:$PROJECT_DIR/fine_tuning/data/"
echo ""
echo "  3. Or prepare data on the pod:"
echo "     cd $PROJECT_DIR"
echo "     pip install -r requirements.txt  # for playground imports"
echo "     python -m fine_tuning.prepare_dataset"
echo ""
echo "  4. Start fine-tuning:"
echo "     cd $PROJECT_DIR"
echo "     python -m fine_tuning.train_lora              # cloud_14b profile (default)"
echo "     python -m fine_tuning.train_lora --local       # local_7b profile (less VRAM)"
echo "     python -m fine_tuning.train_lora --use-llamafactory  # LLaMA-Factory UI"
echo ""
echo "  5. After training, merge and create Ollama model:"
echo "     python -m fine_tuning.merge_adapter \\"
echo "       --adapter fine_tuning/adapters/td-playground-lora/final_adapter \\"
echo "       --create-ollama"
echo ""
echo "  6. Download the adapter back to local machine:"
echo "     scp -r runpod:$PROJECT_DIR/fine_tuning/adapters/td-playground-lora ./fine_tuning/adapters/"
echo ""
echo "Estimated costs (RunPod):"
echo "  - A100 80GB: ~\$1.50-2.50/hour"
echo "  - Fine-tuning 200 examples, 3 epochs: ~1-3 hours"
echo "  - Total estimate: ~\$3-8"
echo ""
