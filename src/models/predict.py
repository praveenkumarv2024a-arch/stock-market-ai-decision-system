import joblib
import pandas as pd
import numpy as np
from src.features.engineer import FeatureEngineer

def predict_latest(symbols):
    # Lazy imports to speed up app startup
    from xgboost import XGBClassifier
    from lightgbm import LGBMClassifier
    
    print("--- AI Decision Engine ---")
    try:
        model = joblib.load("data/best_model.pkl")
    except:
        print("Model not found. Switching to Technical Fallback.")
        model = None

    model_type = type(model).__name__
    print(f"Loaded Model: {model_type}")

    fe = FeatureEngineer()
    
    results = []
    
    for symbol in symbols:
        # Load latest data
        df = fe.prepare_data(symbol)
        if df is None or df.empty:
            print(f"Skipping {symbol} (insufficient data)")
            continue
            
        latest_row = df.iloc[[-1]] 
        
        drop_cols = ['target', 'future_close', 'future_return', 'date']
        X = latest_row.drop(columns=[c for c in drop_cols if c in latest_row.columns])
        X = X.select_dtypes(include=[np.number])
        
        # --- Fix: Align columns ---
        if hasattr(model, "feature_names_in_"):
            expected_cols = model.feature_names_in_
            X = X.reindex(columns=expected_cols, fill_value=0)
        elif hasattr(model, "get_booster"):
            try:
                expected_cols = model.get_booster().feature_names
                if expected_cols:
                     X = X.reindex(columns=expected_cols, fill_value=0)
            except: pass
        
        # --- "Strongly Buy" Score Logic (0-100%) ---
        buy_score = 50.0 
        
        # 0. STRICT TECHNICAL OVERRIDES
        rsi = latest_row['RSI'].values[0] if 'RSI' in latest_row.columns else 50
        
        override = False
        if rsi < 30: 
            buy_score = 90.0 + (30 - rsi) 
            if buy_score > 99: buy_score = 99
            override = True
        elif rsi > 70:
            buy_score = 40.0 - (rsi - 70)
            if buy_score < 15: buy_score = 15
            override = True
            
        if not override and model:
            try:
                # 1. Try AI Probability
                if hasattr(model, "predict_proba"):
                    probs = model.predict_proba(X)[0]
                    classes = list(model.classes_)
                    buy_cls = max(classes)
                    sell_cls = min(classes)
                    
                    p_buy = probs[classes.index(buy_cls)]
                    p_sell = probs[classes.index(sell_cls)]
                    
                    buy_score = 50.0 + (p_buy * 50.0) - (p_sell * 50.0)
                    
                else:
                    # 2. AI Native Prediction (Fallback)
                    pred = model.predict(X)[0]
                    if pred == 1: buy_score = 75.0
                    elif pred == -1: buy_score = 25.0
                    else: buy_score = 50.0

            except Exception as e:
                print(f"AI Error: {e}")
                buy_score = 50.0

        # --- Multi-Factor Upgrades ---
        pe = latest_row['trailingPE'].iloc[0] if 'trailingPE' in latest_row.columns else 0
        pb = latest_row['priceToBook'].iloc[0] if 'priceToBook' in latest_row.columns else 0
        sent = latest_row['sentiment_score'].iloc[0] if 'sentiment_score' in latest_row.columns else 0
        
        if not override:
            if pe > 0:
                if pe < 15: buy_score += 10
                elif pe > 30: buy_score -= 10
                elif pe > 50: buy_score -= 15
            
            if pb > 0:
                if pb < 1.0: buy_score += 5
                elif pb > 5.0: buy_score -= 5
                
            if sent > 0.2: buy_score += 10
            elif sent < -0.2: buy_score -= 10
        
        # Clip to 15-99 (Aggressive Floor matching dashboard)
        buy_score = max(15, min(99, buy_score))
        
        # Text Label for legacy support or UI display
        decision_label = "Strongly Buy" # The metric name
        
        print(f"\n{symbol}:")
        print(f"  Price: {latest_row['close'].values[0]}")
        print(f"  RSI: {rsi:.2f}")
        print(f"  Buy Score: {buy_score:.1f}%")
        
        results.append({
            "Symbol": symbol,
            "Price": latest_row['close'].values[0],
            "Decision": decision_label,
            "Confidence": buy_score / 100.0 # Standardize to 0-1 for consistency
        })
        
    return pd.DataFrame(results)

if __name__ == "__main__":
    predict_latest(["RELIANCE.NS", "TCS.NS", "INFY.NS"])
