"""
AI Assistant page: chat-based RAG Q&A over recent financial news, with
conversation memory and clickable source citations.
"""

import re

import streamlit as st

from logger import get_logger
from ui_components import ICONS

logger = get_logger("app")


def _render_sources(sources: str):
    """Render a sources block as clickable markdown link chips."""
    if not sources or sources == "No relevant sources found" or sources == "No sources available":
        st.caption("No sources available for this answer.")
        return

    for line in sources.splitlines():
        line = line.strip()
        if not line:
            continue
        match = re.match(r"^-?\s*(.*?)\s*\((https?://[^\s)]+)\)\s*$", line)
        if match:
            label, url = match.group(1), match.group(2)
            st.markdown(
                f"<a href='{url}' target='_blank' style='display:inline-block; "
                f"margin:2px 4px 2px 0; padding:4px 10px; border-radius:14px; "
                f"background-color:var(--app-info-bg); color:var(--app-info-fg); "
                f"text-decoration:none; font-size:0.85em;'>{label}</a>",
                unsafe_allow_html=True,
            )
        else:
            st.caption(line)


def render_ai_assistant():
    """Render AI assistant with RAG-based Q&A."""
    st.title(f"{ICONS['chat']} AI Assistant")

    st.write("Ask questions about your stocks and recent financial news.")

    # Check if RAG is ready
    status = st.session_state.pipeline.get_pipeline_status()

    if not status['configuration']['openai_configured']:
        st.error(f"{ICONS['warning']} OpenAI API key not configured. Please set OPENAI_API_KEY in .env file.")
        return

    if not status['vector_store_exists']:
        st.warning(f"{ICONS['warning']} RAG system not initialized. Please fetch news first from the News Feed page.")
        if st.button("Initialize RAG System"):
            with st.spinner("Building vector store..."):
                result = st.session_state.pipeline.rebuild_vector_store()
                if result['success']:
                    st.success("RAG system initialized!")
                    st.rerun()
                else:
                    st.error(f"Failed to initialize RAG system: {result['error']}")
        return

    # Controls
    col1, col2 = st.columns([3, 1])

    with col2:
        if st.button(f"{ICONS['delete']} Clear History", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.pipeline.rag_engine.clear_conversation_history()
            st.rerun()

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander(f"{ICONS['sources']} Sources"):
                    _render_sources(message["sources"])

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
                        with st.expander(f"{ICONS['sources']} Sources"):
                            _render_sources(sources)

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
    with st.expander("Example Questions"):
        st.write("- What's the recent news about AAPL?")
        st.write("- What is the sentiment on TSLA stock?")
        st.write("- Summarize the latest tech stock news")
        st.write("- Which stocks have positive news recently?")
        st.write("- What are the key events affecting MSFT?")
