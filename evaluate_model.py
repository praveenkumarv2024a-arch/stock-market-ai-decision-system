import joblib
import pandas as pd
import numpy as np
from src.features.engineer import FeatureEngineer
from sklearn.metrics import accuracy_score, classification_report

def evaluate():
    print("Loading Model...")
    try:
        model = joblib.load("data/best_model.pkl")
    except:
        print("Model not found.")
        return

    print(f"Model Type: {type(model).__name__}")
    
    fe = FeatureEngineer()
    STOCKS = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]
    all_data = []

    print("Fetching Test Data...")
    for symbol in STOCKS:
        try:
            df = fe.prepare_data(symbol)
            if df is not None and not df.empty:
                all_data.append(df)
        except Exception as e:
            print(f"Skip {symbol}: {e}")

    if not all_data:
        print("No data.")
        return

    full_df = pd.concat(all_data)
    
    # Drop non-feature columns
    drop_cols = ['target', 'future_close', 'future_return', 'date']
    X = full_df.drop(columns=[c for c in drop_cols if c in full_df.columns])
    y = full_df['target']
    X = X.select_dtypes(include=[np.number])

    # Re-align features
    if hasattr(model, 'feature_names_in_'):
        X = X.reindex(columns=model.feature_names_in_, fill_value=0)
    elif hasattr(model, "get_booster"):
        try:
             expected_cols = model.get_booster().feature_names
             if expected_cols:
                  X = X.reindex(columns=expected_cols, fill_value=0)
        except: pass

    print("Predicting...")
    # Map 0..N back if XGBoost
    if type(model).__name__ in ["XGBClassifier", "LGBMClassifier"]:
        y_pred_mapped = model.predict(X)
        y_pred = y_pred_mapped - 1
    else:
        y_pred = model.predict(X)

    acc = accuracy_score(y, y_pred)
    print(f"Accuracy: {acc:.4f}")
    print("\nReport:")
    print(classification_report(y, y_pred))

if __name__ == "__main__":
    evaluate()
