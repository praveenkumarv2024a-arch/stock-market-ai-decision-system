from src.data.storage import DataStore
import json

db = DataStore()
symbol = "INFY.NS"

print(f"--- Checking Data for {symbol} ---")

# Check Fundamentals
fund = db.get_latest_fundamentals(symbol)
print(f"\n[Fundamentals]")
if fund:
    print(json.dumps(fund, indent=2))
else:
    print("NO DATA FOUND")

# Check News
news = db.get_recent_news(symbol)
print(f"\n[News]")
print(f"Count: {len(news)}")
if news:
    print(f"First Item: {news[0].get('title')}")
else:
    print("NO NEWS FOUND")
