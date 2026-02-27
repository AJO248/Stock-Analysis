"""
Custom exceptions for the stock analysis platform.
"""


class StockAnalysisError(Exception):
    """Base exception for the stock analysis platform."""
    pass


class ConfigurationError(StockAnalysisError):
    """Raised when there's a configuration issue."""
    pass


class ScraperError(StockAnalysisError):
    """Raised when web scraping fails."""
    pass


class NetworkError(ScraperError):
    """Raised when network request fails."""
    pass


class ParsingError(ScraperError):
    """Raised when HTML parsing fails."""
    pass


class APILimitError(StockAnalysisError):
    """Raised when API rate limit is exceeded."""
    pass


class APIError(StockAnalysisError):
    """Raised when API call fails."""
    pass


class VectorStoreError(StockAnalysisError):
    """Raised when vector store operations fail."""
    pass


class DatabaseError(StockAnalysisError):
    """Raised when database operations fail."""
    pass


class PortfolioError(StockAnalysisError):
    """Raised when portfolio operations fail."""
    pass


class SummarizationError(StockAnalysisError):
    """Raised when text summarization fails."""
    pass
