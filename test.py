from app.schema import get_schema_summary, allowed_sets
from app.prompt import build_prompt
from app.examples import few_shot_block
from app.nl2sql import generate_sql
from app.validate import validate_sql
import asyncio

schema_text = get_schema_summary()
prompt = build_prompt("Show total orders per city.", schema_text, few_shot_block())
sql = asyncio.run(generate_sql(prompt))
print("RAW:", sql)

allowed_tables, allowed_columns = allowed_sets()
ok, msg, cleaned = validate_sql(sql, list(allowed_tables), allowed_columns)
print("VALID:", ok, msg)
print("CLEANED:", cleaned)