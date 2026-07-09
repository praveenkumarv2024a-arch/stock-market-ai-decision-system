import time
from src.features.engineer import FeatureEngineer
import json
import os

TRACKED_FILE = 'src/data/tracked_stocks.json'

def load_tracked_stocks():
    if os.path.exists(TRACKED_FILE):
        with open(TRACKED_FILE, 'r') as f:
            return json.load(f)
    return []

def debug_full_loop():
    TRACKED_STOCKS = load_tracked_stocks()
    print(f"Loaded {len(TRACKED_STOCKS)} stocks.")
    
    fe = FeatureEngineer()
    data = []
    
    print("Starting Loop...")
    for i, symbol in enumerate(TRACKED_STOCKS):
        try:
            print(f"Processing {i+1}/{len(TRACKED_STOCKS)}: {symbol}")
            # 1. Get Data
            df = fe.prepare_data(symbol, is_training=False)
            if df is None or df.empty:
                print(f"  -> EMPTY DF for {symbol}")
                continue
                
            latest = df.iloc[-1]
            print(f"  -> Success. Price: {latest['close']}")

            # Predict Logic (Replicating app.py)
            drop_cols = ['target', 'future_close', 'future_return', 'date']
            import numpy as np
            X = df.iloc[[-1]].drop(columns=[c for c in drop_cols if c in df.columns]).select_dtypes(include=[np.number])
            
            # Load Model
            from joblib import load
            try:
                model = load('data/best_model.pkl')
                pred = model.predict(X)[0]
                print(f"  -> Prediction: {pred}")
            except Exception as me:
                 print(f"  -> Model Error: {me}")

            data.append(symbol)
            
        except Exception as e:
            print(f"  -> ERROR for {symbol}: {e}")
            import traceback
            traceback.print_exc()

    print(f"Loop Complete. Total items: {len(data)}")

if __name__ == "__main__":
    debug_full_loop()
