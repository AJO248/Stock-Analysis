"""
News scraper module for collecting financial news from Finnhub API.
"""

import time
from datetime import datetime
from typing import List, Dict, Any, Optional

import requests

import config
from logger import get_logger
from exceptions import ScraperError, NetworkError, ParsingError
from utils import clean_text, validate_url, parse_date, retry_with_backoff
from database import DatabaseManager

logger = get_logger("news_scraper")


class BaseScraper:
    """Base class for news scrapers."""
    
    def __init__(self, db_manager: DatabaseManager = None):
        """
        Initialize scraper.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager or DatabaseManager()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': config.USER_AGENT})
    
    def _make_request(self, url: str, timeout: int = 30) -> requests.Response:
        """
        Make HTTP request with error handling.
        
        Args:
            url: URL to fetch
            timeout: Request timeout in seconds
        
        Returns:
            Response object
        
        Raises:
            NetworkError: If request fails
        """
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout:
            raise NetworkError(f"Request timeout: {url}")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Request failed: {e}")
    
    def scrape(self, ticker: str) -> List[Dict[str, Any]]:
        """
        Scrape news for a ticker. Must be implemented by subclasses.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            List of article dictionaries
        """
        raise NotImplementedError("Subclasses must implement scrape()")


class FinnhubScraper(BaseScraper):
    """Scraper for Finnhub API - Reliable stock news source."""
    
    def __init__(self, db_manager: DatabaseManager = None):
        super().__init__(db_manager)
        self.source_name = "Finnhub"
        self.rate_limit = config.NEWS_SOURCES['finnhub']['rate_limit']
        self.api_key = config.FINNHUB_API_KEY
        
        if not self.api_key:
            logger.warning("Finnhub API key not configured")
    
    def scrape(self, ticker: str) -> List[Dict[str, Any]]:
        """
        Fetch company news from Finnhub API.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            List of article dictionaries
        """
        if not self.api_key:
            logger.warning("Finnhub API key not set, skipping scrape")
            return []
        
        ticker = ticker.upper()
        logger.info(f"Fetching news from Finnhub for {ticker}")
        
        try:
            import finnhub
            
            # Initialize Finnhub client
            finnhub_client = finnhub.Client(api_key=self.api_key)
            
            # Get company news from last 7 days
            from datetime import datetime, timedelta
            to_date = datetime.now()
            from_date = to_date - timedelta(days=config.ARTICLE_MAX_AGE_DAYS)
            
            # Fetch news
            news_items = finnhub_client.company_news(
                ticker,
                _from=from_date.strftime('%Y-%m-%d'),
                to=to_date.strftime('%Y-%m-%d')
            )
            
            articles = []
            
            # Process news items
            for item in news_items[:config.MAX_ARTICLES_PER_STOCK]:
                try:
                    article = self._parse_finnhub_article(item, ticker)
                    if article and validate_url(article['url']):
                        # Check if article already exists
                        existing = self.db_manager.get_article_by_url(article['url'])
                        if not existing:
                            article_id = self.db_manager.save_article(article)
                            article['id'] = article_id
                            articles.append(article)
                        else:
                            logger.debug(f"Article already in DB: {article['url']}")
                
                except Exception as e:
                    logger.warning(f"Failed to parse Finnhub article: {e}")
                    continue
            
            logger.info(f"Scraped {len(articles)} new articles for {ticker} from Finnhub")
            time.sleep(self.rate_limit)  # Respect rate limiting
            
            return articles
        
        except ImportError:
            logger.error("finnhub-python package not installed. Run: pip install finnhub-python")
            return []
        except Exception as e:
            logger.error(f"Finnhub API error for {ticker}: {e}")
            return []
    
    def _parse_finnhub_article(self, item: Dict[str, Any], ticker: str) -> Optional[Dict[str, Any]]:
        """
        Parse a Finnhub news item into article dictionary.
        
        Args:
            item: Finnhub news item
            ticker: Stock ticker
        
        Returns:
            Article dictionary or None
        """
        try:
            # Finnhub returns timestamp in Unix format
            published_timestamp = item.get('datetime', 0)
            published_date = datetime.fromtimestamp(published_timestamp) if published_timestamp else None
            
            article = {
                'ticker': ticker,
                'title': clean_text(item.get('headline', '')),
                'url': item.get('url', ''),
                'summary': clean_text(item.get('summary', '')),
                'content': clean_text(item.get('summary', '')),  # Finnhub provides summary
                'source': item.get('source', self.source_name),
                'published_date': published_date.isoformat() if published_date else None,
                'scraped_date': datetime.now().isoformat()
            }
            
            # Filter out articles without title or URL
            if not article['title'] or not article['url']:
                return None
            
            return article
        
        except Exception as e:
            logger.debug(f"Failed to parse Finnhub article: {e}")
            return None


class NewsAggregator:
    """Aggregates news from multiple sources."""
    
    def __init__(self, db_manager: DatabaseManager = None):
        """
        Initialize news aggregator.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager or DatabaseManager()
        self.scrapers = []
        
        # Initialize Finnhub scraper (only active scraper)
        if config.NEWS_SOURCES.get('finnhub', {}).get('enabled') and config.FINNHUB_API_KEY:
            self.scrapers.append(FinnhubScraper(self.db_manager))
        else:
            logger.warning("Finnhub scraper not configured. Set FINNHUB_API_KEY in .env file.")
        
        logger.info(f"Initialized NewsAggregator with {len(self.scrapers)} scraper(s)")
    
    def scrape_ticker(self, ticker: str) -> List[Dict[str, Any]]:
        """
        Scrape news for a ticker from all sources.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            List of all articles from all sources
        """
        all_articles = []
        
        for scraper in self.scrapers:
            try:
                articles = scraper.scrape(ticker)
                all_articles.extend(articles)
            except Exception as e:
                logger.error(f"Scraper {scraper.__class__.__name__} failed for {ticker}: {e}")
                continue
        
        logger.info(f"Total {len(all_articles)} new articles scraped for {ticker}")
        return all_articles
    
    def scrape_multiple_tickers(self, tickers: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scrape news for multiple tickers.
        
        Args:
            tickers: List of stock ticker symbols
        
        Returns:
            Dictionary mapping tickers to their articles
        """
        results = {}
        
        for ticker in tickers:
            try:
                articles = self.scrape_ticker(ticker)
                results[ticker] = articles
            except Exception as e:
                logger.error(f"Failed to scrape {ticker}: {e}")
                results[ticker] = []
        
        total_articles = sum(len(articles) for articles in results.values())
        logger.info(f"Scraped {total_articles} total articles for {len(tickers)} tickers")
        
        return results
