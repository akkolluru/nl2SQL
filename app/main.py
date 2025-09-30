# app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .schema import get_schema_summary, allowed_sets
from .prompt import build_prompt
from .nl2sql import generate_sql
from .validate import validate_sql
from .db import run_sql

app = FastAPI(title="NL2SQL MVP")

class QueryIn(BaseModel):
    question: str
    # later you can add language, user_id, etc.

class QueryOut(BaseModel):
    sql: str
    columns: list[str]
    rows: list[dict]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/query", response_model=QueryOut)
async def query(q: QueryIn):
    question = q.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Empty question.")

    # 1) schema-aware prompt
    schema_text = get_schema_summary()
    prompt = build_prompt(question, schema_text)

    # 2) LLM → SQL
    sql = await generate_sql(prompt)

    # 3) validate
    allowed_tables, allowed_columns = allowed_sets()
    ok, msg, cleaned = validate_sql(sql, list(allowed_tables), allowed_columns)
    if not ok:
        raise HTTPException(status_code=422, detail={"error": msg, "sql": cleaned})

    # 4) execute (safe: read-only user; LIMIT enforced in db.run_sql)
    cols, rows = run_sql(cleaned)
    return {"sql": cleaned, "columns": cols, "rows": rows}