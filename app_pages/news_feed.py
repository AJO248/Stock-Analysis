"""
News Feed page: browse recent articles per ticker with AI summaries and a
sentiment badge.
"""

from datetime import datetime

import streamlit as st

from ui_components import ICONS, badge, section_header

SENTIMENT_KIND = {
    'bullish': 'success',
    'bearish': 'danger',
    'neutral': 'neutral',
}


def render_news_feed():
    """Render news feed with articles and summaries."""
    st.title(f"{ICONS['news']} News Feed")

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
        if st.button(f"{ICONS['refresh']} Fetch News", use_container_width=True):
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
        summary_data = db_manager.get_summary(article['id'])
        sentiment = summary_data.get('sentiment', 'neutral') if summary_data else 'neutral'

        with st.expander(f"**[{article['ticker']}]** {article['title']}", expanded=False):
            badge(sentiment.title(), SENTIMENT_KIND.get(sentiment, 'neutral'))
            st.write("")

            col1, col2 = st.columns([3, 1])

            with col1:
                if summary_data:
                    st.markdown("**AI Summary:**")
                    st.write(summary_data['summary'])
                else:
                    st.write(article.get('summary', 'No summary available'))

            with col2:
                st.write(f"**Source:** {article['source']}")
                if article.get('published_date'):
                    pub_date = datetime.fromisoformat(article['published_date'])
                    st.write(f"**Published:** {pub_date.strftime('%Y-%m-%d')}")

                if article.get('url'):
                    st.markdown(f"[{ICONS['link']} Read Full Article]({article['url']})")
