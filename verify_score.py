import sys
import os
import pandas as pd

# Add src to path
sys.path.append(os.getcwd())

try:
    from src.models.predict import predict_latest
    from src.models.explain import ModelExplainer
    
    print("--- Verifying Predict Logic ---")
    df = predict_latest(["RELIANCE.NS", "TCS.NS"])
    print(df[['Symbol', 'Decision', 'Confidence']])
    
    row = df.iloc[0]
    decision = row['Decision']
    conf = row['Confidence']
    
    if decision != "Strongly Buy":
        print(f"FAIL: Decision label is '{decision}', expected 'Strongly Buy'")
    else:
        print("PASS: Decision label is correct.")
        
    print(f"Confidence (0-1): {conf}")
    
    print("\n--- Verifying Explain Logic ---")
    explainer = ModelExplainer()
    text = explainer.get_natural_language_explanation("RELIANCE.NS")
    print(text[:200] + "...")
    
    if "Strongly Buy" in text and "%" in text:
        print("PASS: Explanation contains expected keywords.")
    else:
        print("FAIL: Explanation missing keywords.")

except Exception as e:
    print(f"CRASH: {e}")
    import traceback
    traceback.print_exc()
