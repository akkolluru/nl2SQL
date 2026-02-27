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
from app.rag_builder import RAGSearcher
from app.self_correct import generate_sql_with_retry
from app.schema_linker import link_schema

def normalize_sql(sql: str) -> str:
    """Normalize SQL for fair EM comparison: strip LIMIT, lowercase, re-parse."""
    try:
        parsed = sqlglot.parse_one(sql)
        # Remove LIMIT clause (our pipeline auto-appends LIMIT)
        if parsed.args.get("limit"):
            parsed.args["limit"] = None
        return parsed.sql().lower().strip().rstrip(";")
    except Exception:
        # Fallback: manual normalization
        s = sql.strip().rstrip(";").lower()
        # Strip trailing LIMIT N
        import re
        s = re.sub(r"\s+limit\s+\d+\s*$", "", s)
        return s

async def evaluate_question(item: dict, lang: str, db_adapter: SQLiteAdapter, rag: RAGSearcher) -> dict:
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
        "attempts": 0,
        "latency_sec": 0.0
    }

    if not question:
        result["error"] = "Missing translated question"
        return result

    try:
        full_schema = db_adapter.get_schema_summary()

        # Schema Linking: pre-filter to relevant tables/columns
        schema_text = await link_schema(question, full_schema)

        # RAG: retrieve similar examples
        examples = rag.search(question, k=3)
        examples_block = rag.format_examples(examples)

        prompt = build_prompt(question, schema_text, language=lang, examples_block=examples_block or None)

        # Self-correction: retry up to 3 times on error
        try:
            cleaned_sql, attempts = await generate_sql_with_retry(
                prompt, db_adapter, max_retries=3
            )
            result["predicted_sql"] = cleaned_sql
            result["attempts"] = attempts
        except RuntimeError as e:
            result["error"] = str(e)
            return result

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
    parser.add_argument("--limit", type=int, default=0, help="Limit to N questions (0 = all)")
    parser.add_argument("--dry-run", action="store_true", help="Run only the first 10 questions")
    args = parser.parse_args()

    # Initialize RAG
    print("Initializing RAG (ChromaDB)...")
    rag = RAGSearcher()
    rag.index_spider()
    print(f"RAG ready — {rag._collection.count()} examples indexed.")

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
    elif args.limit > 0:
        print(f"Limiting to {args.limit} questions.")
        items = items[:args.limit]

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
            res = await evaluate_question(item, args.lang, adapter, rag)
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
