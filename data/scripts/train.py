
import os
import sys
import argparse
import logging
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer

# Disable parallelism for tokenizers to avoid deadlocks
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def format_instruction(sample):
    """
    Format the sample into the prompt structure.
    """
    return f"""### Instruction:
{sample['question']}

### Response:
{sample['query']}
"""

def main():
    parser = argparse.ArgumentParser(description="Fine-tune Mistral on Indic-Spider")
    parser.add_argument("--base_model", type=str, default="mistralai/Mistral-7B-v0.1", help="Base model ID")
    parser.add_argument("--data_path", type=str, default="data/processed/indic_spider_train.jsonl", help="Path to JSONL dataset")
    parser.add_argument("--output_dir", type=str, default="models/mistral-indic-spider-lora", help="Output directory")
    parser.add_argument("--steps", type=int, default=1000, help="Number of training steps")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size per device")
    args = parser.parse_args()

    logger.info("="*50)
    logger.info(f"Starting Fine-Tuning Script")
    logger.info(f"Base Model: {args.base_model}")
    logger.info(f"Dataset: {args.data_path}")
    logger.info(f"Output Dir: {args.output_dir}")
    logger.info(f"Target Steps: {args.steps}")
    logger.info("="*50)

    # Check GPU
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        logger.info(f"GPU Detected: {gpu_name}")
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        logger.info(f"Total VRAM: {vram_gb:.2f} GB")
    else:
        logger.warning("No GPU detected! Training will be extremely slow or fail.")

    # 1. Quantization Config
    logger.info("Configuring 4-bit quantization (BitsAndBytes)...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16
    )

    # 2. Load Model
    logger.info(f"Loading base model model weights from {args.base_model}...")
    try:
        model = AutoModelForCausalLM.from_pretrained(
            args.base_model,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )
        logger.info("Base model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return

    # Enable gradient checkpointing
    logger.info("Enabling gradient checkpointing and preparing model for k-bit training...")
    model.gradient_checkpointing_enable()
    model = prepare_model_for_kbit_training(model)

    # 3. LoRA Config
    logger.info("Setting up LoRA (Low-Rank Adaptation) configuration...")
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    model = get_peft_model(model, peft_config)
    
    logger.info("LoRA Model Architecture:")
    model.print_trainable_parameters()

    # 4. Load Dataset
    logger.info(f"Loading dataset from {args.data_path}...")
    if not os.path.exists(args.data_path):
        logger.error(f"Dataset file not found: {args.data_path}")
        logger.info("Tip: Run 'python data/scripts/translate_data.py' to generate it.")
        return

    try:
        dataset = load_dataset("json", data_files=args.data_path, split="train")
        logger.info(f"Dataset loaded. Total samples: {len(dataset)}")
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        return

    # 5. Tokenizer
    logger.info("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right" 

    # 6. Training Arguments
    logger.info("Configuring training arguments...")
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=4,
        max_steps=args.steps,
        learning_rate=2e-4,
        fp16=True, 
        logging_steps=10,
        optim="paged_adamw_8bit",
        save_strategy="steps",
        save_steps=100,
        warmup_steps=50,
        report_to="none"  # Disable wandb/mlflow for now
    )

    # 7. Trainer
    logger.info("Initializing SFTTrainer...")
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        peft_config=peft_config,
        max_seq_length=512,
        tokenizer=tokenizer,
        args=training_args,
        formatting_func=format_instruction,
    )

    logger.info("="*50)
    logger.info("STARTING TRAINING LOOP")
    logger.info(f"Logs will be printed every 10 steps.")
    logger.info("="*50)
    
    try:
        trainer.train()
        logger.info("Training completed successfully!")
    except Exception as e:
        logger.error(f"Training failed: {e}")
        return

    logger.info(f"Saving fine-tuned adapter to {args.output_dir}...")
    trainer.model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    logger.info("Save complete.")

if __name__ == "__main__":
    main()
