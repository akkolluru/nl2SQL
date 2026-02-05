
import mysql.connector
from typing import List, Tuple, Dict, Set, Any
from .base import BaseAdapter

class MySQLAdapter(BaseAdapter):
    def __init__(self, host, user, password, db_name):
        self.config = {
            "host": host,
            "user": user,
            "password": password,
            "database": db_name,
            "connection_timeout": 5
        }
        self.conn = None

    def connect(self) -> None:
        # For this simple MVP, we might connect per query or manage a pool.
        # Keeping it simple: connect if not connected.
        if self.conn is None or not self.conn.is_connected():
            self.conn = mysql.connector.connect(**self.config)

    def close(self) -> None:
        if self.conn and self.conn.is_connected():
            self.conn.close()

    def get_schema_summary(self) -> str:
        self.connect()
        try:
            cur = self.conn.cursor()
            cur.execute("""
                SELECT TABLE_NAME, COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME, ORDINAL_POSITION;
            """, (self.config["database"],))
            
            tables = {}
            for t, c in cur.fetchall():
                tables.setdefault(t, []).append(c)
            
            parts = []
            for t, cols in tables.items():
                parts.append(f"{t}(" + ", ".join(cols) + ")")
            return "Tables: " + "; ".join(parts)
        finally:
            cur.close()
            # We can keep connection open or close it. 
            # For now, let's keep it open or manage it in upper layers. 
            # Re-implementation of original logic closed it every time.
            self.close() 

    def get_allowed_sets(self) -> Tuple[Set[str], Dict[str, Set[str]]]:
        self.connect()
        try:
            cur = self.conn.cursor()
            cur.execute("""
                SELECT TABLE_NAME, COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s;
            """, (self.config["database"],))
            
            allowed_tables = set()
            allowed_columns = {}
            for t, c in cur.fetchall():
                allowed_tables.add(t)
                allowed_columns.setdefault(t, set()).add(c)
            return allowed_tables, allowed_columns
        finally:
            cur.close()
            self.close()

    def execute_query(self, sql: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        self.connect()
        try:
            cur = self.conn.cursor(dictionary=True)
            # Enforce limit if missing (simple hack from original db.py?)
            # The original db.py check "LIMIT" existence.
            if "LIMIT" not in sql.upper():
                sql += " LIMIT 50"
            
            cur.execute(sql)
            rows = cur.fetchall()
            # If rows is empty, cursor.column_names might be available if executed
            cols = list(cur.column_names) if cur.column_names else []
            return cols, rows
        finally:
            cur.close()
            self.close()
