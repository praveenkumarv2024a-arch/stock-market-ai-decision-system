import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from src.features.engineer import FeatureEngineer
import joblib
import os

STOCKS = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "TATAMOTORS.NS"]

def train_and_compare():
    print("--- Starting Model Comparison ---")
    fe = FeatureEngineer()
    all_data = []

    for symbol in STOCKS:
        print(f"Processing {symbol}...")
        df = fe.prepare_data(symbol)
        if df is not None and not df.empty:
            all_data.append(df)
    
    if not all_data:
        print("No data available for training.")
        return

    full_df = pd.concat(all_data)
    
    # Check class balance
    print("\nClass Distribution:")
    print(full_df['target'].value_counts())
    
    # 2. Train/Test Split
    drop_cols = ['target', 'future_close', 'future_return', 'date']
    X = full_df.drop(columns=[c for c in drop_cols if c in full_df.columns])
    y = full_df['target']
    
    # Clean X
    X = X.select_dtypes(include=[np.number])
    
    print(f"\nTraining with {len(X)} samples and {X.shape[1]} features.")
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 3. Define Models
    # Shift target classes to [0, 1, 2] for XGB/LGBM if needed (they usually handle it, but sklearn is safer map)
    # Our targets are -1, 0, 1.
    # XGBoost needs 0, 1, 2.
    y_train_mapped = y_train + 1 
    y_test_mapped = y_test + 1
    
    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000),
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
        "XGBoost": XGBClassifier(use_label_encoder=False, eval_metric='mlogloss', random_state=42),
        "LightGBM": LGBMClassifier(random_state=42, verbose=-1)
    }
    
    best_name = None
    best_acc = 0.0
    best_model = None
    
    results = []

    print("\n--- Model Evaluation ---")
    for name, model in models.items():
        try:
            # XGB/LGBM prefer mapped labels 0..N
            if name in ["XGBoost", "LightGBM"]:
                model.fit(X_train, y_train_mapped)
                y_pred_mapped = model.predict(X_test)
                y_pred = y_pred_mapped - 1 # Map back to -1, 0, 1
            else:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
            
            acc = accuracy_score(y_test, y_pred)
            print(f"{name}: Accuracy = {acc:.4f}")
            
            results.append({"Model": name, "Accuracy": acc})
            
            if acc > best_acc:
                best_acc = acc
                best_name = name
                best_model = model
                
        except Exception as e:
            print(f"Failed to train {name}: {e}")

    print(f"\nResult: Best Model: {best_name} with Accuracy: {best_acc:.4f}")
    
    # Print detailed report for best model
    if best_model:
        if best_name in ["XGBoost", "LightGBM"]:
             y_pred_mapped = best_model.predict(X_test)
             y_pred = y_pred_mapped - 1
        else:
             y_pred = best_model.predict(X_test)
             
        print("\nDetailed Report for Best Model:")
        print(classification_report(y_test, y_pred))
        
        # Save
        joblib.dump(best_model, "data/best_model.pkl")
        # Save metadata about which model type it is (optional, or just imply from pickle)
        print("Best model saved to data/best_model.pkl")

if __name__ == "__main__":
    train_and_compare()
