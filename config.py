"""
Configuration settings for the AI-powered stock analysis platform.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "60"))

# Separate config for embeddings (can use different endpoint/key)
OPENAI_EMBEDDINGS_API_KEY = os.getenv("OPENAI_EMBEDDINGS_API_KEY", OPENAI_API_KEY)
OPENAI_EMBEDDINGS_BASE_URL = os.getenv("OPENAI_EMBEDDINGS_BASE_URL", OPENAI_BASE_URL)

# Finnhub API Configuration
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
FINNHUB_ENABLED = bool(FINNHUB_API_KEY)  # Auto-enable if key is set

# RAG Feature Toggle (uses lightweight TF-IDF - no extra dependencies)
RAG_ENABLED = os.getenv("RAG_ENABLED", "true").lower() == "true"  # Enabled by default

# LLM Parameters
LLM_TEMPERATURE = 0.3  # Lower temperature for more focused financial analysis
LLM_MAX_TOKENS = 500  # Limit response length to manage costs
EMBEDDING_CHUNK_SIZE = 1000
EMBEDDING_CHUNK_OVERLAP = 200

# Stock Portfolio Settings
DEFAULT_TICKERS = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
PORTFOLIO_FILE = DATA_DIR / "portfolio.json"

# News Scraping Configuration
NEWS_SOURCES = {
    "finnhub": {
        "enabled": True,
        "rate_limit": 1.0,  # Free tier: 60 calls/minute
    },
}

USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
SCRAPING_DELAY = float(os.getenv("SCRAPING_DELAY", "1.5"))
MAX_ARTICLES_PER_STOCK = 10
ARTICLE_MAX_AGE_DAYS = 7

# Cache Configuration (in seconds)
STOCK_CACHE_DURATION = int(os.getenv("STOCK_CACHE_DURATION", "300"))  # 5 minutes
NEWS_CACHE_DURATION = int(os.getenv("NEWS_CACHE_DURATION", "3600"))  # 1 hour
SUMMARY_CACHE_DURATION = int(os.getenv("SUMMARY_CACHE_DURATION", "86400"))  # 24 hours
VECTOR_STORE_REFRESH_HOURS = 6

# Database Configuration
DB_PATH = Path(os.getenv("DB_PATH", str(DATA_DIR / "news_cache.db")))
VECTOR_STORE_PATH = Path(os.getenv("VECTOR_STORE_PATH", str(DATA_DIR / "vector_store")))
VECTOR_STORE_PATH.mkdir(parents=True, exist_ok=True)

# RAG Configuration
RAG_TOP_K = 5  # Number of documents to retrieve
RAG_SIMILARITY_THRESHOLD = 0.7
RAG_CHAIN_TYPE = "stuff"  # Options: stuff, map_reduce, refine, map_rerank

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "app.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# Streamlit Configuration
APP_TITLE = "AI-Powered Stock Analysis Platform"
APP_ICON = "📈"
DEFAULT_PAGE = "Portfolio Dashboard"

# Prompt Templates
SUMMARIZATION_PROMPT = """You are a financial analyst. Summarize the following news article focusing on:
- Stock price impact (bullish/bearish/neutral)
- Key events or announcements
- Important financial metrics or forecasts
- Overall sentiment

Keep the summary concise (3-5 bullet points).

Article:
{article_text}

Summary:"""

RAG_SYSTEM_PROMPT = """You are an AI financial assistant with access to recent stock news and analysis.
Answer questions based on the provided context. Always cite your sources by mentioning the article titles.
If you don't have enough information, say so clearly. Be precise and factual."""

# Validation
def validate_config():
    """Validate critical configuration settings."""
    errors = []
    
    if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here":
        errors.append("OPENAI_API_KEY is not set. Please configure it in .env file.")
    
    if not DATA_DIR.exists():
        errors.append(f"Data directory does not exist: {DATA_DIR}")
    
    return errors

# Run validation on import
config_errors = validate_config()
if config_errors:
    print("⚠️  Configuration warnings:")
    for error in config_errors:
        print(f"  - {error}")
