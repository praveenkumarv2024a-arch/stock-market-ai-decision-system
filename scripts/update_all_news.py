
import json
import time
from src.data.yahoo_news import fetch_and_store_yahoo_news

def update_all():
    print("Loading tracked stocks...")
    with open('src/data/tracked_stocks.json', 'r') as f:
        stocks = json.load(f)

    print(f"Updating news for {len(stocks)} stocks...")
    
    for i, symbol in enumerate(stocks):
        print(f"[{i+1}/{len(stocks)}] Fetching news for {symbol}...")
        fetch_and_store_yahoo_news(symbol)
        time.sleep(1) # Polite delay

    print("News update complete.")

if __name__ == "__main__":
    update_all()
