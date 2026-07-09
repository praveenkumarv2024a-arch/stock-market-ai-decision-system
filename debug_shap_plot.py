import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import shap
import joblib
from src.features.engineer import FeatureEngineer
import os

# Mock the class structure slightly to test the logic
class MockExplainer:
    def __init__(self):
        self.model = joblib.load("data/best_model.pkl")
    
    def explain(self, symbol):
        print(f"Explain {symbol}")
        fe = FeatureEngineer()
        df = fe.prepare_data(symbol)
        
        latest_row = df.iloc[[-1]]
        drop_cols = ['target', 'future_close', 'future_return', 'date']
        X = latest_row.drop(columns=[c for c in drop_cols if c in latest_row.columns])
        X = X.select_dtypes(include=[np.number])
        
        # Align cols
        if hasattr(self.model, "feature_names_in_"):
             X = X.reindex(columns=self.model.feature_names_in_, fill_value=0)
        
        # Explain
        explainer = shap.TreeExplainer(self.model)
        shap_values = explainer.shap_values(X)
        
        prediction_raw = self.model.predict(X)[0]
        classes = self.model.classes_
        class_idx = np.where(classes == prediction_raw)[0][0]
        
        print(f"Pred: {prediction_raw}, ClassIdx: {class_idx}")
        print(f"SHAP shape: {np.array(shap_values).shape}")
        
        if isinstance(shap_values, list):
             class_shap_values = shap_values[class_idx]
        elif len(np.array(shap_values).shape) == 3:
             class_shap_values = shap_values[:, :, class_idx]
        else:
            class_shap_values = shap_values
            
        print(f"Class SHAP shape: {class_shap_values.shape}")
        
        # 1. Base Value
        if isinstance(explainer.expected_value, (list, np.ndarray)):
             base = explainer.expected_value[class_idx]
        else:
             base = explainer.expected_value
             
        # 2. SHAP values for class
        # CRITICAL CHECK: Logic from explain.py
        sv = class_shap_values[0] if len(class_shap_values.shape) > 1 else class_shap_values
        print(f"Final SV shape: {sv.shape}")
        
        # 3. Features
        feat = X.iloc[0].values
        
        exp = shap.Explanation(
            values=sv,
            base_values=base,
            data=feat,
            feature_names=X.columns.tolist()
        )
        
        # Plotting
        plt.close('all')
        plt.clf()
        fig = plt.figure(figsize=(10, 6))
        
        shap.plots.waterfall(exp, show=False, max_display=10)
        
        plt.tight_layout()
        plt.savefig(f"test_{symbol}.png", bbox_inches='tight', dpi=100)
        print(f"Saved test_{symbol}.png")

try:
    m = MockExplainer()
    m.explain("INFY.NS")
except Exception as e:
    import traceback
    traceback.print_exc()
