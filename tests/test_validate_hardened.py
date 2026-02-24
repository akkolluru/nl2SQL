import pytest
from app.validate import validate_sql

@pytest.fixture
def schema():
    return ["users"], {"users": {"id", "name", "role", "password"}}

def test_auto_limit_enforcement(schema):
    sql = "SELECT id, name FROM users"
    tables, cols = schema
    ok, msg, cleaned = validate_sql(sql, tables, cols)
    
    assert ok is True
    assert "LIMIT" in cleaned.upper()
    assert cleaned.endswith(";")

def test_comment_injection(schema):
    sql = "SELECT id FROM users -- AND role = 'admin'"
    tables, cols = schema
    ok, msg, cleaned = validate_sql(sql, tables, cols)
    
    assert ok is False
    assert "comment pattern" in msg

def test_tautology_injection_1(schema):
    sql = "SELECT id FROM users WHERE id = 1 OR 1=1"
    tables, cols = schema
    ok, msg, cleaned = validate_sql(sql, tables, cols)
    
    assert ok is False
    assert "tautology pattern" in msg

def test_tautology_injection_2(schema):
    sql = "SELECT id FROM users WHERE name = 'John' OR 'a'='a'"
    tables, cols = schema
    ok, msg, cleaned = validate_sql(sql, tables, cols)
    
    assert ok is False
    assert "tautology pattern" in msg

def test_blocked_keywords(schema):
    sql = "DELETE FROM users WHERE id = 1"
    tables, cols = schema
    ok, msg, cleaned = validate_sql(sql, tables, cols)
    
    assert ok is False
    assert "Only SELECT queries are allowed" in msg or "Blocked keyword" in msg
