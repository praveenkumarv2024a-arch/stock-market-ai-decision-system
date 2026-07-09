
from src.data.news_scraper import fetch_google_news
from src.data.fundamentals import fetch_fundamentals
from src.models.nlp import NewsSentimentAnalyzer
import pandas as pd
import json

def debug_fetch(symbol):
    print(f"\n--- Debugging {symbol} ---")
    
    # 1. Fundamentals
    print(f"Fetching fundamentals...")
    try:
        fund = fetch_fundamentals(symbol)
        print("Fundamentals keys:", fund.keys() if fund else "None")
        print("Fundamentals payload:", json.dumps(fund, indent=2))
    except Exception as e:
        print(f"Fundamentals Error: {e}")
        
    # 2. News
    print(f"Fetching news...")
    try:
        analyzer = NewsSentimentAnalyzer()
        query = f"{symbol} stock news"
        news_df = fetch_google_news(query)
        if not news_df.empty:
            print(f"Found {len(news_df)} articles.")
            print(news_df[['title', 'published']].head())
            
            news_df['sentiment_score'] = news_df['title'].apply(analyzer.get_sentiment)
            print("Sentiment Scores:", news_df['sentiment_score'].tolist())
        else:
            print("No news found.")
    except Exception as e:
        print(f"News Error: {e}")

if __name__ == "__main__":
    debug_fetch("INFY.NS")
    debug_fetch("RELIANCE.NS")
