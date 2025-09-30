# app/prompt.py

SYSTEM_INSTR = (
    "You convert English questions into a SINGLE MySQL SELECT query.\n"
    "- Output only SQL, no commentary.\n"
    "- Use only tables/columns from the provided schema.\n"
    "- Prefer safe queries. Do NOT modify data.\n"
)

def build_prompt(user_question: str, schema_text: str, examples_block: str | None = None) -> str:
    """
    Compose a schema-aware prompt for the LLM.
    schema_text: e.g. 'Tables: customers(customer_id, name,...); orders(order_id, ...)'
    examples_block: optional few-shot examples to guide the model.
    """
    parts = [SYSTEM_INSTR, "Database schema (compact):", schema_text, ""]
    if examples_block:
        parts += ["Examples:", examples_block, ""]
    parts += [f"Question: {user_question}", "SQL:"]
    return "\n".join(parts)