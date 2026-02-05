
import json
import os
from typing import List, Tuple, Dict, Set, Any
from .base import BaseAdapter

class JSONSchemaAdapter(BaseAdapter):
    """
    Adapter that loads schema definitions from a JSON file.
    Useful for testing or when the live DB is not available.
    
    Expected JSON format:
    {
        "tables": {
            "table_name": ["col1", "col2", "col3"],
            "orders": ["id", "amount", "customer_id"]
        }
    }
    """
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.schema_data = {}

    def connect(self) -> None:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Schema file not found at {self.file_path}")
        
        with open(self.file_path, "r") as f:
            self.schema_data = json.load(f)

    def close(self) -> None:
        self.schema_data = {}

    def get_schema_summary(self) -> str:
        self.connect()
        tables = self.schema_data.get("tables", {})
        parts = []
        for t, cols in tables.items():
            parts.append(f"{t}(" + ", ".join(cols) + ")")
        return "Tables: " + "; ".join(parts)

    def get_allowed_sets(self) -> Tuple[Set[str], Dict[str, Set[str]]]:
        self.connect()
        tables = self.schema_data.get("tables", {})
        allowed_tables = set(tables.keys())
        allowed_columns = {t: set(cols) for t, cols in tables.items()}
        return allowed_tables, allowed_columns

    def execute_query(self, sql: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        # Execution is not supported in file-only mode
        return [], []
