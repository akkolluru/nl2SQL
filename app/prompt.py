# app/prompt.py

LANG_INSTRUCTIONS: dict[str, str] = {
    "en": (
        "You are an expert SQL generator. Convert the question into a SINGLE SELECT query.\n"
        "STRICT RULES:\n"
        "1. Output ONLY raw SQL. No explanations, no markdown, no comments.\n"
        "2. Use ONLY the EXACT table and column names from the schema. "
        "If a column is named 'name', use 'name' — do NOT use 'Name', 'Singer_Name', etc.\n"
        "3. If the answer can come from a single table, do NOT use JOIN.\n"
        "4. Do NOT use table aliases (AS T1, AS T2) unless absolutely required.\n"
        "5. Always include all columns requested in the question.\n"
        "6. For counting, use COUNT(*).\n"
        "7. Do NOT add LIMIT unless asked.\n"
    ),
    "hi": (
        "The question below is written in Hindi. Understand it and convert it "
        "into a SINGLE MySQL SELECT query.\n"
        "- Output only SQL, no commentary.\n"
        "- Use only tables/columns from the provided schema.\n"
        "- Do NOT modify data. SELECT only.\n"
    ),
    "te": (
        "The question below is written in Telugu. Understand it and convert it "
        "into a SINGLE MySQL SELECT query.\n"
        "- Output only SQL, no commentary.\n"
        "- Use only tables/columns from the provided schema.\n"
        "- Do NOT modify data. SELECT only.\n"
    ),
}

SUPPORTED_LANGUAGES: list[str] = list(LANG_INSTRUCTIONS.keys())


def build_prompt(
    user_question: str,
    schema_text: str,
    language: str = "en",
    examples_block: str | None = None,
) -> str:
    """
    Compose a schema-aware, language-aware prompt for the LLM.

    Args:
        user_question: The user's natural language question.
        schema_text:   Compact schema string, e.g. 'Tables: t(col1, col2); ...'
        language:      ISO-like language code: 'en', 'hi', or 'te'.
        examples_block: Optional few-shot examples to guide the model.

    Raises:
        ValueError: If the language is not supported.
    """
    if language not in LANG_INSTRUCTIONS:
        raise ValueError(
            f"Unsupported language: '{language}'. "
            f"Supported: {SUPPORTED_LANGUAGES}"
        )

    system_instr = LANG_INSTRUCTIONS[language]

    parts = [system_instr, "Database schema (compact):", schema_text, ""]
    if examples_block:
        parts += ["Examples:", examples_block, ""]
    parts += [f"Question: {user_question}", "SQL:"]
    return "\n".join(parts)