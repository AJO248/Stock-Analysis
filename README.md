# Stock News Analyzer

A tool for tracking stocks, scraping news, generating AI summaries, and asking questions using retrieval-augmented generation (RAG).

**Stack**: Streamlit + yfinance + Finnhub API + an OpenAI-compatible chat endpoint (e.g. near.ai) + OpenAI-compatible embeddings API + FAISS + SQLite

## Setup

```bash
python -m venv venv
source venv/bin/activate      # macOS/Linux/Git Bash
venv\Scripts\Activate.ps1     # Windows PowerShell
venv\Scripts\activate.bat     # Windows cmd.exe
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

At minimum you'll need:

```
OPENAI_API_KEY=your_open_ai_key
OPENAI_BASE_URL=https://cloud-api.near.ai/v1
OPENAI_MODEL=openai/gpt-oss-120b
FINNHUB_API_KEY=your_finnhub_key
```

Run: `streamlit run app.py`

## Usage

1. Settings → "Update All Data" (scrapes news, builds the semantic search index)
2. Browse Portfolio/News/AI Assistant pages
3. CLI: `python main_pipeline.py update`

## Architecture

The AI Assistant is backed by a real retrieval-augmented generation pipeline, not a keyword search:

1. Articles are loaded into LangChain `Document` objects and chunked with `RecursiveCharacterTextSplitter`.
2. Chunks are embedded via the **OpenAI embeddings API** (`OpenAIEmbeddings`, model `EMBEDDING_MODEL_NAME`, default `text-embedding-3-small`) — called against `OPENAI_BASE_URL`/`OPENAI_API_KEY` by default. If your chat endpoint doesn't also serve an embeddings route, point `OPENAI_EMBEDDINGS_BASE_URL`/`OPENAI_EMBEDDINGS_API_KEY` at one that does (e.g. real OpenAI) — see `.env.example`.
3. Embeddings are indexed in a **FAISS** vector store, persisted to disk (`data/vector_store/`) and reloaded across runs.
4. At query time, the question is embedded and matched against the FAISS index via similarity search to retrieve the most relevant article chunks.
5. Retrieved chunks, plus prior turns pulled from a LangChain `ConversationBufferMemory`, are assembled into a prompt sent to the configured chat model (`ChatOpenAI` pointed at `OPENAI_BASE_URL`).

## Testing

The project uses `pytest`. Run the full suite from the repo root:

```bash
pytest -v
```

Coverage includes:
- `tests/test_utils.py` — pure formatting/validation helpers
- `tests/test_database.py` — SQLite persistence layer, run against a temporary DB file
- `tests/test_stock_tracker.py` — portfolio logic, with `yfinance.Ticker` mocked (no network calls)
- `tests/test_rag_engine.py` — builds a real FAISS index from fixture articles using a deterministic fake embeddings client and asserts topically-relevant retrieval; the chat LLM call is mocked so no API key or network access is required

## Files

```
├── app.py               # Streamlit entry point: page config, session state, sidebar, routing
├── app_pages/            # One module per sidebar page (dashboard, news feed, AI assistant, settings)
├── config.py             # Configuration
├── main_pipeline.py      # Orchestrator
├── news_scraper.py       # Finnhub scraper
├── rag_engine.py         # FAISS + API embeddings RAG Q&A
├── ui_components.py      # Shared design-system components (icons, badges, nav, theme)
├── stock_tracker.py      # yfinance wrapper
├── summarizer.py         # AI summaries
├── database.py           # SQLite manager
├── exceptions.py         # Custom exception hierarchy
├── utils.py / logger.py  # Shared helpers
├── tests/                # pytest suite
├── .streamlit/config.toml  # UI theme
└── data/
    ├── news_cache.db
    ├── vector_store/      # persisted FAISS index
    └── portfolio.json
```
