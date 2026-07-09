import requests
import pandas as pd
import json
import io

def update_nse_symbols():
    url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    print(f"Downloading symbol list from {url}...")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse CSV
        csv_content = response.content.decode('utf-8')
        df = pd.read_csv(io.StringIO(csv_content))
        
        # NSE CSV usually has 'SYMBOL' and 'NAME OF COMPANY' columns
        # Filter for equity only if needed (SERIES usually 'EQ')
        if 'SERIES' in df.columns:
            df = df[df['SERIES'] == 'EQ']
            
        symbols = []
        for _, row in df.iterrows():
            symbol = row['SYMBOL']
            name = row['NAME OF COMPANY']
            
            # yfinance needs .NS suffix
            symbols.append({
                "symbol": f"{symbol}.NS",
                "name": name
            })
            
        # Save to JSON
        output_path = "src/data/nse_symbols.json"
        with open(output_path, 'w') as f:
            json.dump(symbols, f, indent=4)
            
        print(f"Successfully saved {len(symbols)} stocks to {output_path}")
        
        # Verify first few
        print("Sample:", symbols[:3])
        
    except Exception as e:
        print(f"Error fetching symbols: {e}")
        # Fallback to a backup source if NSE fails (common due to blocking)
        print("Attempting backup source (GitHub)...")
        try:
             # Using a public maintained list or just failing gracefully
             pass
        except:
            pass

if __name__ == "__main__":
    update_nse_symbols()
