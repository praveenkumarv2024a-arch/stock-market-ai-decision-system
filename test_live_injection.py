import sys
import os
import pandas as pd
sys.path.append(os.getcwd())

from src.features.engineer import FeatureEngineer

def test_injection():
    fe = FeatureEngineer()
    symbol = "RELIANCE.NS"
    
    # 1. Normal Prep
    print("--- Normal Prep ---")
    df_normal = fe.prepare_data(symbol, is_training=False)
    if df_normal is None:
        print("No data found for symbol")
        return

    last_price = df_normal.iloc[-1]['close']
    last_rsi = df_normal.iloc[-1]['RSI']
    print(f"Normal Last Price: {last_price}")
    print(f"Normal RSI: {last_rsi}")
    
    # 2. Injected Prep (Massive price jump)
    print("\n--- Injected Prep (Price +10%) ---")
    fake_price = last_price * 1.10
    df_injected = fe.prepare_data(symbol, is_training=False, live_price=fake_price)
    
    inj_price = df_injected.iloc[-1]['close']
    inj_rsi = df_injected.iloc[-1]['RSI']
    print(f"Injected Last Price: {inj_price}")
    print(f"Injected RSI: {inj_rsi}")
    
    if abs(inj_price - fake_price) < 0.1:
        print("PASS: Price injection worked.")
    else:
        print("FAIL: Price injection failed.")
        
    if inj_rsi != last_rsi:
        print("PASS: RSI changed (Indicators recalculated).")
    else:
        print("FAIL: RSI did not change.")

if __name__ == "__main__":
    test_injection()
