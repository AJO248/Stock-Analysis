"""
Settings page: portfolio management, data pipeline controls, database
statistics, and configuration summary.
"""

from datetime import datetime

import streamlit as st

import config


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
            with st.spinner("Rebuilding semantic search index..."):
                success = st.session_state.pipeline.rebuild_vector_store()
                if success:
                    st.success("✅ Index rebuilt")
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
    st.write(f"**Embedding Model:** {config.EMBEDDING_MODEL_NAME}")

    if not config_info['openai_configured']:
        st.warning("⚠️ Please configure OPENAI_API_KEY in .env file to enable AI features")
