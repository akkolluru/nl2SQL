# app/schema_linker.py
"""
Schema Linking — pre-filter irrelevant tables and columns.

Before generating SQL, we ask the LLM to identify which tables and columns
from the full schema are relevant to the question. This dramatically reduces
hallucination of non-existent columns and unnecessary JOINs.
"""

from __future__ import annotations

import json
import logging

import httpx

from .config import settings

logger = logging.getLogger(__name__)


async def link_schema(question: str, full_schema: str) -> str:
    """
    Ask the LLM which tables/columns are relevant to the question.
    Returns a filtered schema string containing only relevant parts.
    Falls back to the full schema if linking fails.
    """
    linking_prompt = (
        "Given the database schema and question below, identify ONLY the "
        "tables and columns needed to answer the question.\n\n"
        f"Schema:\n{full_schema}\n\n"
        f"Question: {question}\n\n"
        'Respond with JSON: {"tables": ["table1", "table2"], '
        '"columns": ["table1.col1", "table2.col2"]}'
    )

    url = f"{settings.ollama_url}/api/generate"
    payload = {
        "model": settings.ollama_model,
        "prompt": linking_prompt,
        "stream": False,
        "format": "json",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            output = resp.json().get("response", "").strip()

        data = json.loads(output)
        tables = data.get("tables", [])
        columns = data.get("columns", [])

        if not tables:
            logger.warning("Schema linking returned no tables, using full schema.")
            return full_schema

        # Build filtered schema from the full schema text
        filtered = _filter_schema(full_schema, tables, columns)
        logger.info("Schema linking: %d tables, %d columns selected.", len(tables), len(columns))
        return filtered

    except Exception as e:
        logger.warning("Schema linking failed (%s), using full schema.", e)
        return full_schema


def _filter_schema(full_schema: str, tables: list[str], columns: list[str]) -> str:
    """
    Filter the full schema string to only include the identified tables.
    Preserves foreign key lines that reference selected tables.
    """
    tables_lower = {t.lower() for t in tables}

    lines = full_schema.split("\n")
    filtered_parts = []

    for line in lines:
        if line.startswith("Tables:"):
            # Parse individual table definitions: "table(col1, col2); table2(col3)"
            table_defs = line.replace("Tables: ", "").split("; ")
            kept = []
            for td in table_defs:
                table_name = td.split("(")[0].strip().lower()
                if table_name in tables_lower:
                    kept.append(td)
            if kept:
                filtered_parts.append("Tables: " + "; ".join(kept))

        elif line.startswith("Foreign Keys:"):
            # Keep only FK relationships involving selected tables
            fk_defs = line.replace("Foreign Keys: ", "").split("; ")
            kept_fks = []
            for fk in fk_defs:
                # Format: "table.col → table2.col2"
                parts = fk.split(".")
                if parts and parts[0].strip().lower() in tables_lower:
                    kept_fks.append(fk)
            if kept_fks:
                filtered_parts.append("Foreign Keys: " + "; ".join(kept_fks))

    if not filtered_parts:
        return full_schema

    return "\n".join(filtered_parts)
