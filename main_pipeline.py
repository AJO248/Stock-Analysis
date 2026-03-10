"""
Main pipeline orchestration for the stock analysis platform.
Coordinates data collection, summarization, and RAG indexing.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

import config
from logger import get_logger
from database import DatabaseManager
from stock_tracker import StockPortfolio
from news_scraper import NewsAggregator
from summarizer import NewsSummarizer
from rag_engine import RAGQueryEngine
from exceptions import StockAnalysisError

logger = get_logger("pipeline")


class DataPipeline:
    """Orchestrates the data collection and processing pipeline."""
    
    def __init__(self):
        """Initialize pipeline components."""
        logger.info("Initializing Data Pipeline")
        
        self.db_manager = DatabaseManager()
        self.portfolio = StockPortfolio()
        self.news_aggregator = NewsAggregator(self.db_manager)
        self.summarizer = NewsSummarizer(self.db_manager)
        self.rag_engine = RAGQueryEngine(self.db_manager) if config.RAG_ENABLED else None
        
        logger.info("Data Pipeline initialized successfully")
    
    def run_full_update(self, tickers: List[str] = None) -> Dict[str, Any]:
        """
        Run complete update pipeline: fetch news, summarize, update vector store.
        
        Args:
            tickers: List of tickers to process (uses portfolio if None)
        
        Returns:
            Dictionary with pipeline results and statistics
        """
        logger.info("=" * 60)
        logger.info("Starting FULL UPDATE pipeline")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        # Use portfolio tickers if not specified
        if tickers is None:
            tickers = self.portfolio.get_portfolio()
        
        if not tickers:
            logger.warning("No tickers to process")
            return {
                'success': False,
                'error': 'No tickers configured'
            }
        
        results = {
            'start_time': start_time.isoformat(),
            'tickers_processed': 0,
            'articles_scraped': 0,
            'articles_summarized': 0,
            'vector_store_updated': False,
            'errors': [],
            'success': True
        }
        
        try:
            # Step 1: Fetch stock prices
            logger.info(f"Step 1/4: Fetching stock prices for {len(tickers)} tickers")
            stock_data = self.portfolio.fetch_current_prices(use_cache=False)
            results['stock_data'] = stock_data
            logger.info(f"Fetched data for {len(stock_data)} stocks")
            
            # Step 2: Scrape news
            logger.info(f"Step 2/4: Scraping news articles")
            news_by_ticker = self.news_aggregator.scrape_multiple_tickers(tickers)
            
            total_articles = 0
            for ticker, articles in news_by_ticker.items():
                total_articles += len(articles)
                results['tickers_processed'] += 1
            
            results['articles_scraped'] = total_articles
            logger.info(f"Scraped {total_articles} new articles")
            
            # Step 3: Summarize articles
            logger.info(f"Step 3/4: Generating AI summaries")
            summarized_count = 0
            
            for ticker, articles in news_by_ticker.items():
                if not articles:
                    continue
                
                try:
                    summarized_articles = self.summarizer.summarize_batch(
                        articles, 
                        use_cache=True
                    )
                    summarized_count += len(summarized_articles)
                except Exception as e:
                    logger.error(f"Failed to summarize articles for {ticker}: {e}")
                    results['errors'].append(f"Summarization failed for {ticker}: {e}")
            
            results['articles_summarized'] = summarized_count
            logger.info(f"Generated {summarized_count} summaries")
            
            # Step 4: Update vector store
            if self.rag_engine:
                logger.info(f"Step 4/4: Updating RAG vector store")
                try:
                    # Get all recent articles for vector store
                    all_articles = self.db_manager.get_recent_articles(
                        days=config.ARTICLE_MAX_AGE_DAYS
                    )
                    
                    if all_articles:
                        self.rag_engine.build_vector_store(
                            articles=all_articles,
                            force_rebuild=True
                        )
                        results['vector_store_updated'] = True
                        logger.info("Vector store updated successfully")
                    else:
                        logger.warning("No articles available for vector store")
                
                except Exception as e:
                    logger.error(f"Failed to update vector store: {e}")
                    results['errors'].append(f"Vector store update failed: {e}")
                    results['vector_store_updated'] = False
            else:
                logger.info("Step 4/4: Skipping RAG vector store (disabled)")
            
            # Calculate duration
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            results['end_time'] = end_time.isoformat()
            results['duration_seconds'] = duration
            
            logger.info("=" * 60)
            logger.info(f"Pipeline completed in {duration:.2f} seconds")
            logger.info(f"Results: {results['articles_scraped']} scraped, "
                       f"{results['articles_summarized']} summarized")
            logger.info("=" * 60)
            
            return results
        
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            results['success'] = False
            results['error'] = str(e)
            return results
    
    def run_incremental_update(self, tickers: List[str] = None) -> Dict[str, Any]:
        """
        Run incremental update: only process new data since last run.
        
        Args:
            tickers: List of tickers to process (uses portfolio if None)
        
        Returns:
            Dictionary with update results
        """
        logger.info("Starting INCREMENTAL UPDATE pipeline")
        
        # For simplicity, incremental update is similar to full but uses cache more
        # In a production system, you'd track last update time and only fetch new data
        
        results = self.run_full_update(tickers)
        results['update_type'] = 'incremental'
        
        return results
    
    def update_single_ticker(self, ticker: str) -> Dict[str, Any]:
        """
        Update data for a single ticker.
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dictionary with update results
        """
        logger.info(f"Updating data for {ticker}")
        
        results = {
            'ticker': ticker,
            'success': True,
            'articles_scraped': 0,
            'articles_summarized': 0
        }
        
        try:
            # Scrape news
            articles = self.news_aggregator.scrape_ticker(ticker)
            results['articles_scraped'] = len(articles)
            
            # Summarize articles
            if articles:
                summarized = self.summarizer.summarize_batch(articles)
                results['articles_summarized'] = len(summarized)
            
            logger.info(f"Updated {ticker}: {results['articles_scraped']} articles, "
                       f"{results['articles_summarized']} summaries")
            
            return results
        
        except Exception as e:
            logger.error(f"Failed to update {ticker}: {e}")
            results['success'] = False
            results['error'] = str(e)
            return results
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get current pipeline status and statistics.
        
        Returns:
            Dictionary with status information
        """
        db_stats = self.db_manager.get_stats()
        portfolio = self.portfolio.get_portfolio()
        
        status = {
            'portfolio_size': len(portfolio),
            'portfolio_tickers': portfolio,
            'database_stats': db_stats,
            'vector_store_exists': (config.VECTOR_STORE_PATH / "tfidf_index.pkl").exists(),
            'configuration': {
                'openai_configured': bool(config.OPENAI_API_KEY and 
                                         config.OPENAI_API_KEY != "your_openai_api_key_here"),
                'max_articles_per_stock': config.MAX_ARTICLES_PER_STOCK,
                'article_max_age_days': config.ARTICLE_MAX_AGE_DAYS,
            }
        }
        
        return status
    
    def cleanup(self, days: int = 30):
        """
        Clean up old data from database.
        
        Args:
            days: Remove data older than this many days
        """
        logger.info(f"Cleaning up data older than {days} days")
        self.db_manager.cleanup_old_data(days)
    
    def rebuild_vector_store(self, days: int = 7):
        """
        Rebuild vector store from existing articles.
        
        Args:
            days: Include articles from last N days
        """
        if not self.rag_engine:
            logger.warning("RAG is disabled. Cannot rebuild vector store.")
            return False
        
        logger.info(f"Rebuilding vector store with articles from last {days} days")
        
        try:
            articles = self.db_manager.get_recent_articles(days=days)
            
            if not articles:
                logger.warning("No articles available for rebuilding vector store")
                return False
            
            self.rag_engine.build_vector_store(articles=articles, force_rebuild=True)
            logger.info(f"Vector store rebuilt with {len(articles)} articles")
            return True
        
        except Exception as e:
            logger.error(f"Failed to rebuild vector store: {e}")
            return False


def main():
    """Main function for running pipeline from command line."""
    import sys
    
    # Setup logging
    logger.info("Stock Analysis Platform - Data Pipeline")
    
    # Initialize pipeline
    pipeline = DataPipeline()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "update":
            # Run full update
            results = pipeline.run_full_update()
            print(f"\nPipeline Results:")
            print(f"  Articles scraped: {results['articles_scraped']}")
            print(f"  Articles summarized: {results['articles_summarized']}")
            print(f"  Vector store updated: {results['vector_store_updated']}")
            print(f"  Duration: {results.get('duration_seconds', 0):.2f}s")
            
        elif command == "status":
            # Show status
            status = pipeline.get_pipeline_status()
            print(f"\nPipeline Status:")
            print(f"  Portfolio: {status['portfolio_size']} tickers")
            print(f"  Tickers: {', '.join(status['portfolio_tickers'])}")
            print(f"  Total articles: {status['database_stats'].get('total_articles', 0)}")
            print(f"  Total summaries: {status['database_stats'].get('total_summaries', 0)}")
            print(f"  Vector store: {'Exists' if status['vector_store_exists'] else 'Not built'}")
            print(f"  OpenAI configured: {status['configuration']['openai_configured']}")
            
        elif command == "cleanup":
            # Clean up old data
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            pipeline.cleanup(days)
            print(f"Cleaned up data older than {days} days")
            
        elif command == "rebuild":
            # Rebuild vector store
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            success = pipeline.rebuild_vector_store(days)
            if success:
                print("Vector store rebuilt successfully")
            else:
                print("Failed to rebuild vector store")
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: update, status, cleanup, rebuild")
    
    else:
        # Show usage
        print("Usage: python main_pipeline.py [command]")
        print("\nCommands:")
        print("  update   - Run full update pipeline")
        print("  status   - Show pipeline status")
        print("  cleanup  - Clean up old data")
        print("  rebuild  - Rebuild vector store")


if __name__ == "__main__":
    main()
