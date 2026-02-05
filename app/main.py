# app/main.py
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from .prompt import build_prompt
from .nl2sql import generate_sql
from .validate import validate_sql
# New database adapter imports
from .database.factory import get_adapter
from .database.base import BaseAdapter

app = FastAPI(title="NL2SQL MVP")

# Dependency to get DB adapter
def get_db() -> BaseAdapter:
    adapter = get_adapter()
    try:
        yield adapter
    finally:
        adapter.close()

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
async def query(q: QueryIn, db: BaseAdapter = Depends(get_db)):
    question = q.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Empty question.")

    # 1) schema-aware prompt
    # Use adapter to get schema summary
    try:
        schema_text = db.get_schema_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    prompt = build_prompt(question, schema_text)

    # 2) LLM → SQL
    sql = await generate_sql(prompt)

    # 3) validate
    # Use adapter to get allowed tables/columns
    try:
        allowed_tables, allowed_columns = db.get_allowed_sets()
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Database schema fetch error: {str(e)}")

    ok, msg, cleaned = validate_sql(sql, list(allowed_tables), allowed_columns)
    if not ok:
        raise HTTPException(status_code=422, detail={"error": msg, "sql": cleaned})

    # 4) execute
    try:
        cols, rows = db.execute_query(cleaned)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")
        
    return {"sql": cleaned, "columns": cols, "rows": rows}