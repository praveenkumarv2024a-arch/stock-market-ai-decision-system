import sys
import os
import io

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.models.explain import ModelExplainer
    
    print("Initializing Explainer...")
    explainer = ModelExplainer()
    
    symbol = "TCS.NS"
    print(f"Generating explanation for {symbol}...")
    
    text = explainer.get_natural_language_explanation(symbol)
    print("\n--- Result ---")
    print(text)
    print("\n--------------")

except Exception as e:
    print("\n!!! CRASH !!!")
    print(e)
    import traceback
    traceback.print_exc()
