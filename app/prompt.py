# app/prompt.py

LANG_INSTRUCTIONS: dict[str, str] = {
    "en": (
        "You convert English questions into a SINGLE MySQL SELECT query.\n"
        "- Output only SQL, no commentary.\n"
        "- Use only tables/columns from the provided schema.\n"
        "- Do NOT modify data. SELECT only.\n"
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