import json

def filter_symbols():
    # Load Nifty 50 symbols (from tracking list)
    with open('src/data/tracked_stocks.json', 'r') as f:
        nifty50_symbols = set(json.load(f))
        
    # Load all symbols
    with open('src/data/nse_symbols.json', 'r') as f:
        all_symbols = json.load(f)
        
    print(f"Total symbols before: {len(all_symbols)}")
    
    # Filter
    filtered = [s for s in all_symbols if s['symbol'] in nifty50_symbols]
    
    print(f"Total symbols after: {len(filtered)}")
    
    # Save back
    with open('src/data/nse_symbols.json', 'w') as f:
        json.dump(filtered, f, indent=4)
        
    print("nse_symbols.json updated.")

if __name__ == "__main__":
    filter_symbols()
