# Stock News Analyzer

Tracks portfolio, scrapes financial news, generates AI summaries, and answers questions about stocks using RAG.

**Stack**: Streamlit + yfinance + Finnhub + OpenAI + LangChain + FAISS + SQLite

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Configure API keys in .env
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://cloud-api.near.ai/v1
FINNHUB_API_KEY=your_key

# Run
streamlit run app.py
```

Get API keys: [OpenAI](https://platform.openai.com/api-keys) | [Finnhub](https://finnhub.io)

## Usage

**Web UI**: Go to Settings → "Update All Data" to fetch news, then browse Portfolio/News/AI Assistant pages.

**CLI**:

```bash
python main_pipeline.py update    # Fetch everything
python main_pipeline.py status    # Check database
python main_pipeline.py cleanup 30  # Delete old articles
```

## Troubleshooting

- **No API key error**: Check `.env` file, restart Streamlit
- **Scraped: 0**: Verify FINNHUB_API_KEY in `.env`, check logs/app.log
- **Rate limits**: Wait, or upgrade API tier
- **Vector store errors**: Delete `data/vector_store/`, rebuild in Settings

## Structure

```
├── app.py                 # Streamlit UI
├── config.py              # Settings
├── main_pipeline.py       # Orchestrator
├── news_scraper.py        # Finnhub API
├── rag_engine.py          # Q&A system
├── stock_tracker.py       # Portfolio
├── summarizer.py          # AI summaries
├── database.py            # SQLite
├── data/
│   ├── news_cache.db
│   ├── portfolio.json
│   └── vector_store/
└── logs/app.log
```

---
