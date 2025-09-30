import mysql.connector as mysql
from .config import settings

def get_schema_summary() -> str:
    """
    Returns a compact, human-readable schema string for prompting.
    Example:
      "Tables: customers(customer_id, name, city, email); orders(order_id, customer_id, order_date, amount_paid, status)"
    """
    conn = mysql.connect(
        host=settings.db_host,
        user=settings.db_user,
        password=settings.db_pass,
        database=settings.db_name,
        connection_timeout=5,
    )
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT TABLE_NAME, COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
            ORDER BY TABLE_NAME, ORDINAL_POSITION;
        """, (settings.db_name,))
        tables = {}
        for t, c in cur.fetchall():
            tables.setdefault(t, []).append(c)

        parts = []
        for t, cols in tables.items():
            parts.append(f"{t}(" + ", ".join(cols) + ")")
        return "Tables: " + "; ".join(parts)
    finally:
        cur.close()
        conn.close()


def allowed_sets() -> tuple[set[str], dict[str, set[str]]]:
    """
    Returns:
      - allowed_tables: set of table names
      - allowed_columns: dict table -> set(columns)
    Used by validation to ensure SQL only references real tables/cols.
    """
    conn = mysql.connect(
        host=settings.db_host,
        user=settings.db_user,
        password=settings.db_pass,
        database=settings.db_name,
        connection_timeout=5,
    )
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT TABLE_NAME, COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s;
        """, (settings.db_name,))

        allowed_tables: set[str] = set()
        allowed_columns: dict[str, set[str]] = {}
        for t, c in cur.fetchall():
            allowed_tables.add(t)
            allowed_columns.setdefault(t, set()).add(c)
        return allowed_tables, allowed_columns
    finally:
        cur.close()
        conn.close()