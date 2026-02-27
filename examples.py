"""
Example usage of the Stock Analysis Platform components.
This file demonstrates how to use the platform programmatically.
"""

from datetime import datetime
from stock_tracker import StockPortfolio
from news_scraper import NewsAggregator
from summarizer import NewsSummarizer
from rag_engine import RAGQueryEngine
from database import DatabaseManager
from main_pipeline import DataPipeline

# ========================================
# Example 1: Using Stock Portfolio Tracker
# ========================================

def example_portfolio():
    """Example: Track and fetch stock prices."""
    print("\n" + "="*60)
    print("Example 1: Stock Portfolio Tracker")
    print("="*60)
    
    # Initialize portfolio
    portfolio = StockPortfolio()
    
    # Add a stock
    portfolio.add_stock("NVDA")
    print(f"Portfolio: {portfolio.get_portfolio()}")
    
    # Fetch current prices
    prices = portfolio.fetch_current_prices()
    
    for ticker, data in prices.items():
        print(f"\n{ticker}:")
        print(f"  Price: ${data['current_price']:.2f}")
        print(f"  Change: {data['percent_change']:+.2f}%")
        print(f"  Sentiment: {data.get('sentiment', 'N/A')}")


# ========================================
# Example 2: Scraping News
# ========================================

def example_news_scraping():
    """Example: Scrape news for specific tickers."""
    print("\n" + "="*60)
    print("Example 2: News Scraping")
    print("="*60)
    
    # Initialize components
    db_manager = DatabaseManager()
    scraper = NewsAggregator(db_manager)
    
    # Scrape news for specific tickers
    tickers = ["AAPL", "TSLA"]
    results = scraper.scrape_multiple_tickers(tickers)
    
    for ticker, articles in results.items():
        print(f"\n{ticker}: Found {len(articles)} articles")
        if articles:
            print(f"  Latest: {articles[0]['title'][:60]}...")


# ========================================
# Example 3: AI Summarization
# ========================================

def example_summarization():
    """Example: Generate AI summaries for articles."""
    print("\n" + "="*60)
    print("Example 3: AI Summarization")
    print("="*60)
    
    # Initialize components
    db_manager = DatabaseManager()
    summarizer = NewsSummarizer(db_manager)
    
    # Get recent articles
    articles = db_manager.get_recent_articles(ticker="AAPL", days=1, limit=3)
    
    if not articles:
        print("No articles found. Run news scraping first.")
        return
    
    # Summarize articles
    print(f"\nSummarizing {len(articles)} articles...")
    
    for article in articles:
        # Check if summary exists
        summary_data = db_manager.get_summary(article['id'])
        
        if not summary_data:
            # Generate summary
            try:
                summary_data = summarizer.summarize_article(article)
                print(f"\n✓ Summarized: {article['title'][:50]}...")
                print(f"  Sentiment: {summary_data.get('sentiment', 'N/A')}")
            except Exception as e:
                print(f"\n✗ Failed: {e}")
        else:
            print(f"\n✓ (Cached) {article['title'][:50]}...")


# ========================================
# Example 4: RAG Query System
# ========================================

def example_rag_queries():
    """Example: Ask questions using RAG."""
    print("\n" + "="*60)
    print("Example 4: RAG Question Answering")
    print("="*60)
    
    # Initialize components
    db_manager = DatabaseManager()
    rag_engine = RAGQueryEngine(db_manager)
    
    # Build or load vector store
    print("\nInitializing RAG system...")
    try:
        rag_engine.build_vector_store(days=7)
        print("✓ Vector store ready")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return
    
    # Example questions
    questions = [
        "What's the recent news about Apple?",
        "What is the sentiment on Tesla stock?",
        "Which stocks have positive news?",
    ]
    
    for question in questions:
        print(f"\nQ: {question}")
        try:
            response = rag_engine.query(question, use_conversation=False)
            print(f"A: {response['answer'][:200]}...")
            print(f"Sources: {len(response.get('source_documents', []))} articles")
        except Exception as e:
            print(f"Error: {e}")


# ========================================
# Example 5: Complete Pipeline
# ========================================

def example_full_pipeline():
    """Example: Run complete data pipeline."""
    print("\n" + "="*60)
    print("Example 5: Complete Pipeline")
    print("="*60)
    
    # Initialize pipeline
    pipeline = DataPipeline()
    
    # Check status
    status = pipeline.get_pipeline_status()
    print(f"\nCurrent Status:")
    print(f"  Portfolio: {status['portfolio_size']} stocks")
    print(f"  Articles: {status['database_stats'].get('total_articles', 0)}")
    print(f"  Summaries: {status['database_stats'].get('total_summaries', 0)}")
    
    # Run update for specific tickers
    print("\nRunning update for AAPL and MSFT...")
    results = pipeline.run_full_update(tickers=["AAPL", "MSFT"])
    
    print(f"\nResults:")
    print(f"  Articles scraped: {results['articles_scraped']}")
    print(f"  Articles summarized: {results['articles_summarized']}")
    print(f"  Vector store updated: {results['vector_store_updated']}")
    print(f"  Duration: {results.get('duration_seconds', 0):.2f}s")


# ========================================
# Example 6: Database Queries
# ========================================

def example_database_queries():
    """Example: Query database directly."""
    print("\n" + "="*60)
    print("Example 6: Database Queries")
    print("="*60)
    
    db_manager = DatabaseManager()
    
    # Get statistics
    stats = db_manager.get_stats()
    print(f"\nDatabase Statistics:")
    print(f"  Total articles: {stats.get('total_articles', 0)}")
    print(f"  Total summaries: {stats.get('total_summaries', 0)}")
    print(f"  Unique tickers: {stats.get('unique_tickers', 0)}")
    print(f"  Cached queries: {stats.get('cached_queries', 0)}")
    
    # Get recent articles for specific ticker
    articles = db_manager.get_recent_articles(ticker="AAPL", days=3, limit=5)
    print(f"\nRecent AAPL articles ({len(articles)}):")
    for article in articles:
        print(f"  - {article['title'][:60]}...")
        print(f"    Source: {article['source']}, Date: {article['published_date']}")


# ========================================
# Main - Run Examples
# ========================================

def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("Stock Analysis Platform - Usage Examples")
    print("="*60)
    print("\nThese examples demonstrate how to use the platform")
    print("programmatically without the web interface.")
    print("\nNote: Some examples require:")
    print("  1. OpenAI API key configured in .env")
    print("  2. Existing data in database (run pipeline first)")
    print("="*60)
    
    examples = {
        "1": ("Stock Portfolio", example_portfolio),
        "2": ("News Scraping", example_news_scraping),
        "3": ("AI Summarization", example_summarization),
        "4": ("RAG Queries", example_rag_queries),
        "5": ("Full Pipeline", example_full_pipeline),
        "6": ("Database Queries", example_database_queries),
    }
    
    print("\nSelect example to run:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    print("  a. Run all examples")
    print("  q. Quit")
    
    choice = input("\nYour choice: ").strip().lower()
    
    if choice == "q":
        print("Goodbye!")
        return
    
    if choice == "a":
        # Run all examples
        for name, func in examples.values():
            try:
                func()
            except Exception as e:
                print(f"\n✗ Error in {name}: {e}")
    elif choice in examples:
        # Run selected example
        name, func = examples[choice]
        try:
            func()
        except Exception as e:
            print(f"\n✗ Error: {e}")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
