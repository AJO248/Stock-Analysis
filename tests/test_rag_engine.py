"""
Tests for RAGQueryEngine (rag_engine.py).

Builds a real FAISS index from a handful of fixture articles using a
deterministic fake embeddings client (see conftest.FakeEmbeddings) - no
network calls to an embeddings API. The chat LLM is mocked so no
OpenAI-compatible API key or network access is required for
query()/conversation-memory tests either.
"""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import config
from database import DatabaseManager
from rag_engine import RAGQueryEngine


@pytest.fixture
def rag_db(temp_db_path: Path) -> DatabaseManager:
    return DatabaseManager(db_path=temp_db_path)


@pytest.fixture
def built_engine(tmp_path: Path, rag_db, sample_articles, fake_embeddings, monkeypatch):
    """A RAGQueryEngine with a real FAISS index built from sample_articles."""
    monkeypatch.setattr(config, "VECTOR_STORE_PATH", tmp_path / "vector_store")

    engine = RAGQueryEngine(db_manager=rag_db, api_key="test-key")
    engine.vector_store_path = config.VECTOR_STORE_PATH
    engine._embeddings = fake_embeddings  # bypass the real embeddings API

    for article in sample_articles:
        article["id"] = rag_db.save_article(article)

    engine.build_vector_store(articles=sample_articles, force_rebuild=True)
    return engine


class TestBuildVectorStore:
    def test_vector_store_is_built(self, built_engine):
        assert built_engine.vector_store is not None

    def test_index_persisted_to_disk(self, built_engine):
        assert (built_engine.vector_store_path / "index.faiss").exists()


class TestClearVectorStore:
    def test_clear_removes_index_files_and_resets_state(self, built_engine):
        assert (built_engine.vector_store_path / "index.faiss").exists()

        built_engine.clear_vector_store()

        assert not (built_engine.vector_store_path / "index.faiss").exists()
        assert not (built_engine.vector_store_path / "index.pkl").exists()
        assert built_engine.vector_store is None

    def test_clear_also_resets_conversation_memory(self, built_engine):
        built_engine.memory.save_context({"question": "Q"}, {"answer": "A"})
        assert len(built_engine.memory.chat_memory.messages) > 0

        built_engine.clear_vector_store()

        assert len(built_engine.memory.chat_memory.messages) == 0


class TestRetrieval:
    def test_retrieves_topically_relevant_articles_for_apple_query(self, built_engine):
        results = built_engine.get_relevant_articles("Tell me about Apple iPhone sales", k=3)

        assert len(results) > 0
        tickers = [r["ticker"] for r in results]
        # Apple-related chunks should dominate the top results for an Apple-specific query
        assert "AAPL" in tickers

    def test_retrieves_topically_relevant_articles_for_tesla_query(self, built_engine):
        results = built_engine.get_relevant_articles("What's going on with Tesla deliveries?", k=3)

        assert len(results) > 0
        tickers = [r["ticker"] for r in results]
        assert "TSLA" in tickers

    def test_retrieve_relevant_docs_returns_documents(self, built_engine):
        docs = built_engine._retrieve_relevant_docs("Microsoft Azure cloud growth", k=2)
        assert len(docs) > 0
        assert any(doc.metadata.get("ticker") == "MSFT" for doc in docs)

    def test_get_relevant_articles_without_index_raises(self, rag_db):
        engine = RAGQueryEngine(db_manager=rag_db, api_key="test-key")
        from exceptions import VectorStoreError
        with pytest.raises(VectorStoreError):
            engine.get_relevant_articles("anything")


class TestQueryWithMockedLLM:
    def _mock_llm(self, engine, answer="This is a mocked answer."):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = SimpleNamespace(content=answer)
        engine.llm = mock_llm
        return mock_llm

    def test_query_returns_answer_and_sources(self, built_engine):
        self._mock_llm(built_engine)

        response = built_engine.query("What's happening with Apple?", use_cache=False)

        assert response["answer"] == "This is a mocked answer."
        assert response["from_cache"] is False
        assert "sources" in response

    def test_query_uses_cache_on_second_call(self, built_engine):
        self._mock_llm(built_engine)

        first = built_engine.query("What's happening with Apple?", use_cache=True)
        second = built_engine.query("What's happening with Apple?", use_cache=True)

        assert first["from_cache"] is False
        assert second["from_cache"] is True
        assert second["answer"] == first["answer"]

    def test_conversation_memory_round_trips(self, built_engine):
        mock_llm = self._mock_llm(built_engine)

        built_engine.query("What's happening with Apple?", use_conversation=True, use_cache=False)
        assert len(built_engine.memory.chat_memory.messages) == 2  # human + ai

        # Second call should include prior turn in the prompt sent to the LLM
        built_engine.query("And what about Tesla?", use_conversation=True, use_cache=False)
        second_call_prompt = mock_llm.invoke.call_args[0][0]
        assert "Previous conversation" in second_call_prompt
        assert len(built_engine.memory.chat_memory.messages) == 4

    def test_clear_conversation_history(self, built_engine):
        self._mock_llm(built_engine)
        built_engine.query("What's happening with Apple?", use_conversation=True, use_cache=False)
        assert len(built_engine.memory.chat_memory.messages) > 0

        built_engine.clear_conversation_history()
        assert len(built_engine.memory.chat_memory.messages) == 0
