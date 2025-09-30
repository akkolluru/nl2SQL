# app/validate.py
from typing import Tuple
import re
import sqlglot
from sqlglot.errors import ParseError

BLOCKED_KEYWORDS = {
    "DROP", "TRUNCATE", "ALTER", "RENAME",
    "INSERT", "UPDATE", "DELETE", "REPLACE",
    "CREATE", "GRANT", "REVOKE",
}
BLOCKED_FUNCTIONS = {"LOAD_FILE", "SLEEP"}

def _strip_code_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = s.strip("`")
        if "\n" in s:
            s = s.split("\n", 1)[-1]
    return s.strip()

def _ensure_semicolon(sql: str) -> str:
    sql = sql.strip()
    return sql if sql.endswith(";") else (sql + ";")

def _only_select(sql: str) -> bool:
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
    Validates LLM-produced SQL (SELECT-only MVP) with alias-aware schema checks.
    Returns (ok, message, cleaned_sql).
    """
    if not sql or not sql.strip():
        return False, "Empty SQL.", sql

    # Clean + normalize
    sql = _strip_code_fences(sql)
    sql = _ensure_semicolon(sql)
    sql_upper = sql.upper()

    # Policy: SELECT-only for MVP
    if not _only_select(sql):
        return False, "Only SELECT queries are allowed in this MVP.", sql

    blocked = _contains_blocked(sql_upper)
    if blocked:
        return False, blocked, sql

    # Parse
    try:
        ast = sqlglot.parse_one(sql, read="mysql")
    except ParseError as e:
        return False, f"Syntax error: {e}", sql

    # Build table -> alias map and alias -> table map
    # sqlglot Table nodes carry .name and optional .alias
    table_to_alias = {}
    alias_to_table = {}
    real_tables = set()

    for tnode in ast.find_all(sqlglot.exp.Table):
        tname = tnode.name  # real table name
        real_tables.add(tname)
        alias = None
        if tnode.args.get("alias"):
            alias = tnode.args["alias"].name
        if alias:
            table_to_alias[tname] = alias
            alias_to_table[alias] = tname

    # Check that all referenced real tables exist
    for t in real_tables:
        if t not in allowed_tables:
            return False, f"Unknown table: {t}", sql

    # Column checks (qualified + unqualified)
    for col in ast.find_all(sqlglot.exp.Column):
        qualifier = col.table  # may be alias or real table or None
        cname = col.name

        if qualifier:
            # Resolve qualifier: it might be an alias; map back to real table
            if qualifier in allowed_tables:
                real = qualifier
            elif qualifier in alias_to_table:
                real = alias_to_table[qualifier]
            else:
                return False, f"Unknown table or alias: {qualifier}", sql

            if cname not in allowed_columns.get(real, set()):
                return False, f"Unknown column: {qualifier}.{cname}", sql
        else:
            # Unqualified column: accept if it exists in ANY allowed table
            if not any(cname in allowed_columns.get(t, set()) for t in allowed_tables):
                return False, f"Unknown column: {cname}", sql

    # JOIN sanity: require ON/USING to avoid cartesian blowups
    for j in ast.find_all(sqlglot.exp.Join):
        if not (j.args.get("on") or j.args.get("using")):
            return False, "JOIN without ON/USING clause is not allowed.", sql

    return True, "ok", sql