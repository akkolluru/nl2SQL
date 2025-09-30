# app/nl2sql.py

import httpx
from .config import settings

async def generate_sql(prompt: str) -> str:
    """
    Sends the schema-aware prompt to Ollama and extracts the SQL.
    """
    url = f"{settings.ollama_url}/api/generate"
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            url,
            json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
        )
        resp.raise_for_status()
        output = resp.json().get("response", "").strip()

        # clean common LLM artifacts
        if output.startswith("```"):
            output = output.strip("`")
            # drop leading "sql" tag if present
            if output.lower().startswith("sql"):
                output = output.split("\n", 1)[-1]
        if ";" in output:
            # keep only up to first semicolon
            output = output.split(";", 1)[0] + ";"

        return output