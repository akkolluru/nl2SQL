# app/validate.py
from typing import Tuple
import re
import sqlglot
from sqlglot.errors import ParseError

# Blocklists (paranoid but simple for MVP)
BLOCKED_KEYWORDS = {
    "DROP", "TRUNCATE", "ALTER", "RENAME",
    "INSERT", "UPDATE", "DELETE", "REPLACE",
    "CREATE", "GRANT", "REVOKE",
}
# Optional: disallow risky functions in MVP
BLOCKED_FUNCTIONS = {"LOAD_FILE", "SLEEP"}

def _strip_code_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = s.strip("`")
        # remove leading language tag if present
        s = s.split("\n", 1)[-1]
    return s.strip()

def _ensure_semicolon(sql: str) -> str:
    sql = sql.strip()
    return sql if sql.endswith(";") else (sql + ";")

def _only_select(sql: str) -> bool:
    # quick-and-dirty: first non-whitespace token should be SELECT
    head = re.sub(r"^\s+", "", sql, flags=re.MULTILINE)
    return head.upper().startswith("SELECT")

def _contains_blocked(sql_upper: str) -> str | None:
    for kw in BLOCKED_KEYWORDS:
        if re.search(rf"\b{kw}\b", sql_upper):
            return f"Blocked keyword detected: {kw}"
    for fn in BLOCKED_FUNCTIONS:
        if re.search(rf"\b{fn}\s*\(", sql_upper):
            return f"Blocked function detected: {fn}"
    return None

def validate_sql(
    sql: str,
    allowed_tables: list[str],
    allowed_columns: dict[str, set[str]],
) -> Tuple[bool, str, str]:
    """
    Validates an LLM-produced SQL string.

    Returns (ok, message, cleaned_sql)
      - ok: bool (True if safe to execute)
      - message: reason if not ok
      - cleaned_sql: normalized sql (fences removed, ends with ;)
    """
    if not sql or not sql.strip():
        return False, "Empty SQL.", sql

    # 0) clean common artifacts
    sql = _strip_code_fences(sql)
    sql = _ensure_semicolon(sql)
    sql_upper = sql.upper()

    # 1) only SELECT for MVP
    if not _only_select(sql):
        return False, "Only SELECT queries are allowed in this MVP.", sql

    # 2) block dangerous keywords/functions
    blocked = _contains_blocked(sql_upper)
    if blocked:
        return False, blocked, sql

    # 3) parse syntax with sqlglot (MySQL dialect)
    try:
        ast = sqlglot.parse_one(sql, read="mysql")
    except ParseError as e:
        return False, f"Syntax error: {e}", sql

    # 4) schema checks: tables & columns must exist
    ref_tables = {t.name for t in ast.find_all(sqlglot.exp.Table)}
    for t in ref_tables:
        if t not in allowed_tables:
            return False, f"Unknown table: {t}", sql

    # Column checks (qualified and unqualified)
    for col in ast.find_all(sqlglot.exp.Column):
        t = col.table  # may be None
        c = col.name
        if t:
            if t not in allowed_tables:
                return False, f"Unknown table: {t}", sql
            if c not in allowed_columns.get(t, set()):
                return False, f"Unknown column: {t}.{c}", sql
        else:
            # Unqualified: allow if col exists in ANY table (simple MVP rule)
            if not any(c in allowed_columns.get(tt, set()) for tt in allowed_tables):
                return False, f"Unknown column: {c}", sql

    # 5) OPTIONAL: simple join sanity (avoid accidental cartesian blowups)
    # If there is a JOIN, prefer it has an ON or USING clause.
    for j in ast.find_all(sqlglot.exp.Join):
        if not (j.args.get("on") or j.args.get("using")):
            return False, "JOIN without ON/USING clause is not allowed.", sql

    return True, "ok", sql