import yfinance as yf
import pandas as pd

def fetch_stock_data(ticker, period="1d", interval="1m"):
    """
    Fetches live/historical stock data for a given ticker.
    
    Args:
        ticker (str): The stock ticker symbol (e.g., 'RELIANCE.NS').
        period (str): The period to fetch data for (e.g., '1d', '1mo', '1y').
        interval (str): The data interval (e.g., '1m', '1d').
        
    Returns:
        pd.DataFrame: DataFrame containing the stock data.
    """
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period, interval=interval)
        if data.empty:
            print(f"No data found for {ticker}")
            return None
        return data
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

if __name__ == "__main__":
    # Test
    df = fetch_stock_data("RELIANCE.NS")
    if df is not None:
        print(df.tail())
