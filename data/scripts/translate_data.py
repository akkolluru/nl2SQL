import argparse
import json
import logging
import os
import sys
from typing import List, Dict, Any

import torch
from datasets import load_dataset
from tqdm import tqdm
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from IndicTransToolkit.processor import IndicProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 32
MAX_LENGTH = 128
NUM_BEAMS = 4
MODEL_NAME = "ai4bharat/indictrans2-en-indic-1B"
SRC_LANG = "eng_Latn"
TGT_LANGS = {
    "hindi": "hin_Deva",
    "telugu": "tel_Telugu"
}

def translate_batch(
    input_sentences: List[str],
    src_lang: str,
    tgt_lang: str,
    model: Any,
    tokenizer: Any,
    ip: IndicProcessor,
    device: torch.device
) -> List[str]:
    """
    Translates a batch of sentences from src_lang to tgt_lang.
    """
    try:
        # Preprocess
        batch = ip.preprocess_batch(input_sentences, src_lang=src_lang, tgt_lang=tgt_lang)

        # Tokenize
        inputs = tokenizer(
            batch,
            padding="longest",
            truncation=True,
            max_length=MAX_LENGTH,
            return_tensors="pt"
        ).to(device)

        # Generate
        with torch.no_grad():
            generated_tokens = model.generate(
                **inputs,
                num_beams=NUM_BEAMS,
                max_length=MAX_LENGTH
            )

        # Decode
        decoded_tokens = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)

        # Postprocess
        outputs = ip.postprocess_batch(decoded_tokens, lang=tgt_lang)
        return outputs
    except Exception as e:
        logger.error(f"Error translating batch to {tgt_lang}: {e}")
        # Return empty strings or original on failure to keep alignment?
        # Requirement says "handle exceptions ... skip rather than crashing".
        # But if we skip, we lose alignment with the dataset.
        # Better to return None or empty string and filter later, or just log.
        # I'll return None for failed items so strict type hinting might need Optional.
        # For simplicity in batch processing, if the whole batch fails, we are in trouble.
        # I will return a list of empty strings to maintain length.
        return [""] * len(input_sentences)

def main():
    parser = argparse.ArgumentParser(description="Translate Spider dataset to Hindi and Telugu.")
    parser.add_argument("--split", type=str, default="train", help="Dataset split to process (e.g., train, validation).")
    args = parser.parse_args()

    split_name = args.split
    output_dir = "data/processed"
    output_file = os.path.join(output_dir, f"indic_spider_{split_name}.jsonl")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Loading Spider dataset split: {split_name}...")
    try:
        dataset = load_dataset("spider", split=split_name)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        sys.exit(1)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    logger.info(f"Loading model: {MODEL_NAME}...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
        model = AutoModelForSeq2SeqLM.from_pretrained(
            MODEL_NAME,
            trust_remote_code=True,
            # torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            # Commented out dtype optimization to be safe, but float16 is standard for 1B models on GPU.
        ).to(device)
        ip = IndicProcessor(inference=True)
    except Exception as e:
        logger.error(f"Failed to load model or processor: {e}")
        sys.exit(1)

    logger.info("Starting translation...")

    buffer = []

    # Open file handle
    try:
        with open(output_file, "w", encoding="utf-8") as f_out:
            # Iterate in batches
            # The dataset object is indexable, but for batching it's easier to iterate
            # We can use a custom batcher or just slice.

            total_size = len(dataset)
            for i in tqdm(range(0, total_size, BATCH_SIZE), desc="Translating"):
                batch_indices = range(i, min(i + BATCH_SIZE, total_size))
                batch_items = dataset.select(batch_indices)

                questions = batch_items["question"]

                # Translate to Hindi
                hindi_translations = translate_batch(
                    questions, SRC_LANG, TGT_LANGS["hindi"], model, tokenizer, ip, device
                )

                # Translate to Telugu
                telugu_translations = translate_batch(
                    questions, SRC_LANG, TGT_LANGS["telugu"], model, tokenizer, ip, device
                )

                # Combine and Write
                for idx, item in enumerate(batch_items):
                    # Check if translations failed (empty string)
                    q_hin = hindi_translations[idx]
                    q_tel = telugu_translations[idx]

                    if not q_hin or not q_tel:
                        logger.warning(f"Skipping item {item['db_id']} due to translation failure.")
                        continue

                    output_record = {
                        "db_id": item["db_id"],
                        "query": item["query"],
                        "question": item["question"],
                        "question_hindi": q_hin,
                        "question_telugu": q_tel
                    }

                    f_out.write(json.dumps(output_record, ensure_ascii=False) + "\n")

    except Exception as e:
        logger.error(f"An error occurred during processing: {e}")
        sys.exit(1)

    logger.info(f"Processing complete. Data saved to {output_file}")

if __name__ == "__main__":
    main()
