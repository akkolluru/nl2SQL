import argparse
import json
import os
import sys
import time
import asyncio
import pandas as pd
import sqlglot

# Add root project dir to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.prompt import build_prompt, SUPPORTED_LANGUAGES
from app.nl2sql import generate_sql
from app.validate import validate_sql
from app.database.sqlite_adapter import SQLiteAdapter

def normalize_sql(sql: str) -> str:
    try:
        return sqlglot.parse_one(sql).sql()
    except Exception:
        return sql.strip()

async def evaluate_question(item: dict, lang: str, db_adapter: SQLiteAdapter) -> dict:
    t0 = time.time()
    db_id = item["db_id"]
    gold_sql = item["query"]
    
    # Select question based on language
    if lang == "en":
        question = item["question"]
    elif lang == "hi":
        question = item.get("question_hindi", "")
    elif lang == "te":
        question = item.get("question_telugu", "")
    else:
        question = ""

    result = {
        "db_id": db_id,
        "question": question,
        "gold_sql": gold_sql,
        "predicted_sql": "",
        "error": None,
        "ex_match": 0,
        "em_match": 0,
        "latency_sec": 0.0
    }

    if not question:
        result["error"] = "Missing translated question"
        return result

    try:
        # Pipeline
        schema_text = db_adapter.get_schema_summary()
        prompt = build_prompt(question, schema_text, language=lang)
        predicted_sql = await generate_sql(prompt)
        
        allowed_tables, allowed_columns = db_adapter.get_allowed_sets()
        ok, msg, cleaned_sql = validate_sql(predicted_sql, list(allowed_tables), allowed_columns)
        
        if not ok:
            result["predicted_sql"] = cleaned_sql
            result["error"] = f"Validation failed: {msg}"
            return result
            
        result["predicted_sql"] = cleaned_sql

        # Calculate EX (Execution Match)
        try:
            _, pred_rows = db_adapter.execute_query(cleaned_sql)
            _, gold_rows = db_adapter.execute_query(gold_sql)
            
            # Simple list-of-dicts comparison. Order might matter depending on query,
            # but for a basic MVP benchmark, direct equality is a good proxy.
            if pred_rows == gold_rows:
                result["ex_match"] = 1
        except Exception as e:
            result["error"] = f"Execution error: {str(e)}"

        # Calculate EM (Exact Match)
        if normalize_sql(cleaned_sql).lower() == normalize_sql(gold_sql).lower():
            result["em_match"] = 1

    except Exception as e:
        result["error"] = f"Pipeline error: {str(e)}"
    finally:
        result["latency_sec"] = round(time.time() - t0, 2)

    return result

async def main():
    parser = argparse.ArgumentParser(description="Run Spider benchmark")
    parser.add_argument("--lang", type=str, choices=SUPPORTED_LANGUAGES, default="en", help="Language to test")
    parser.add_argument("--dry-run", action="store_true", help="Run only the first 10 questions")
    args = parser.parse_args()

    # Determine input file
    if args.lang == "en":
        data_file = "spider_data/dev.json"
    else:
        data_file = "data/processed/indic_spider_dev.jsonl"

    if not os.path.exists(data_file):
        print(f"Error: Data file {data_file} not found.")
        sys.exit(1)

    # Load data
    print(f"Loading data from {data_file}...")
    items = []
    if data_file.endswith(".json"):
        with open(data_file, "r") as f:
            items = json.load(f)
    else:
        with open(data_file, "r") as f:
            items = [json.loads(line) for line in f]

    if args.dry_run:
        print("Dry run enabled. Limiting to 10 questions.")
        items = items[:10]

    results = []
    
    # We iterate sequentially to not overwhelm Ollama
    for i, item in enumerate(items):
        db_id = item["db_id"]
        db_path = f"spider_data/database/{db_id}/{db_id}.sqlite"
        
        if not os.path.exists(db_path):
            print(f"Warning: DB {db_path} not found. Skipping.")
            continue
            
        adapter = SQLiteAdapter(db_path)
        try:
            res = await evaluate_question(item, args.lang, adapter)
            results.append(res)
        finally:
            adapter.close()
            
        # Progress
        if (i + 1) % 5 == 0 or (i + 1) == len(items):
            print(f"Processed {i + 1}/{len(items)} questions...")

    # Summarize
    df = pd.DataFrame(results)
    total = len(df)
    
    if total == 0:
        print("No questions processed.")
        sys.exit(0)
        
    ex_score = df["ex_match"].mean() * 100
    em_score = df["em_match"].mean() * 100
    error_rate = df["error"].notna().mean() * 100
    avg_latency = df["latency_sec"].mean()

    print("\n" + "="*40)
    print(f"BENCHMARK SUMMARY ({args.lang.upper()})")
    print("="*40)
    print(f"Total Questions : {total}")
    print(f"Execution Match : {ex_score:.2f}%")
    print(f"Exact Match     : {em_score:.2f}%")
    print(f"Error Rate      : {error_rate:.2f}%")
    print(f"Avg Latency     : {avg_latency:.2f} s/query")
    print("="*40)

    # Save
    out_prefix = "dry_run" if args.dry_run else f"spider_dev_{args.lang}"
    out_file = f"data/benchmark_results/{out_prefix}.csv"
    df.to_csv(out_file, index=False)
    print(f"Detailed results saved to {out_file}")

if __name__ == "__main__":
    asyncio.run(main())
