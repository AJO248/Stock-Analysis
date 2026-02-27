# 📈 AI-Powered Stock Analysis Platform

An intelligent stock analysis platform that tracks your portfolio, scrapes financial news, generates AI-powered summaries, and provides an interactive RAG-based question-answering system for financial insights.

## 🌟 Features

### 1. **Stock Portfolio Tracking**

- Track multiple stocks with real-time price updates
- View current prices, daily changes, and performance metrics
- Automatic caching to minimize API calls (respects rate limits)
- Historical data analysis

### 2. **Automated News Scraping**

- Scrapes financial news from multiple sources:
  - Yahoo Finance
  - Google News RSS feeds
- Intelligent deduplication to avoid duplicate articles
- Configurable scraping intervals and rate limiting
- Stores articles in local SQLite database

### 3. **AI-Powered Summarization**

- Uses OpenAI GPT models to generate concise summaries
- Extracts key insights from financial articles:
  - Stock price impact (bullish/bearish/neutral)
  - Key events and announcements
  - Important financial metrics
  - Overall sentiment analysis
- Smart caching to minimize API costs

### 4. **RAG-Based Q&A System**

- Interactive question-answering using Retrieval-Augmented Generation
- Ask natural language questions about your stocks
- Provides contextual answers with source citations
- Maintains conversation history for multi-turn dialogues
- Uses FAISS vector store for efficient similarity search

### 5. **Web Interface**

- Beautiful Streamlit-based user interface
- Four main sections:
  - **Portfolio Dashboard**: Live stock prices and performance
  - **News Feed**: Latest articles with AI summaries
  - **AI Assistant**: Chat interface for Q&A
  - **Settings**: Portfolio and data management

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Web Interface                   │
│  (Portfolio | News Feed | AI Assistant | Settings)          │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                  Data Pipeline Orchestrator                  │
│  (Coordinates all components and data flow)                  │
└─────────┬──────────┬──────────┬──────────┬──────────────────┘
          │          │          │          │
    ┌─────┴────┐ ┌──┴───────┐ ┌┴─────────┐ ┌┴──────────────┐
    │ Stock    │ │ News     │ │ AI       │ │ RAG Query     │
    │ Tracker  │ │ Scraper  │ │ Summariz │ │ Engine        │
    │          │ │          │ │ er       │ │               │
    │ yfinance │ │ BS4,     │ │ OpenAI   │ │ LangChain +   │
    │          │ │ Scrapy   │ │ GPT      │ │ FAISS         │
    └─────┬────┘ └──┬───────┘ └┬─────────┘ └┬──────────────┘
          │          │          │            │
          └──────────┴──────────┴────────────┘
                     │
          ┌──────────┴──────────┐
          │  Database Manager   │
          │  (SQLite + FAISS)   │
          └─────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- Internet connection for scraping and API calls

### Installation

1. **Clone or download this repository**

```bash
cd /home/jun/Downloads/repos/python
```

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

```bash
cp .env.template .env
```

Edit `.env` file and add your OpenAI API key:

```env
OPENAI_API_KEY=your_actual_api_key_here
```

5. **Run the application**

```bash
streamlit run app.py
```

The web interface will open automatically at `http://localhost:8501`

## 📖 Usage Guide

### 1. Initial Setup

1. **Configure Your Portfolio** (Settings page)
   - Add stock tickers you want to track
   - Default portfolio includes: AAPL, MSFT, GOOGL, TSLA, AMZN

2. **Fetch Initial Data** (Settings page)
   - Click "Update All Data" to scrape news and generate summaries
   - This will take a few minutes on first run
   - The system will build the RAG vector store automatically

### 2. Monitoring Your Portfolio

- Go to **Portfolio Dashboard** to see:
  - Current prices and daily changes
  - Top gainers and losers
  - Refresh prices with the button

### 3. Reading News

- Go to **News Feed** to:
  - Browse latest financial news articles
  - Read AI-generated summaries
  - Filter by ticker or date range
  - See sentiment analysis (bullish/bearish/neutral)

### 4. Asking Questions

- Go to **AI Assistant** to:
  - Ask questions about your stocks
  - Get contextual answers with source citations
  - Have multi-turn conversations

**Example Questions:**

- "What's the recent news about AAPL?"
- "What is the sentiment on TSLA stock?"
- "Summarize the latest tech stock news"
- "Which stocks have positive news recently?"
- "What are the key events affecting MSFT?"

### 5. Command Line Usage

You can also run the pipeline from command line:

```bash
# Run full update
python main_pipeline.py update

# Check status
python main_pipeline.py status

# Clean up old data (30+ days)
python main_pipeline.py cleanup 30

# Rebuild vector store
python main_pipeline.py rebuild 7
```

## ⚙️ Configuration

Key settings in `config.py`:

- `DEFAULT_TICKERS`: Default stock tickers to track
- `MAX_ARTICLES_PER_STOCK`: Maximum articles to scrape per stock (default: 10)
- `ARTICLE_MAX_AGE_DAYS`: How many days of articles to keep (default: 7)
- `STOCK_CACHE_DURATION`: Stock price cache duration in seconds (default: 300)
- `NEWS_CACHE_DURATION`: News cache duration in seconds (default: 3600)
- `OPENAI_MODEL`: OpenAI model to use (default: gpt-3.5-turbo)
- `RAG_TOP_K`: Number of documents to retrieve for RAG (default: 5)

## 💰 Cost Optimization

The platform is designed for **free-tier usage** with OpenAI:

### Cost Saving Features:

- **Aggressive caching**: Summaries and embeddings are cached in database
- **Smart updates**: Only processes new articles
- **GPT-3.5-turbo**: Uses cheaper model (~94% less than GPT-4)
- **Small embeddings**: Uses `text-embedding-3-small` model
- **Rate limiting**: Built-in delays to respect API limits

### Estimated Costs (Free Tier):

- **News scraping**: Free (Yahoo Finance, Google News)
- **Stock data**: Free (yfinance)
- **OpenAI API**:
  - Embeddings: ~$0.13 per 1M tokens
  - Completions: ~$0.50 per 1M tokens (GPT-3.5-turbo)
  - **Typical usage**: $0.50-$2.00/month for personal use

### Staying Within Free Tier:

- Limit updates to once or twice daily
- Track 5-10 stocks maximum
- Use caching effectively (already enabled)
- Monitor usage on [OpenAI dashboard](https://platform.openai.com/usage)

## 🔒 Legal & Ethical Considerations

### Web Scraping:

- Yahoo Finance: "Personal use only" per their TOS
- Google News RSS: Generally allowed for personal use
- **For commercial use**: Consider paid news APIs (NewsAPI, Alpha Vantage)
- Always respect `robots.txt` and rate limits

### Data Accuracy:

- AI summaries may contain inaccuracies or "hallucinations"
- Always verify important information with original sources
- The platform is for educational/informational purposes only
- **Not financial advice**: Do not make investment decisions solely based on this tool

## 🛠️ Troubleshooting

### Common Issues:

**1. "OpenAI API key not configured"**

- Ensure `.env` file exists with valid `OPENAI_API_KEY`
- Restart the Streamlit app after changing `.env`

**2. "No articles found"**

- Click "Fetch News" button to scrape articles
- Check internet connection
- Some tickers may have limited news coverage

**3. "Rate limit exceeded"**

- OpenAI free tier has strict limits (3 RPM, 200 RPD)
- Wait a few minutes and try again
- Consider upgrading to paid tier if needed

**4. Scraping fails**

- Websites may change their HTML structure
- Check logs in `logs/app.log` for details
- May need to update scraper selectors

**5. Vector store errors**

- Delete `data/vector_store/` folder
- Click "Rebuild Vector Store" in Settings

## 📁 Project Structure

```
python/
├── app.py                 # Streamlit web interface
├── config.py              # Configuration settings
├── database.py            # SQLite database manager
├── exceptions.py          # Custom exceptions
├── logger.py              # Logging configuration
├── main_pipeline.py       # Pipeline orchestrator
├── news_scraper.py        # News scraping module
├── rag_engine.py          # RAG Q&A system
├── stock_tracker.py       # Stock portfolio tracker
├── summarizer.py          # AI summarization engine
├── utils.py               # Utility functions
├── requirements.txt       # Python dependencies
├── .env.template          # Environment template
├── .gitignore            # Git ignore rules
├── README.md             # This file
├── SETUP.md              # Detailed setup guide
├── data/                 # Data directory (created automatically)
│   ├── news_cache.db     # SQLite database
│   ├── portfolio.json    # Portfolio configuration
│   └── vector_store/     # FAISS vector store
└── logs/                 # Log files (created automatically)
    └── app.log           # Application logs
```

## 🎯 Future Enhancements

Potential improvements:

- [ ] Add more news sources (NewsAPI, Alpha Vantage)
- [ ] Implement price alerts and notifications
- [ ] Add technical analysis indicators
- [ ] Support for multiple portfolios
- [ ] Export reports (PDF, CSV)
- [ ] Integration with brokerage APIs
- [ ] Real-time WebSocket updates
- [ ] Sentiment analysis visualization
- [ ] Social media sentiment tracking
- [ ] Backtesting capabilities

## 📝 License

This project is for educational purposes only. Use at your own risk.

## 🤝 Contributing

This is a personal learning project, but suggestions and improvements are welcome!

## 📧 Support

For issues or questions:

1. Check the troubleshooting section above
2. Review logs in `logs/app.log`
3. Ensure all dependencies are installed correctly

## ⚠️ Disclaimer

This software is provided for educational and informational purposes only. It is not financial advice, and should not be used as the sole basis for investment decisions. Always conduct your own research and consult with qualified financial advisors before making investment decisions. The creators of this software are not responsible for any financial losses incurred through its use.

---

**Happy Analyzing! 📈🚀**
