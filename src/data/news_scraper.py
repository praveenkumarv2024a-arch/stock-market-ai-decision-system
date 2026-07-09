import feedparser
import pandas as pd
from datetime import datetime

def fetch_google_news(query):
    """
    Fetches news from Google News RSS feed for a specific query.
    
    Args:
        query (str): The search query (e.g., 'Reliance Industries NSE').
        
    Returns:
        pd.DataFrame: DataFrame containing news title, link, and published date.
    """
    encoded_query = query.replace(" ", "+")
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
    
    feed = feedparser.parse(url)
    
    news_list = []
    for entry in feed.entries:
        # Parse date
        published = datetime.now().isoformat()
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            import time
            published = datetime.fromtimestamp(time.mktime(entry.published_parsed)).isoformat()
            
        news_list.append({
            "title": entry.title,
            "link": entry.link,
            "published": published,
            "summary": entry.summary if 'summary' in entry else ""
        })
        
    return pd.DataFrame(news_list)

if __name__ == "__main__":
    # Test
    df = fetch_google_news("Reliance Industries stock filetype:html") # added filetype to avoid some generic google/search noise potentially, though standard query works fine.
    # Let's stick to standard query
    df = fetch_google_news("Reliance Industries NSE")
    print(df.head())
