"""
Tests for StockPortfolio (stock_tracker.py). yfinance.Ticker is mocked so no
network calls are made.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from stock_tracker import StockPortfolio


@pytest.fixture
def portfolio_file(tmp_path: Path) -> Path:
    return tmp_path / "portfolio.json"


@pytest.fixture
def portfolio(portfolio_file: Path) -> StockPortfolio:
    # Starts empty on disk -> falls back to config.DEFAULT_TICKERS on first load,
    # but we don't rely on those tickers in the tests below.
    return StockPortfolio(portfolio_file=portfolio_file)


def _make_history_df(closes):
    return pd.DataFrame({"Close": closes})


class TestAddStock:
    def test_add_valid_new_ticker(self, portfolio):
        mock_ticker = MagicMock()
        mock_ticker.info = {"symbol": "NVDA"}

        with patch("stock_tracker.yf.Ticker", return_value=mock_ticker):
            assert portfolio.add_stock("NVDA") is True
        assert "NVDA" in portfolio.get_portfolio()

    def test_add_invalid_ticker_format_rejected(self, portfolio):
        assert portfolio.add_stock("not-a-ticker!!") is False

    def test_add_duplicate_ticker_rejected(self, portfolio):
        mock_ticker = MagicMock()
        mock_ticker.info = {"symbol": "NVDA"}

        with patch("stock_tracker.yf.Ticker", return_value=mock_ticker):
            portfolio.add_stock("NVDA")
            assert portfolio.add_stock("NVDA") is False

    def test_add_ticker_not_found_in_yfinance(self, portfolio):
        mock_ticker = MagicMock()
        mock_ticker.info = {}

        with patch("stock_tracker.yf.Ticker", return_value=mock_ticker):
            assert portfolio.add_stock("FAKE1") is False

    def test_add_stock_network_error_returns_false(self, portfolio):
        with patch("stock_tracker.yf.Ticker", side_effect=requests.exceptions.ConnectionError("network down")):
            assert portfolio.add_stock("NVDA") is False


class TestRemoveStock:
    def test_remove_existing_ticker(self, portfolio):
        mock_ticker = MagicMock()
        mock_ticker.info = {"symbol": "NVDA"}
        with patch("stock_tracker.yf.Ticker", return_value=mock_ticker):
            portfolio.add_stock("NVDA")

        assert portfolio.remove_stock("NVDA") is True
        assert "NVDA" not in portfolio.get_portfolio()

    def test_remove_nonexistent_ticker_returns_false(self, portfolio):
        assert portfolio.remove_stock("ZZZZ") is False


class TestFetchStockData:
    def test_fetch_stock_data_success(self, portfolio):
        mock_ticker = MagicMock()
        mock_ticker.info = {
            "longName": "NVIDIA Corporation",
            "previousClose": 100.0,
            "open": 101.0,
            "dayHigh": 105.0,
            "dayLow": 99.0,
            "volume": 1000000,
            "marketCap": 2_000_000_000,
            "sector": "Technology",
            "industry": "Semiconductors",
        }
        mock_ticker.history.return_value = _make_history_df([98.0, 110.0])

        with patch("stock_tracker.yf.Ticker", return_value=mock_ticker):
            data = portfolio.fetch_stock_data("NVDA", use_cache=False)

        assert data is not None
        assert data["ticker"] == "NVDA"
        assert data["current_price"] == 110.0
        assert data["previous_close"] == 100.0
        assert round(data["percent_change"], 2) == 10.0

    def test_fetch_stock_data_empty_history_returns_none(self, portfolio):
        mock_ticker = MagicMock()
        mock_ticker.info = {}
        mock_ticker.history.return_value = pd.DataFrame()

        with patch("stock_tracker.yf.Ticker", return_value=mock_ticker):
            assert portfolio.fetch_stock_data("NVDA", use_cache=False) is None

    def test_fetch_stock_data_network_error_returns_none(self, portfolio):
        with patch("stock_tracker.yf.Ticker", side_effect=requests.exceptions.ConnectionError("network down")):
            assert portfolio.fetch_stock_data("NVDA", use_cache=False) is None

    def test_fetch_stock_data_uses_cache(self, portfolio):
        mock_ticker = MagicMock()
        mock_ticker.info = {"previousClose": 100.0}
        mock_ticker.history.return_value = _make_history_df([98.0, 105.0])

        with patch("stock_tracker.yf.Ticker", return_value=mock_ticker) as mock_yf:
            first = portfolio.fetch_stock_data("NVDA", use_cache=True)
            second = portfolio.fetch_stock_data("NVDA", use_cache=True)

        assert first == second
        # yf.Ticker should only have been constructed once thanks to caching
        assert mock_yf.call_count == 1
