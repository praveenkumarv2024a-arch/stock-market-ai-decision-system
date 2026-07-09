import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

DB_PATH = "data/market_data.db"

def get_connection():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return None
    return sqlite3.connect(DB_PATH)

def analyze_prices(symbol):
    conn = get_connection()
    if not conn: return
    
    query = f"SELECT * FROM stock_prices WHERE symbol='{symbol}' ORDER BY timestamp"
    df = pd.read_sql(query, conn)
    conn.close()
    
    if df.empty:
        print(f"No price data found for {symbol}")
        return

    print(f"Price Data for {symbol}: {len(df)} records")
    print(df.tail())
    
    # Plot
    fig = go.Figure(data=[go.Candlestick(x=df['timestamp'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'])])
    
    fig.update_layout(title=f'{symbol} Stock Price', yaxis_title='Price (INR)')
    # fig.show() # Cannot show interactive in this env easily, saving to HTML
    fig.write_html(f"data/{symbol}_price_chart.html")
    print(f"Saved chart to data/{symbol}_price_chart.html")

def analyze_news_sentiment(symbol):
    conn = get_connection()
    if not conn: return
    
    query = f"SELECT * FROM news WHERE symbol='{symbol}'"
    df = pd.read_sql(query, conn)
    conn.close()
    
    if df.empty:
        print(f"No news data found for {symbol}")
        return

    print(f"News Data for {symbol}: {len(df)} records")
    print(df[['title', 'sentiment_score']].head())
    
    # Sentiment Distribution
    fig = px.histogram(df, x="sentiment_score", title=f"Sentiment Distribution for {symbol}")
    fig.write_html(f"data/{symbol}_sentiment_dist.html")
    print(f"Saved sentiment chart to data/{symbol}_sentiment_dist.html")

if __name__ == "__main__":
    # Ensure we assume some data exists. If not, this will print "No data"
    # User needs to run main.py first.
    analyze_prices("RELIANCE.NS")
    analyze_news_sentiment("RELIANCE.NS")
