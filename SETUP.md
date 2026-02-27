# 🔧 Detailed Setup Guide

Complete guide for setting up the AI-Powered Stock Analysis Platform.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Python Installation](#python-installation)
3. [Project Setup](#project-setup)
4. [OpenAI API Configuration](#openai-api-configuration)
5. [First Run](#first-run)
6. [Verification](#verification)
7. [Optional Configuration](#optional-configuration)
8. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements:

- **OS**: Linux, macOS, or Windows 10/11
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Disk Space**: 500MB for application + data
- **Internet**: Stable connection for API calls and scraping

### Required Accounts:

- **OpenAI Account** (for GPT and embeddings)
  - Free tier available with limitations
  - Credit card required for API access

---

## Python Installation

### Check if Python is installed:

```bash
python --version
# or
python3 --version
```

Should show Python 3.8 or higher.

### Install Python if needed:

**Linux (Ubuntu/Debian):**

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**macOS:**

```bash
# Using Homebrew
brew install python3
```

**Windows:**

1. Download from [python.org](https://www.python.org/downloads/)
2. Run installer
3. ✅ Check "Add Python to PATH"
4. Install

---

## Project Setup

### Step 1: Navigate to Project Directory

```bash
cd /home/jun/Downloads/repos/python
```

### Step 2: Create Virtual Environment

**Why?** Isolates project dependencies from system Python.

```bash
python3 -m venv venv
```

### Step 3: Activate Virtual Environment

**Linux/macOS:**

```bash
source venv/bin/activate
```

**Windows:**

```bash
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### Step 4: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:

- `yfinance` - Stock data
- `beautifulsoup4` - Web scraping
- `openai` - AI models
- `langchain` - RAG framework
- `faiss-cpu` - Vector store
- `streamlit` - Web interface
- And other dependencies...

**Installation time**: 2-5 minutes depending on your connection.

---

## OpenAI API Configuration

### Step 1: Get OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/signup)
2. Sign up or log in
3. Navigate to [API Keys](https://platform.openai.com/api-keys)
4. Click "Create new secret key"
5. Copy the key (starts with `sk-`)
6. **Important**: Save it securely - you won't see it again!

### Step 2: Add Credits (if needed)

- Free tier has strict limits: 3 requests/min, 200 requests/day
- For better experience, add $5-10 credit
- Go to [Billing](https://platform.openai.com/account/billing/overview)

### Step 3: Configure Environment File

1. **Copy the template:**

```bash
cp .env.template .env
```

2. **Edit the `.env` file:**

```bash
nano .env  # or use any text editor
```

3. **Replace the placeholder:**

```env
OPENAI_API_KEY=sk-your-actual-key-here
```

4. **Save and close** (Ctrl+X, then Y, then Enter in nano)

### Step 4: Verify Configuration

```bash
python -c "import config; print('API Key configured:', bool(config.OPENAI_API_KEY and config.OPENAI_API_KEY != 'your_openai_api_key_here'))"
```

Should print: `API Key configured: True`

---

## First Run

### Step 1: Start the Application

```bash
streamlit run app.py
```

You should see output like:

```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

### Step 2: Open in Browser

- Browser should open automatically
- If not, manually go to `http://localhost:8501`

### Step 3: Initial Setup in Web Interface

1. **Navigate to Settings** (⚙️ Settings in sidebar)

2. **Configure Portfolio** (optional - has defaults)
   - Default stocks: AAPL, MSFT, GOOGL, TSLA, AMZN
   - Add/remove tickers as desired

3. **Fetch Initial Data**
   - Click "🔄 Update All Data" button
   - Wait 2-5 minutes for:
     - News scraping
     - AI summarization
     - Vector store building
   - You'll see progress indicators

4. **Check Status**
   - Sidebar should show:
     - ✅ OpenAI API: Configured
     - ✅ RAG System: Ready
     - Articles and summaries count

---

## Verification

### Test 1: Portfolio Dashboard

1. Go to "📊 Portfolio Dashboard"
2. Should see:
   - Stock prices for all tickers
   - Green/red price changes
   - Gainers and losers
3. Click "🔄 Refresh Prices" to verify live updates

### Test 2: News Feed

1. Go to "📰 News Feed"
2. Should see:
   - Multiple articles for each stock
   - AI-generated summaries
   - Sentiment indicators (🟢🔴⚪)
3. Expand articles to read full summaries

### Test 3: AI Assistant

1. Go to "💬 AI Assistant"
2. Should see:
   - Chat interface
   - No error messages
3. Ask a test question: "What's the recent news about AAPL?"
4. Should receive:
   - Contextual answer
   - Source citations
5. Try follow-up questions to test conversation

### Test 4: Command Line

```bash
# Check pipeline status
python main_pipeline.py status
```

Should show:

```
Pipeline Status:
  Portfolio: 5 tickers
  Tickers: AAPL, MSFT, GOOGL, TSLA, AMZN
  Total articles: 50
  Total summaries: 50
  Vector store: Exists
  OpenAI configured: True
```

---

## Optional Configuration

### Customize Settings in `config.py`

**Change default tickers:**

```python
DEFAULT_TICKERS = ["AAPL", "NVDA", "AMD", "INTC"]
```

**Adjust caching:**

```python
STOCK_CACHE_DURATION = 600  # 10 minutes instead of 5
NEWS_CACHE_DURATION = 7200   # 2 hours instead of 1
```

**Change AI model:**

```python
OPENAI_MODEL = "gpt-4"  # Use GPT-4 (more expensive but better)
```

**Adjust scraping limits:**

```python
MAX_ARTICLES_PER_STOCK = 20  # Get more articles per stock
```

### Schedule Automatic Updates (Linux/Mac)

Add to crontab for daily updates at 9 AM:

```bash
crontab -e
```

Add line:

```
0 9 * * * cd /home/jun/Downloads/repos/python && source venv/bin/activate && python main_pipeline.py update
```

---

## Troubleshooting

### Issue 1: Import Errors

**Error**: `ModuleNotFoundError: No module named 'X'`

**Solution**:

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall requirements
pip install -r requirements.txt
```

### Issue 2: OpenAI API Errors

**Error**: `AuthenticationError: Invalid API key`

**Solution**:

1. Check `.env` file has correct key
2. Key should start with `sk-`
3. No quotes around the key in .env
4. Restart Streamlit after changing .env

**Error**: `RateLimitError: Rate limit exceeded`

**Solution**:

1. Free tier: 3 requests/min, 200/day
2. Wait a few minutes
3. Or add credits to OpenAI account
4. Check usage at [OpenAI Dashboard](https://platform.openai.com/usage)

### Issue 3: Scraping Fails

**Error**: Articles not loading or "Network error"

**Solution**:

1. Check internet connection
2. Some tickers have limited news
3. Try different tickers (AAPL usually has lots of news)
4. Check `logs/app.log` for details:
   ```bash
   tail -f logs/app.log
   ```

### Issue 4: Vector Store Errors

**Error**: "Vector store not initialized" or FAISS errors

**Solution**:

```bash
# Delete existing vector store
rm -rf data/vector_store/

# Rebuild in app
# Go to Settings → "🔨 Rebuild Vector Store"
```

### Issue 5: Permission Errors

**Error**: `PermissionError: Cannot create directory`

**Solution**:

```bash
# Linux/Mac: Ensure correct permissions
chmod -R 755 /home/jun/Downloads/repos/python

# Windows: Run terminal as administrator
```

### Issue 6: Port Already in Use

**Error**: `Address already in use`

**Solution**:

```bash
# Find and kill process using port 8501
# Linux/Mac:
lsof -ti:8501 | xargs kill -9

# Or use different port:
streamlit run app.py --server.port 8502
```

### Issue 7: Data Directory Issues

**Error**: Database or data errors

**Solution**:

```bash
# Fresh start - delete all data
rm -rf data/
rm -rf logs/

# Restart app - directories will be recreated
streamlit run app.py
```

---

## Performance Optimization

### Speed Up Initial Load

**Enable aggressive caching:**

In `.env`:

```env
STOCK_CACHE_DURATION=3600       # 1 hour
NEWS_CACHE_DURATION=21600       # 6 hours
SUMMARY_CACHE_DURATION=86400    # 24 hours
```

### Reduce API Costs

1. **Limit article count:**

   ```python
   # In config.py
   MAX_ARTICLES_PER_STOCK = 5  # Instead of 10
   ```

2. **Use cache aggressively** - already default

3. **Batch updates** - update once or twice daily, not continuously

4. **Monitor usage**: [OpenAI Usage Dashboard](https://platform.openai.com/usage)

---

## Security Best Practices

### 1. Protect Your API Key

- ✅ Never commit `.env` to git (already in `.gitignore`)
- ✅ Don't share your API key
- ✅ Regenerate key if exposed
- ✅ Use environment variables in production

### 2. Database Security

- Database contains cached articles and summaries
- No sensitive financial data stored
- Safe to backup and share (no personal info)

### 3. Network Security

- App runs on localhost by default (port 8501)
- Not exposed to internet unless you configure it
- For remote access, use SSH tunnel or VPN

---

## Next Steps

1. ✅ **Verify all tests pass** (see Verification section)
2. 📚 **Read the README.md** for usage examples
3. 🎯 **Customize your portfolio** in Settings
4. 💬 **Try asking questions** in AI Assistant
5. 📈 **Monitor your stocks** daily

---

## Additional Resources

- **OpenAI Documentation**: https://platform.openai.com/docs
- **Streamlit Documentation**: https://docs.streamlit.io
- **LangChain Documentation**: https://python.langchain.com
- **yfinance Documentation**: https://github.com/ranaroussi/yfinance

---

## Getting Help

If you encounter issues:

1. **Check logs**: `less logs/app.log`
2. **Search error messages**: Google the specific error
3. **Verify prerequisites**: Python version, dependencies, API key
4. **Fresh start**: Delete `data/` and `logs/`, restart

---

**Setup Complete! 🎉**

Your AI-powered stock analysis platform is ready to use!

```bash
# Start the app
streamlit run app.py
```

Then go to http://localhost:8501 and start analyzing! 📈
