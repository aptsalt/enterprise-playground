# QLoRA Fine-Tuning Pipeline

End-to-end documentation of the QLoRA fine-tuning pipeline for the Enterprise Playground system.

## Pipeline Overview

```mermaid
flowchart TB
    subgraph DATA["Data Pipeline"]
        scraper["Playwright Scraper<br/>40+ TD Banking URLs"]
        raw_data["Raw JSON Data<br/>workflows/raw/"]
        workflow_mapper["Workflow Mapper<br/>Pydantic Schemas"]
        structured["Structured Workflows<br/>workflows/structured/"]
        prepare_dataset["prepare_dataset.py<br/>Alpaca Format + Quality Scoring"]
        train_jsonl["train.jsonl<br/>194 examples"]
        val_jsonl["val.jsonl<br/>22 examples"]
    end

    subgraph MODEL["Model & LoRA Setup"]
        tokenizer["Qwen2.5 Tokenizer<br/>ChatML Format"]
        bnb_config["BitsAndBytes Config<br/>NF4 4-bit Quantization"]
        base_model["Qwen2.5-Coder-7B-Instruct<br/>4-bit Quantized ~4.5GB"]
        lora_config["LoRA Config<br/>r=16, alpha=32, 7 modules"]
        peft_model["PEFT Model<br/>Trainable: ~0.5%"]
    end

    subgraph TRAIN["Training Loop"]
        chatml_format["ChatML Formatting<br/>max_length=2048"]
        sft_config["SFTConfig<br/>lr=2e-4, cosine, bf16"]
        sft_trainer["SFTTrainer<br/>TRL v0.27"]
        training_loop["Training<br/>75 steps x 3 epochs"]
    end

    subgraph GPU["GPU Resources"]
        gpu_vram["RTX 4090<br/>16GB VRAM"]
        loss_curve["Loss: 0.891 → 0.164<br/>Accuracy: 95.8%"]
    end

    subgraph OUTPUT["Output Artifacts"]
        checkpoints["Checkpoints<br/>every 100 steps"]
        final_adapter["Final LoRA Adapter<br/>~50MB safetensors"]
        merge["merge_adapter.py<br/>Merge into Base"]
        deploy["Ollama Deployment<br/>td-playground model"]
    end

    scraper -->|"extract pages"| raw_data
    raw_data -->|"map to schemas"| workflow_mapper
    workflow_mapper -->|"validate & structure"| structured
    structured -->|"generate examples"| prepare_dataset
    prepare_dataset -->|"90/10 split"| train_jsonl
    prepare_dataset -->|"90/10 split"| val_jsonl

    tokenizer -->|"encode tokens"| chatml_format
    bnb_config -->|"quantize weights"| base_model
    base_model -->|"inject adapters"| peft_model
    lora_config -->|"configure rank"| peft_model

    train_jsonl -->|"feed batches"| chatml_format
    val_jsonl -->|"eval every 50 steps"| sft_trainer
    chatml_format -->|"formatted dataset"| sft_trainer
    peft_model -->|"trainable model"| sft_trainer
    sft_config -->|"hyperparameters"| sft_trainer
    sft_trainer -->|"forward + backward"| training_loop

    gpu_vram -.->|"~14.5GB peak"| training_loop
    training_loop -->|"log metrics"| loss_curve
    training_loop -->|"save periodically"| checkpoints
    training_loop -->|"save final"| final_adapter
    final_adapter -->|"merge weights"| merge
    merge -->|"create GGUF"| deploy
```

## Stage Details

### 1. Data Collection (Scraper)
- **Tool**: Playwright-based headless browser
- **Source**: 40+ TD Banking URLs across 8 categories
- **Output**: Raw JSON files in `workflows/raw/`
- **Categories**: Accounts, Credit Cards, Mortgages, Loans, Investing, Insurance, Tools, Segments

### 2. Workflow Mapping
- **Tool**: `workflow_mapper.py` with Pydantic models
- **Input**: Raw scraped JSON
- **Output**: Structured workflow definitions in `workflows/structured/`
- **Schema**: WorkflowStep, FormField, NavigationFlow, ComponentHierarchy

### 3. Dataset Preparation
- **Tool**: `fine_tuning/prepare_dataset.py`
- **Format**: Alpaca-style (system, instruction, input, output)
- **Split**: 90% train (194 examples), 10% validation (22 examples)
- **Quality**: Scored 1-5 based on output completeness and HTML validity

### 4. Model Setup
| Parameter | Value |
|-----------|-------|
| Base Model | Qwen/Qwen2.5-Coder-7B-Instruct |
| Quantization | 4-bit NF4 (BitsAndBytes) |
| Compute dtype | bfloat16 |
| Double quantization | Enabled |
| VRAM footprint | ~4.5GB |

### 5. LoRA Configuration
| Parameter | Value |
|-----------|-------|
| Rank (r) | 16 |
| Alpha | 32 |
| Scaling factor | 2x (alpha/rank) |
| Target modules | q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj |
| Dropout | 0.05 |
| Trainable params | ~0.5% of total |

### 6. Training Configuration
| Parameter | Value |
|-----------|-------|
| Trainer | TRL SFTTrainer v0.27 |
| Batch size | 1 (per device) |
| Gradient accumulation | 4 (effective batch = 4) |
| Learning rate | 2e-4 |
| LR scheduler | Cosine with 3% warmup |
| Optimizer | paged_adamw_32bit |
| Max length | 2048 tokens |
| Precision | bf16 |
| Gradient checkpointing | Enabled |
| Max grad norm | 0.3 |

### 7. Training Results
| Metric | Start | End |
|--------|-------|-----|
| Train Loss | 0.891 | 0.164 |
| Token Accuracy | 79.1% | 95.8% |
| Eval Loss | — | 0.223 |
| Eval Accuracy | — | 93.7% |
| Total Steps | — | 75 |
| Epochs | — | 3 |

### 8. GPU Usage (RTX 4090 16GB)
| Component | VRAM |
|-----------|------|
| Quantized model | ~4.5GB |
| LoRA adapters | ~200MB |
| Optimizer states | ~1.5GB (paged) |
| Activations + KV cache | ~8GB |
| **Peak total** | **~14.5GB** |

### 9. Output Artifacts
- **Checkpoints**: `adapters/td-playground-lora/checkpoint-*/`
- **Final adapter**: `adapters/td-playground-lora/final_adapter/`
  - `adapter_model.safetensors` (~50MB)
  - `adapter_config.json`
  - Tokenizer files

### 10. Deployment Path
```bash
# Merge adapter into base model
python -m fine_tuning.merge_adapter --adapter adapters/td-playground-lora/final_adapter --create-ollama

# Deploy to Ollama
ollama create td-playground -f Modelfile
```
