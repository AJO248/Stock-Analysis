"""
Demo data for testing the application without live scraping.
Use this when news APIs are not available.
"""

from datetime import datetime, timedelta

def get_demo_articles():
    """Generate demo articles for testing."""
    base_date = datetime.now()
    
    demo_articles = [
        {
            'title': 'Apple Announces Record Q1 Earnings, Stock Rises 5%',
            'content': 'Apple Inc. reported better-than-expected earnings for Q1 2026, with revenue reaching $120 billion. The tech giant saw strong iPhone sales and growing services revenue. CEO Tim Cook highlighted the success of their AI integration efforts and the upcoming Vision Pro 2 launch.',
            'url': 'https://example.com/apple-earnings-q1-2026',
            'ticker': 'AAPL',
            'source': 'Demo Source',
            'published_date': (base_date - timedelta(hours=2)).isoformat(),
        },
        {
            'title': 'Microsoft Cloud Revenue Surges 30% Year-Over-Year',
            'content': 'Microsoft Corporation continues to dominate the cloud market with Azure revenue growing 30% YoY. The company also announced new AI partnerships and expansion of Copilot services across all platforms. Azure now powers 40% of Fortune 500 companies.',
            'url': 'https://example.com/microsoft-cloud-growth',
            'ticker': 'MSFT',
            'source': 'Demo Source',
            'published_date': (base_date - timedelta(hours=5)).isoformat(),
        },
        {
            'title': 'Google Unveils Advanced AI Search Features',
            'content': 'Alphabet Inc. introduced revolutionary AI-powered search capabilities that integrate real-time information with personalized recommendations. The new features leverage Google\'s latest Gemini Ultra model and promise to redefine how users interact with information.',
            'url': 'https://example.com/google-ai-search',
            'ticker': 'GOOGL',
            'source': 'Demo Source',
            'published_date': (base_date - timedelta(hours=8)).isoformat(),
        },
        {
            'title': 'Tesla Cybertruck Production Reaches 2,000 Units Per Week',
            'content': 'Tesla Inc. announced a major production milestone for the Cybertruck, now manufacturing 2,000 units weekly. The company also revealed plans for a more affordable model and expansion of charging infrastructure. Stock analysts upgraded their price targets following the news.',
            'url': 'https://example.com/tesla-cybertruck-production',
            'ticker': 'TSLA',
            'source': 'Demo Source',
            'published_date': (base_date - timedelta(hours=12)).isoformat(),
        },
        {
            'title': 'Amazon Prime Reaches 300 Million Subscribers Globally',
            'content': 'Amazon.com Inc. celebrated a major milestone as Prime membership surpassed 300 million subscribers worldwide. AWS continued its strong growth trajectory, and the company announced plans for drone delivery expansion to 20 new cities.',
            'url': 'https://example.com/amazon-prime-milestone',
            'ticker': 'AMZN',
            'source': 'Demo Source',
            'published_date': (base_date - timedelta(hours=24)).isoformat(),
        },
        {
            'title': 'Apple\'s AI Chip Development Accelerates, Challenges NVIDIA',
            'content': 'Sources reveal Apple is making significant progress on proprietary AI chips that could rival NVIDIA\'s offerings. The chips are designed specifically for on-device AI processing in future iPhones and Macs, reducing reliance on cloud computing.',
            'url': 'https://example.com/apple-ai-chip',
            'ticker': 'AAPL',
            'source': 'Demo Source',
            'published_date': (base_date - timedelta(days=1)).isoformat(),
        },
        {
            'title': 'Microsoft Acquires Leading Cybersecurity Startup for $8B',
            'content': 'Microsoft announced the acquisition of CyberShield, a cutting-edge cybersecurity company, for $8 billion. The move strengthens Microsoft\'s security portfolio and is expected to integrate seamlessly with Azure and Microsoft 365 platforms.',
            'url': 'https://example.com/microsoft-cybersecurity-acquisition',
            'ticker': 'MSFT',
            'source': 'Demo Source',
            'published_date': (base_date - timedelta(days=1, hours=6)).isoformat(),
        },
        {
            'title': 'Alphabet Reports Breakthrough in Quantum Computing',
            'content': 'Google\'s quantum computing division announced a major breakthrough that could solve previously impossible computational problems. The advancement puts Google years ahead of competitors and opens new possibilities for drug discovery and cryptography.',
            'url': 'https://example.com/google-quantum-breakthrough',
            'ticker': 'GOOGL',
            'source': 'Demo Source',
            'published_date': (base_date - timedelta(days=2)).isoformat(),
        },
        {
            'title': 'Tesla Energy Storage Business Grows 200%, Outpaces Auto Sales',
            'content': 'Tesla\'s energy storage division is experiencing explosive growth, with Megapack installations increasing 200% year-over-year. Some analysts suggest energy could become Tesla\'s primary revenue source within 5 years.',
            'url': 'https://example.com/tesla-energy-growth',
            'ticker': 'TSLA',
            'source': 'Demo Source',
            'published_date': (base_date - timedelta(days=2, hours=12)).isoformat(),
        },
        {
            'title': 'Amazon Launches Revolutionary AI Shopping Assistant',
            'content': 'Amazon unveiled an AI-powered shopping assistant that can understand natural language, predict needs, and provide personalized recommendations. Early testing shows a 40% increase in customer satisfaction and 25% boost in sales.',
            'url': 'https://example.com/amazon-ai-assistant',
            'ticker': 'AMZN',
            'source': 'Demo Source',
            'published_date': (base_date - timedelta(days=3)).isoformat(),
        },
    ]
    
    return demo_articles


def get_demo_summaries():
    """Generate demo summaries for testing."""
    return {
        'articles': [
            {
                'summary': 'Apple exceeded Q1 expectations with $120B revenue driven by iPhone sales and services growth.',
                'stock_impact': 'bullish',
                'key_events': ['Record Q1 earnings', 'Strong iPhone sales', 'AI integration success'],
                'sentiment': 'Very Positive',
                'key_points': [
                    'Revenue: $120 billion (beat estimates)',
                    'iPhone sales remain strong',
                    'Services revenue growing',
                    'AI features gaining traction',
                    'Vision Pro 2 launch upcoming'
                ]
            },
            {
                'summary': 'Microsoft Azure revenue surged 30% YoY, solidifying cloud dominance with new AI partnerships.',
                'stock_impact': 'bullish',
                'key_events': ['30% Azure growth', 'AI partnerships expansion', 'Copilot adoption'],
                'sentiment': 'Positive',
                'key_points': [
                    'Azure revenue up 30% YoY',
                    'Powers 40% of Fortune 500',
                    'Copilot integration expanding',
                    'Strong enterprise adoption',
                    'AI cloud services leading'
                ]
            },
        ]
    }


if __name__ == "__main__":
    articles = get_demo_articles()
    print(f"Generated {len(articles)} demo articles")
    for article in articles:
        print(f"  - {article['ticker']}: {article['title']}")
