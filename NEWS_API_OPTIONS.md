# Alternative News API Options

## Why Web Scraping Fails

Yahoo Finance and Google News actively block automated scraping:

- HTTP 429 (Too Many Requests)
- Changed URL structures
- Bot detection
- IP blocking

## Recommended Solutions

### 1. NewsAPI.org (Easiest)

- **Free tier**: 100 requests/day
- **Pros**: Reliable, well-documented, easy to integrate
- **Setup**: Get API key from https://newsapi.org
- **Cost**: Free for development, $449/mo for production

```python
# Example integration
import requests

def fetch_news_from_newsapi(ticker):
    api_key = "your_newsapi_key"
    url = f"https://newsapi.org/v2/everything?q={ticker}&apiKey={api_key}"
    response = requests.get(url)
    return response.json()['articles']
```

### 2. Alpha Vantage (Financial Focus)

- **Free tier**: 25 requests/day
- **Pros**: Financial data specific, includes sentiment
- **Setup**: Get API key from https://www.alphavantage.co/support/#api-key
- **Cost**: Free

```python
# Example
url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={key}"
```

### 3. Finnhub.io (Best for Stocks)

- **Free tier**: 60 requests/minute
- **Pros**: Real-time market news, earnings, press releases
- **Setup**: Get API key from https://finnhub.io
- **Cost**: Free tier available

```python
# Example
import finnhub
client = finnhub.Client(api_key="your_key")
news = client.company_news(ticker, from_date='2024-01-01', to_date='2024-12-31')
```

### 4. Polygon.io

- **Free tier**: Limited
- **Pros**: Comprehensive financial data
- **Cost**: Free tier limited, $99+/mo for more

### 5. Demo Mode (For Testing)

Use sample/cached data for development without external APIs.

## Quick Migration Guide

### Update config.py

```python
# Add new API keys
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
ALPHAVANTAGE_KEY = os.getenv("ALPHAVANTAGE_KEY", "")
FINNHUB_KEY = os.getenv("FINNHUB_KEY", "")
```

### Update .env

```
NEWSAPI_KEY=your_newsapi_key_here
ALPHAVANTAGE_KEY=your_alphavantage_key_here
FINNHUB_KEY=your_finnhub_key_here
```

## Recommendation

For this project, I recommend:

1. **NewsAPI** - Simplest integration, good free tier
2. **Finnhub** - Best for stock-specific news
3. **Alpha Vantage** - Good balance, includes sentiment

All three have better reliability than web scraping and won't get blocked.
