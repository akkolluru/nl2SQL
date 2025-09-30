import mysql.connector as mysql
from .config import settings

def run_sql(query: str):
    """
    Connects to MySQL, runs a validated SQL query,
    and returns column names + rows.
    """
    conn = mysql.connect(
        host=settings.db_host,
        user=settings.db_user,
        password=settings.db_pass,
        database=settings.db_name,
        connection_timeout=5,
        charset="utf8mb4",
        use_pure=True,
    )
    try:
        cur = conn.cursor(dictionary=True)

        # Safety: add LIMIT if missing
        q_lower = query.lower()
        if "select" in q_lower and " limit " not in q_lower:
            query = query.rstrip(";") + f" LIMIT {settings.default_limit};"

        cur.execute(query)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        return cols, rows
    finally:
        cur.close()
        conn.close()