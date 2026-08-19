"""
Streamlit web interface for the AI-powered stock analysis platform.
"""

import streamlit as st

import config
from logger import get_logger
from main_pipeline import DataPipeline
from app_pages.dashboard import render_portfolio_dashboard
from app_pages.news_feed import render_news_feed
from app_pages.ai_assistant import render_ai_assistant
from app_pages.settings import render_settings

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

        # Portfolio Quick View - compact tag-style ticker display
        st.subheader("📈 Portfolio")
        portfolio = st.session_state.pipeline.portfolio.get_portfolio()
        st.write(f"**{len(portfolio)} stocks tracked**")

        if portfolio:
            tags_html = " ".join(
                f"<span style='display:inline-block; margin:2px; padding:3px 10px; "
                f"border-radius:12px; background-color:#EAF4EF; color:#1B7F5F; "
                f"font-size:0.85em; font-weight:600;'>{ticker}</span>"
                for ticker in portfolio
            )
            st.markdown(tags_html, unsafe_allow_html=True)

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
