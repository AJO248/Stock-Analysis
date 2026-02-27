#!/bin/bash

# Quick Start Script for Stock Analysis Platform
# This script automates the initial setup process

set -e  # Exit on error

echo "🚀 Starting Stock Analysis Platform Setup..."
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check Python version
echo "📋 Step 1: Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version | cut -d' ' -f2)
    echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
    PYTHON_CMD=python
else
    echo -e "${RED}✗ Python not found. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Step 2: Create virtual environment if not exists
echo ""
echo "📦 Step 2: Setting up virtual environment..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Step 3: Activate virtual environment
echo ""
echo "⚡ Step 3: Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Step 4: Install/upgrade pip
echo ""
echo "🔧 Step 4: Upgrading pip..."
pip install --upgrade pip --quiet
echo -e "${GREEN}✓ Pip upgraded${NC}"

# Step 5: Install dependencies
echo ""
echo "📥 Step 5: Installing dependencies..."
echo "This may take a few minutes..."
pip install -r requirements.txt --quiet
echo -e "${GREEN}✓ All dependencies installed${NC}"

# Step 6: Setup .env file
echo ""
echo "🔑 Step 6: Configuring environment..."
if [ ! -f ".env" ]; then
    cp .env.template .env
    echo -e "${YELLOW}⚠️  Created .env file from template${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env and add your OPENAI_API_KEY${NC}"
    echo ""
    read -p "Press Enter to open .env file for editing..."
    ${EDITOR:-nano} .env
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Step 7: Create necessary directories
echo ""
echo "📁 Step 7: Creating data directories..."
mkdir -p data logs
echo -e "${GREEN}✓ Directories created${NC}"

# Step 8: Verify configuration
echo ""
echo "🔍 Step 8: Verifying configuration..."
$PYTHON_CMD -c "
import config
if config.OPENAI_API_KEY and config.OPENAI_API_KEY != 'your_openai_api_key_here':
    print('${GREEN}✓ OpenAI API key configured${NC}')
else:
    print('${YELLOW}⚠️  OpenAI API key not configured. Please edit .env file.${NC}')
" || echo -e "${YELLOW}⚠️  Could not verify configuration${NC}"

# All done!
echo ""
echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Setup complete!${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Make sure your OpenAI API key is configured in .env file"
echo "   Run: nano .env"
echo ""
echo "2. Start the application:"
echo "   Run: streamlit run app.py"
echo ""
echo "3. Your browser should open automatically at:"
echo "   http://localhost:8501"
echo ""
echo "4. In the Settings page, click 'Update All Data' to:"
echo "   - Fetch stock prices"
echo "   - Scrape news articles"
echo "   - Generate AI summaries"
echo "   - Build RAG vector store"
echo ""
echo "📚 For detailed instructions, see:"
echo "   - README.md - Overview and features"
echo "   - SETUP.md - Detailed setup guide"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

# Ask if user wants to start the app now
read -p "Would you like to start the application now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Starting Streamlit application..."
    echo ""
    streamlit run app.py
fi
