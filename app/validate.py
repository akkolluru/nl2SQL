# app/validate.py
"""
SQL Safety Validation Engine.

Validates LLM-generated SQL using AST parsing (sqlglot), injection
detection, blocked keyword filtering, and schema-aware table/column checks.
"""

import logging
import re
from typing import Tuple

import sqlglot
try:
    from sqlglot.errors import ParseError
except ImportError:
    # Older sqlglot versions don't expose ParseError separately
    ParseError = Exception  # type: ignore[misc, assignment]

from .config import settings

logger = logging.getLogger(__name__)

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
            
    # Injection patterns
    # 1. Comment injection
    if "--" in sql_upper or "/*" in sql_upper:
        return "Possible SQL injection detected (comment pattern)"
        
    # 2. Tautology injection (e.g. OR 1=1, OR 'a'='a')
    if re.search(r"\bOR\b\s+(?:'[^']*'|[\d]+)\s*=\s*(?:'[^']*'|[\d]+)", sql_upper):
        return "Possible SQL injection detected (tautology pattern)"
        
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
    sql_before_clean = sql
    sql = _ensure_semicolon(sql)
    sql_upper = sql.upper()

    # Normalize allowed sets to lowercase for case-insensitive matching
    allowed_tables_lower = [t.lower() for t in allowed_tables]
    allowed_columns_lower: dict[str, set[str]] = {
        t.lower(): {c.lower() for c in cols}
        for t, cols in allowed_columns.items()
    }
    
    def fmt_log(reason: str) -> str:
        return f"Query Blocked | Reason: {reason} | SQL: {sql_before_clean.replace(chr(10), ' ')}"

    # Policy: SELECT-only for MVP
    if not _only_select(sql):
        msg = "Only SELECT queries are allowed in this MVP."
        logger.warning(fmt_log(msg))
        return False, msg, sql

    blocked = _contains_blocked(sql_upper)
    if blocked:
        logger.warning(fmt_log(blocked))
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

    # Check that all referenced real tables exist (case-insensitive)
    for t in real_tables:
        if t.lower() not in allowed_tables_lower:
            return False, f"Unknown table: {t}", sql

    # Collect SELECT aliases (e.g., COUNT(x) AS total_orders)
    # These are valid column references in ORDER BY, GROUP BY, HAVING
    select_aliases: set[str] = set()
    for expr in ast.find_all(sqlglot.exp.Alias):
        if expr.alias:
            select_aliases.add(expr.alias.lower())

    # Column checks (qualified + unqualified) — case-insensitive
    for col in ast.find_all(sqlglot.exp.Column):
        qualifier = col.table  # may be alias or real table or None
        cname = col.name

        # Skip if this column name is a SELECT alias (e.g., ORDER BY total_orders)
        if not qualifier and cname.lower() in select_aliases:
            continue

        if qualifier:
            # Resolve qualifier: it might be an alias; map back to real table
            if qualifier.lower() in [t.lower() for t in allowed_tables]:
                real = qualifier
            elif qualifier in alias_to_table:
                real = alias_to_table[qualifier]
            else:
                return False, f"Unknown table or alias: {qualifier}", sql

            if cname.lower() not in allowed_columns_lower.get(real.lower(), set()):
                return False, f"Unknown column: {qualifier}.{cname}", sql
        else:
            # Unqualified column: accept if it exists in ANY allowed table
            if not any(cname.lower() in allowed_columns_lower.get(t.lower(), set()) for t in allowed_tables):
                return False, f"Unknown column: {cname}", sql

    # JOIN sanity: require ON/USING to avoid cartesian blowups
    for j in ast.find_all(sqlglot.exp.Join):
        if not (j.args.get("on") or j.args.get("using")):
            msg = "JOIN without ON/USING clause is not allowed."
            logger.warning(fmt_log(msg))
            return False, msg, sql

    # Enforce LIMIT
    limit = ast.args.get("limit")
    if not limit:
        # Append limit
        limit_val = getattr(settings, "default_limit", 100)
        ast = ast.limit(limit_val)
        sql = ast.sql(dialect="mysql") + ";"

    return True, "ok", sql