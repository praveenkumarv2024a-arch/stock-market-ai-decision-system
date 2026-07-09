import shap
import joblib
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg') # Fix: Non-interactive backend for server
import matplotlib.pyplot as plt
from src.features.engineer import FeatureEngineer
import threading
import os

class ModelExplainer:
    _plot_lock = threading.Lock() # Class-level lock to prevent race conditions

    def __init__(self, model_path="data/best_model.pkl", model=None):
        self.model_path = model_path
        if model:
            self.model = model
        else:
            try:
                self.model = joblib.load(model_path)
            except Exception as e:
                print(f"Error loading model: {e}")
                self.model = None
            
    def get_explainer(self, X_train_sample):
        """
        Returns a SHAP explainer appropriate for the model type.
        """
        model_type = type(self.model).__name__
        
        # Tree-based models (XGBoost, RandomForest, LightGBM)
        if model_type in ["XGBClassifier", "RandomForestClassifier", "LGBMClassifier"]:
            return shap.TreeExplainer(self.model)
        
        # Logistic Regression
        elif model_type == "LogisticRegression":
            return shap.LinearExplainer(self.model, X_train_sample)
            
        else:
            # Fallback
            return shap.KernelExplainer(self.model.predict_proba, X_train_sample)

    def explain_latest(self, symbol, live_price=None):
        if not self.model:
            print("Model not loaded.")
            return

        fe = FeatureEngineer()
        df = fe.prepare_data(symbol, is_training=False, live_price=live_price)
        
        if df is None or df.empty:
            print(f"No data for {symbol}")
            return

        # Prepare input features X
        # Prepare input features X
        latest_row = df.iloc[[-1]]
        drop_cols = ['target', 'future_close', 'future_return', 'date']
        X = latest_row.drop(columns=[c for c in drop_cols if c in latest_row.columns])
        X = X.select_dtypes(include=[np.number])

        # --- Fix: Align columns with training data ---
        if hasattr(self.model, "feature_names_in_"):
            expected_cols = self.model.feature_names_in_
            X = X.reindex(columns=expected_cols, fill_value=0)
        elif hasattr(self.model, "get_booster"):
            try:
                expected_cols = self.model.get_booster().feature_names
                if expected_cols:
                     X = X.reindex(columns=expected_cols, fill_value=0)
            except: pass

        # We need an explainer. 
        try:
            explainer = shap.TreeExplainer(self.model)
            shap_values = explainer.shap_values(X)
        except Exception as e:
            print(f"TreeExplainer failed ({e}), using KernelExplainer...")
            # KernelExplainer needs background data (X_train) usually, but we can try passing the row 
            # Or usually we need a summary. Let's create a small background summary
            # Actually, let's just use the single row (less accurate baseline but works)
            # Wrap predict_proba to avoid attribute setting issues on the model object
            def predict_wrapper(data):
                return self.model.predict_proba(data)
                
            explainer = shap.KernelExplainer(predict_wrapper, X)
            shap_values = explainer.shap_values(X)
        
        # Compute SHAP values (already done above)
        
        # SHAP values might be a list (for multi-class) or array
        # Our target is BUY=1, SELL=-1, HOLD=0.
        # Sklearn/XGB usually outputs a list of arrays for classification [Class 0, Class 1, Class 2]
        # We want to explain the "BUY" signal (Class index for 1) if prediction is BUY
        # Or explain "SELL" (Class index for -1) if prediction is SELL.
        # Let's just default to showing the 'BUY' contribution for now or ask user?
        # Let's generate a plot for the predicted class.
        
        # --- LOGIC SYNC START ---
        # 1. Technical Overrides
        rsi_val = X.get('RSI', X.get('rsi', None))
        if isinstance(rsi_val, pd.Series): rsi_val = rsi_val.iloc[0]
        
        buy_score = 50.0
        override = False # Initialize safely
        
        if rsi_val is not None:
            if rsi_val < 30: 
                buy_score = 90.0 + (30 - rsi_val)
                if buy_score > 99: buy_score = 99
                override = True
            elif rsi_val > 70: 
                # Aggressive Tuning:
                # RSI 70 -> 40, RSI 90 -> 20.
                buy_score = 40.0 - (rsi_val - 70)
                if buy_score < 15: buy_score = 15
                override = True
            
        model_base_score = 50.0
        if not override:
             # 2. Model Logic with Probability 
             try:
                 if hasattr(self.model, "predict_proba"):
                     probs = self.model.predict_proba(X)[0]
                     classes = list(self.model.classes_)
                     buy_cls = max(classes)
                     sell_cls = min(classes)
                     
                     p_buy = probs[classes.index(buy_cls)]
                     p_sell = probs[classes.index(sell_cls)]
                     
                     buy_score = 50.0 + (p_buy * 50.0) - (p_sell * 50.0)
                 else:
                     pred = self.model.predict(X)[0]
                     if pred == 1: buy_score = 75.0
                     elif pred == -1: buy_score = 25.0
                     else: buy_score = 50.0
                     
             except Exception as e:
                 print(f"Logic Error: {e}")
                 buy_score = 50.0
                 
             model_base_score = buy_score
             
             # --- Multi-Factor Upgrades ---
             pe = X.get('trailingPE', pd.Series([0])).iloc[0]
             pb = X.get('priceToBook', pd.Series([0])).iloc[0]
             sent = X.get('sentiment_score', pd.Series([0])).iloc[0]
             
             if pe > 0:
                 if pe < 15: buy_score += 10
                 elif pe > 30: buy_score -= 10
                 elif pe > 50: buy_score -= 15
             
             if pb > 0:
                 if pb < 1.0: buy_score += 5
                 elif pb > 5.0: buy_score -= 5
                 
             if sent > 0.2: buy_score += 10
             elif sent < -0.2: buy_score -= 10
        else:
             model_base_score = buy_score # If overridden, base is the override
        
        # Aggressive Floor: Never go below 15%
        buy_score = max(15, min(99, buy_score))
        
        # Decide which class to explain
        # If High Score (>50), explain why it's BUY (positive class)
        # If Low Score (<50), we can explain why it's SELL (negative class) or why it's NOT BUY.
        # Standard: Explain the positive class (BUY) always? 
        # SHAP usually explains "Why is the output X?". 
        # If output is probability of Class 1.
        
        # For tree explainer, it usually explains the raw score (margin).
        # We need to map back to the correct class index for Buy.
        class_idx = 1 # Assuming index 1 is Buy. Need to verify.
        if hasattr(self.model, "classes_"):
             try: class_idx = list(self.model.classes_).index(max(self.model.classes_))
             except: class_idx = 1 # Fallback
             
        decision_text = f"Score: {buy_score:.0f}%"
        print(f"Explaining prediction: {buy_score:.1f}%")
        # --- LOGIC SYNC END ---
        
        # Get SHAP values for that class
        # shap_values might be:
        # 1. List of arrays (one per class) -> [ (N, F), (N, F), ... ]
        # 2. 3D array -> (N, F, C)
        # 3. 2D array (if binary/reg) -> (N, F)
        
        if isinstance(shap_values, list):
             class_shap_values = shap_values[class_idx]
        elif len(shap_values.shape) == 3:
            # (N, F, C) -> We want (N, F) for the specific class
            class_shap_values = shap_values[:, :, class_idx]
        else:
            class_shap_values = shap_values
            
        # Now class_shap_values should be (N, F) -> (1, 22)

            
        # Waterfall Plot (Static Image - More Robust)
        try:
            # Waterfall needs Explanation object
            # For kernel explainer/generic, we construct it manually
            
            # 1. Base Value
            if isinstance(explainer.expected_value, (list, np.ndarray)):
                 base = explainer.expected_value[class_idx]
            else:
                 base = explainer.expected_value
                 
            # 2. SHAP values for class
            sv = class_shap_values[0] if len(class_shap_values.shape) > 1 else class_shap_values
            
            # 3. Features
            feat = X.iloc[0].values
            
            exp = shap.Explanation(
                values=sv,
                base_values=base,
                data=feat,
                feature_names=X.columns.tolist()
            )
            
            # Use the lock to prevent thread race conditions on Matplotlib global state
            with ModelExplainer._plot_lock:
                try:
                    # 1. Clear state aggressively
                    plt.close('all')
                    plt.clf()
                    
                    # 2. Create Plot
                    fig = plt.figure(figsize=(12, 6), dpi=100) # Explicit figure
                    shap.plots.waterfall(exp, show=False, max_display=8)
                    
                    if abs(model_base_score - buy_score) >= 1:
                        plt.title(f"Model Base: {model_base_score:.0f}% -> Final Score: {buy_score:.0f}%")
                    else:
                        plt.title(f"Why {buy_score:.0f}% Buy Confidence?")
                        
                    plt.tight_layout()
                    
                    # 3. Save with retry/force logic
                    output_path = f"data/{symbol}_explanation.png"
                    if os.path.exists(output_path):
                        try:
                            os.remove(output_path) # Remove existing file to avoid permission issues on overwrite
                        except OSError as e:
                            print(f"Error removing existing plot file {output_path}: {e}")
                    plt.savefig(output_path, bbox_inches='tight', dpi=100)
                    print(f"Saved explanation plot to {output_path}")
                except Exception as e:
                    print(f"Plotting inner failed: {e}")
                finally:
                    plt.close('all') # Cleanup inside the lock
            
        except Exception as e:
            print(f"Plotting failed: {e}")

    def get_natural_language_explanation(self, symbol, live_price=None):
        """
        Generates a natural language explanation for the AI's decision.
        """
        if not self.model: return "Model not loaded."
        
        # Initialize model_classes safely at start
        model_classes = [0, 1]
        if hasattr(self.model, "classes_"):
            model_classes = self.model.classes_

        fe = FeatureEngineer()
        # Fix: Use is_training=False so we explain the ACTUAL latest prediction (Today's Live Candle)
        df = fe.prepare_data(symbol, is_training=False, live_price=live_price)
        
        if df is None or df.empty: return "Insufficient data for analysis."

        override = False # Initialize safely
        
        # Prepare X
        latest_row = df.iloc[[-1]]
        drop_cols = ['target', 'future_close', 'future_return', 'date']
        X = latest_row.drop(columns=[c for c in drop_cols if c in latest_row.columns])
        X = X.select_dtypes(include=[np.number])

        # Debug Printing (Helper to find sync issues)
        debug_vals = []
        for col in ['close', 'RSI', 'volume', 'SMA_20']:
            if col in latest_row.columns:
                val = latest_row[col].iloc[0]
                debug_vals.append(f"{col}={round(val, 2)}")
        print(f"Explain Debug {symbol}: {', '.join(debug_vals)}")

        # --- Fix: Align columns with training data ---
        if hasattr(self.model, "feature_names_in_"):
            # Scikit-learn / XGBoost (recent)
            expected_cols = self.model.feature_names_in_
            # Reindex adds missing cols with NaN, we fill with 0
            X = X.reindex(columns=expected_cols, fill_value=0)
        elif hasattr(self.model, "get_booster"):
            # XGBoost raw booster
            try:
                expected_cols = self.model.get_booster().feature_names
                if expected_cols:
                    X = X.reindex(columns=expected_cols, fill_value=0)
            except: pass
        
        # --- LOAD SETTINGS FOR CONSISTENCY ---
        import json
        settings_path = 'data/settings.json'
        risk_mode = 'balanced'
        try:
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    s = json.load(f)
                    risk_mode = s.get('risk_tolerance', 'balanced')
        except: pass

        # Thresholds matching app.py
        threshold_buy = 0.5
        threshold_sell = 0.5
        
        # Initialize probabilities to avoid UnboundLocalError
        p_buy = 0.0
        p_sell = 0.0
        
        # --- TECHNICAL OVERRIDES (Must Match predict.py) ---
        rsi_val = X.get('RSI', X.get('rsi', None))
        if isinstance(rsi_val, pd.Series): rsi_val = rsi_val.iloc[0]
        
        if rsi_val is not None:
            if rsi_val < 30: 
                buy_score = 90.0 + (30 - rsi_val)
                if buy_score > 99: buy_score = 99
                override = True
            elif rsi_val > 70: 
                # Aggressive Tuning:
                # RSI 70 -> 40, RSI 90 -> 20.
                buy_score = 40.0 - (rsi_val - 70)
                if buy_score < 15: buy_score = 15
                override = True
            
        if not override:
             # Regular AI Logic
             try:
                 if hasattr(self.model, "predict_proba"):
                     probs = self.model.predict_proba(X)[0]
                     classes = list(model_classes)
                     buy_cls = max(classes)
                     sell_cls = min(classes)
                     
                     p_buy = probs[classes.index(buy_cls)]
                     p_sell = probs[classes.index(sell_cls)]
                     
                     buy_score = 50.0 + (p_buy * 50.0) - (p_sell * 50.0)
                 else:
                     pred = self.model.predict(X)[0]
                     if pred == 1: buy_score = 75.0
                     elif pred == -1: buy_score = 25.0
                     else: buy_score = 50.0
                     
             except Exception as e:
                 print(f"Explanation Logic Error: {e}")
                 buy_score = 50.0
        
        # --- Multi-Factor Upgrades (Synced) ---
        pe = latest_row['trailingPE'].iloc[0] if 'trailingPE' in latest_row else 0
        pb = latest_row['priceToBook'].iloc[0] if 'priceToBook' in latest_row else 0
        sent = latest_row['sentiment_score'].iloc[0] if 'sentiment_score' in latest_row else 0
        
        modifiers_text = []

        # 1. Valuation Modifiers
        if pe > 0:
            if pe < 15: 
                buy_score += 10
                modifiers_text.append("Undervalued P/E (+10%)")
            elif pe > 30: 
                buy_score -= 10
                modifiers_text.append("Overvalued P/E (-10%)")
            elif pe > 50: 
                buy_score -= 15
                modifiers_text.append("High P/E Penalty (-15%)")
        
        if pb > 0:
            if pb < 1.0: 
                buy_score += 5
                modifiers_text.append("Deep Value P/B (+5%)")
            elif pb > 5.0: 
                buy_score -= 5
                modifiers_text.append("Premium Valuation P/B (-5%)")
            
        # 2. Sentiment Modifiers
        if sent > 0.2: 
            buy_score += 10
            modifiers_text.append("Positive News Sentiment (+10%)")
        elif sent < -0.2: 
            buy_score -= 10
            modifiers_text.append("Negative News Sentiment (-10%)")
        
        # Aggressive Floor: Never go below 15%
        buy_score = max(15, min(99, buy_score))

        # --- Explain WHY ---
        # Get SHAP values
        try:
             explainer_shap = self.get_explainer(X) # Needs background set ideally, but checks tree
             
             # Calculate SHAP values
             if hasattr(explainer_shap, "shap_values"):
                 shap_values = explainer_shap.shap_values(X)
                 
                 # Logic for binary/multiclass extraction
                 # We want drivers for the BUY class (Positive)
                 if isinstance(shap_values, list):
                     vals = shap_values[-1] # Assume last is Buy
                 elif len(np.array(shap_values).shape) == 3:
                     vals = shap_values[0, :, -1] 
                 else:
                     vals = shap_values[0] # Binary
                 
                 # Find top driver
                 feature_names = X.columns.tolist()
                 # Pair feature with value
                 pairs = list(zip(feature_names, vals))
                 
                 # Sort by absolute impact
                 pairs.sort(key=lambda x: abs(x[1]), reverse=True)
                 top_feat, top_val = pairs[0] 
                 
                 direction = "increasing" if top_val > 0 else "decreasing"
                 reason = f"The 'Strongly Buy' score is **{buy_score:.0f}%** primarily because **{top_feat}** is {direction} the confidence."
             else:
                 reason = f"The AI gives a 'Strongly Buy' score of **{buy_score:.0f}%** based on technical patterns."
                 
        except Exception as e:
             print(f"SHAP val calc error: {e}")
             reason = f"The AI calculated a score of **{buy_score:.0f}%**."

        # Add to output
        explanation = f"{reason}\n\n"

        # DEBUG INFO (Visible to user to help debug)
        rsi_str = f"{rsi_val:.2f}" if rsi_val else "N/A"
        debug_str = f"\n\n*Debug: [V4-SCORE] Score={buy_score:.1f}%, RSI={rsi_str}*"
        
        # Ensure shap_values exists for drivers
        if 'shap_values' not in locals():
            try:
                explainer = shap.TreeExplainer(self.model)
                shap_values = explainer.shap_values(X)
            except:
                def predict_wrapper(data): return self.model.predict_proba(data)
                explainer = shap.KernelExplainer(predict_wrapper, X)
                shap_values = explainer.shap_values(X)

        # We want to show "Why Buy?" (Class 1/2) and "Why Sell?" (Class -1/0)
        # Assuming classes are ordered [-1, 0, 1] or [0, 1, 2]
        # Sell Index = 0
        feature_names = X.columns.tolist()
        
        sell_idx = 0
        # Buy Index = 2 (if 3 classes) or 1 (if binary)
        
        # Helper to extract top features for a specific class index
        buy_idx = len(model_classes) - 1
        
        # Helper to extract top features for a specific class index
        def get_drivers(target_idx):
            if isinstance(shap_values, list):
                vals = shap_values[target_idx]
            elif len(shap_values.shape) == 3:
                vals = shap_values[:, :, target_idx]
            else:
                # Binary case: If target is 1 (Positive), use vals. If 0 (Negative), use -vals
                if target_idx == 1: vals = shap_values
                else: vals = -shap_values
            
            # Use raw array
            if isinstance(vals, list): vals = vals[0] # Should be array by now but safety check
            if vals.ndim > 1: vals = vals[0]
            
            drivers = []
            
            # Fix zip: feature_names and vals must be same length
            # If not, truncate or pad?
            limit = min(len(feature_names), len(vals))
            
            for name, impact, val in zip(feature_names[:limit], vals[:limit], X.iloc[0].values[:limit]):
                # We only care if it PUSHES towards this class (Impact > 0)
                if impact > 0:
                    drivers.append({
                        "name": name.replace("_", " ").title(),
                        "impact": impact,
                        "value": val
                    })
            drivers.sort(key=lambda x: x['impact'], reverse=True)
            return drivers[:4] # Top 4

        buy_drivers = get_drivers(buy_idx)
        sell_drivers = get_drivers(sell_idx)
        
        
        # Narrative Construction
        narrative = [f"The **Strongly Buy** confidence is **{buy_score:.0f}%**."]
        
        if buy_score >= 60:
            narrative.append("\n**✅ Bullish Drivers (Boosting Score):**")
            # Show Positive Impact features
            if buy_drivers:
                for item in buy_drivers:
                     val_str = f"{item['value']:.2f}"
                     narrative.append(f"• **{item['name']}** ({val_str})")
            
            narrative.append("\n**⚠️ Drag Factors (Reducing Score):**")
            if sell_drivers: # Features pushing towards sell (negative impact on buy)
                for item in sell_drivers:
                     narrative.append(f"• **{item['name']}** (Resistance)")
                     
        elif buy_score <= 40:
             narrative.append("\n**🔻 Bearish Drivers (Lowering Score):**")
             # Sell drivers are essentially features with negative Buy impact
             if sell_drivers: # These are features pushing to 'Sell' class.
                 for item in sell_drivers:
                     val_str = f"{item['value']:.2f}"
                     narrative.append(f"• **{item['name']}** ({val_str})")
                     
             narrative.append("\n**💡 Silver Linings (Positives):**")
             if buy_drivers:
                  for item in buy_drivers:
                       narrative.append(f"• **{item['name']}**")
        
        else:
             # Neutral
             narrative.append("The signal is mixed.")
             narrative.append("\n**Bullish Factors:**")
             for item in buy_drivers[:3]: narrative.append(f"• {item['name']}")
             narrative.append("\n**Bearish Factors:**")
             for item in sell_drivers[:3]: narrative.append(f"• {item['name']}")
        
        # --- NEW: Fundamental & Contextual Analysis ---
        narrative.append("\n**📊 Fundamental & News Context:**")
        
        # Extract specific column values from X (which has all features)
        def get_val(col):
            if col in X.columns: return X.iloc[0][col]
            return None

        pe = get_val('trailingPE')
        pb = get_val('priceToBook')
        sent = get_val('sentiment_score')
        
        context_items = []
        
        # Valuation Logic
        if pe:
            pe_status = "Undervalued" if pe < 15 else "Overvalued" if pe > 25 else "Fair Value"
            context_items.append(f"• **P/E Ratio**: {pe:.1f} ({pe_status})")
        
        if pb:
            pb_status = "Undervalued" if pb < 1 else "Premium" if pb > 3 else "Fair"
            context_items.append(f"• **P/B Ratio**: {pb:.1f} ({pb_status})")
            
        # Sentiment Logic
        if sent is not None:
             sent_str = "Positive" if sent > 0.1 else "Negative" if sent < -0.1 else "Neutral"
             context_items.append(f"• **Recent News**: {sent:.2f} Sentiment ({sent_str})")
             
        if context_items:
            narrative.extend(context_items)
        else:
            narrative.append("• Fundamental data unavailable for deep context.")

        if modifiers_text:
            narrative.append("\n**⚖️ Score Adjustments:**")
            for mod in modifiers_text:
                narrative.append(f"• {mod}")

        narrative.append(debug_str)
        
        return "\n".join(narrative)
        
        return "\n".join(narrative)
        
if __name__ == "__main__":
    explainer = ModelExplainer()
    explainer.explain_latest("RELIANCE.NS")
