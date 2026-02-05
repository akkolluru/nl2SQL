
import os
from .base import BaseAdapter
from .mysql_adapter import MySQLAdapter
from .sqlite_adapter import SQLiteAdapter
from .json_adapter import JSONSchemaAdapter
from ..config import settings

def get_adapter() -> BaseAdapter:
    """
    Factory to get the configured database adapter.
    """
    # Check for Schema File config (Priority for testing)
    # We assume settings might have this, or we fallback to live DB
    # For MVP, let's say if DB_TYPE env var is "json", use it.
    
    db_type = os.getenv("DB_TYPE", "mysql").lower()
    
    if db_type == "sqlite":
        # Need a path config
        return SQLiteAdapter(os.getenv("SQLITE_PATH", "data/spider.db"))
        
    if db_type == "json":
        return JSONSchemaAdapter(os.getenv("SCHEMA_FILE", "data/schema_definitions/schema.json"))
    
    # Default to MySQL
    return MySQLAdapter(
        host=settings.db_host,
        user=settings.db_user,
        password=settings.db_pass,
        db_name=settings.db_name
    )

def get_sqlite_adapter(db_path: str) -> BaseAdapter:
    return SQLiteAdapter(db_path)
