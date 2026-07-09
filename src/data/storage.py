import sqlite3
import pandas as pd
from datetime import datetime
import os

class DataStore:
    def __init__(self, db_path="data/market_data.db"):
        self.db_path = db_path
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.create_tables()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def create_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Stock Prices Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                UNIQUE(symbol, timestamp)
            )
        ''')
        
        # News Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                title TEXT NOT NULL,
                link TEXT UNIQUE,
                published DATETIME,
                summary TEXT,
                sentiment_score REAL,
                fetched_at DATETIME
            )
        ''')
        
        # Fundamentals Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fundamentals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                fetched_at DATETIME NOT NULL,
                metric TEXT NOT NULL,
                value REAL,
                UNIQUE(symbol, fetched_at, metric)
            )
        ''')
        
        # Portfolio Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio (
                symbol TEXT PRIMARY KEY,
                quantity INTEGER,
                avg_price REAL,
                last_updated DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()

    def add_portfolio_holding(self, symbol, quantity, price):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            # Check existing
            cursor.execute("SELECT quantity, avg_price FROM portfolio WHERE symbol=?", (symbol,))
            row = cursor.fetchone()
            
            if row:
                old_qty, old_price = row
                new_qty = old_qty + quantity
                # Weighted Average Price
                if new_qty > 0:
                    new_avg = ((old_qty * old_price) + (quantity * price)) / new_qty
                else:
                    new_avg = 0
                
                cursor.execute("UPDATE portfolio SET quantity=?, avg_price=?, last_updated=? WHERE symbol=?", 
                               (new_qty, new_avg, datetime.now(), symbol))
            else:
                cursor.execute("INSERT INTO portfolio (symbol, quantity, avg_price, last_updated) VALUES (?, ?, ?, ?)",
                               (symbol, quantity, price, datetime.now()))
            
            conn.commit()
            print(f"Updated portfolio: {symbol}")
        except Exception as e:
            print(f"Error adding to portfolio: {e}")
        finally:
            conn.close()

    def get_portfolio(self):
        conn = self.get_connection()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM portfolio")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def delete_portfolio_holding(self, symbol):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM portfolio WHERE symbol=?", (symbol,))
            conn.commit()
        finally:
            conn.close()

    def save_stock_data(self, df, symbol):
        if df is None or df.empty:
            return
        
        conn = self.get_connection()
        try:
            # yfinance returns index as DatetimeIndex (often localized)
            # We want to flatten it to columns
            data = df.copy()
            data.reset_index(inplace=True)
            
            # Stanardize column names
            # Expected yfinance cols: Date/Datetime, Open, High, Low, Close, Volume
            # Rename first col to timestamp if it's Date/Datetime
            if 'Date' in data.columns:
                data.rename(columns={'Date': 'timestamp'}, inplace=True)
            elif 'Datetime' in data.columns:
                data.rename(columns={'Datetime': 'timestamp'}, inplace=True)
            
            # Ensure columns are present and lowercase for consistency map
            # Actually we mapped to DB columns manually or use to_sql
            # Let's use specific insert to handle duplicates specifically if needed
            # or use pandas to_sql with if_exists='append' (but that fails on constraint)
            
            # Simple approach: iterate and execute insert or ignore
            cursor = conn.cursor()
            for _, row in data.iterrows():
                # Convert timestamp to string if it's not already
                ts = row['timestamp'].isoformat() if hasattr(row['timestamp'], 'isoformat') else str(row['timestamp'])
                
                cursor.execute('''
                    INSERT OR IGNORE INTO stock_prices (symbol, timestamp, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol, ts, 
                    row.get('Open'), row.get('High'), row.get('Low'), row.get('Close'), row.get('Volume')
                ))
            conn.commit()
            print(f"Saved {len(data)} price records for {symbol}")
        except Exception as e:
            print(f"Error saving stock data for {symbol}: {e}")
        finally:
            conn.close()

    def save_news(self, df, symbol):
        if df is None or df.empty:
            return
            
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            fetched_at = datetime.now()
            
            for _, row in df.iterrows():
                cursor.execute('''
                    INSERT OR IGNORE INTO news (symbol, title, link, published, summary, sentiment_score, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol, row['title'], row['link'], 
                    row['published'], row.get('summary', ''), 
                    row.get('sentiment_score'), # Add sentiment_score
                    fetched_at
                ))
            conn.commit()
            print(f"Saved news for {symbol}")
        except Exception as e:
            print(f"Error saving news for {symbol}: {e}")
        finally:
            conn.close()

    def save_fundamentals(self, fundamentals, symbol):
        if not fundamentals:
            return
            
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            fetched_at = datetime.now()
            
            # Fundamentals is a dict: {metric: value}
            # We want to save each metric
            for metric, value in fundamentals.items():
                if metric == "symbol": continue
                
                # Check if value is basic type
                if isinstance(value, (int, float, str)) or value is None:
                    cursor.execute('''
                        INSERT OR IGNORE INTO fundamentals (symbol, fetched_at, metric, value)
                        VALUES (?, ?, ?, ?)
                    ''', (symbol, fetched_at, metric, value))
            
            conn.commit()
            print(f"Saved fundamentals for {symbol}")
        except Exception as e:
            print(f"Error saving fundamentals for {symbol}: {e}")
        finally:
            conn.close()

    def get_latest_fundamentals(self, symbol):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            # Get latest date
            cursor.execute("SELECT MAX(fetched_at) FROM fundamentals WHERE symbol=?", (symbol,))
            latest = cursor.fetchone()[0]
            if not latest: return {}
            
            cursor.execute("SELECT metric, value FROM fundamentals WHERE symbol=? AND fetched_at=?", (symbol, latest))
            rows = cursor.fetchall()
            return {row[0]: row[1] for row in rows}
        finally:
            conn.close()

    def get_latest_price(self, symbol):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT close FROM stock_prices WHERE symbol=? ORDER BY timestamp DESC LIMIT 1", (symbol,))
            row = cursor.fetchone()
            if row:
                return row[0]
            return 0.0
        finally:
            conn.close()

    def get_recent_news(self, symbol, limit=5):
        conn = self.get_connection()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT title, link, published, sentiment_score, summary, symbol 
                FROM news 
                WHERE symbol=? 
                ORDER BY published DESC 
                LIMIT ?
            ''', (symbol, limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_all_news(self, limit=50):
        conn = self.get_connection()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT title, link, published, sentiment_score, summary, symbol
                FROM news 
                WHERE published >= date('now', '-12 months')
                ORDER BY published DESC 
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

if __name__ == "__main__":
    db = DataStore()
    print("Database verified at", db.db_path)
