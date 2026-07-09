
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from src.data.yahoo_news import fetch_and_store_yahoo_news, fetch_google_fallback
from src.data.storage import DataStore
import json

symbols = ["CIPLA.NS", "HDFCBANK.NS"]

print("--- Testing Google Fallback Direct ---")
for sym in symbols:
    print(f"Fetching Google Fallback for {sym}...")
    items = fetch_google_fallback(sym)
    print(f"Found {len(items)} items.")
    for i in items[:3]:
        print(f"  - {i['title']} ({i['providerPublishTime']})")

print("\n--- Testing Full Pipeline ---")
for sym in symbols:
    print(f"Running pipeline for {sym}...")
    fetch_and_store_yahoo_news(sym)

print("\n--- Checking Database ---")
db = DataStore()
for sym in symbols:
    news = db.get_recent_news(sym)
    print(f"DB Items for {sym}: {len(news)}")
    if news:
        print(f"  Latest: {news[0]['title']} ({news[0]['published']})")
