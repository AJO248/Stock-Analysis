"""
Streamlit web interface for the AI-powered stock analysis platform.
"""

import streamlit as st

import config
from logger import get_logger
from main_pipeline import DataPipeline
from ui_components import ICONS, badge, inject_theme_css, nav_button, section_header
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

PAGES = [
    ("dashboard", "Portfolio Dashboard", "dashboard", render_portfolio_dashboard),
    ("news", "News Feed", "news", render_news_feed),
    ("chat", "AI Assistant", "chat", render_ai_assistant),
    ("settings", "Settings", "settings", render_settings),
]


@st.cache_resource(show_spinner="Starting up...")
def get_pipeline() -> DataPipeline:
    """Build the pipeline once per server process, not once per browser session,
    so portfolio/RAG state is shared across tabs instead of rebuilt each time.
    """
    return DataPipeline()


# Initialize session state
def init_session_state():
    """Initialize Streamlit session state variables."""
    if 'pipeline' not in st.session_state:
        st.session_state.pipeline = get_pipeline()

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if 'last_update' not in st.session_state:
        st.session_state.last_update = None

    if 'active_page' not in st.session_state:
        st.session_state.active_page = "dashboard"

    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False


init_session_state()


# Sidebar navigation
def render_sidebar():
    """Render sidebar with navigation and controls."""
    with st.sidebar:
        st.title(f"{ICONS['portfolio']} Stock Analysis")
        st.toggle("Dark mode", key="dark_mode")
        st.markdown("---")

        # Navigation
        for page_key, label, icon_key, _ in PAGES:
            if nav_button(label, icon_key, page_key, st.session_state.active_page):
                st.session_state.active_page = page_key
                st.rerun()

        st.markdown("---")

        # Portfolio Quick View - compact tag-style ticker display
        section_header("Portfolio", "portfolio")
        portfolio = st.session_state.pipeline.portfolio.get_portfolio()
        st.write(f"**{len(portfolio)} stocks tracked**")

        if portfolio:
            tags_html = " ".join(
                f"<span style='display:inline-block; margin:2px; padding:3px 10px; "
                f"border-radius:12px; background-color:var(--app-success-bg); "
                f"color:var(--app-success-fg); font-size:0.85em; font-weight:600;'>{ticker}</span>"
                for ticker in portfolio
            )
            st.markdown(tags_html, unsafe_allow_html=True)

        st.markdown("---")

        # System Status
        section_header("System Status", "status")
        status = st.session_state.pipeline.get_pipeline_status()

        api_configured = status['configuration']['openai_configured']
        badge("OpenAI API Configured" if api_configured else "OpenAI API Not Configured",
              "success" if api_configured else "danger",
              "check" if api_configured else "cancel")

        vector_store_exists = status['vector_store_exists']
        badge("RAG System Ready" if vector_store_exists else "RAG System Not Initialized",
              "success" if vector_store_exists else "danger",
              "check" if vector_store_exists else "cancel")

        db_stats = status['database_stats']
        st.write(f"**Articles:** {db_stats.get('total_articles', 0)}")
        st.write(f"**Summaries:** {db_stats.get('total_summaries', 0)}")

        # Last update time
        if st.session_state.last_update:
            st.write(f"**Last Update:** {st.session_state.last_update.strftime('%H:%M:%S')}")


# Main app
def main():
    """Main application entry point."""
    inject_theme_css(st.session_state.dark_mode)

    render_sidebar()

    for page_key, _, _, render_fn in PAGES:
        if st.session_state.active_page == page_key:
            render_fn()
            break


if __name__ == "__main__":
    main()
