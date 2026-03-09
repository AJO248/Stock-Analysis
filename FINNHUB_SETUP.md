# 🚀 Finnhub News API Setup Guide

## What Is Finnhub?

Finnhub is a reliable financial data API that provides:
- ✅ **Free tier**: 60 API calls/minute
- ✅ **Stock news**: Company news, press releases, earnings
- ✅ **No rate limiting issues**: Professional API
- ✅ **Easy integration**: Simple Python client

## Setup Steps

### 1. Get Your FREE Finnhub API Key

1. Visit: **https://finnhub.io/register**
2. Sign up with email (free, no credit card required)
3. Copy your API key from the dashboard

### 2. Add API Key to .env File

```bash
# Edit your .env file
nano .env

# Add this line (replace with your actual key):
FINNHUB_API_KEY=your_actual_finnhub_api_key_here
```

### 3. Install Dependencies

```bash
# Run the setup script (creates venv and installs everything)
./start.sh

# OR manually with venv:
source venv/bin/activate  # Linux/Mac
pip install finnhub-python
```

### 4. Test It Works

```bash
# Activate venv
source venv/bin/activate

# Test Finnhub connection
python3 -c "
import finnhub
import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('FINNHUB_API_KEY')
if api_key:
    client = finnhub.Client(api_key=api_key)
    news = client.company_news('AAPL', _from='2026-03-01', to='2026-03-10')
    print(f'✓ Finnhub working! Found {len(news)} AAPL news articles')
else:
    print('✗ FINNHUB_API_KEY not set in .env file')
"
```

### 5. Run the App

```bash
streamlit run app.py
```

Then go to **Settings** → Click **"Update All Data"**

You should now see articles being scraped!

## Free Tier Limits

- **60 API calls per minute**
- **30 API calls per second**  
- **Company news**: Last 1 year
- **Market news**: Available

For this app with 5 stocks, you'll use:
- ~5 API calls per update
- Well within free tier limits!

## Troubleshooting

### Error: "finnhub-python not installed"
```bash
source venv/bin/activate
pip install finnhub-python
```

### Error: "API key not set"
Check your `.env` file has:
```
FINNHUB_API_KEY=your_key_here
```

### Error: "API rate limit exceeded"
Free tier = 60 calls/min. Wait 1 minute and try again.

### Still Getting 0 Articles?

1. Check logs: `tail -20 logs/app.log`
2. Verify API key works in test above
3. Make sure you have tickers in portfolio

## What Changed

- ✅ Disabled Yahoo Finance (blocked)
- ✅ Disabled Google News (RSS issues)
- ✅ Added Finnhub API scraper
- ✅ Updated requirements.txt
- ✅ Updated config.py

## Next Steps

Once working, you can:
- Add more tickers in Settings
- Adjust scraping frequency
- Explore other Finnhub data (earnings, financials)

Enjoy reliable news scraping! 🎉
