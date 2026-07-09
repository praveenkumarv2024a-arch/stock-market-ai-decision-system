import requests
import time
import json
from src.main import process_symbol
from src.data.storage import DataStore

# NIFTY 50 Components (as of late 2024/2025 aprox)
NIFTY_50 = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "BHARTIARTL.NS", "ITC.NS", "SBIN.NS", "LICI.NS", "HINDUNILVR.NS",
    "LT.NS", "BAJFINANCE.NS", "MARUTI.NS", "HCLTECH.NS", "SUNPHARMA.NS",
    "TATAMOTORS.NS", "ADANIENT.NS", "KOTAKBANK.NS", "AXISBANK.NS", "NTPC.NS",
    "TITAN.NS", "ULTRACEMCO.NS", "ONGC.NS", "POWERGRID.NS", "M&M.NS",
    "ADANIPORTS.NS", "COALINDIA.NS", "WIPRO.NS", "JSWSTEEL.NS", "TATASTEEL.NS",
    "BAJAJFINSV.NS", "LTIM.NS", "TECHM.NS", "GRASIM.NS", "BRITANNIA.NS",
    "HINDALCO.NS", "CIPLA.NS", "EICHERMOT.NS", "INDUSINDBK.NS", "DRREDDY.NS",
    "DIVISLAB.NS", "APOLLOHOSP.NS", "SBILIFE.NS", "ASIANPAINT.NS", "TATACONSUM.NS",
    "BPCL.NS", "HEROMOTOCO.NS", "UPL.NS", "ADANIGREEN.NS"
]

def bulk_import_top_50():
    db = DataStore()
    print(f"Starting bulk import of {len(NIFTY_50)} Stocks...")
    print("WARNING: This may take a few minutes to respect API rate limits.")
    
    # We need to tell the app these are tracked.
    # The app stores TRACKED_STOCKS in memory (list).
    # To persist, we should probably output a list or add via API.
    # Since app is running, using API is best to update state.
    
    api_url = "http://localhost:5001/api/stocks"
    
    success_count = 0
    for i, symbol in enumerate(NIFTY_50):
        print(f"[{i+1}/{len(NIFTY_50)}] Adding {symbol}...")
        try:
            # Call API to add (this triggers fetch in background of app)
            # But duplicate logic check exists.
            resp = requests.post(api_url, json={"symbol": symbol})
            if resp.status_code == 200:
                print(f" -> Success: {resp.json().get('message')}")
                success_count += 1
            else:
                print(f" -> Failed: {resp.text}")
                
            # Sleep to avoid Rate Limit (Yahoo blocks aggressive IPS)
            time.sleep(2) 
            
        except Exception as e:
            print(f" -> Error: {e}")
            
    print(f"\nImport Completed. Successfully added {success_count} stocks.")

if __name__ == "__main__":
    bulk_import_top_50()
