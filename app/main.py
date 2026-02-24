# app/main.py
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, field_validator
from .prompt import build_prompt, SUPPORTED_LANGUAGES
from .nl2sql import generate_sql
from .validate import validate_sql
from .database.factory import get_adapter
from .database.base import BaseAdapter

app = FastAPI(
    title="NL2SQL — Multilingual",
    description="Natural Language to SQL API supporting English, Hindi, and Telugu.",
    version="0.2.0",
)

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
    # 1) Schema introspection
    try:
        schema_text = db.get_schema_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # 2) Build language-aware prompt
    try:
        prompt = build_prompt(q.question, schema_text, language=q.language)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 3) LLM → SQL
    sql = await generate_sql(prompt)

    # 4) Safety validation
    try:
        allowed_tables, allowed_columns = db.get_allowed_sets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schema fetch error: {str(e)}")

    ok, msg, cleaned = validate_sql(sql, list(allowed_tables), allowed_columns)
    if not ok:
        raise HTTPException(
            status_code=422,
            detail={"error": msg, "sql": cleaned, "language": q.language},
        )

    # 5) Execute (read-only)
    try:
        cols, rows = db.execute_query(cleaned)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")

    return {"sql": cleaned, "columns": cols, "rows": rows, "language": q.language}