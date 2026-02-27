"""
Database manager for the stock analysis platform.
Handles SQLite operations for caching news articles, summaries, and metadata.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

import config
from logger import get_logger
from exceptions import DatabaseError

logger = get_logger("database")


class DatabaseManager:
    """Manages SQLite database operations for caching and persistence."""
    
    def __init__(self, db_path: Path = None):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or config.DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            return conn
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to connect to database: {e}")
    
    def _init_database(self):
        """Initialize database schema."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Articles table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS articles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticker TEXT NOT NULL,
                        title TEXT NOT NULL,
                        url TEXT UNIQUE NOT NULL,
                        summary TEXT,
                        content TEXT,
                        source TEXT,
                        published_date TEXT,
                        scraped_date TEXT NOT NULL,
                        UNIQUE(url)
                    )
                """)
                
                # Summaries table (AI-generated summaries)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS summaries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        article_id INTEGER NOT NULL,
                        summary TEXT NOT NULL,
                        sentiment TEXT,
                        key_points TEXT,
                        created_date TEXT NOT NULL,
                        FOREIGN KEY (article_id) REFERENCES articles(id)
                    )
                """)
                
                # Vector store metadata table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS embeddings_metadata (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        article_id INTEGER NOT NULL,
                        embedding_model TEXT NOT NULL,
                        created_date TEXT NOT NULL,
                        FOREIGN KEY (article_id) REFERENCES articles(id)
                    )
                """)
                
                # Query cache table (cache RAG query results)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS query_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query_text TEXT NOT NULL,
                        response TEXT NOT NULL,
                        sources TEXT,
                        created_date TEXT NOT NULL
                    )
                """)
                
                # Create indexes for performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_ticker ON articles(ticker)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_scraped ON articles(scraped_date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_summaries_article ON summaries(article_id)")
                
                conn.commit()
                logger.info("Database initialized successfully")
        
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to initialize database: {e}")
    
    def save_article(self, article: Dict[str, Any]) -> int:
        """
        Save article to database.
        
        Args:
            article: Article data dictionary
        
        Returns:
            Article ID
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR IGNORE INTO articles 
                    (ticker, title, url, summary, content, source, published_date, scraped_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article.get('ticker', ''),
                    article.get('title', ''),
                    article.get('url', ''),
                    article.get('summary', ''),
                    article.get('content', ''),
                    article.get('source', ''),
                    article.get('published_date', ''),
                    article.get('scraped_date', datetime.now().isoformat())
                ))
                
                # Get the inserted or existing article ID
                cursor.execute("SELECT id FROM articles WHERE url = ?", (article.get('url'),))
                result = cursor.fetchone()
                
                conn.commit()
                
                article_id = result[0] if result else cursor.lastrowid
                logger.debug(f"Saved article {article_id}: {article.get('title', '')[:50]}")
                return article_id
        
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to save article: {e}")
    
    def get_article_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get article by URL."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM articles WHERE url = ?", (url,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Failed to get article by URL: {e}")
            return None
    
    def get_recent_articles(self, ticker: str = None, days: int = 7, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent articles, optionally filtered by ticker.
        
        Args:
            ticker: Stock ticker symbol (optional)
            days: Number of days to look back
            limit: Maximum number of articles
        
        Returns:
            List of article dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                if ticker:
                    cursor.execute("""
                        SELECT * FROM articles 
                        WHERE ticker = ? AND scraped_date >= ?
                        ORDER BY published_date DESC, scraped_date DESC
                        LIMIT ?
                    """, (ticker, cutoff_date, limit))
                else:
                    cursor.execute("""
                        SELECT * FROM articles 
                        WHERE scraped_date >= ?
                        ORDER BY published_date DESC, scraped_date DESC
                        LIMIT ?
                    """, (cutoff_date, limit))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        
        except sqlite3.Error as e:
            logger.error(f"Failed to get recent articles: {e}")
            return []
    
    def save_summary(self, article_id: int, summary: str, sentiment: str = None, 
                     key_points: str = None) -> int:
        """
        Save AI-generated summary for an article.
        
        Args:
            article_id: Article ID
            summary: Summary text
            sentiment: Sentiment analysis result
            key_points: Key points extracted
        
        Returns:
            Summary ID
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO summaries 
                    (article_id, summary, sentiment, key_points, created_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    article_id,
                    summary,
                    sentiment,
                    key_points,
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                logger.debug(f"Saved summary for article {article_id}")
                return cursor.lastrowid
        
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to save summary: {e}")
    
    def get_summary(self, article_id: int) -> Optional[Dict[str, Any]]:
        """Get summary for an article."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM summaries 
                    WHERE article_id = ?
                    ORDER BY created_date DESC
                    LIMIT 1
                """, (article_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Failed to get summary: {e}")
            return None
    
    def cache_query(self, query_text: str, response: str, sources: str = None):
        """Cache a RAG query and response."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO query_cache (query_text, response, sources, created_date)
                    VALUES (?, ?, ?, ?)
                """, (query_text, response, sources, datetime.now().isoformat()))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to cache query: {e}")
    
    def get_cached_query(self, query_text: str, max_age_hours: int = 1) -> Optional[Dict[str, Any]]:
        """Get cached query result if not too old."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cutoff_date = (datetime.now() - timedelta(hours=max_age_hours)).isoformat()
                
                cursor.execute("""
                    SELECT * FROM query_cache 
                    WHERE query_text = ? AND created_date >= ?
                    ORDER BY created_date DESC
                    LIMIT 1
                """, (query_text, cutoff_date))
                
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Failed to get cached query: {e}")
            return None
    
    def cleanup_old_data(self, days: int = 30):
        """
        Remove old data from database.
        
        Args:
            days: Remove data older than this many days
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                # Delete old articles and cascading data
                cursor.execute("DELETE FROM articles WHERE scraped_date < ?", (cutoff_date,))
                deleted_articles = cursor.rowcount
                
                # Delete old query cache
                cursor.execute("DELETE FROM query_cache WHERE created_date < ?", (cutoff_date,))
                deleted_queries = cursor.rowcount
                
                conn.commit()
                logger.info(f"Cleanup: removed {deleted_articles} articles and {deleted_queries} cached queries")
        
        except sqlite3.Error as e:
            logger.error(f"Failed to cleanup old data: {e}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                cursor.execute("SELECT COUNT(*) FROM articles")
                stats['total_articles'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM summaries")
                stats['total_summaries'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT ticker) FROM articles")
                stats['unique_tickers'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM query_cache")
                stats['cached_queries'] = cursor.fetchone()[0]
                
                return stats
        
        except sqlite3.Error as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
