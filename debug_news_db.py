import sqlite3
import datetime

db_path = "data/market_data.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Current System Time (Python) ---")
print(datetime.datetime.now())

print("\n--- SQLite 'now' ---")
cursor.execute("SELECT datetime('now', 'localtime')")
print(cursor.fetchone()[0])
cursor.execute("SELECT date('now', '-12 months')")
print(f"Filter date (SQLite): {cursor.fetchone()[0]}")

print("\n--- Sample News Items (Raw) ---")
cursor.execute("SELECT title, published FROM news ORDER BY published DESC LIMIT 5")
rows = cursor.fetchall()
for r in rows:
    print(f"Date: {r[1]} | Title: {r[0][:50]}...")

conn.close()
