# app/main.py
"""
FastAPI backend — orchestrates the full NL→SQL pipeline.

Pipeline: Schema Introspection → Schema Linking → RAG → Prompt → LLM
          → Self-Correction (validate + retry) → Execute → Return
"""

import logging

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, field_validator
from .prompt import build_prompt, SUPPORTED_LANGUAGES
from .nl2sql import generate_sql
from .validate import validate_sql
from .database.factory import get_adapter
from .database.base import BaseAdapter
from .rag_builder import RAGSearcher
from .schema_linker import link_schema
from .self_correct import generate_sql_with_retry

logger = logging.getLogger(__name__)

app = FastAPI(
    title="NL2SQL — Multilingual",
    description="Natural Language to SQL API supporting English, Hindi, and Telugu.",
    version="0.4.0",
)

# ---------------------------------------------------------------------------
# RAG initialization (Phase 1)
# ---------------------------------------------------------------------------
rag = RAGSearcher()


@app.on_event("startup")
def _init_rag() -> None:
    """Index Spider examples on first launch (no-op if already indexed)."""
    count = rag.index_spider()
    logger.info("RAG ready — %d examples in ChromaDB.", count)

# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------

def get_db() -> BaseAdapter:
    adapter = get_adapter()
    try:
        yield adapter
    finally:
        adapter.close()

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class QueryIn(BaseModel):
    question: str
    language: str = "en"   # 'en' | 'hi' | 'te'

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language '{v}'. Supported: {SUPPORTED_LANGUAGES}"
            )
        return v

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question must not be empty.")
        return v


class QueryOut(BaseModel):
    sql: str
    columns: list[str]
    rows: list[dict]
    language: str   # echo back the language used


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "supported_languages": SUPPORTED_LANGUAGES}


@app.post("/query", response_model=QueryOut)
async def query(q: QueryIn, db: BaseAdapter = Depends(get_db)):
    # 1) Schema introspection (with types + foreign keys)
    try:
        full_schema = db.get_schema_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # 2) Schema Linking — pre-filter to relevant tables/columns
    schema_text = await link_schema(q.question, full_schema)

    # 3) RAG — retrieve similar NL-SQL examples
    examples = rag.search(q.question, k=3)
    examples_block = rag.format_examples(examples)
    logger.info("RAG returned %d examples for query.", len(examples))

    # 4) Build language-aware prompt (with RAG examples injected)
    try:
        prompt = build_prompt(
            q.question, schema_text,
            language=q.language,
            examples_block=examples_block or None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 5) LLM → SQL with self-correction (retry up to 3x on error)
    try:
        cleaned, attempts = await generate_sql_with_retry(
            prompt, db, max_retries=3
        )
        logger.info("SQL generated in %d attempt(s).", attempts)
    except RuntimeError as e:
        raise HTTPException(
            status_code=422,
            detail={"error": str(e), "language": q.language},
        )

    # 6) Execute (read-only)
    try:
        cols, rows = db.execute_query(cleaned)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")

    return {"sql": cleaned, "columns": cols, "rows": rows, "language": q.language}