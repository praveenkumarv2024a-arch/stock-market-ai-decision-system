from src.data.news_scraper import fetch_google_news
import pandas as pd

try:
    print("Fetching news for verification...")
    df = fetch_google_news("TCS NSE")
    if not df.empty:
        print("First 3 rows (Published):")
        print(df['published'].head(3))
        
        # Check format
        first_date = df.iloc[0]['published']
        print(f"\nSample Date format: {first_date}")
        if first_date[0].isdigit() and 'T' in first_date:
            print("SUCCESS: Date appears to be ISO format.")
        else:
            print("FAILURE: Date format is likely incorrect.")
    else:
        print("No news found to verify.")
except Exception as e:
    print(f"Error: {e}")
