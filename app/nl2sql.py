# app/nl2sql.py
"""
LLM client — sends the prompt to Ollama and extracts SQL.

Phase 2: Uses Ollama's JSON format constraint so the model is forced
to output structured JSON. We then parse & validate with Pydantic.
"""

from __future__ import annotations

import json
import logging

import httpx
from pydantic import BaseModel, ValidationError

from .config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic model for the structured LLM response
# ---------------------------------------------------------------------------
class SQLResponse(BaseModel):
    sql: str


# ---------------------------------------------------------------------------
# SQL extraction helpers
# ---------------------------------------------------------------------------
def _clean_sql(raw: str) -> str:
    """Strip markdown fences, trailing semicolons, whitespace."""
    sql = raw.strip()
    if sql.startswith("```"):
        sql = sql.strip("`")
        if sql.lower().startswith("sql"):
            sql = sql.split("\n", 1)[-1]
    sql = sql.strip()
    if ";" in sql:
        sql = sql.split(";", 1)[0] + ";"
    return sql


def _extract_sql_from_text(text: str) -> str:
    """Fallback: extract SQL from raw text when JSON parsing fails."""
    return _clean_sql(text)


def _extract_sql_from_json(text: str) -> str | None:
    """Try to parse the LLM output as JSON and extract the 'sql' key."""
    try:
        parsed = SQLResponse.model_validate_json(text)
        return _clean_sql(parsed.sql)
    except (ValidationError, json.JSONDecodeError):
        return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
async def generate_sql(prompt: str) -> str:
    """
    Send the prompt to Ollama with JSON format constraint.
    Returns the extracted SQL string.
    """
    url = f"{settings.ollama_url}/api/generate"
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt + '\n\nRespond with JSON: {"sql": "<your SQL query>"}',
        "stream": False,
        "format": "json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        output = resp.json().get("response", "").strip()

    # Try JSON-constrained path first (Phase 2)
    sql = _extract_sql_from_json(output)
    if sql:
        logger.info("Constrained decoding: extracted SQL from JSON.")
        return sql

    # Fallback to raw text extraction
    logger.warning("JSON parse failed, falling back to text extraction.")
    return _extract_sql_from_text(output)