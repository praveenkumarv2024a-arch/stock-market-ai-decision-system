
from src.features.engineer import FeatureEngineer
from src.data.storage import DataStore
import pandas as pd

def test_logic(symbol):
    print(f"\n--- Testing App Logic for {symbol} ---")
    
    # 1. Test Feature Engineer Merge (Sentiment = 0 issue)
    print("1. Feature Engineer Prepare Data:")
    fe = FeatureEngineer()
    try:
        df = fe.prepare_data(symbol, is_training=False)
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            print(f"Latest Date: {latest.name}")
            print(f"Sentiment: {latest.get('sentiment_score', 'MISSING')}")
            print(f"Close: {latest.get('close')}")
            
            # Check if we have sentiment in DB at all
            sent_df = fe.load_news_sentiment(symbol)
            print(f"Sentiment DB Rows: {len(sent_df)}")
            if not sent_df.empty:
                print("Latest Sentiment Dates:", sent_df.index[-3:].tolist())
        else:
            print("DF is empty/None")
    except Exception as e:
        print(f"FE Error: {e}")

    # 2. Test Details API Logic (Fundamentals)
    print("\n2. Fundamentals Logic:")
    db = DataStore()
    try:
        fund = db.get_latest_fundamentals(symbol)
        print(f"Fundamentals Keys: {list(fund.keys())}")
        print(f"Sample Values: {list(fund.values())[:3]}")
    except Exception as e:
        print(f"DB Error: {e}")

if __name__ == "__main__":
    test_logic("RELIANCE.NS")
    test_logic("INFY.NS")
