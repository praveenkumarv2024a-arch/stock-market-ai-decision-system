from src.data.fundamentals import fetch_fundamentals
from src.data.storage import DataStore

# Manually tracking the list we know are in the app, or we could fetch from DB
# Ideally app.py has the state.
import sqlite3

STOCKS = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "TATAMOTORS.NS", "SBIN.NS", "ZOMATO.NS"]

def refresh_all():
    db = DataStore()
    print("Refetching fundamentals with new metrics...")
    for symbol in STOCKS:
        print(f"Update: {symbol}")
        data = fetch_fundamentals(symbol)
        if data:
            db.save_fundamentals(data, symbol)
    print("Done.")

if __name__ == "__main__":
    refresh_all()
