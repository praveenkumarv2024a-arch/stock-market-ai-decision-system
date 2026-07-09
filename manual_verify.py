from src.data.fundamentals import fetch_and_store_fundamentals
from src.data.storage import DataStore
import time

symbol = "TCS.NS"
print(f"Fetching fundamentals for {symbol}...")
fetch_and_store_fundamentals(symbol)

print("Checking database...")
db = DataStore()
fund = db.get_latest_fundamentals(symbol)

if fund:
    print("\nSUCCESS! Fundamentals found:")
    for k, v in fund.items():
        print(f"{k}: {v}")
else:
    print("\nFAILURE: No fundamentals in DB.")

# Check News as well
print("\nChecking News...")
news = db.get_recent_news(symbol)
if news:
    print(f"Found {len(news)} news items.")
    print(f"Latest: {news[0]['title']}")
else:
    print("No news found.")
