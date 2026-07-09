import json
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.main import process_symbol
from src.models.explain import ModelExplainer

def refresh_tracked():
    try:
        with open('src/data/tracked_stocks.json', 'r') as f:
            stocks = json.load(f)
    except:
        print("No tracked stocks file.")
        return

    print(f"Refreshing data for {len(stocks)} tracked stocks...")
    explainer = ModelExplainer()
    
    for i, symbol in enumerate(stocks):
        print(f"[{i+1}/{len(stocks)}] {symbol}")
        try:
            # Fetch Price/News/Fundamentals
            process_symbol(symbol, live=True) # Try live, fallback to history
            
            # Generate Analysis
            explainer.explain_latest(symbol)
            
        except Exception as e:
            print(f"Failed {symbol}: {e}")

if __name__ == "__main__":
    refresh_tracked()
