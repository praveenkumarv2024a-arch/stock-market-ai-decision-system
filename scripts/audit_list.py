
import json

with open('src/data/tracked_stocks.json', 'r') as f:
    stocks = json.load(f)

print(f"Total Count: {len(stocks)}")
print(f"Unique Count: {len(set(stocks))}")

# List of standard Nifty 50 (approximate for check)
nifty_50_check = [
    "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS",
    "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS",
    "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS", "DRREDDY.NS",
    "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
    "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ITC.NS",
    "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LTIM.NS",
    "LT.NS", "M&M.NS", "MARUTI.NS", "NESTLEIND.NS", "NTPC.NS",
    "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS",
    "SUNPHARMA.NS", "TATASTEEL.NS", "TCS.NS", "TATACONSUM.NS", "TATAMOTORS.NS",
    "TECHM.NS", "TITAN.NS", "ULTRACEMCO.NS", "WIPRO.NS", "BEL.NS", "JIOFIN.NS", "TRENT.NS"
]
# Note: Nifty 50 changes. JIOFIN/TRENT/BEL are recent entrants replacing UPL/others. 
# Depending on specific list, it might vary.
# We will just print what is NOT in tracked list from this set.

current_set = set(stocks)
possible_missing = [s for s in nifty_50_check if s not in current_set]
print(f"Missing from standard set: {possible_missing}")
