# Fine-Tuning Deep Dive

A comprehensive guide to every step of the Enterprise Playground QLoRA fine-tuning pipeline — from raw scraped data to a deployable LoRA adapter that generates TD Banking UI playgrounds.

---

## Table of Contents

1. [Why Fine-Tune?](#1-why-fine-tune)
2. [Data Pipeline](#2-data-pipeline)
3. [Dataset Format (Alpaca)](#3-dataset-format-alpaca)
4. [Base Model Selection](#4-base-model-selection)
5. [Quantization (4-bit NF4)](#5-quantization-4-bit-nf4)
6. [LoRA Adapters](#6-lora-adapters)
7. [Training Configuration](#7-training-configuration)
8. [The Training Loop](#8-the-training-loop)
9. [Training Results & Metrics](#9-training-results--metrics)
10. [Output Artifacts](#10-output-artifacts)
11. [RAG & Vector Embeddings](#11-rag--vector-embeddings)
12. [How It All Generates Elements](#12-how-it-all-generates-elements)
13. [Deployment Path](#13-deployment-path)
14. [Resources](#14-resources)

---

## 1. Why Fine-Tune?

The base `qwen2.5-coder:14b` model generates decent HTML/CSS/JS, but it has no knowledge of TD Banking's specific design system, workflow patterns, form structures, or product pages. Fine-tuning teaches the model:

- TD's green/white color palette and typography
- Banking-specific UI patterns (rate tables, product comparison cards, application forms)
- Navigation structures (breadcrumbs, mega-menus, segment pages)
- Realistic placeholder data (account types, interest rates, product names)
- Correct component hierarchies (hero → features → CTA → footer)

**Without fine-tuning**: Generic HTML that looks like a template.
**With fine-tuning**: HTML that looks like it came from td.com.

### Further Reading
- [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685) — Original LoRA paper (Microsoft, 2021)
- [QLoRA: Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314) — QLoRA paper (Dettmers et al., 2023)

---

## 2. Data Pipeline

### Step 2.1: Web Scraping

**Tool**: Playwright headless browser (`scraper/td_scraper.py`)

The scraper visits 40+ TD Banking URLs across 8 categories and extracts:
- Page structure (headings, paragraphs, sections)
- Forms (field labels, types, validation rules)
- CTAs (button text, links, positioning)
- Navigation patterns (menus, breadcrumbs, tabs)
- Screenshots (1920x1080 viewport captures)

```
Config: config.py → WORKFLOW_CATEGORIES
Output: workflows/raw/*.json
```

**Categories scraped:**
| Category | Pages | Examples |
|----------|-------|---------|
| Accounts | 5 | Chequing, Savings, US Dollar, Browse All |
| Credit Cards | 8 | Cash Back, Travel, Aeroplan, Low Rate, Student |
| Mortgages | 6 | Rates, Calculator, First-Time Buyer, FlexLine |
| Loans | 5 | Personal, Lines of Credit, Student LOC |
| Investing | 6 | TFSA, RRSP, FHSA, GIC, Mutual Funds |
| Insurance | 4 | Travel, Mortgage Protection, Loan Protection |
| Tools | 4 | Mortgage Calculator, Loan Calculator, TFSA Calculator |
| Segments | 3 | New to Canada, Students, Youth |

### Step 2.2: Workflow Mapping

**Tool**: `scraper/workflow_mapper.py` with Pydantic models (`workflows/schema.py`)

Raw JSON is mapped into structured workflow definitions:

```python
class WorkflowStep(BaseModel):
    step_number: int
    page_title: str
    url: str
    action: str           # What the user does
    outcome: str          # What happens next
    sections: list[Section]
    forms: list[FormField]

class Workflow(BaseModel):
    workflow_id: str
    name: str
    category: str
    description: str
    steps: list[WorkflowStep]
    prerequisites: list[str]
    tags: list[str]
```

```
Input:  workflows/raw/*.json
Output: workflows/structured/workflow_*.json
Count:  63 structured workflows
```

### Step 2.3: Dataset Preparation

**Tool**: `fine_tuning/prepare_dataset.py`

Converts structured workflows into training examples:

1. **Template expansion** — Each workflow generates multiple instruction/output pairs:
   - "Create a landing page for [product]"
   - "Build a comparison table for [category]"
   - "Generate an application form for [product]"

2. **Quality scoring** (1-5) — Based on:
   - Output HTML completeness
   - Form field coverage
   - Responsive design patterns
   - Realistic data usage

3. **Train/validation split** — 90/10 stratified by category

```
Input:  workflows/structured/workflow_*.json
Output: fine_tuning/data/train.jsonl (194 examples)
        fine_tuning/data/val.jsonl (22 examples)
```

---

## 3. Dataset Format (Alpaca)

Each training example follows the Alpaca instruction-tuning format:

```json
{
  "system": "You are a TD Banking UI specialist. Generate production-quality HTML/CSS/JS...",
  "instruction": "Create a mortgage rates comparison page with current fixed and variable rates",
  "input": "Category: mortgages, Products: 1-year fixed, 3-year fixed, 5-year fixed, variable",
  "output": "<!DOCTYPE html>\n<html lang=\"en\">\n<head>...</head>\n<body>...<table class=\"rate-table\">...</table>...</body>\n</html>"
}
```

**Field purposes:**
| Field | Purpose | Avg Length |
|-------|---------|------------|
| `system` | Persona + constraints for the model | ~200 chars |
| `instruction` | What to generate (user's request) | ~150 chars |
| `input` | Additional context (optional) | ~100 chars |
| `output` | Complete HTML/CSS/JS playground | ~5000 chars |

### ChatML Conversion

During training, each example is converted to Qwen's ChatML format:

```
<|im_start|>system
You are a TD Banking UI specialist...<|im_end|>
<|im_start|>user
Create a mortgage rates comparison page with current fixed and variable rates

Category: mortgages, Products: 1-year fixed, 3-year fixed, 5-year fixed, variable<|im_end|>
<|im_start|>assistant
<!DOCTYPE html>
<html lang="en">
...<|im_end|>
```

This is handled by the `format_example()` function in `train_lora.py:103-118`.

### Further Reading
- [Stanford Alpaca](https://github.com/tatsu-lab/stanford_alpaca) — Original Alpaca instruction-tuning format
- [HuggingFace SFT Trainer Docs](https://huggingface.co/docs/trl/en/sft_trainer) — How TRL handles dataset formatting

---

## 4. Base Model Selection

### Qwen2.5-Coder-7B-Instruct

We use Qwen's 7B coding-specialized model for local training on RTX 4090:

| Property | Value |
|----------|-------|
| **Model** | `Qwen/Qwen2.5-Coder-7B-Instruct` |
| **Parameters** | 7.6 billion |
| **Architecture** | Transformer decoder-only |
| **Context window** | 32,768 tokens (we use 2048 for training) |
| **Vocabulary** | 152,064 tokens |
| **Chat format** | ChatML (`<\|im_start\|>` / `<\|im_end\|>`) |
| **Specialization** | Code generation (92 programming languages) |
| **Full precision size** | ~15 GB (fp16) |
| **4-bit quantized size** | ~4.5 GB |

### Why Qwen2.5-Coder?

1. **Code-specialized** — Pre-trained on code corpora, understands HTML/CSS/JS natively
2. **Instruction-tuned** — Already follows instructions well (Instruct variant)
3. **Fits on 4090** — 7B at 4-bit = ~4.5GB VRAM, leaves room for training overhead
4. **ChatML format** — Clean template system for system/user/assistant roles
5. **Open weights** — Apache 2.0 license, no restrictions on fine-tuning

### Model Hierarchy

```
Training (local):  Qwen2.5-Coder-7B-Instruct  (4-bit, ~4.5GB)
Inference (local): qwen2.5-coder:14b           (Q4_K_M, ~8.5GB via Ollama)
Router (local):    qwen2.5:3b                  (Q4, ~2GB via Ollama)
```

### Further Reading
- [Qwen2.5-Coder: Powerful, Diverse, Practical](https://www.alibabacloud.com/blog/qwen2-5-coder-series-powerful-diverse-practical_601765) — Official blog post
- [Qwen2.5-Coder on HuggingFace](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct) — Model card with benchmarks
- [QwenLM GitHub](https://github.com/QwenLM) — Official repository

---

## 5. Quantization (4-bit NF4)

### What Is Quantization?

Quantization reduces the precision of model weights from 16-bit floats (2 bytes per weight) to 4-bit integers (0.5 bytes per weight), achieving a ~4x memory reduction.

```
7B params × 2 bytes (fp16)  = ~14 GB  ← Doesn't fit training on 16GB
7B params × 0.5 bytes (4-bit) = ~3.5 GB  ← Fits with room for gradients
```

### NF4 (Normal Float 4-bit)

NF4 is a quantization type introduced by the QLoRA paper. Unlike uniform 4-bit quantization, NF4 uses a non-uniform distribution that matches the typical bell-curve distribution of neural network weights:

```python
BitsAndBytesConfig(
    load_in_4bit=True,              # Enable 4-bit loading
    bnb_4bit_quant_type="nf4",      # Normal Float 4 (non-uniform)
    bnb_4bit_compute_dtype=torch.bfloat16,  # Compute in bf16 for accuracy
    bnb_4bit_use_double_quant=True, # Quantize the quantization constants too
)
```

### Double Quantization

`bnb_4bit_use_double_quant=True` applies a second round of quantization to the quantization constants themselves, saving an additional ~0.4 GB on a 7B model.

### Compute Dtype

While weights are stored in 4-bit, actual computation happens in bfloat16 for numerical stability. The weights are dequantized on-the-fly during forward/backward passes.

### VRAM Breakdown After Quantization

| Component | Size |
|-----------|------|
| Quantized model weights | ~4.5 GB |
| Quantization constants | ~0.3 GB |
| **Total model footprint** | **~4.8 GB** |

### Further Reading
- [Making LLMs even more accessible with bitsandbytes, 4-bit quantization and QLoRA](https://huggingface.co/blog/4bit-transformers-bitsandbytes) — HuggingFace blog
- [BitsAndBytes Quantization Guide](https://huggingface.co/docs/transformers/en/quantization/bitsandbytes) — Official documentation
- [bitsandbytes-foundation/bitsandbytes](https://github.com/bitsandbytes-foundation/bitsandbytes) — GitHub repository

---

## 6. LoRA Adapters

### What Is LoRA?

LoRA (Low-Rank Adaptation) freezes all original model weights and injects small trainable matrices into specific layers. Instead of updating the full weight matrix W (dimensions d×d), LoRA decomposes the update into two small matrices:

```
W_new = W_frozen + (A × B)

Where:
  W_frozen: Original weights (frozen, 4-bit)
  A: d × r matrix (trainable, r << d)
  B: r × d matrix (trainable, r << d)
  r: Rank (we use r=16)
```

For a layer with 4096×4096 weights:
- Full fine-tuning: 16,777,216 parameters
- LoRA (r=16): 4096×16 + 16×4096 = 131,072 parameters (0.78% of full)

### Our LoRA Configuration

```python
LoraConfig(
    r=16,                    # Rank — controls adapter capacity
    lora_alpha=32,           # Scaling factor (alpha/rank = 2x)
    target_modules=[         # Which layers get adapters
        "q_proj",            # Query projection (attention)
        "k_proj",            # Key projection (attention)
        "v_proj",            # Value projection (attention)
        "o_proj",            # Output projection (attention)
        "gate_proj",         # Gate projection (MLP)
        "up_proj",           # Up projection (MLP)
        "down_proj",         # Down projection (MLP)
    ],
    lora_dropout=0.05,       # Regularization
    bias="none",             # Don't train bias terms
    task_type="CAUSAL_LM",   # Causal language modeling
)
```

### Parameter Counts

| Component | Parameters | Trainable? |
|-----------|-----------|------------|
| Base model (frozen) | ~7.6 billion | No |
| LoRA adapters | ~40 million | Yes |
| **Trainable %** | **~0.5%** | |

### Why These 7 Target Modules?

- **Attention layers** (q/k/v/o_proj): Control how the model attends to input context. Training these teaches the model to focus on TD-specific patterns.
- **MLP layers** (gate/up/down_proj): Control the model's learned representations. Training these teaches domain-specific feature transformations.

This "all linear layers" approach covers the full transformer block, giving the adapter maximum expressiveness for the rank budget.

### Scaling Factor

`lora_alpha=32` with `r=16` gives a scaling factor of 2x. The effective weight update is:

```
ΔW = (alpha / r) × A × B = 2 × A × B
```

Higher scaling = larger updates per step. 2x is a moderate setting that balances learning speed with stability.

### Further Reading
- [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685) — Original paper
- [PEFT: Parameter-Efficient Fine-Tuning](https://huggingface.co/docs/peft/en/index) — HuggingFace PEFT docs
- [PEFT Blog Post](https://huggingface.co/blog/peft) — Practical guide to PEFT methods

---

## 7. Training Configuration

### SFTConfig (Supervised Fine-Tuning)

```python
SFTConfig(
    output_dir="fine_tuning/adapters/td-playground-lora",
    num_train_epochs=3,
    per_device_train_batch_size=1,        # 1 sample per step (VRAM limited)
    per_device_eval_batch_size=1,
    gradient_accumulation_steps=4,         # Effective batch = 1 × 4 = 4
    learning_rate=2e-4,                    # Aggressive for LoRA
    weight_decay=0.01,                     # L2 regularization
    warmup_ratio=0.03,                     # 3% of steps for LR warmup
    lr_scheduler_type="cosine",            # Cosine decay to near-zero
    logging_steps=10,                      # Log every 10 steps
    eval_strategy="steps",
    eval_steps=50,                         # Evaluate every 50 steps
    save_strategy="steps",
    save_steps=100,                        # Checkpoint every 100 steps
    save_total_limit=3,                    # Keep last 3 checkpoints
    bf16=True,                             # bfloat16 mixed precision
    gradient_checkpointing=True,           # Trade compute for VRAM
    max_grad_norm=0.3,                     # Gradient clipping
    report_to="none",                      # No W&B / MLflow
    optim="paged_adamw_32bit",             # Paged optimizer for VRAM savings
    packing=False,                         # No sequence packing
    max_length=2048,                       # Max token sequence length
)
```

### Key Decisions Explained

**`per_device_train_batch_size=1` + `gradient_accumulation_steps=4`**

With 16GB VRAM, we can only fit 1 sample at a time. Gradient accumulation simulates a batch size of 4 by accumulating gradients over 4 forward passes before updating weights.

**`learning_rate=2e-4`**

Aggressive for full fine-tuning, but appropriate for LoRA since we're only updating ~0.5% of parameters. The small adapter capacity means we need stronger gradient signals.

**`lr_scheduler_type="cosine"`**

Learning rate follows a cosine curve: starts at 2e-4, warms up over 3% of steps, then smoothly decays to near-zero. Prevents oscillation in later training.

```
LR: 0 → 2e-4 (warmup) → 2e-4 (peak) ↘ ~0 (cosine decay)
```

**`gradient_checkpointing=True`**

Instead of storing all intermediate activations in VRAM (needed for backward pass), recompute them on-the-fly. Saves ~40% VRAM at the cost of ~20% slower training.

**`optim="paged_adamw_32bit"`**

Paged AdamW stores optimizer states in CPU RAM when VRAM runs out, automatically paging them back in when needed. Critical for fitting 7B training on 16GB.

**`max_length=2048`**

Truncates sequences to 2048 tokens. Our HTML outputs average ~1500 tokens, so this captures most examples with some headroom. Longer sequences = more VRAM.

**`packing=False`**

Packing concatenates multiple short sequences into one long sequence for efficiency. Disabled because: (1) our sequences are already fairly long, (2) no flash attention available on Windows/CUDA combo, (3) packing without flash attention causes VRAM spikes.

### Further Reading
- [TRL SFTTrainer Documentation](https://huggingface.co/docs/trl/en/sft_trainer) — Official TRL docs
- [Distributed SFT with TRL](https://huggingface.co/blog/jlzhou/distributed-sft-with-trl-and-deepspeed-part2) — Advanced TRL usage

---

## 8. The Training Loop

### What Happens Each Step

```
Step 1: Load batch (1 example)
    ↓
Step 2: Tokenize with ChatML format
    ↓
Step 3: Forward pass through quantized model
    - 4-bit weights dequantized to bf16 on-the-fly
    - LoRA adapters add their contribution: output = base(x) + LoRA(x)
    - Cross-entropy loss computed against target tokens
    ↓
Step 4: Backward pass
    - Gradients computed only for LoRA parameters (~40M params)
    - Base model weights stay frozen (no gradients)
    - Gradient checkpointing: recompute activations as needed
    ↓
Step 5: Gradient accumulation
    - If step % 4 != 0: accumulate gradients, go to step 1
    - If step % 4 == 0: proceed to step 6
    ↓
Step 6: Optimizer step
    - Paged AdamW updates LoRA weights
    - Gradient clipping at max_norm=0.3
    - Learning rate adjusted by cosine scheduler
    ↓
Step 7: Logging (every 10 steps)
    - Training loss, learning rate, token accuracy
    ↓
Step 8: Evaluation (every 50 steps)
    - Run validation set (22 examples) through model
    - Compute eval loss and eval accuracy
    ↓
Step 9: Checkpoint (every 100 steps)
    - Save adapter weights + optimizer state
    - Keep only last 3 checkpoints
```

### Timeline of Our Training Run

```
Step  0:  Training starts
Step  1:  Loss = 0.891, Token Acc = 79.1%
          ↓ Learning HTML structure patterns
Step 10:  Loss = 0.650
          ↓ Learning TD-specific styling
Step 20:  Loss = 0.420
          ↓ Learning form patterns
Step 25:  Epoch 1 complete. Loss = 0.298
          ↓ Solid TD Banking understanding
Step 30:  Loss = 0.250
Step 40:  Loss = 0.210
Step 50:  Eval: loss = 0.280, acc = 91.2%
          ↓ Not overfitting — eval tracks train
Step 50:  Epoch 2 complete. Loss = 0.194
Step 60:  Loss = 0.178
Step 70:  Loss = 0.168
Step 75:  Epoch 3 complete. Final loss = 0.164
          ↓ Training complete!
          Final eval: loss = 0.223, acc = 93.7%
```

### VRAM Usage During Training

| Phase | VRAM Usage |
|-------|-----------|
| Model loading (4-bit) | ~4.8 GB |
| + LoRA adapters | ~5.0 GB |
| + Optimizer states (paged) | ~6.5 GB |
| + Forward pass activations | ~10 GB |
| + Backward pass (checkpointed) | ~14.5 GB |
| **Peak** | **~14.5 / 16 GB** |

---

## 9. Training Results & Metrics

### Loss Curve

```
Loss
1.0 ┤ ●
    │  ╲
0.8 ┤   ╲
    │    ╲
0.6 ┤     ╲
    │      ╲
0.4 ┤       ╲____
    │             ╲___
0.2 ┤                  ╲___●── Eval Loss (0.223)
    │                      ●── Train Loss (0.164)
0.0 ┤
    └─────────────────────────
    0    25    50    75  Steps
```

### Final Metrics

| Metric | Start | End | Change |
|--------|-------|-----|--------|
| Train Loss | 0.891 | 0.164 | -81.6% |
| Token Accuracy | 79.1% | 95.8% | +16.7pp |
| Eval Loss | — | 0.223 | — |
| Eval Accuracy | — | 93.7% | — |

### Interpretation

- **Loss 0.164**: The model predicts the next token correctly with high confidence on training data.
- **Eval loss 0.223**: Slightly higher than train loss — healthy gap indicates no severe overfitting.
- **Token accuracy 95.8%**: For each position in the output, the model picks the right token ~96% of the time.
- **3 epochs**: Enough to learn TD patterns without memorizing exact outputs.

### Training Run Stats

| Stat | Value |
|------|-------|
| Total steps | 75 |
| Epochs | 3 |
| Training examples | 194 |
| Validation examples | 22 |
| Training duration | ~37 minutes |
| GPU | NVIDIA RTX 4090 16GB |
| Peak VRAM | ~14.5 GB |

---

## 10. Output Artifacts

### Directory Structure

```
fine_tuning/adapters/td-playground-lora/
├── checkpoint-*/                    # Periodic saves
│   ├── adapter_model.safetensors    # LoRA weights at that step
│   ├── optimizer.pt                 # Optimizer states
│   ├── scheduler.pt                 # LR scheduler state
│   └── trainer_state.json           # Full training history
├── final_adapter/                   # Final trained adapter
│   ├── adapter_model.safetensors    # LoRA weights (~50MB)
│   ├── adapter_config.json          # LoRA configuration
│   ├── tokenizer.json               # Tokenizer data
│   ├── tokenizer_config.json        # Tokenizer settings
│   ├── special_tokens_map.json      # Special token mappings
│   └── vocab.json                   # Vocabulary
└── trainer_state.json               # Training log history
```

### Key Files

**`adapter_model.safetensors` (~50MB)**
The trained LoRA weight matrices (A and B for each target module). This is what gets merged into the base model or loaded at inference time.

**`adapter_config.json`**
```json
{
  "base_model_name_or_path": "Qwen/Qwen2.5-Coder-7B-Instruct",
  "r": 16,
  "lora_alpha": 32,
  "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
  "lora_dropout": 0.05,
  "bias": "none",
  "task_type": "CAUSAL_LM"
}
```

**`trainer_state.json`**
Contains the full loss history (every 10 steps), eval results (every 50 steps), learning rate schedule, and best checkpoint info. The ML Observatory reads this file to render loss curves.

---

## 11. RAG & Vector Embeddings

### What Is RAG?

RAG (Retrieval-Augmented Generation) supplements the LLM's knowledge by retrieving relevant documents from a vector database at query time. Instead of relying solely on what the model memorized during training, RAG provides fresh context.

```
Without RAG:  User prompt → LLM → Generic output
With RAG:     User prompt → Search vector DB → Inject context → LLM → Informed output
```

### How Vector Embeddings Work

An embedding model converts text into a dense vector (list of numbers) that captures semantic meaning. Similar texts produce similar vectors.

```
"TD chequing account"     → [0.23, -0.45, 0.87, 0.12, ...]  (768 dimensions)
"TD savings account"      → [0.21, -0.42, 0.85, 0.14, ...]  (very similar!)
"mortgage payment calc"   → [0.56, 0.13, -0.22, 0.78, ...]  (different topic)
```

**Cosine similarity** measures how close two vectors are:
- 1.0 = identical meaning
- 0.0 = unrelated
- -1.0 = opposite meaning

### Our Embedding Model: nomic-embed-text

| Property | Value |
|----------|-------|
| Model | `nomic-embed-text` via Ollama |
| Parameters | 137 million |
| Dimensions | 768 |
| Max tokens | 8192 |
| Runs on | CPU only (zero VRAM impact) |
| Disk size | ~270 MB |

### Our Vector Store: ChromaDB

| Property | Value |
|----------|-------|
| Database | ChromaDB (embedded, persistent) |
| Storage | `.chroma/chroma.sqlite3` (~4 MB) |
| Index type | HNSW (Hierarchical Navigable Small Worlds) |
| Distance metric | Cosine |
| Total chunks | 303 |
| Collection name | `td_workflows` |

### How RAG Is Used in Generation

```python
# playground/generator.py (simplified)
class PlaygroundGenerator:
    def generate(self, prompt, style):
        # 1. Query RAG for relevant TD Banking context
        rag_chunks = self.rag.query(prompt)  # Top-3 similar chunks

        # 2. Build enriched prompt
        rag_context = ""
        for chunk in rag_chunks:
            rag_context += f"---\n{chunk['content']}\n"

        # 3. Send to 14B generator with RAG context
        full_prompt = f"{prompt}\n\nRelevant TD Banking context:\n{rag_context}"
        response = ollama.generate(model="qwen2.5-coder:14b", prompt=full_prompt)
```

### Chunk Types in the Vector Store

| Type | Count | Source | Content |
|------|-------|--------|---------|
| `overview` | ~63 | Workflow JSONs | Workflow name, category, description, tags |
| `step` | ~120 | Workflow JSONs | Step actions, form fields, sections, URLs |
| `scraped_page` | ~120 | Raw HTML | Full page content from td.com |

### RAG + Fine-Tuning: Complementary Approaches

| Aspect | Fine-Tuning | RAG |
|--------|------------|-----|
| **What it does** | Teaches patterns and style | Provides specific content |
| **When applied** | Training time (one-time) | Inference time (every query) |
| **Updates** | Requires retraining | Just re-ingest new data |
| **Strengths** | Style, structure, patterns | Facts, details, specifics |
| **Example** | "Generate HTML with TD's green palette" | "TD Aeroplan Visa earns 1.5 pts/dollar" |

Together, fine-tuning gives the model TD's "design language" while RAG injects accurate product details at generation time.

### Further Reading
- [ChromaDB Official Site](https://www.trychroma.com/) — Getting started guide
- [Introducing Nomic Embed](https://www.nomic.ai/blog/posts/nomic-embed-text-v1) — nomic-embed-text announcement
- [nomic-embed-text on Ollama](https://ollama.com/library/nomic-embed-text) — Ollama model page
- [Vector Embeddings Explained](https://weaviate.io/blog/vector-embeddings-explained) — Visual guide by Weaviate
- [What Are Vector Embeddings?](https://www.datacamp.com/blog/vector-embedding) — DataCamp intuitive explanation
- [How to Build a RAG-Powered Chat App with ChromaDB](https://thenewstack.io/how-to-build-a-rag-powered-llm-chat-app-with-chromadb-and-python/) — The New Stack tutorial
- [Build a RAG Solution with ChromaDB and Ollama](https://dev.to/sophyia/how-to-build-a-rag-solution-with-llama-index-chromadb-and-ollama-20lb) — DEV Community tutorial

---

## 12. How It All Generates Elements

### The Full Request Flow

```
User types: "Create a credit card comparison page"
                    ↓
    ┌───────────────────────────────────┐
    │  1. ROUTER (qwen2.5:3b, ~2GB)    │
    │  Classifies: "generation" task    │
    │  Detects: category=credit_cards   │
    └───────────────┬───────────────────┘
                    ↓
    ┌───────────────────────────────────┐
    │  2. CACHE CHECK                   │
    │  Semantic similarity search       │
    │  against previous generations     │
    │  Threshold: 0.85 cosine sim       │
    │  → Miss (no similar prior gen)    │
    └───────────────┬───────────────────┘
                    ↓
    ┌───────────────────────────────────┐
    │  3. RAG RETRIEVAL                 │
    │  nomic-embed-text embeds query    │
    │  ChromaDB returns top-3 chunks:   │
    │  - Credit card comparison overview│
    │  - Cash-back card form fields     │
    │  - Travel rewards rate table      │
    └───────────────┬───────────────────┘
                    ↓
    ┌───────────────────────────────────┐
    │  4. PROMPT ASSEMBLY               │
    │  System prompt (TD specialist)    │
    │  + User instruction               │
    │  + RAG context (3 chunks)         │
    │  + Style directive (banking)      │
    └───────────────┬───────────────────┘
                    ↓
    ┌───────────────────────────────────┐
    │  5. GENERATOR (14B, ~8.5GB)       │
    │  qwen2.5-coder:14b generates      │
    │  complete HTML/CSS/JS             │
    │  Streams tokens to browser        │
    │  (with fine-tuned LoRA adapter    │
    │   merged, knows TD patterns)      │
    └───────────────┬───────────────────┘
                    ↓
    ┌───────────────────────────────────┐
    │  6. POST-PROCESSING               │
    │  Save to playground/generated/    │
    │  Record metrics (latency, size)   │
    │  Cache the response               │
    │  Return playground URL            │
    └───────────────────────────────────┘
                    ↓
    User sees: Interactive HTML playground
    with TD-styled credit card comparison
    table, real product names, green/white
    palette, responsive layout
```

### What Fine-Tuning Adds

Without fine-tuning, the 14B model generates generic HTML. With the LoRA adapter merged:

| Element | Without Fine-Tuning | With Fine-Tuning |
|---------|-------------------|-----------------|
| Colors | Random or blue | TD Green (#1a5336), white, grey |
| Typography | System fonts | TD-style font stack |
| Layout | Basic flexbox | Hero → features → CTA → footer |
| Forms | Generic inputs | TD-style form groups with validation |
| Data | "Lorem ipsum" | "TD All-Inclusive Banking Plan, $16.95/mo" |
| Components | Generic cards | Rate comparison tables, product cards |
| Navigation | Simple nav bar | Breadcrumbs + mega-menu pattern |

### What RAG Adds

RAG provides real-time factual context that the fine-tuned model uses to fill in specifics:

| Without RAG | With RAG |
|-------------|----------|
| "Credit Card A, Credit Card B" | "TD Cash Back Visa, TD Aeroplan Visa Infinite" |
| "X% annual fee" | "$0 annual fee, earn 1% unlimited cash back" |
| Generic feature list | Actual TD card features from scraped data |

---

## 13. Deployment Path

### Option A: Merge and Deploy to Ollama

```bash
# 1. Merge LoRA adapter into base model
python -m fine_tuning.merge_adapter \
  --adapter fine_tuning/adapters/td-playground-lora/final_adapter \
  --create-ollama

# 2. Creates a Modelfile + merged weights
# 3. Registers with Ollama as td-playground model
ollama create td-playground -f Modelfile

# 4. Update config to use fine-tuned model
# Set GENERATOR_MODEL=td-playground in .env
```

### Option B: Direct LoRA Inference (PEFT)

Load the adapter at runtime without merging:

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM

base = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-Coder-7B-Instruct", ...)
model = PeftModel.from_pretrained(base, "fine_tuning/adapters/td-playground-lora/final_adapter")
```

### Option C: Cloud Training → Local Deployment

For the 14B model (too large for local training):

```bash
# 1. Upload dataset to RunPod GPU instance
# 2. Train with cloud_14b profile (A100 80GB)
python -m fine_tuning.train_lora --base-model Qwen/Qwen2.5-Coder-14B-Instruct --epochs 5

# 3. Download adapter (~100MB)
# 4. Merge and deploy locally via Ollama
```

---

## 14. Resources

### Papers
- [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685) — Edward J. Hu et al. (Microsoft, 2021)
- [QLoRA: Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314) — Tim Dettmers et al. (2023)

### Official Documentation
- [HuggingFace PEFT](https://huggingface.co/docs/peft/en/index) — Parameter-Efficient Fine-Tuning library
- [HuggingFace TRL](https://huggingface.co/docs/trl/en/index) — Transformer Reinforcement Learning (SFTTrainer)
- [BitsAndBytes Quantization](https://huggingface.co/docs/transformers/en/quantization/bitsandbytes) — 4-bit/8-bit quantization
- [ChromaDB](https://www.trychroma.com/) — Embedding database
- [Ollama nomic-embed-text](https://ollama.com/library/nomic-embed-text) — Embedding model

### Blog Posts & Tutorials
- [Making LLMs accessible with bitsandbytes and QLoRA](https://huggingface.co/blog/4bit-transformers-bitsandbytes) — HuggingFace
- [Parameter-Efficient Fine-Tuning using PEFT](https://huggingface.co/blog/peft) — HuggingFace
- [Qwen2.5-Coder Series: Powerful, Diverse, Practical](https://www.alibabacloud.com/blog/qwen2-5-coder-series-powerful-diverse-practical_601765) — Alibaba
- [Introducing Nomic Embed](https://www.nomic.ai/blog/posts/nomic-embed-text-v1) — Nomic AI
- [QLoRA: Fine-Tune LLMs on Your GPU](https://kaitchup.substack.com/p/qlora-fine-tune-a-large-language-model-on-your-gpu-27bed5a03e2b) — KaitchUp (RTX 4090 focused)
- [How to Fine-Tune LLMs on a Budget](https://www.runpod.io/articles/guides/how-to-fine-tune-large-language-models-on-a-budget) — RunPod
- [Fine-Tune Gemma using QLoRA](https://ai.google.dev/gemma/docs/core/huggingface_text_finetune_qlora) — Google AI (TRL example)

### Vector Embeddings & RAG
- [Vector Embeddings Explained](https://weaviate.io/blog/vector-embeddings-explained) — Weaviate (visual guide)
- [What Are Vector Embeddings?](https://www.datacamp.com/blog/vector-embedding) — DataCamp
- [Vector Embeddings Explained](https://opencv.org/blog/vector-embeddings/) — OpenCV
- [Build a RAG Chat App with ChromaDB](https://thenewstack.io/how-to-build-a-rag-powered-llm-chat-app-with-chromadb-and-python/) — The New Stack
- [RAG with ChromaDB and Ollama](https://dev.to/sophyia/how-to-build-a-rag-solution-with-llama-index-chromadb-and-ollama-20lb) — DEV Community
- [RAG Made Simple with ChromaDB](https://promptlyai.in/rag-made-simple/) — PromptlyAI

### GitHub Repositories
- [microsoft/LoRA](https://github.com/microsoft/LoRA) — Original LoRA implementation
- [artidoro/qlora](https://github.com/artidoro/qlora) — QLoRA reference implementation
- [huggingface/peft](https://github.com/huggingface/peft) — PEFT library
- [huggingface/trl](https://github.com/huggingface/trl) — TRL library
- [bitsandbytes-foundation/bitsandbytes](https://github.com/bitsandbytes-foundation/bitsandbytes) — Quantization library
- [chroma-core/chroma](https://github.com/chroma-core/chroma) — ChromaDB
- [QwenLM](https://github.com/QwenLM) — Qwen model family
