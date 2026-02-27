# ---------------------------------------------------------
# OVERNIGHT FINE-TUNING SCRIPT — COLAB / KAGGLE
# ---------------------------------------------------------
# HOW TO USE:
# 1. Go to https://colab.research.google.com or https://kaggle.com
# 2. Select GPU runtime (T4 on Colab, P100 on Kaggle)
# 3. Upload "spider_train_full.jsonl" from training/ folder
# 4. Paste this entire file into a single cell and run it
# 5. Leave it running overnight (~3-4 hours for 7000 examples)
# 6. The GGUF file will be auto-saved to Google Drive!
# ---------------------------------------------------------

# ==========================================
# STEP 0: Mount Google Drive (auto-save backup)
# ==========================================
try:
    from google.colab import drive
    drive.mount('/content/drive')
    DRIVE_DIR = '/content/drive/MyDrive/nl2sql_model'
    import os
    os.makedirs(DRIVE_DIR, exist_ok=True)
    print(f"✅ Google Drive mounted. Model will be saved to: {DRIVE_DIR}")
except Exception:
    DRIVE_DIR = None
    print("⚠️ Google Drive not available (Kaggle?). Will save locally only.")

# ==========================================
# STEP 1: Install Dependencies (~2 min)
# ==========================================
import subprocess, sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "unsloth", "-q"])
subprocess.check_call([sys.executable, "-m", "pip", "install", "--force-reinstall",
    "--no-cache-dir", "--no-deps", "xformers", "trl", "peft",
    "accelerate", "bitsandbytes", "-q"])

# ==========================================
# STEP 2: Load Model (Qwen2.5-Coder-7B, 4-bit)
# ==========================================
from unsloth import FastLanguageModel
import torch

max_seq_length = 2048
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit",
    max_seq_length=max_seq_length,
    dtype=None,
    load_in_4bit=True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                     "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=3407,
)
print("✅ Model loaded with LoRA adapters.")

# ==========================================
# STEP 3: Load & Format the Spider Dataset
# ==========================================
from datasets import load_dataset

prompt_template = """You are an expert SQL generator. Convert the question into a SINGLE SELECT query.
STRICT RULES:
1. Output ONLY raw SQL. No explanations, no markdown.
2. Use ONLY the EXACT table and column names from the schema.
3. If the answer can come from a single table, do NOT use JOIN.
4. For counting, use COUNT(*).

Schema:
{schema}

Question:
{question}

SQL:
{sql}"""

EOS_TOKEN = tokenizer.eos_token

def formatting_func(examples):
    texts = []
    for schema, question, sql in zip(
        examples["schema"], examples["question"], examples["sql"]
    ):
        text = prompt_template.format(
            schema=schema, question=question, sql=sql
        ) + EOS_TOKEN
        texts.append(text)
    return {"text": texts}

# Load the full Spider training data
dataset = load_dataset("json", data_files="spider_train_full.jsonl", split="train")
dataset = dataset.map(formatting_func, batched=True)
print(f"✅ Dataset loaded: {len(dataset)} examples")
print(f"   Sample prompt:\n{dataset[0]['text'][:300]}...")

# ==========================================
# STEP 4: Train (~3-4 hours on T4)
# ==========================================
from trl import SFTTrainer
from transformers import TrainingArguments

# For overnight: num_train_epochs=3 gives solid results
# With 7000 examples, batch_size=2, grad_accum=4 → ~2625 steps/epoch
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    dataset_num_proc=2,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        num_train_epochs=3,         # 3 full passes over the data
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=50,           # Print loss every 50 steps
        save_steps=500,             # Checkpoint every 500 steps
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        seed=3407,
        output_dir="outputs",
    ),
)

print("🚀 Starting training... (this will take 3-4 hours on a T4 GPU)")
trainer_stats = trainer.train()
print(f"✅ Training complete! Final loss: {trainer_stats.training_loss:.4f}")

# ==========================================
# STEP 5: Export to GGUF for Ollama
# ==========================================
print("📦 Exporting to GGUF format (for Ollama on your Mac)...")
model.save_pretrained_gguf(
    "nl2sql_finetuned",
    tokenizer,
    quantization_method="q4_k_m"
)

# Copy GGUF to Google Drive so it survives disconnection
import glob, shutil
gguf_files = glob.glob("nl2sql_finetuned*/**/*.gguf", recursive=True)
if not gguf_files:
    gguf_files = glob.glob("nl2sql_finetuned*/*.gguf")

gguf_path = gguf_files[0] if gguf_files else "NOT_FOUND"
print(f"GGUF file location: {gguf_path}")

if DRIVE_DIR and os.path.exists(gguf_path):
    dest = os.path.join(DRIVE_DIR, os.path.basename(gguf_path))
    shutil.copy2(gguf_path, dest)
    print(f"✅ GGUF copied to Google Drive: {dest}")
    # Also copy the Modelfile
    modelfile_path = os.path.join(os.path.dirname(gguf_path), "Modelfile")
    if os.path.exists(modelfile_path):
        shutil.copy2(modelfile_path, os.path.join(DRIVE_DIR, "Modelfile"))

print(f"""
============================================
✅ DONE! NEXT STEPS:
============================================
1. GGUF file is at: {gguf_path}
   (Also saved to Google Drive if mounted)
2. Download the .gguf file to your Mac
3. On your Mac, create a Modelfile:
   echo 'FROM ./{os.path.basename(gguf_path)}' > Modelfile
4. Import into Ollama:
   ollama create nl2sql-finetuned -f Modelfile
5. Update your .env:
   OLLAMA_MODEL=nl2sql-finetuned
6. Re-run the benchmark:
   python scripts/benchmark_spider.py --limit 50
============================================
""")
