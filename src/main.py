import argparse
from src.data.stock_price import fetch_stock_data
from src.data.news_scraper import fetch_google_news
from src.data.fundamentals import fetch_and_store_fundamentals
from src.data.storage import DataStore
from src.models.nlp import NewsSentimentAnalyzer
import time

# List of Indian Stocks to Track (Example)
STOCKS = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "TATAMOTORS.NS"]

def process_symbol(symbol, live=False, db=None, analyzer=None):
    """Fetches and saves data for a single symbol."""
    if db is None: db = DataStore()
    if analyzer is None: analyzer = NewsSentimentAnalyzer()
    
    print(f"\nProcessing {symbol}...")
    
    # 1. Fundamentals
    # fetch_and_store_fundamentals handles saving to DB internally
    fetch_and_store_fundamentals(symbol)
        
    # 2. News
    # 2. News
    # Use robust Yahoo/Google fetcher which handles saving internally
    from src.data.yahoo_news import fetch_and_store_yahoo_news
    fetch_and_store_yahoo_news(symbol)
        
    # 3. Stock Price
    if live:
        print(f"Fetching live 1m data for {symbol}...")
        price_df = fetch_stock_data(symbol, period="1d", interval="1m")
        if price_df is None or price_df.empty:
            print(f"Live data unavailable (Market Closed?), fetching history...")
            # Fallback to daily data
            price_df = fetch_stock_data(symbol, period="1mo", interval="1d")
    else:
        price_df = fetch_stock_data(symbol, period="1mo", interval="1d")
        
    if price_df is not None and not price_df.empty:
        db.save_stock_data(price_df, symbol)
    else:
        # Raise error so the UI knows
        raise ValueError(f"No pricing data found for {symbol}. (Delisted or Invalid?)")

def run_pipeline(live=False):
    db = DataStore()
    sentiment_analyzer = NewsSentimentAnalyzer()
    
    print(f"Starting data collection for {len(STOCKS)} stocks...")
    
    for symbol in STOCKS:
        process_symbol(symbol, live, db, sentiment_analyzer)
            
    print("\nData collection cycle completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Run in live mode (fetch 1m data)")
    args = parser.parse_args()
    
    run_pipeline(live=args.live)
