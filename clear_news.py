import sqlite3
conn = sqlite3.connect("data/market_data.db")
cursor = conn.cursor()
cursor.execute("DELETE FROM news")
conn.commit()
conn.close()
print("News table cleared.")
