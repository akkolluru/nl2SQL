# tests/test_constrained.py
"""Unit tests for Phase 2 — constrained decoding helpers."""

from app.nl2sql import _clean_sql, _extract_sql_from_json, _extract_sql_from_text


# ---- _clean_sql ----

def test_clean_sql_strips_fences():
    raw = "```sql\nSELECT * FROM users;\n```"
    assert "SELECT" in _clean_sql(raw)
    assert "```" not in _clean_sql(raw)


def test_clean_sql_keeps_semicolon():
    assert _clean_sql("SELECT 1; DROP TABLE x;") == "SELECT 1;"


def test_clean_sql_plain_query():
    assert _clean_sql("  SELECT id FROM t  ") == "SELECT id FROM t"


# ---- _extract_sql_from_json ----

def test_json_extraction_valid():
    text = '{"sql": "SELECT * FROM orders"}'
    result = _extract_sql_from_json(text)
    assert result == "SELECT * FROM orders"


def test_json_extraction_invalid():
    assert _extract_sql_from_json("not json at all") is None


def test_json_extraction_missing_key():
    assert _extract_sql_from_json('{"query": "SELECT 1"}') is None


# ---- _extract_sql_from_text (fallback) ----

def test_text_fallback():
    text = "```sql\nSELECT name FROM users;\n```"
    result = _extract_sql_from_text(text)
    assert "SELECT" in result
    assert "```" not in result
