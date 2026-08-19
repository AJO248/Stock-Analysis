"""
Portfolio Dashboard page: current positions as metric cards, a historical
price chart for a selected ticker, and a gainers/losers bar chart.
"""

from datetime import datetime

import streamlit as st
import plotly.graph_objects as go

from utils import format_percentage

GAIN_COLOR = "#1B7F5F"
LOSS_COLOR = "#C0392B"


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

    # Metric cards grid
    st.subheader("📈 Current Positions")

    tickers = list(summary['stocks'].keys())
    cards_per_row = 4
    for row_start in range(0, len(tickers), cards_per_row):
        row_tickers = tickers[row_start:row_start + cards_per_row]
        cols = st.columns(len(row_tickers))
        for col, ticker in zip(cols, row_tickers):
            data = summary['stocks'][ticker]
            with col:
                st.metric(
                    label=f"{ticker} · {data['name']}",
                    value=f"${data['current_price']:,.2f}",
                    delta=f"{data['percent_change']:+.2f}%"
                )

    st.markdown("---")

    # Historical price chart
    st.subheader("📉 Price History")
    chart_col1, chart_col2 = st.columns([1, 3])
    with chart_col1:
        selected_ticker = st.selectbox("Select ticker", tickers, key="dashboard_chart_ticker")
        period = st.selectbox(
            "Period", ["5d", "1mo", "3mo", "6mo", "1y"], index=1, key="dashboard_chart_period"
        )

    with chart_col2:
        hist = st.session_state.pipeline.portfolio.get_historical_data(selected_ticker, period=period)
        if hist is not None and not hist.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist['Close'],
                mode='lines',
                line=dict(color="#1B7F5F", width=2),
                fill='tozeroy',
                fillcolor='rgba(27, 127, 95, 0.1)',
                name=selected_ticker
            ))
            fig.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                height=320,
                xaxis_title=None,
                yaxis_title="Price ($)",
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No historical data available for {selected_ticker}.")

    st.markdown("---")

    # Gainers and losers as a horizontal bar chart
    st.subheader("📊 Gainers & Losers")

    movers = summary['gainers'][:5] + summary['losers'][:5]
    if movers:
        movers.sort(key=lambda x: x[1])
        movers_tickers = [m[0] for m in movers]
        movers_values = [m[1] for m in movers]
        colors = [GAIN_COLOR if v >= 0 else LOSS_COLOR for v in movers_values]

        fig = go.Figure(go.Bar(
            x=movers_values,
            y=movers_tickers,
            orientation='h',
            marker_color=colors,
            text=[format_percentage(v) for v in movers_values],
            textposition='outside',
        ))
        fig.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=max(220, 40 * len(movers_tickers)),
            xaxis_title="% Change",
            yaxis_title=None,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No movers to display today.")
