"""
Shared pytest fixtures for the Stock-Analysis test suite.
"""

from pathlib import Path

import pytest


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Path to a throwaway SQLite database file for a single test."""
    return tmp_path / "test_news_cache.db"


@pytest.fixture
def sample_articles():
    """A handful of representative article dicts, covering two distinct topics/tickers."""
    return [
        {
            "ticker": "AAPL",
            "title": "Apple posts record iPhone sales, beats analyst estimates",
            "url": "https://example.com/news/aapl-record-sales",
            "summary": "Apple reported record-breaking iPhone sales this quarter, "
                       "driven by strong demand in international markets.",
            "content": "Apple Inc. announced quarterly earnings that beat Wall Street "
                       "expectations, with iPhone revenue climbing 15% year-over-year. "
                       "The company cited strong demand in China and India.",
            "source": "TestWire",
            "published_date": "2024-01-15T09:00:00",
        },
        {
            "ticker": "AAPL",
            "title": "Apple unveils new AI features for iOS",
            "url": "https://example.com/news/aapl-ai-features",
            "summary": "Apple announced a suite of new on-device AI features coming to iOS.",
            "content": "Apple revealed new machine learning capabilities that will ship "
                       "with the next iOS update, focusing on privacy-preserving AI "
                       "running locally on iPhone hardware.",
            "source": "TestWire",
            "published_date": "2024-01-16T09:00:00",
        },
        {
            "ticker": "TSLA",
            "title": "Tesla stock drops after missing delivery targets",
            "url": "https://example.com/news/tsla-delivery-miss",
            "summary": "Tesla shares fell sharply after the company missed quarterly "
                       "delivery targets amid weakening EV demand.",
            "content": "Tesla reported vehicle deliveries below analyst expectations, "
                       "sending shares down over 8% in early trading. Analysts pointed "
                       "to increased competition in the EV market.",
            "source": "TestWire",
            "published_date": "2024-01-17T09:00:00",
        },
        {
            "ticker": "TSLA",
            "title": "Tesla faces new regulatory scrutiny over Autopilot",
            "url": "https://example.com/news/tsla-autopilot-probe",
            "summary": "Regulators opened a new investigation into Tesla's Autopilot "
                       "system following a series of accidents.",
            "content": "Federal safety regulators announced an expanded probe into "
                       "Tesla's driver-assistance software after reviewing crash reports "
                       "involving the Autopilot feature.",
            "source": "TestWire",
            "published_date": "2024-01-18T09:00:00",
        },
        {
            "ticker": "MSFT",
            "title": "Microsoft cloud revenue accelerates on AI demand",
            "url": "https://example.com/news/msft-cloud-ai",
            "summary": "Microsoft's Azure cloud division posted accelerating growth, "
                       "fueled by enterprise AI adoption.",
            "content": "Microsoft reported Azure revenue growth of 30%, ahead of "
                       "estimates, as enterprise customers ramped up spending on "
                       "generative AI services built on the platform.",
            "source": "TestWire",
            "published_date": "2024-01-19T09:00:00",
        },
    ]
