# app/database/sqlite_adapter.py
"""
SQLite database adapter — used for Spider benchmark evaluation.

Reads schema info via PRAGMA commands and executes read-only SQL queries.
"""

import os
import sqlite3
from typing import Any, Dict, List, Set, Tuple

from .base import BaseAdapter


class SQLiteAdapter(BaseAdapter):
    """Database adapter for SQLite files (e.g., Spider benchmark databases)."""
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
        """Return compact schema string with column types and foreign keys."""
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cursor.fetchall()]

        parts = []
        for t in tables:
            cursor.execute(f"PRAGMA table_info({t})")
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
                fk_parts.append(f"{t}.{fk[3]} → {fk[2]}.{fk[4]}")

        schema = "Tables: " + "; ".join(parts)
        if fk_parts:
            schema += "\nForeign Keys: " + "; ".join(fk_parts)
        return schema

    def get_allowed_sets(self) -> Tuple[Set[str], Dict[str, Set[str]]]:
        """Return (set_of_table_names, dict_of_table→column_sets) for validation."""
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables_list = [r[0] for r in cursor.fetchall()]

        allowed_tables = set(tables_list)
        allowed_columns: Dict[str, Set[str]] = {}

        for t in tables_list:
            cursor.execute(f"PRAGMA table_info({t})")
            cols = [r[1] for r in cursor.fetchall()]
            allowed_columns[t] = set(cols)

        return allowed_tables, allowed_columns

    def execute_query(self, sql: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Execute a read-only SQL query and return (columns, rows)."""
        self.connect()
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()

        # Safety: enforce LIMIT if missing
        if "LIMIT" not in sql.upper():
            sql += " LIMIT 50"

        cursor.execute(sql)
        rows = cursor.fetchall()

        cols = [d[0] for d in cursor.description] if cursor.description else []
        result_rows = [dict(row) for row in rows]
        return cols, result_rows
