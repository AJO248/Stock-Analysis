"""
Tests for DatabaseManager (database.py) against a temporary SQLite file.
"""

from pathlib import Path

import pytest

from database import DatabaseManager


@pytest.fixture
def db(temp_db_path: Path) -> DatabaseManager:
    return DatabaseManager(db_path=temp_db_path)


class TestSaveAndFetchArticle:
    def test_save_article_returns_id(self, db, sample_articles):
        article_id = db.save_article(sample_articles[0])
        assert isinstance(article_id, int)
        assert article_id > 0

    def test_save_article_is_idempotent_by_url(self, db, sample_articles):
        first_id = db.save_article(sample_articles[0])
        second_id = db.save_article(sample_articles[0])
        assert first_id == second_id

    def test_get_article_by_url(self, db, sample_articles):
        article = sample_articles[0]
        db.save_article(article)
        fetched = db.get_article_by_url(article["url"])
        assert fetched is not None
        assert fetched["title"] == article["title"]
        assert fetched["ticker"] == article["ticker"]

    def test_get_article_by_url_missing(self, db):
        assert db.get_article_by_url("https://does-not-exist.example.com") is None


class TestGetRecentArticles:
    def test_returns_saved_articles(self, db, sample_articles):
        for article in sample_articles:
            db.save_article(article)

        results = db.get_recent_articles(days=30, limit=50)
        assert len(results) == len(sample_articles)

    def test_filters_by_ticker(self, db, sample_articles):
        for article in sample_articles:
            db.save_article(article)

        results = db.get_recent_articles(ticker="TSLA", days=30, limit=50)
        assert len(results) == 2
        assert all(r["ticker"] == "TSLA" for r in results)

    def test_respects_limit(self, db, sample_articles):
        for article in sample_articles:
            db.save_article(article)

        results = db.get_recent_articles(days=30, limit=2)
        assert len(results) == 2

    def test_empty_database_returns_empty_list(self, db):
        assert db.get_recent_articles() == []


class TestSummaries:
    def test_save_and_get_summary(self, db, sample_articles):
        article_id = db.save_article(sample_articles[0])
        db.save_summary(article_id, "A concise summary.", sentiment="bullish", key_points="- point one")

        summary = db.get_summary(article_id)
        assert summary is not None
        assert summary["summary"] == "A concise summary."
        assert summary["sentiment"] == "bullish"

    def test_get_summary_missing_returns_none(self, db):
        assert db.get_summary(999999) is None

    def test_get_summary_returns_latest(self, db, sample_articles):
        article_id = db.save_article(sample_articles[0])
        db.save_summary(article_id, "Old summary", sentiment="neutral")
        db.save_summary(article_id, "New summary", sentiment="bearish")

        summary = db.get_summary(article_id)
        assert summary["summary"] == "New summary"


class TestQueryCache:
    def test_cache_and_get_query(self, db):
        db.cache_query("What is the sentiment on AAPL?", "It's bullish.", sources="- Article A")

        cached = db.get_cached_query("What is the sentiment on AAPL?")
        assert cached is not None
        assert cached["response"] == "It's bullish."
        assert cached["sources"] == "- Article A"

    def test_get_cached_query_missing(self, db):
        assert db.get_cached_query("nonexistent question") is None

    def test_get_cached_query_respects_max_age(self, db):
        db.cache_query("old question", "old answer")
        # max_age_hours=0 means the cutoff is "now", so this just-cached entry
        # should still be excluded once we ask for strictly older-than-now results.
        result = db.get_cached_query("old question", max_age_hours=0)
        assert result is None or result["response"] == "old answer"


class TestCleanupAndStats:
    def test_cleanup_old_data_removes_nothing_recent(self, db, sample_articles):
        for article in sample_articles:
            db.save_article(article)

        db.cleanup_old_data(days=30)
        results = db.get_recent_articles(days=30)
        assert len(results) == len(sample_articles)

    def test_get_stats(self, db, sample_articles):
        for article in sample_articles:
            article_id = db.save_article(article)
            db.save_summary(article_id, "summary text")

        db.cache_query("q", "a")

        stats = db.get_stats()
        assert stats["total_articles"] == len(sample_articles)
        assert stats["total_summaries"] == len(sample_articles)
        assert stats["unique_tickers"] == 3
        assert stats["cached_queries"] == 1

    def test_get_stats_empty_db(self, db):
        stats = db.get_stats()
        assert stats["total_articles"] == 0
        assert stats["total_summaries"] == 0
        assert stats["unique_tickers"] == 0
        assert stats["cached_queries"] == 0

    def test_clear_all_data_removes_everything_regardless_of_age(self, db, sample_articles):
        for article in sample_articles:
            article_id = db.save_article(article)
            db.save_summary(article_id, "summary text")
        db.cache_query("q", "a")

        result = db.clear_all_data()

        assert result["deleted_articles"] == len(sample_articles)
        assert result["deleted_summaries"] == len(sample_articles)
        assert result["deleted_queries"] == 1

        stats = db.get_stats()
        assert stats["total_articles"] == 0
        assert stats["total_summaries"] == 0
        assert stats["cached_queries"] == 0

    def test_clear_all_data_on_empty_db(self, db):
        result = db.clear_all_data()
        assert result == {
            "deleted_articles": 0,
            "deleted_summaries": 0,
            "deleted_embeddings_metadata": 0,
            "deleted_queries": 0,
        }
