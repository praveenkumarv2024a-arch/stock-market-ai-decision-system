
import sqlite3
import pandas as pd

def check_db():
    conn = sqlite3.connect('data/market_data.db')
    cursor = conn.cursor()
    
    print("--- Fundamentals Summary ---")
    try:
        df = pd.read_sql("SELECT symbol, COUNT(*) as count, MAX(fetched_at) as last_update FROM fundamentals GROUP BY symbol", conn)
        print(df)
        
        print("\n--- Fundamentals Sample (RELIANCE.NS) ---")
        cursor.execute("SELECT * FROM fundamentals WHERE symbol='RELIANCE.NS' LIMIT 5")
        print(cursor.fetchall())

        print("\n--- Fundamentals Sample (TCS.NS) ---")
        cursor.execute("SELECT * FROM fundamentals WHERE symbol='TCS.NS' LIMIT 5")
        print(cursor.fetchall())
        
    except Exception as e:
        print(e)
        
    print("\n--- News Summary ---")
    try:
        df = pd.read_sql("SELECT symbol, COUNT(*) as count FROM news GROUP BY symbol", conn)
        print(df)
    except Exception as e:
        print(e)

    conn.close()

if __name__ == "__main__":
    check_db()
