from src.data.stock_price import fetch_stock_data
from src.data.news_scraper import fetch_google_news
from src.data.fundamentals import fetch_fundamentals

def test_modules():
    print("--- Testing Stock Price ---\n")
    price_df = fetch_stock_data("RELIANCE.NS", period="1d", interval="1m")
    if price_df is not None:
        print(f"Successfully fetched {len(price_df)} rows of price data.")
        print(price_df.tail())
    else:
        print("Failed to fetch price data.")

    print("\n--- Testing News ---\n")
    news_df = fetch_google_news("Reliance Industries")
    if not news_df.empty:
        print(f"Successfully fetched {len(news_df)} news items.")
        print(news_df[['title', 'published']].head())
    else:
        print("Failed to fetch news or no news found.")

    print("\n--- Testing Fundamentals ---\n")
    fund_data = fetch_fundamentals("RELIANCE.NS")
    if fund_data:
        print("Successfully fetched fundamentals.")
        for k, v in fund_data.items():
            print(f"{k}: {v}")
    else:
        print("Failed to fetch fundamentals.")

if __name__ == "__main__":
    test_modules()
