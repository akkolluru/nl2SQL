
import os
import argparse
import json
import sqlite3
import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel
from tqdm import tqdm

# Disable parallelism
os.environ["TOKENIZERS_PARALLELISM"] = "false"

def load_model(base_model_id, adapter_path=None):
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        base_model_id,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )
    
    if adapter_path:
        print(f"Loading adapter from {adapter_path}")
        model = PeftModel.from_pretrained(model, adapter_path)
        
    tokenizer = AutoTokenizer.from_pretrained(base_model_id, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    
    return model, tokenizer

def generate_sql(model, tokenizer, question, schema):
    prompt = f"### Instruction:\n{question}\n\n### Schema:\n{schema}\n\n### Response:\n"
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs, 
            max_new_tokens=150, 
            do_sample=False, # Greedy decoding for determinism
            pad_token_id=tokenizer.eos_token_id
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract SQL after "### Response:"
    if "### Response:" in response:
        sql = response.split("### Response:")[1].strip()
    else:
        sql = response.strip()
    
    # Basic cleanup
    sql = sql.split(";")[0].strip()
    return sql

def execute_sql(db_path, sql):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        conn.close()
        return result, None
    except Exception as e:
        return None, str(e)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_model", type=str, default="mistralai/Mistral-7B-v0.1")
    parser.add_argument("--adapter_path", type=str, default=None, help="Path to LoRA adapter")
    parser.add_argument("--split", type=str, default="validation")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    # Load Model
    model, tokenizer = load_model(args.base_model, args.adapter_path)
    model.eval()

    # Load Data (Spider validation)
    dataset = load_dataset("spider", split=args.split)
    if args.limit:
        dataset = dataset.select(range(args.limit))

    results = []
    correct_exec = 0
    valid_sql = 0

    print(f"Benchmarking on {len(dataset)} examples...")
    
    # Iterate
    for item in tqdm(dataset):
        db_id = item["db_id"]
        # In a real scenario, we need the schema for this specific DB.
        # Spider dataset has 'db_id'. We assume we can get schema text nicely.
        # For simplicity, we'll placeholder the schema fetching or assume standard Spider paths.
        # Check: /home/arun/Projects/nl2SQL/data/spider/database/{db_id}/{db_id}.sqlite
        # We need to construct schema text from the sqlite file dynamically or from tables.json.
        
        # NOTE: For this MVP benchmark script within the constraints, 
        # let's assume we can query the SQLite DB to get schema.
        
        db_path = f"data/spider/database/{db_id}/{db_id}.sqlite"
        if not os.path.exists(db_path):
            # Try to find where spider data is... 
            # If not found, skip execution test
            schema_text = "Tables: <placeholder>" 
            db_path = None
        else:
            # Quick schema introspection similar to app/schema.py but for sqlite
            try:
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [r[0] for r in cur.fetchall()]
                schema_parts = []
                for t in tables:
                    cur.execute(f"PRAGMA table_info({t})")
                    cols = [r[1] for r in cur.fetchall()]
                    schema_parts.append(f"{t}({', '.join(cols)})")
                schema_text = "Tables: " + "; ".join(schema_parts)
                conn.close()
            except:
                schema_text = "Tables: <error>"

        # Generate
        gen_sql = generate_sql(model, tokenizer, item["question"], schema_text)
        
        # Execute (Gold vs Generated)
        is_correct = False
        error_msg = None
        
        if db_path:
            gold_sql = item["query"]
            gold_res, gold_err = execute_sql(db_path, gold_sql)
            gen_res, gen_err = execute_sql(db_path, gen_sql)
            
            if not gen_err:
                valid_sql += 1
                if str(gen_res) == str(gold_res): # Simple exact set match (naive)
                    is_correct = True
                    correct_exec += 1
            else:
                error_msg = gen_err
        
        results.append({
            "question": item["question"],
            "gold_sql": item["query"],
            "gen_sql": gen_sql,
            "correct": is_correct,
            "error": error_msg
        })

    # Metrics
    exec_acc = (correct_exec / len(dataset)) * 100
    valid_perc = (valid_sql / len(dataset)) * 100
    
    print(f"--- Results ---")
    print(f"Valid SQL: {valid_perc:.2f}%")
    print(f"Execution Accuracy: {exec_acc:.2f}%")
    
    # Save results
    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
