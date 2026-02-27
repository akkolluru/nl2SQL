
import sqlite3
import os
from typing import List, Tuple, Dict, Set, Any
from .base import BaseAdapter

class SQLiteAdapter(BaseAdapter):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None

    def connect(self) -> None:
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"SQLite DB not found at {self.db_path}")
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None

    def get_schema_summary(self) -> str:
        self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [r[0] for r in cursor.fetchall()]

            parts = []
            for t in tables:
                cursor.execute(f"PRAGMA table_info({t})")
                # rows: (cid, name, type, notnull, dflt_value, pk)
                cols = []
                for r in cursor.fetchall():
                    col_str = f"{r[1]} {r[2]}" if r[2] else r[1]
                    if r[5]:  # pk flag
                        col_str += " PK"
                    cols.append(col_str)
                parts.append(f"{t}({', '.join(cols)})")

            # Add foreign key info
            fk_parts = []
            for t in tables:
                cursor.execute(f"PRAGMA foreign_key_list({t})")
                for fk in cursor.fetchall():
                    # fk: (id, seq, table, from, to, on_update, on_delete, match)
                    fk_parts.append(f"{t}.{fk[3]} → {fk[2]}.{fk[4]}")

            schema = "Tables: " + "; ".join(parts)
            if fk_parts:
                schema += "\nForeign Keys: " + "; ".join(fk_parts)
            return schema
        finally:
            pass

    def get_allowed_sets(self) -> Tuple[Set[str], Dict[str, Set[str]]]:
        self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables_list = [r[0] for r in cursor.fetchall()]
            
            allowed_tables = set(tables_list)
            allowed_columns = {}
            
            for t in tables_list:
                cursor.execute(f"PRAGMA table_info({t})")
                cols = [r[1] for r in cursor.fetchall()]
                allowed_columns[t] = set(cols)
                
            return allowed_tables, allowed_columns
        finally:
            pass

    def execute_query(self, sql: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        self.connect()
        try:
            # SQLite doesn't support dictionary cursor natively in same way, but can use row_factory
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()
            
            # Simple safety: LIMIT
            if "LIMIT" not in sql.upper():
                sql += " LIMIT 50"
                
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            # Extract headers
            if cursor.description:
                cols = [d[0] for d in cursor.description]
            else:
                cols = []
                
            # Convert rows to dicts
            result_rows = [dict(row) for row in rows]
            return cols, result_rows
        finally:
            # We don't close here to allow reuse, main app manages lifecycle or we close in dependency injection
            pass
