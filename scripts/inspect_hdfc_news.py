
import sqlite3
import pandas as pd

def check_hdfc_news():
    conn = sqlite3.connect('data/market_data.db')
    cursor = conn.cursor()
    
    print("--- News for HDFCBANK.NS ---")
    cursor.execute("SELECT title, link, published FROM news WHERE symbol='HDFCBANK.NS'")
    rows = cursor.fetchall()
    
    for row in rows:
        print(f"[{row[2]}] {row[0]}")
        
    conn.close()

if __name__ == "__main__":
    check_hdfc_news()
