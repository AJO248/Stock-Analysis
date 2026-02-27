"""
AI-powered summarization engine using OpenAI API.
"""

from typing import List, Dict, Any, Optional
import time

from openai import OpenAI, OpenAIError, RateLimitError

import config
from logger import get_logger
from exceptions import SummarizationError, APILimitError, APIError
from utils import retry_with_backoff, truncate_text
from database import DatabaseManager

logger = get_logger("summarizer")


class NewsSummarizer:
    """AI-powered news summarizer using OpenAI GPT models."""
    
    def __init__(self, db_manager: DatabaseManager = None, api_key: str = None):
        """
        Initialize news summarizer.
        
        Args:
            db_manager: Database manager instance
            api_key: OpenAI API key (uses config if not provided)
        """
        self.db_manager = db_manager or DatabaseManager()
        self.api_key = api_key or config.OPENAI_API_KEY
        
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            logger.warning("OpenAI API key not configured. Summarization will not work.")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=config.OPENAI_BASE_URL,
                timeout=config.OPENAI_TIMEOUT,
                max_retries=config.OPENAI_MAX_RETRIES
            )
        
        self.model = config.OPENAI_MODEL
        self.temperature = config.LLM_TEMPERATURE
        self.max_tokens = config.LLM_MAX_TOKENS
        
        logger.info(f"Initialized NewsSummarizer with model: {self.model}")
    
    def _check_client(self):
        """Check if OpenAI client is initialized."""
        if self.client is None:
            raise APIError("OpenAI client not initialized. Please configure OPENAI_API_KEY.")
    
    @retry_with_backoff(
        max_retries=3,
        base_delay=2.0,
        exceptions=(RateLimitError, APIError)
    )
    def summarize_article(self, article: Dict[str, Any], use_cache: bool = True) -> Dict[str, Any]:
        """
        Summarize a single news article.
        
        Args:
            article: Article dictionary with 'title', 'content', 'url', etc.
            use_cache: Whether to check cache first
        
        Returns:
            Dictionary with summary and metadata
        """
        self._check_client()
        
        article_id = article.get('id')
        
        # Check cache if article has ID
        if use_cache and article_id:
            cached_summary = self.db_manager.get_summary(article_id)
            if cached_summary:
                logger.debug(f"Using cached summary for article {article_id}")
                return cached_summary
        
        # Prepare article text
        title = article.get('title', '')
        content = article.get('content', article.get('summary', ''))
        
        if not content:
            logger.warning(f"No content to summarize for article: {title}")
            return {
                'summary': 'No content available for summarization.',
                'sentiment': 'neutral',
                'key_points': ''
            }
        
        # Truncate if too long (to manage token usage)
        article_text = f"Title: {title}\n\nContent: {truncate_text(content, max_length=2000)}"
        
        try:
            # Create prompt
            prompt = config.SUMMARIZATION_PROMPT.format(article_text=article_text)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial analyst assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            summary_text = response.choices[0].message.content.strip()
            
            # Extract sentiment if mentioned in summary
            sentiment = self._extract_sentiment(summary_text)
            
            # Extract key points
            key_points = self._extract_key_points(summary_text)
            
            result = {
                'summary': summary_text,
                'sentiment': sentiment,
                'key_points': key_points,
            }
            
            # Cache the summary if article has ID
            if article_id:
                self.db_manager.save_summary(
                    article_id=article_id,
                    summary=summary_text,
                    sentiment=sentiment,
                    key_points=key_points
                )
            
            logger.debug(f"Generated summary for: {title[:50]}...")
            return result
        
        except RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise APILimitError(f"Rate limit exceeded: {e}")
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise APIError(f"OpenAI API error: {e}")
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            raise SummarizationError(f"Failed to summarize article: {e}")
    
    def _extract_sentiment(self, summary: str) -> str:
        """Extract sentiment from summary text."""
        summary_lower = summary.lower()
        
        # Simple keyword-based sentiment detection
        bullish_keywords = ['bullish', 'positive', 'growth', 'gain', 'increase', 'rise', 'surge', 'rally']
        bearish_keywords = ['bearish', 'negative', 'decline', 'loss', 'decrease', 'fall', 'drop', 'plunge']
        
        bullish_count = sum(1 for keyword in bullish_keywords if keyword in summary_lower)
        bearish_count = sum(1 for keyword in bearish_keywords if keyword in summary_lower)
        
        if bullish_count > bearish_count:
            return 'bullish'
        elif bearish_count > bullish_count:
            return 'bearish'
        else:
            return 'neutral'
    
    def _extract_key_points(self, summary: str) -> str:
        """Extract key points from summary (bullet points)."""
        # Find lines that look like bullet points
        lines = summary.split('\n')
        key_points = []
        
        for line in lines:
            line = line.strip()
            if line.startswith(('-', '•', '*', '·')) or (line and line[0].isdigit() and '.' in line[:3]):
                key_points.append(line)
        
        return '\n'.join(key_points) if key_points else summary
    
    def summarize_batch(self, articles: List[Dict[str, Any]], use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Summarize multiple articles.
        
        Args:
            articles: List of article dictionaries
            use_cache: Whether to check cache first
        
        Returns:
            List of articles with summaries added
        """
        self._check_client()
        
        results = []
        
        for i, article in enumerate(articles):
            try:
                summary_data = self.summarize_article(article, use_cache=use_cache)
                article_with_summary = article.copy()
                article_with_summary.update(summary_data)
                results.append(article_with_summary)
                
                # Small delay between API calls to avoid rate limiting
                if i < len(articles) - 1:
                    time.sleep(0.5)
            
            except APILimitError:
                logger.warning("Rate limit reached, stopping batch summarization")
                # Return what we have so far
                break
            except Exception as e:
                logger.error(f"Failed to summarize article {article.get('title', '')[:50]}: {e}")
                # Continue with other articles
                continue
        
        logger.info(f"Summarized {len(results)}/{len(articles)} articles")
        return results
    
    def generate_ticker_summary(self, ticker: str, days: int = 7) -> Optional[str]:
        """
        Generate an overall summary of news for a specific ticker.
        
        Args:
            ticker: Stock ticker symbol
            days: Number of days to look back
        
        Returns:
            Overall summary text
        """
        self._check_client()
        
        # Get recent articles for the ticker
        articles = self.db_manager.get_recent_articles(ticker=ticker, days=days)
        
        if not articles:
            logger.info(f"No recent articles found for {ticker}")
            return None
        
        # Collect summaries
        summaries = []
        for article in articles[:10]:  # Limit to 10 most recent
            summary_data = self.db_manager.get_summary(article['id'])
            if summary_data:
                summaries.append(f"- {article['title']}: {summary_data['summary']}")
        
        if not summaries:
            logger.info(f"No summaries available for {ticker}")
            return None
        
        # Generate overall summary
        combined_text = f"Recent news for {ticker}:\n\n" + "\n\n".join(summaries)
        
        try:
            prompt = f"""Based on the following news summaries for {ticker}, provide a brief overall analysis:
- What is the general sentiment?
- What are the key themes or events?
- What might be the potential impact on the stock?

News summaries:
{truncate_text(combined_text, max_length=3000)}

Overall Analysis:"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            overall_summary = response.choices[0].message.content.strip()
            logger.info(f"Generated overall summary for {ticker}")
            return overall_summary
        
        except Exception as e:
            logger.error(f"Failed to generate overall summary for {ticker}: {e}")
            return None
    
    def estimate_token_cost(self, text: str) -> Dict[str, Any]:
        """
        Estimate token usage and cost for text.
        
        Args:
            text: Text to estimate
        
        Returns:
            Dictionary with token count and cost estimates
        """
        # Rough estimation: ~4 characters per token
        estimated_tokens = len(text) // 4
        
        # GPT-3.5-turbo pricing (approximate)
        input_cost_per_1k = 0.0005
        output_cost_per_1k = 0.0015
        
        estimated_cost = (estimated_tokens / 1000) * input_cost_per_1k
        
        return {
            'estimated_input_tokens': estimated_tokens,
            'estimated_cost_usd': estimated_cost,
            'model': self.model
        }
