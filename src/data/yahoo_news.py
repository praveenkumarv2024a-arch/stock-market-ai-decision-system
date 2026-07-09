
import yfinance as yf
import pandas as pd
from datetime import datetime
from textblob import TextBlob
from src.data.storage import DataStore
import feedparser
import requests

def fetch_google_fallback(symbol, days=3):
    """Fallback using Google News RSS with headers"""
    try:
        # Clean symbol for search (e.g. RELIANCE.NS -> Reliance Industries)
        query = symbol.replace('.NS', '').replace('.BO', '')
        # Force recent news
        query += f" when:{days}d"
        encoded = query.replace(" ", "+")
        # scoring=n enforces "Newest"
        url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en&scoring=n"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        feed = feedparser.parse(response.content)
        
        news_items = []
        for entry in feed.entries:
            # Parse published time
            pub_ts = time.time()
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                 pub_ts = time.mktime(entry.published_parsed)
            
            news_items.append({
                'title': entry.title,
                'link': entry.link,
                'providerPublishTime': pub_ts,
                'publisher': entry.source.title if hasattr(entry, 'source') else 'Google News'
            })
        return news_items
    except Exception as e:
        print(f"Google Fallback Error for {symbol}: {e}")
        return []

import time

def fetch_and_store_yahoo_news(symbol, db_path="data/market_data.db"):
    try:
        all_news = []
        
        # 1. Try Yahoo Finance
        try:
            ticker = yf.Ticker(symbol)
            y_news = ticker.news
            if y_news:
                all_news.extend(y_news)
        except:
            pass
            
        # 2. Always fetch Google News to ensure freshness (merged)
        g_news = fetch_google_fallback(symbol, days=3)
        if g_news:
             all_news.extend(g_news)
        
        if not all_news:
            # Try 7 days fallback
            # print(f"No news for {symbol}, trying 7 days...")
            g_news_wide = fetch_google_fallback(symbol, days=7)
            all_news.extend(g_news_wide)
            
        if not all_news:
            print(f"No news found for {symbol} (All sources)")
            return

        db = DataStore(db_path)
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Track inserted links to avoid duplicates in this batch
        seen_links = set()

        # Sort by time descending (newest first)
        all_news.sort(key=lambda x: x.get('providerPublishTime', 0), reverse=True)

        for item in all_news:
            title = item.get('title', '')
            link = item.get('link', '')
            
            if link in seen_links:
                continue
            seen_links.add(link)
            
            # Timestamp handling
            pub_ts = item.get('providerPublishTime', 0)
            if pub_ts:
                try:
                    published = datetime.fromtimestamp(pub_ts).isoformat()
                except:
                    published = datetime.now().isoformat()
            else:
                published = datetime.now().isoformat()
                
            blob = TextBlob(title)
            sentiment = blob.sentiment.polarity 

            cursor.execute("""
                INSERT OR IGNORE INTO news (symbol, title, link, published, sentiment_score, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (symbol, title, link, published, sentiment, datetime.now().isoformat()))
            
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error fetching News pipeline for {symbol}: {e}")

if __name__ == "__main__":
    # Test
    symbol = "RELIANCE.NS"
    print(f"Fetching news for {symbol}...")
    fetch_and_store_yahoo_news(symbol)
    
    # Verify
    try:
        db = DataStore()
        news = db.get_recent_news(symbol)
        print(f"Found {len(news)} news items.")
        for n in news:
            print(f"- {n['title']} ({n['sentiment_score']})")
    except Exception as e:
        print(f"Verification failed: {e}")
