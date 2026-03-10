# Stock News Analyzer

tool for tracking stocks, scraping news, generating AI summaries, and asking questions using lightweight RAG.

**Stack**: Streamlit + yfinance + Finnhub API + near.ai + TF-IDF RAG + SQLite

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `.env`:

```
OPENAI_API_KEY=your_open_ai_key
OPENAI_BASE_URL=https://cloud-api.near.ai/v1
OPENAI_MODEL=openai/gpt-oss-120b
FINNHUB_API_KEY=your_finnhub_key
```

Run: `streamlit run app.py`

## Usage

1. Settings → "Update All Data" (scrapes news, builds index)
2. Browse Portfolio/News/AI Assistant pages
3. CLI: `python main_pipeline.py update`

## Files

```
├── app.py              # Streamlit interface
├── config.py           # Configuration
├── main_pipeline.py    # Orchestrator
├── news_scraper.py     # Finnhub scraper
├── rag_engine.py       # TF-IDF RAG Q&A
├── stock_tracker.py    # yfinance wrapper
├── summarizer.py       # AI summaries
├── database.py         # SQLite manager
└── data/
    ├── news_cache.db
    └── portfolio.json
```
