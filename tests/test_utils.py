"""
Tests for pure utility functions in utils.py. No mocking needed.
"""

import pytest

from utils import (
    format_currency,
    format_percentage,
    validate_ticker,
    calculate_percentage_change,
)


class TestFormatCurrency:
    def test_positive_amount(self):
        assert format_currency(1234.5) == "$1,234.50"

    def test_zero(self):
        assert format_currency(0) == "$0.00"

    def test_negative_amount(self):
        assert format_currency(-99.999) == "$-100.00"

    def test_custom_currency_symbol(self):
        assert format_currency(10, currency="€") == "€10.00"


class TestFormatPercentage:
    def test_positive_value(self):
        assert format_percentage(12.345) == "12.35%"

    def test_zero(self):
        assert format_percentage(0) == "0.00%"

    def test_negative_value(self):
        assert format_percentage(-5.1) == "-5.10%"

    def test_custom_decimals(self):
        assert format_percentage(3.14159, decimals=3) == "3.142%"


class TestValidateTicker:
    @pytest.mark.parametrize("ticker", ["AAPL", "MSFT", "A", "TSLA", "goog"])
    def test_valid_tickers(self, ticker):
        assert validate_ticker(ticker) is True

    @pytest.mark.parametrize("ticker", ["", "TOOLONGTICKER", "123", "AA PL", None])
    def test_invalid_tickers(self, ticker):
        assert validate_ticker(ticker) is False

    def test_ticker_with_dot_suffix(self):
        assert validate_ticker("BRK.A") is True


class TestCalculatePercentageChange:
    def test_increase(self):
        assert calculate_percentage_change(100, 110) == 10.0

    def test_decrease(self):
        assert calculate_percentage_change(100, 90) == -10.0

    def test_no_change(self):
        assert calculate_percentage_change(50, 50) == 0.0

    def test_zero_old_value_avoids_division_error(self):
        assert calculate_percentage_change(0, 100) == 0.0
