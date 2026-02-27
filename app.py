"""
Streamlit web interface for the AI-powered stock analysis platform.
"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Any

import config
from logger import get_logger
from stock_tracker import StockPortfolio
from database import DatabaseManager
from summarizer import NewsSummarizer
from rag_engine import RAGQueryEngine
from main_pipeline import DataPipeline
from utils import format_currency, format_percentage

logger = get_logger("app")


# Page configuration
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)


# Initialize session state
def init_session_state():
    """Initialize Streamlit session state variables."""
    if 'pipeline' not in st.session_state:
        st.session_state.pipeline = DataPipeline()
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'last_update' not in st.session_state:
        st.session_state.last_update = None


init_session_state()


# Sidebar navigation
def render_sidebar():
    """Render sidebar with navigation and controls."""
    with st.sidebar:
        st.title(f"{config.APP_ICON} Stock Analysis")
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Navigation",
            ["📊 Portfolio Dashboard", "📰 News Feed", "💬 AI Assistant", "⚙️ Settings"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Portfolio Quick View
        st.subheader("📈 Portfolio")
        portfolio = st.session_state.pipeline.portfolio.get_portfolio()
        st.write(f"**{len(portfolio)} stocks tracked**")
        for ticker in portfolio:
            st.write(f"• {ticker}")
        
        st.markdown("---")
        
        # System Status
        st.subheader("🔧 System Status")
        status = st.session_state.pipeline.get_pipeline_status()
        
        api_configured = status['configuration']['openai_configured']
        st.write(f"**OpenAI API:** {'✅ Configured' if api_configured else '❌ Not configured'}")
        
        vector_store_exists = status['vector_store_exists']
        st.write(f"**RAG System:** {'✅ Ready' if vector_store_exists else '❌ Not initialized'}")
        
        db_stats = status['database_stats']
        st.write(f"**Articles:** {db_stats.get('total_articles', 0)}")
        st.write(f"**Summaries:** {db_stats.get('total_summaries', 0)}")
        
        # Last update time
        if st.session_state.last_update:
            st.write(f"**Last Update:** {st.session_state.last_update.strftime('%H:%M:%S')}")
        
        return page


# Portfolio Dashboard Page
def render_portfolio_dashboard():
    """Render portfolio dashboard with stock prices and performance."""
    st.title("📊 Portfolio Dashboard")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🔄 Refresh Prices", use_container_width=True):
            with st.spinner("Fetching latest prices..."):
                st.session_state.pipeline.portfolio.fetch_current_prices(use_cache=False)
                st.session_state.last_update = datetime.now()
                st.rerun()
    
    # Get portfolio summary
    with st.spinner("Loading portfolio data..."):
        summary = st.session_state.pipeline.portfolio.get_portfolio_summary()
    
    if not summary['stocks']:
        st.warning("No stock data available. Please check your internet connection.")
        return
    
    # Display metrics
    st.subheader("📈 Current Positions")
    
    # Create DataFrame for display
    stocks_data = []
    for ticker, data in summary['stocks'].items():
        stocks_data.append({
            'Ticker': ticker,
            'Name': data['name'],
            'Price': data['current_price'],
            'Change': data['price_change'],
            'Change %': data['percent_change'],
            'Volume': data['volume'],
            'Sector': data['sector']
        })
    
    df = pd.DataFrame(stocks_data)
    
    # Style the dataframe
    def color_change(val):
        if isinstance(val, (int, float)):
            color = 'green' if val > 0 else 'red' if val < 0 else 'gray'
            return f'color: {color}'
        return ''
    
    styled_df = df.style.applymap(color_change, subset=['Change', 'Change %'])
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    # Gainers and Losers
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🟢 Top Gainers")
        if summary['gainers']:
            for ticker, change in summary['gainers'][:5]:
                st.write(f"**{ticker}**: {format_percentage(change)}")
        else:
            st.write("No gainers today")
    
    with col2:
        st.subheader("🔴 Top Losers")
        if summary['losers']:
            for ticker, change in summary['losers'][:5]:
                st.write(f"**{ticker}**: {format_percentage(change)}")
        else:
            st.write("No losers today")


# News Feed Page
def render_news_feed():
    """Render news feed with articles and summaries."""
    st.title("📰 News Feed")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        # Ticker filter
        portfolio = st.session_state.pipeline.portfolio.get_portfolio()
        selected_ticker = st.selectbox(
            "Filter by Ticker",
            ["All"] + portfolio
        )
    
    with col2:
        # Days filter
        days = st.slider("Days to show", 1, 7, 3)
    
    with col3:
        if st.button("🔄 Fetch News", use_container_width=True):
            with st.spinner("Fetching and summarizing news..."):
                tickers = [selected_ticker] if selected_ticker != "All" else None
                st.session_state.pipeline.run_full_update(tickers)
                st.session_state.last_update = datetime.now()
                st.success("News updated!")
                st.rerun()
    
    # Get articles
    db_manager = st.session_state.pipeline.db_manager
    
    ticker_filter = None if selected_ticker == "All" else selected_ticker
    articles = db_manager.get_recent_articles(ticker=ticker_filter, days=days, limit=50)
    
    if not articles:
        st.info("No articles found. Click 'Fetch News' to scrape latest articles.")
        return
    
    st.write(f"Showing {len(articles)} articles from the last {days} days")
    
    # Display articles
    for article in articles:
        with st.expander(f"**[{article['ticker']}]** {article['title']}", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Get summary
                summary_data = db_manager.get_summary(article['id'])
                
                if summary_data:
                    st.markdown("**AI Summary:**")
                    st.write(summary_data['summary'])
                    
                    # Sentiment badge
                    sentiment = summary_data.get('sentiment', 'neutral')
                    sentiment_color = {
                        'bullish': '🟢',
                        'bearish': '🔴',
                        'neutral': '⚪'
                    }
                    st.write(f"**Sentiment:** {sentiment_color.get(sentiment, '⚪')} {sentiment.title()}")
                else:
                    st.write(article.get('summary', 'No summary available'))
            
            with col2:
                st.write(f"**Source:** {article['source']}")
                if article.get('published_date'):
                    pub_date = datetime.fromisoformat(article['published_date'])
                    st.write(f"**Published:** {pub_date.strftime('%Y-%m-%d')}")
                
                if article.get('url'):
                    st.markdown(f"[Read Full Article]({article['url']})")


# AI Assistant Page
def render_ai_assistant():
    """Render AI assistant with RAG-based Q&A."""
    st.title("💬 AI Assistant")
    
    st.write("Ask questions about your stocks and recent financial news.")
    
    # Check if RAG is ready
    status = st.session_state.pipeline.get_pipeline_status()
    
    if not status['configuration']['openai_configured']:
        st.error("⚠️ OpenAI API key not configured. Please set OPENAI_API_KEY in .env file.")
        return
    
    if not status['vector_store_exists']:
        st.warning("⚠️ RAG system not initialized. Please fetch news first from the News Feed page.")
        if st.button("Initialize RAG System"):
            with st.spinner("Building vector store..."):
                success = st.session_state.pipeline.rebuild_vector_store()
                if success:
                    st.success("RAG system initialized!")
                    st.rerun()
                else:
                    st.error("Failed to initialize RAG system")
        return
    
    # Controls
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.pipeline.rag_engine.clear_conversation_history()
            st.rerun()
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("📚 Sources"):
                    st.text(message["sources"])
    
    # Chat input
    if question := st.chat_input("Ask a question about your stocks..."):
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": question
        })
        
        # Display user message
        with st.chat_message("user"):
            st.write(question)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.pipeline.rag_engine.query(
                        question,
                        use_conversation=True,
                        use_cache=True
                    )
                    
                    answer = response['answer']
                    sources = response.get('sources', '')
                    
                    st.write(answer)
                    
                    if sources:
                        with st.expander("📚 Sources"):
                            st.text(sources)
                    
                    # Add assistant message to history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })
                
                except Exception as e:
                    st.error(f"Error: {e}")
                    logger.error(f"Query failed: {e}")
    
    # Example questions
    with st.expander("💡 Example Questions"):
        st.write("- What's the recent news about AAPL?")
        st.write("- What is the sentiment on TSLA stock?")
        st.write("- Summarize the latest tech stock news")
        st.write("- Which stocks have positive news recently?")
        st.write("- What are the key events affecting MSFT?")


# Settings Page
def render_settings():
    """Render settings and configuration page."""
    st.title("⚙️ Settings")
    
    # Portfolio Management
    st.subheader("📈 Portfolio Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Current Portfolio:**")
        portfolio = st.session_state.pipeline.portfolio.get_portfolio()
        for ticker in portfolio:
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.write(f"• {ticker}")
            with col_b:
                if st.button("Remove", key=f"remove_{ticker}"):
                    st.session_state.pipeline.portfolio.remove_stock(ticker)
                    st.success(f"Removed {ticker}")
                    st.rerun()
    
    with col2:
        st.write("**Add New Stock:**")
        new_ticker = st.text_input("Ticker Symbol", placeholder="e.g., NVDA").upper()
        if st.button("Add Stock"):
            if new_ticker:
                success = st.session_state.pipeline.portfolio.add_stock(new_ticker)
                if success:
                    st.success(f"Added {new_ticker} to portfolio")
                    st.rerun()
                else:
                    st.error(f"Failed to add {new_ticker}. Please check the ticker symbol.")
    
    st.markdown("---")
    
    # Data Management
    st.subheader("🗂️ Data Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Update All Data", use_container_width=True):
            with st.spinner("Running full update pipeline..."):
                results = st.session_state.pipeline.run_full_update()
                st.session_state.last_update = datetime.now()
                
                if results['success']:
                    st.success(f"✅ Updated! Scraped: {results['articles_scraped']}, Summarized: {results['articles_summarized']}")
                else:
                    st.error(f"❌ Update failed: {results.get('error', 'Unknown error')}")
    
    with col2:
        if st.button("🔨 Rebuild Vector Store", use_container_width=True):
            with st.spinner("Rebuilding vector store..."):
                success = st.session_state.pipeline.rebuild_vector_store()
                if success:
                    st.success("✅ Vector store rebuilt")
                else:
                    st.error("❌ Failed to rebuild")
    
    with col3:
        if st.button("🧹 Clean Old Data", use_container_width=True):
            with st.spinner("Cleaning old data..."):
                st.session_state.pipeline.cleanup(days=30)
                st.success("✅ Cleanup complete")
    
    st.markdown("---")
    
    # Database Statistics
    st.subheader("📊 Database Statistics")
    
    stats = st.session_state.pipeline.db_manager.get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Articles", stats.get('total_articles', 0))
    
    with col2:
        st.metric("Total Summaries", stats.get('total_summaries', 0))
    
    with col3:
        st.metric("Unique Tickers", stats.get('unique_tickers', 0))
    
    with col4:
        st.metric("Cached Queries", stats.get('cached_queries', 0))
    
    st.markdown("---")
    
    # Configuration Info
    st.subheader("🔧 Configuration")
    
    status = st.session_state.pipeline.get_pipeline_status()
    config_info = status['configuration']
    
    st.write(f"**OpenAI Configured:** {'✅ Yes' if config_info['openai_configured'] else '❌ No'}")
    st.write(f"**Max Articles per Stock:** {config_info['max_articles_per_stock']}")
    st.write(f"**Article Max Age:** {config_info['article_max_age_days']} days")
    st.write(f"**Model:** {config.OPENAI_MODEL}")
    st.write(f"**Embedding Model:** {config.OPENAI_EMBEDDING_MODEL}")
    
    if not config_info['openai_configured']:
        st.warning("⚠️ Please configure OPENAI_API_KEY in .env file to enable AI features")


# Main app
def main():
    """Main application entry point."""
    
    # Render sidebar and get selected page
    page = render_sidebar()
    
    # Render selected page
    if page == "📊 Portfolio Dashboard":
        render_portfolio_dashboard()
    elif page == "📰 News Feed":
        render_news_feed()
    elif page == "💬 AI Assistant":
        render_ai_assistant()
    elif page == "⚙️ Settings":
        render_settings()


if __name__ == "__main__":
    main()
