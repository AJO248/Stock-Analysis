"""
Stock portfolio tracker module.
Manages portfolio of stocks and fetches real-time data using yfinance.
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

import yfinance as yf
import pandas as pd

import config
from logger import get_logger
from exceptions import PortfolioError
from utils import validate_ticker, format_currency, format_percentage, calculate_percentage_change

logger = get_logger("stock_tracker")


class StockPortfolio:
    """Manages a portfolio of stocks with data caching."""
    
    def __init__(self, portfolio_file: Path = None):
        """
        Initialize stock portfolio.
        
        Args:
            portfolio_file: Path to portfolio JSON file
        """
        self.portfolio_file = portfolio_file or config.PORTFOLIO_FILE
        self.portfolio_file.parent.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self.load_portfolio()
    
    def load_portfolio(self):
        """Load portfolio from file or initialize with default tickers."""
        try:
            if self.portfolio_file.exists():
                with open(self.portfolio_file, 'r') as f:
                    data = json.load(f)
                    self.tickers = data.get('tickers', [])
                    logger.info(f"Loaded portfolio with {len(self.tickers)} tickers")
            else:
                # Initialize with default tickers
                self.tickers = config.DEFAULT_TICKERS.copy()
                self.save_portfolio()
                logger.info(f"Initialized new portfolio with default tickers")
        
        except Exception as e:
            logger.error(f"Failed to load portfolio: {e}")
            self.tickers = config.DEFAULT_TICKERS.copy()
    
    def save_portfolio(self):
        """Save portfolio to file."""
        try:
            data = {
                'tickers': self.tickers,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.portfolio_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug("Portfolio saved successfully")
        
        except Exception as e:
            raise PortfolioError(f"Failed to save portfolio: {e}")
    
    def add_stock(self, ticker: str) -> bool:
        """
        Add a stock to the portfolio.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            True if added successfully, False otherwise
        """
        ticker = ticker.upper()
        
        if not validate_ticker(ticker):
            logger.warning(f"Invalid ticker format: {ticker}")
            return False
        
        if ticker in self.tickers:
            logger.info(f"Ticker {ticker} already in portfolio")
            return False
        
        # Verify ticker exists by trying to fetch data
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            if not info or 'symbol' not in info:
                logger.warning(f"Ticker {ticker} not found in yfinance")
                return False
        except Exception as e:
            logger.error(f"Failed to verify ticker {ticker}: {e}")
            return False
        
        self.tickers.append(ticker)
        self.save_portfolio()
        logger.info(f"Added {ticker} to portfolio")
        return True
    
    def remove_stock(self, ticker: str) -> bool:
        """
        Remove a stock from the portfolio.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            True if removed successfully, False otherwise
        """
        ticker = ticker.upper()
        
        if ticker not in self.tickers:
            logger.warning(f"Ticker {ticker} not in portfolio")
            return False
        
        self.tickers.remove(ticker)
        self.save_portfolio()
        
        # Clear cache for removed ticker
        if ticker in self._cache:
            del self._cache[ticker]
            del self._cache_timestamps[ticker]
        
        logger.info(f"Removed {ticker} from portfolio")
        return True
    
    def get_portfolio(self) -> List[str]:
        """
        Get list of tickers in portfolio.
        
        Returns:
            List of ticker symbols
        """
        return self.tickers.copy()
    
    def _is_cache_valid(self, ticker: str) -> bool:
        """Check if cached data is still valid."""
        if ticker not in self._cache_timestamps:
            return False
        
        age = datetime.now() - self._cache_timestamps[ticker]
        return age.total_seconds() < config.STOCK_CACHE_DURATION
    
    def fetch_stock_data(self, ticker: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Fetch current stock data for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            use_cache: Whether to use cached data if available
        
        Returns:
            Dictionary with stock data or None if fetch fails
        """
        ticker = ticker.upper()
        
        # Check cache first
        if use_cache and self._is_cache_valid(ticker):
            logger.debug(f"Using cached data for {ticker}")
            return self._cache[ticker]
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get historical data for change calculation
            hist = stock.history(period="5d")
            
            if hist.empty:
                logger.warning(f"No historical data available for {ticker}")
                return None
            
            current_price = hist['Close'].iloc[-1]
            previous_close = info.get('previousClose', hist['Close'].iloc[-2] if len(hist) > 1 else current_price)
            
            # Calculate changes
            price_change = current_price - previous_close
            percent_change = calculate_percentage_change(previous_close, current_price)
            
            # Prepare stock data
            stock_data = {
                'ticker': ticker,
                'name': info.get('longName', info.get('shortName', ticker)),
                'current_price': float(current_price),
                'previous_close': float(previous_close),
                'price_change': float(price_change),
                'percent_change': float(percent_change),
                'open': float(info.get('open', info.get('regularMarketOpen', current_price))),
                'high': float(info.get('dayHigh', info.get('regularMarketDayHigh', current_price))),
                'low': float(info.get('dayLow', info.get('regularMarketDayLow', current_price))),
                'volume': int(info.get('volume', info.get('regularMarketVolume', 0))),
                'market_cap': info.get('marketCap', 0),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'last_updated': datetime.now().isoformat()
            }
            
            # Update cache
            self._cache[ticker] = stock_data
            self._cache_timestamps[ticker] = datetime.now()
            
            logger.debug(f"Fetched data for {ticker}: ${current_price:.2f} ({percent_change:+.2f}%)")
            return stock_data
        
        except Exception as e:
            logger.error(f"Failed to fetch data for {ticker}: {e}")
            return None
    
    def fetch_current_prices(self, use_cache: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        Fetch current prices for all stocks in portfolio.
        
        Args:
            use_cache: Whether to use cached data if available
        
        Returns:
            Dictionary mapping tickers to their data
        """
        results = {}
        
        for ticker in self.tickers:
            stock_data = self.fetch_stock_data(ticker, use_cache=use_cache)
            if stock_data:
                results[ticker] = stock_data
        
        logger.info(f"Fetched data for {len(results)}/{len(self.tickers)} stocks")
        return results
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get summary of entire portfolio.
        
        Returns:
            Dictionary with portfolio summary statistics
        """
        portfolio_data = self.fetch_current_prices()
        
        if not portfolio_data:
            return {
                'total_stocks': 0,
                'total_value': 0,
                'gainers': [],
                'losers': [],
                'last_updated': datetime.now().isoformat()
            }
        
        # Calculate gainers and losers
        gainers = []
        losers = []
        
        for ticker, data in portfolio_data.items():
            if data['percent_change'] > 0:
                gainers.append((ticker, data['percent_change']))
            elif data['percent_change'] < 0:
                losers.append((ticker, data['percent_change']))
        
        # Sort by percentage change
        gainers.sort(key=lambda x: x[1], reverse=True)
        losers.sort(key=lambda x: x[1])
        
        summary = {
            'total_stocks': len(portfolio_data),
            'stocks': portfolio_data,
            'gainers': gainers[:5],  # Top 5 gainers
            'losers': losers[:5],  # Top 5 losers
            'last_updated': datetime.now().isoformat()
        }
        
        return summary
    
    def get_historical_data(self, ticker: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        """
        Get historical price data for a stock.
        
        Args:
            ticker: Stock ticker symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        
        Returns:
            DataFrame with historical data or None if fetch fails
        """
        ticker = ticker.upper()
        
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            
            if hist.empty:
                logger.warning(f"No historical data for {ticker} (period: {period})")
                return None
            
            logger.debug(f"Fetched {len(hist)} historical records for {ticker}")
            return hist
        
        except Exception as e:
            logger.error(f"Failed to fetch historical data for {ticker}: {e}")
            return None


# Convenience functions
def get_stock_info(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Get comprehensive information about a stock.
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Dictionary with stock information
    """
    try:
        stock = yf.Ticker(ticker.upper())
        return stock.info
    except Exception as e:
        logger.error(f"Failed to get info for {ticker}: {e}")
        return None
