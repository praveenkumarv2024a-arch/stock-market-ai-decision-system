from src.features.engineer import FeatureEngineer
from src.data.storage import DataStore

def debug_data():
    symbol = "RELIANCE.NS"
    print(f"Testing Data for {symbol}...")
    
    # 1. Check DB directly
    db = DataStore()
    conn = db.get_connection()
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM stock_prices WHERE symbol='{symbol}'")
        count = cur.fetchone()[0]
        print(f"DB Row Count for {symbol}: {count}")
    except Exception as e:
        print(f"DB Error: {e}")
    finally:
        conn.close()

    # 2. Check Feature Engineer
    fe = FeatureEngineer()
    try:
        df = fe.prepare_data(symbol, is_training=False)
        if df is None:
            print("FeatureEngineer returned None")
        elif df.empty:
            print("FeatureEngineer returned Empty DF")
        else:
            print(f"FeatureEngineer Success! Rows: {len(df)}")
            print(df.tail(1))
    except Exception as e:
        print(f"FeatureEngineer Error: {e}")

if __name__ == "__main__":
    debug_data()
