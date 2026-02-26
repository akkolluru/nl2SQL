# tests/test_rag.py
"""Smoke test for RAG builder — indexes Spider and retrieves examples."""

import pytest
from app.rag_builder import RAGSearcher


@pytest.fixture(scope="module")
def searcher(tmp_path_factory):
    """Create a RAGSearcher using a temp dir so it doesn't pollute project."""
    tmp = tmp_path_factory.mktemp("chroma_test")
    rag = RAGSearcher(persist_dir=str(tmp))
    rag.index_spider()
    return rag


def test_index_populated(searcher: RAGSearcher):
    """After indexing, ChromaDB should have >0 examples."""
    assert searcher.is_populated


def test_search_returns_results(searcher: RAGSearcher):
    """A query should return k results, each with question + sql."""
    results = searcher.search("Show me all customers", k=3)
    assert len(results) == 3
    for r in results:
        assert "question" in r
        assert "sql" in r
        assert "distance" in r


def test_format_examples(searcher: RAGSearcher):
    """format_examples should produce a readable text block."""
    results = searcher.search("How many employees are there?", k=2)
    text = searcher.format_examples(results)
    assert "Example 1:" in text
    assert "Q:" in text
    assert "SQL:" in text
