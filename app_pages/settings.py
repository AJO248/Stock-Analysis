"""
Settings page: portfolio management, data pipeline controls, database
statistics, and configuration summary.
"""

from datetime import datetime

import streamlit as st

import config
from ui_components import ICONS, badge, section_header, stat_card


def render_settings():
    """Render settings and configuration page."""
    st.title(f"{ICONS['settings']} Settings")

    # Portfolio Management
    section_header("Portfolio Management", "portfolio")

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
        if st.button(f"{ICONS['add']} Add Stock"):
            if new_ticker:
                success = st.session_state.pipeline.portfolio.add_stock(new_ticker)
                if success:
                    st.success(f"Added {new_ticker} to portfolio")
                    st.rerun()
                else:
                    st.error(f"Failed to add {new_ticker}. Please check the ticker symbol.")

    st.markdown("---")

    # Data Management
    section_header("Data Management", "database")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(f"{ICONS['refresh']} Update All Data", use_container_width=True):
            with st.spinner("Running full update pipeline..."):
                results = st.session_state.pipeline.run_full_update()
                st.session_state.last_update = datetime.now()

                if results['success']:
                    st.success(f"Updated! Scraped: {results['articles_scraped']}, Summarized: {results['articles_summarized']}")
                else:
                    st.error(f"Update failed: {results.get('error', 'Unknown error')}")

    with col2:
        if st.button(f"{ICONS['build']} Rebuild Vector Store", use_container_width=True):
            with st.spinner("Rebuilding semantic search index..."):
                result = st.session_state.pipeline.rebuild_vector_store()
                if result['success']:
                    st.success("Index rebuilt")
                else:
                    st.error(f"Failed to rebuild: {result['error']}")

    with col3:
        if not st.session_state.get("confirm_clear_all"):
            if st.button(f"{ICONS['clean']} Clear All Data", use_container_width=True):
                st.session_state.confirm_clear_all = True
                st.rerun()
        else:
            st.warning("This deletes ALL articles, summaries, and the search index. Are you sure?")
            confirm_col, cancel_col = st.columns(2)
            with confirm_col:
                if st.button(f"{ICONS['clean']} Yes, clear everything", use_container_width=True):
                    with st.spinner("Clearing all data..."):
                        result = st.session_state.pipeline.clear_all_data()
                    st.session_state.confirm_clear_all = False
                    st.session_state.chat_history = []
                    st.success(
                        f"Cleared {result['deleted_articles']} article(s), "
                        f"{result['deleted_summaries']} summary(ies), and "
                        f"{result['deleted_queries']} cached quer{'y' if result['deleted_queries'] == 1 else 'ies'}"
                    )
                    st.rerun()
            with cancel_col:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.confirm_clear_all = False
                    st.rerun()

    st.markdown("---")

    # Database Statistics
    section_header("Database Statistics", "database")

    stats = st.session_state.pipeline.db_manager.get_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        stat_card("Total Articles", stats.get('total_articles', 0))

    with col2:
        stat_card("Total Summaries", stats.get('total_summaries', 0))

    with col3:
        stat_card("Unique Tickers", stats.get('unique_tickers', 0))

    with col4:
        stat_card("Cached Queries", stats.get('cached_queries', 0))

    st.markdown("---")

    # Configuration Info
    section_header("Configuration", "tune")

    status = st.session_state.pipeline.get_pipeline_status()
    config_info = status['configuration']

    badge("OpenAI Configured" if config_info['openai_configured'] else "OpenAI Not Configured",
          "success" if config_info['openai_configured'] else "danger",
          "check" if config_info['openai_configured'] else "cancel")
    st.write(f"**Max Articles per Stock:** {config_info['max_articles_per_stock']}")
    st.write(f"**Article Max Age:** {config_info['article_max_age_days']} days")
    st.write(f"**Model:** {config.OPENAI_MODEL}")
    st.write(f"**Embedding Model:** {config.EMBEDDING_MODEL_NAME}")

    if not config_info['openai_configured']:
        st.warning(f"{ICONS['warning']} Please configure OPENAI_API_KEY in .env file to enable AI features")
