# app/self_correct.py
"""
Self-Correction Loop — retry SQL generation on validation/execution errors.

When the LLM generates invalid SQL, we feed the error message back into
the prompt and ask it to fix the query. Up to max_retries attempts.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .nl2sql import generate_sql
from .validate import validate_sql

if TYPE_CHECKING:
    from .database.base import BaseAdapter

logger = logging.getLogger(__name__)


async def generate_sql_with_retry(
    prompt: str,
    db_adapter: BaseAdapter,
    max_retries: int = 3,
) -> tuple[str, int]:
    """
    Generate SQL with self-correction on errors.

    Returns (cleaned_sql, attempts_used).
    Raises RuntimeError if all attempts fail.
    """
    allowed_tables, allowed_columns = db_adapter.get_allowed_sets()
    current_prompt = prompt
    last_error = ""
    last_sql = ""

    for attempt in range(1, max_retries + 1):
        # Generate SQL
        sql = await generate_sql(current_prompt)
        last_sql = sql

        # Validate
        ok, msg, cleaned = validate_sql(
            sql, list(allowed_tables), allowed_columns
        )

        if ok:
            # Try executing to catch runtime errors too
            try:
                db_adapter.execute_query(cleaned)
                logger.info("Self-correction: success on attempt %d.", attempt)
                return cleaned, attempt
            except Exception as e:
                last_error = f"Execution error: {e}"
                logger.warning(
                    "Attempt %d: SQL valid but execution failed: %s",
                    attempt, last_error,
                )
        else:
            last_error = msg
            logger.warning(
                "Attempt %d: validation failed: %s", attempt, last_error
            )

        # Build correction prompt for next attempt
        if attempt < max_retries:
            current_prompt = (
                f"{prompt}\n\n"
                f"Your previous SQL was wrong:\n"
                f"  SQL: {sql}\n"
                f"  Error: {last_error}\n\n"
                f"Fix the SQL. Output ONLY the corrected SQL query."
            )

    # All attempts failed — return the last cleaned SQL anyway
    logger.error("Self-correction: all %d attempts failed.", max_retries)
    raise RuntimeError(
        f"Failed after {max_retries} attempts. Last error: {last_error}. "
        f"Last SQL: {last_sql}"
    )
