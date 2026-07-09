import yfinance as yf
import pandas as pd
from datetime import datetime

symbol = "RELIANCE.NS"
print(f"Fetching intraday data for {symbol}...")

# Test 1: Standard 1d/1m
print("\n--- Test 1: period='1d', interval='1m' ---")
df1 = yf.Ticker(symbol).history(period="1d", interval="1m")
print(f"Shape: {df1.shape}")
print(df1.head())
print(df1.tail())

# Test 2: Fallback 5d/1m
print("\n--- Test 2: period='5d', interval='1m' ---")
df2 = yf.Ticker(symbol).history(period="5d", interval="1m")
print(f"Shape: {df2.shape}")

if not df2.empty:
    # Logic to get ONLY the last trading day
    last_dt = df2.index[-1]
    print(f"Last Datetime: {last_dt}")
    last_date = last_dt.date()
    print(f"Last Date: {last_date}")
    
    # Filter for that date
    today_data = df2[df2.index.date == last_date]
    print(f"Filtered Shape: {today_data.shape}")
    print(today_data.head(1))
    print(today_data.tail(1))
else:
    print("5d data also empty!")
