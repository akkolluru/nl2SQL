#!/usr/bin/env python3
"""
Generate a full training dataset from Spider for fine-tuning.

Reads spider_data/train_spider.json + tables.json and produces
a JSONL file with {schema, question, sql} entries ready for Unsloth.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPIDER_TRAIN = PROJECT_ROOT / "spider_data" / "train_spider.json"
SPIDER_TABLES = PROJECT_ROOT / "spider_data" / "tables.json"
OUTPUT = PROJECT_ROOT / "training" / "spider_train_full.jsonl"


def load_schemas(tables_path: Path) -> dict[str, str]:
    """Build db_id -> compact schema string mapping."""
    with open(tables_path) as f:
        tables_data = json.load(f)

    schemas: dict[str, str] = {}
    for db in tables_data:
        db_id = db["db_id"]
        table_names = db["table_names_original"]
        col_names = db["column_names_original"]  # list of [table_idx, col_name]

        # Group columns by table
        table_cols: dict[str, list[str]] = {t: [] for t in table_names}
        for table_idx, col_name in col_names:
            if table_idx >= 0:  # skip the special "*" column at index -1
                table_cols[table_names[table_idx]].append(col_name)

        parts = [f"{t}({', '.join(cols)})" for t, cols in table_cols.items()]
        schemas[db_id] = "Tables: " + "; ".join(parts)

    return schemas


def main():
    if not SPIDER_TRAIN.exists():
        print(f"ERROR: {SPIDER_TRAIN} not found.")
        sys.exit(1)

    schemas = load_schemas(SPIDER_TABLES)

    with open(SPIDER_TRAIN) as f:
        train_data = json.load(f)

    count = 0
    with open(OUTPUT, "w") as out:
        for item in train_data:
            db_id = item["db_id"]
            schema = schemas.get(db_id, "")
            if not schema:
                continue
            entry = {
                "schema": schema,
                "question": item["question"],
                "sql": item["query"],
            }
            out.write(json.dumps(entry) + "\n")
            count += 1

    print(f"Generated {count} training examples → {OUTPUT}")


if __name__ == "__main__":
    main()
