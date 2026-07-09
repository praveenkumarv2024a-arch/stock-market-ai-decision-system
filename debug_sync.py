import sys
import os
import pandas as pd
import joblib

# Setup path
sys.path.append(os.path.abspath("."))

from src.models.explain import ModelExplainer
from src.features.engineer import FeatureEngineer

# Load common model
MODEL_PATH = "data/best_model.pkl"
try:
    model = joblib.load(MODEL_PATH)
    print(f"Loaded model from {MODEL_PATH}")
except:
    print("Could not load model")
    sys.exit(1)

SYMBOL = "INFY.NS"

print(f"\n--- DEBUG SYNC FOR {SYMBOL} ---")

# 1. Simulate DASHBOARD Logic (from app.py / predict.py)
print("\n[DASHBOARD LOGIC]")
fe = FeatureEngineer()
df = fe.prepare_data(SYMBOL, is_training=False)
latest = df.iloc[-1]
rsi = latest.get('RSI', 50)
print(f"Input RSI: {rsi}")

# Custom logic from app.py background loop
decision = "HOLD"
confidence = 0.0

# RSI Override
if rsi < 30:
    decision = "BUY"
    confidence = 0.90
    print("Triggered: RSI < 30 Override")
elif rsi > 70:
    decision = "SELL" 
    confidence = 0.90
    print("Triggered: RSI > 70 Override")
else:
    # Model Prediction
    X = df.iloc[[-1]].drop(columns=['target', 'future_close', 'future_return', 'date'], errors='ignore').select_dtypes(include=['number'])
    
    if hasattr(model, 'feature_names_in_'):
        X = X.reindex(columns=model.feature_names_in_, fill_value=0)
    
    probs = model.predict_proba(X)[0]
    classes = model.classes_
    p_sell = 0.0
    p_buy = 0.0
    
    for idx, cls in enumerate(classes):
        if cls <= 0: p_sell += probs[idx]
        if cls > 0: p_buy += probs[idx]
        
    print(f"Probs: Sell={p_sell:.4f}, Buy={p_buy:.4f}")
    
    if p_buy >= p_sell:
        decision = "BUY"
        confidence = p_buy / (p_buy + p_sell)
    else:
        decision = "SELL"
        confidence = p_sell / (p_buy + p_sell)

print(f"DASHBOARD DECISION: {decision} ({confidence:.2f})")


# 2. Simulate ANALYSIS Logic (ModelExplainer)
print("\n[ANALYSIS LOGIC]")
explainer = ModelExplainer(model=model) # Inject same model
text = explainer.get_natural_language_explanation(SYMBOL)
print(f"ANALYSIS TEXT START: {text[:100]}...")

# Parse text for decision
if "suggests BUY" in text:
    analysis_decision = "BUY"
elif "suggests SELL" in text:
    analysis_decision = "SELL"
else:
    analysis_decision = "UNKNOWN"

print(f"ANALYSIS DECISION: {analysis_decision}")

if decision == analysis_decision:
    print("\nSUCCESS: SYNCED")
else:
    print("\nFAIL: MISMATCH")
