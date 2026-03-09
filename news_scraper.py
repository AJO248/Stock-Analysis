"""
News scraper module for collecting financial news from various sources.
"""

import time
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

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


class YahooFinanceScraper(BaseScraper):
    """Scraper for Yahoo Finance news."""
    
    def __init__(self, db_manager: DatabaseManager = None):
        super().__init__(db_manager)
        self.source_name = "Yahoo Finance"
        self.rate_limit = config.NEWS_SOURCES['yahoo_finance']['rate_limit']
    
    @retry_with_backoff(max_retries=3, exceptions=(NetworkError, ParsingError))
    def scrape(self, ticker: str) -> List[Dict[str, Any]]:
        """
        Scrape Yahoo Finance news for a ticker.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            List of article dictionaries
        """
        ticker = ticker.upper()
        url = config.NEWS_SOURCES['yahoo_finance']['base_url'].format(ticker=ticker)
        
        logger.info(f"Scraping Yahoo Finance news for {ticker}")
        
        try:
            response = self._make_request(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = []
            
            # Find news articles - Yahoo Finance uses various selectors
            # Try multiple selectors as Yahoo's structure may change
            article_containers = (
                soup.find_all('li', class_=re.compile('js-stream-content')) or
                soup.find_all('div', class_=re.compile('Ov\\(h\\)')) or
                soup.find_all('div', {'data-test-locator': 'mega'}) or
                soup.find_all('h3')  # Fallback to h3 tags
            )
            
            for container in article_containers[:config.MAX_ARTICLES_PER_STOCK]:
                try:
                    article = self._parse_article(container, ticker)
                    if article and validate_url(article['url']):
                        # Check if article already exists in DB
                        existing = self.db_manager.get_article_by_url(article['url'])
                        if not existing:
                            article_id = self.db_manager.save_article(article)
                            article['id'] = article_id
                            articles.append(article)
                        else:
                            logger.debug(f"Article already in DB: {article['url']}")
                
                except Exception as e:
                    logger.warning(f"Failed to parse article container: {e}")
                    continue
            
            logger.info(f"Scraped {len(articles)} new articles for {ticker} from Yahoo Finance")
            time.sleep(self.rate_limit)  # Respect rate limiting
            
            return articles
        
        except NetworkError as e:
            logger.error(f"Network error scraping {ticker}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to scrape Yahoo Finance for {ticker}: {e}")
            raise ParsingError(f"Failed to parse Yahoo Finance page: {e}")
    
    def _parse_article(self, container, ticker: str) -> Optional[Dict[str, Any]]:
        """Parse article data from HTML container."""
        try:
            # Try to find title and link
            title_elem = (
                container.find('h3') or 
                container.find('a') or
                container
            )
            
            if not title_elem:
                return None
            
            # Extract link
            link_elem = title_elem.find('a') if title_elem.name != 'a' else title_elem
            if not link_elem:
                # Try parent
                link_elem = container.find('a')
            
            if not link_elem or not link_elem.get('href'):
                return None
            
            url = link_elem['href']
            if not url.startswith('http'):
                url = 'https://finance.yahoo.com' + url
            
            # Extract title
            title = clean_text(link_elem.get_text() or title_elem.get_text())
            if not title:
                return None
            
            # Try to extract summary/description
            summary_elem = container.find('p')
            summary = clean_text(summary_elem.get_text()) if summary_elem else ""
            
            # Try to extract published date
            time_elem = container.find('time')
            published_date = None
            if time_elem:
                date_str = time_elem.get('datetime') or time_elem.get_text()
                published_date = parse_date(date_str)
            
            article = {
                'ticker': ticker,
                'title': title,
                'url': url,
                'summary': summary,
                'content': summary,  # Will be expanded later if needed
                'source': self.source_name,
                'published_date': published_date.isoformat() if published_date else None,
                'scraped_date': datetime.now().isoformat()
            }
            
            return article
        
        except Exception as e:
            logger.debug(f"Failed to parse article: {e}")
            return None


class GoogleNewsScraper(BaseScraper):
    """Scraper for Google News RSS feeds."""
    
    def __init__(self, db_manager: DatabaseManager = None):
        super().__init__(db_manager)
        self.source_name = "Google News"
        self.rate_limit = config.NEWS_SOURCES['google_news']['rate_limit']
    
    @retry_with_backoff(max_retries=3, exceptions=(NetworkError, ParsingError))
    def scrape(self, ticker: str) -> List[Dict[str, Any]]:
        """
        Scrape Google News RSS feed for a ticker.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            List of article dictionaries
        """
        ticker = ticker.upper()
        query = quote_plus(f"{ticker} stock")
        url = config.NEWS_SOURCES['google_news']['base_url'].format(ticker=query)
        
        logger.info(f"Scraping Google News for {ticker}")
        
        try:
            response = self._make_request(url)
            
            # Parse RSS/XML
            root = ET.fromstring(response.content)
            
            articles = []
            
            # Find all items (articles) in the RSS feed
            for item in root.findall('.//item')[:config.MAX_ARTICLES_PER_STOCK]:
                try:
                    article = self._parse_rss_item(item, ticker)
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
                    logger.warning(f"Failed to parse RSS item: {e}")
                    continue
            
            logger.info(f"Scraped {len(articles)} new articles for {ticker} from Google News")
            time.sleep(self.rate_limit)  # Respect rate limiting
            
            return articles
        
        except ET.ParseError as e:
            logger.error(f"Failed to parse RSS feed for {ticker}: {e}")
            raise ParsingError(f"Invalid RSS feed: {e}")
        except NetworkError as e:
            logger.error(f"Network error scraping {ticker}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to scrape Google News for {ticker}: {e}")
            raise
    
    def _parse_rss_item(self, item: ET.Element, ticker: str) -> Optional[Dict[str, Any]]:
        """Parse article data from RSS item."""
        try:
            title_elem = item.find('title')
            link_elem = item.find('link')
            desc_elem = item.find('description')
            date_elem = item.find('pubDate')
            
            if not title_elem or not link_elem:
                return None
            
            title = clean_text(title_elem.text)
            url = link_elem.text
            summary = clean_text(desc_elem.text) if desc_elem is not None else ""
            
            # Parse publication date
            published_date = None
            if date_elem is not None and date_elem.text:
                published_date = parse_date(date_elem.text)
            
            # Clean up Google News redirect URLs
            if 'news.google.com' in url:
                # Try to extract actual URL from Google redirect
                # This is a simplified approach; actual URL might be in the redirect
                match = re.search(r'url=([^&]+)', url)
                if match:
                    url = match.group(1)
            
            article = {
                'ticker': ticker,
                'title': title,
                'url': url,
                'summary': summary,
                'content': summary,
                'source': self.source_name,
                'published_date': published_date.isoformat() if published_date else None,
                'scraped_date': datetime.now().isoformat()
            }
            
            return article
        
        except Exception as e:
            logger.debug(f"Failed to parse RSS item: {e}")
            return None


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
        
        # Initialize enabled scrapers
        if config.NEWS_SOURCES['yahoo_finance']['enabled']:
            self.scrapers.append(YahooFinanceScraper(self.db_manager))
        
        if config.NEWS_SOURCES['google_news']['enabled']:
            self.scrapers.append(GoogleNewsScraper(self.db_manager))
        
        if config.NEWS_SOURCES['finnhub']['enabled'] and config.FINNHUB_API_KEY:
            self.scrapers.append(FinnhubScraper(self.db_manager))
        
        logger.info(f"Initialized NewsAggregator with {len(self.scrapers)} scrapers")
    
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
