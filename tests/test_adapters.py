
import pytest
import os
import json
from app.database.json_adapter import JSONSchemaAdapter
from app.database.sqlite_adapter import SQLiteAdapter

# Fixture for JSON Adapter
@pytest.fixture
def json_adapter(tmp_path):
    schema = {
        "tables": {
            "test_table": ["c1", "c2"]
        }
    }
    p = tmp_path / "schema.json"
    p.write_text(json.dumps(schema))
    return JSONSchemaAdapter(str(p))

def test_json_adapter_schema(json_adapter):
    summary = json_adapter.get_schema_summary()
    assert "test_table(c1, c2)" in summary
    
    tables, cols = json_adapter.get_allowed_sets()
    assert "test_table" in tables
    assert "c1" in cols["test_table"]

# Fixture for SQLite Adapter
@pytest.fixture
def sqlite_adapter(tmp_path):
    import sqlite3
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")
    conn.execute("INSERT INTO users VALUES (1, 'Alice')")
    conn.commit()
    conn.close()
    return SQLiteAdapter(str(db_path))

def test_sqlite_adapter_schema(sqlite_adapter):
    summary = sqlite_adapter.get_schema_summary()
    assert "users" in summary
    assert "id" in summary
    assert "name" in summary

def test_sqlite_adapter_query(sqlite_adapter):
    cols, rows = sqlite_adapter.execute_query("SELECT * FROM users")
    assert len(rows) == 1
    assert rows[0]["name"] == "Alice"
