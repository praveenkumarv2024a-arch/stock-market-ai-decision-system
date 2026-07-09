import time
from src.data.storage import DataStore

print("Testing DB Connection...")
start = time.time()
try:
    db = DataStore()
    news = db.get_all_news(limit=50)
    print(f"Fetched {len(news)} news items in {time.time() - start:.4f}s")
    
    start_port = time.time()
    holdings = db.get_portfolio()
    print(f"Fetched {len(holdings)} holdings in {time.time() - start_port:.4f}s")
    
except Exception as e:
    print(f"DB Error: {e}")
