"""
Utility functions for the stock analysis platform.
"""

import time
import re
from datetime import datetime, timedelta
from typing import Optional, Callable, Any
from functools import wraps
from urllib.parse import urlparse

from logger import get_logger
from exceptions import APILimitError, NetworkError

logger = get_logger("utils")


def validate_ticker(ticker: str) -> bool:
    """
    Validate stock ticker symbol format.
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        True if valid, False otherwise
    """
    if not ticker:
        return False
    
    # Basic validation: 1-5 uppercase letters, may contain dots or hyphens
    pattern = r'^[A-Z]{1,5}(\.[A-Z])?$'
    return bool(re.match(pattern, ticker.upper()))


def clean_text(text: str) -> str:
    """
    Clean and normalize text by removing extra whitespace.
    
    Args:
        text: Input text
    
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL string
    
    Returns:
        True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse various date string formats to datetime object.
    
    Args:
        date_str: Date string in various formats
    
    Returns:
        datetime object or None if parsing fails
    """
    if not date_str:
        return None
    
    # Common date formats
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%a, %d %b %Y %H:%M:%S %Z",  # RSS format
        "%a, %d %b %Y %H:%M:%S %z",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    logger.warning(f"Could not parse date: {date_str}")
    return None


def format_date(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime object to string.
    
    Args:
        dt: datetime object
        format_str: Output format string
    
    Returns:
        Formatted date string
    """
    if not dt:
        return ""
    return dt.strftime(format_str)


def is_recent(dt: datetime, days: int = 7) -> bool:
    """
    Check if datetime is within the specified number of days from now.
    
    Args:
        dt: datetime object to check
        days: Number of days to consider as recent
    
    Returns:
        True if recent, False otherwise
    """
    if not dt:
        return False
    
    now = datetime.now()
    cutoff = now - timedelta(days=days)
    
    # Handle timezone-aware datetimes
    if dt.tzinfo is not None:
        from datetime import timezone
        cutoff = cutoff.replace(tzinfo=timezone.utc)
    
    return dt >= cutoff


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exceptions to catch and retry
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retries = 0
            delay = base_delay
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}")
                        raise
                    
                    # Check if it's a rate limit error
                    if isinstance(e, APILimitError):
                        logger.warning(f"Rate limit hit in {func.__name__}, waiting {delay}s")
                    else:
                        logger.warning(f"Retry {retries}/{max_retries} for {func.__name__}: {e}")
                    
                    time.sleep(delay)
                    delay = min(delay * exponential_base, max_delay)
            
        return wrapper
    return decorator


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Truncate text to specified length.
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to append if truncated
    
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def extract_ticker_from_url(url: str) -> Optional[str]:
    """
    Extract stock ticker from URL if present.
    
    Args:
        url: URL string
    
    Returns:
        Ticker symbol or None
    """
    # Pattern to match common ticker formats in URLs
    patterns = [
        r'/quote/([A-Z]{1,5})',
        r'/symbol/([A-Z]{1,5})',
        r'/stock/([A-Z]{1,5})',
        r'ticker=([A-Z]{1,5})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    
    return None


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """
    Calculate percentage change between two values.
    
    Args:
        old_value: Original value
        new_value: New value
    
    Returns:
        Percentage change
    """
    if old_value == 0:
        return 0.0
    
    return ((new_value - old_value) / old_value) * 100


def format_currency(amount: float, currency: str = "$") -> str:
    """
    Format number as currency string.
    
    Args:
        amount: Amount to format
        currency: Currency symbol
    
    Returns:
        Formatted currency string
    """
    return f"{currency}{amount:,.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format number as percentage string.
    
    Args:
        value: Value to format
        decimals: Number of decimal places
    
    Returns:
        Formatted percentage string
    """
    return f"{value:.{decimals}f}%"
