# app/rag_builder.py
"""
Search-Based Prompting (RAG) — Phase 1.

Loads Spider NL-to-SQL pairs into a local ChromaDB vector database
and retrieves the most similar examples at query time.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SPIDER_TRAIN = _PROJECT_ROOT / "spider_data" / "train_spider.json"
_CHROMA_DIR = _PROJECT_ROOT / "chroma_db"
_COLLECTION_NAME = "spider_examples"
_DEFAULT_K = 3


def _load_spider_pairs(path: Path) -> list[dict]:
    """Read Spider JSON and return list of {question, sql} dicts."""
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [
        {"question": item["question"], "sql": item["query"]}
        for item in raw
        if item.get("question") and item.get("query")
    ]


class RAGSearcher:
    """Thin wrapper around ChromaDB for NL-to-SQL example retrieval."""

    def __init__(self, persist_dir: str | None = None) -> None:
        self._persist_dir = persist_dir or str(_CHROMA_DIR)
        self._ef = embedding_functions.DefaultEmbeddingFunction()
        self._client = chromadb.PersistentClient(path=self._persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            embedding_function=self._ef,
        )

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------
    @property
    def is_populated(self) -> bool:
        return self._collection.count() > 0

    def index_spider(self, path: Path | None = None) -> int:
        """Load Spider train set into ChromaDB if not already indexed."""
        if self.is_populated:
            logger.info(
                "ChromaDB already has %d examples, skipping indexing.",
                self._collection.count(),
            )
            return self._collection.count()

        src = path or _SPIDER_TRAIN
        pairs = _load_spider_pairs(src)
        logger.info("Indexing %d Spider examples into ChromaDB …", len(pairs))

        # ChromaDB add in batches of 500
        batch_size = 500
        for start in range(0, len(pairs), batch_size):
            batch = pairs[start : start + batch_size]
            self._collection.add(
                ids=[f"spider_{start + i}" for i in range(len(batch))],
                documents=[p["question"] for p in batch],
                metadatas=[{"sql": p["sql"]} for p in batch],
            )

        logger.info("Indexing complete — %d examples.", self._collection.count())
        return self._collection.count()

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------
    def search(self, query: str, k: int = _DEFAULT_K) -> list[dict]:
        """
        Return the top-k most similar NL-SQL pairs for *query*.

        Each result is a dict with keys: question, sql, distance.
        """
        if not self.is_populated:
            return []

        results = self._collection.query(
            query_texts=[query],
            n_results=k,
        )

        examples: list[dict] = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            examples.append(
                {"question": doc, "sql": meta["sql"], "distance": dist}
            )
        return examples

    def format_examples(self, examples: list[dict]) -> str:
        """Format retrieved examples as a text block for prompt injection."""
        if not examples:
            return ""
        lines: list[str] = []
        for i, ex in enumerate(examples, 1):
            lines.append(f"Example {i}:")
            lines.append(f"  Q: {ex['question']}")
            lines.append(f"  SQL: {ex['sql']}")
            lines.append("")
        return "\n".join(lines)
