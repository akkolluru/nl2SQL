# ---------------------------------------------------------
# FINE-TUNING SCRIPT FOR GOOGLE COLAB / KAGGLE (GPU REQUIRED)
# ---------------------------------------------------------
# INSTRUCTIONS:
# 1. Open Google Colab (Free or Pro) or Kaggle.
# 2. Select a GPU runtime (T4, P100, A100, etc.).
# 3. Create a single Notebook and paste the cells below in order.
# 4. Upload your 'sample_dataset.jsonl' to the Colab files area.
# ---------------------------------------------------------

# ==========================================
# CELL 1: Install Dependencies
# ==========================================
# Run this cell to install the highly optimized Unsloth library
# !pip install unsloth
# !pip install --force-reinstall --no-cache-dir --no-deps xformers trl peft accelerate bitsandbytes

# ==========================================
# CELL 2: Load Model and Tokenizer
# ==========================================
from unsloth import FastLanguageModel
import torch

max_seq_length = 2048 # Good default for Text-to-SQL
dtype = None # Auto detection
load_in_4bit = True # 4-bit quantization reduces memory by 75%

# We load Qwen2.5-Coder-7B because it is SOTA for coding/SQL right out of the box.
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit",
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
)

# Apply LoRA Adapters (This makes the model trainable on small GPUs)
model = FastLanguageModel.get_peft_model(
    model,
    r = 16, # Rank of the adapter (16 is a solid default)
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj",],
    lora_alpha = 16,
    lora_dropout = 0,
    bias = "none",
    use_gradient_checkpointing = "unsloth",
    random_state = 3407,
)
print("Model loaded with LoRA Adapters successfully.")

# ==========================================
# CELL 3: Prepare the Multilingual Dataset
# ==========================================
from datasets import load_dataset

# We format the prompt exactly how it will look in your FastApi app
prompt_template = """You are a MySQL expert. Convert the English/Hindi/Telugu question into a valid SQL query based on the schema.
Schema:
{schema}

Question:
{question}

SQL:
{sql}"""

EOS_TOKEN = tokenizer.eos_token
def formatting_prompts_func(examples):
    schemas = examples["schema"]
    questions = examples["question"]
    sqls = examples["sql"]
    texts = []
    for schema, question, sql in zip(schemas, questions, sqls):
        # We MUST append the EOS_TOKEN so the model learns when to stop typing!
        text = prompt_template.format(schema=schema, question=question, sql=sql) + EOS_TOKEN
        texts.append(text)
    return { "text" : texts, }

# Load the dataset you uploaded (e.g., sample_dataset.jsonl)
dataset = load_dataset("json", data_files="sample_dataset.jsonl", split="train")
dataset = dataset.map(formatting_prompts_func, batched = True,)
print(f"Dataset formatted! Example prompt:\n{dataset[0]['text']}")

# ==========================================
# CELL 4: Train the Model
# ==========================================
from trl import SFTTrainer
from transformers import TrainingArguments

trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    dataset_num_proc = 2,
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        max_steps = 60, # Change to ~300-500 for your actual presentation!
        learning_rate = 2e-4,
        fp16 = not torch.cuda.is_bf16_supported(),
        bf16 = torch.cuda.is_bf16_supported(),
        logging_steps = 1, # Gives you graphs of the loss going down
        optim = "adamw_8bit",
        weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 3407,
        output_dir = "outputs",
    ),
)

print("Starting training...")
trainer_stats = trainer.train()

# ==========================================
# CELL 5: Export to GGUF (For your Mac)
# ==========================================
# This converts your fine-tuned model into a GGUF file so you can download it
# and run it natively on your Mac using Ollama!

print("Exporting model to GGUF format for Mac/Ollama...")
model.save_pretrained_gguf("finetuned_qwen_sql", tokenizer, quantization_method = "q4_k_m")

print("Done! You can now download the finetuned_qwen_sql.gguf file from Colab.")
