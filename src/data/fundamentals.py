import yfinance as yf
from src.data.storage import DataStore

def fetch_and_store_fundamentals(symbol):
    """
    Fetches fundamental data for a stock using yfinance and stores it in the database.
    """
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # Extract key metrics
        fundamentals = {
            "symbol": symbol,
            
            # Valuation Measures
            "marketCap": info.get('marketCap'),
            "trailingPE": info.get('trailingPE'),
            "forwardPE": info.get('forwardPE'),
            "pegRatio": info.get('pegRatio'),
            "priceToSalesTrailing12Months": info.get('priceToSalesTrailing12Months'),
            "priceToBook": info.get('priceToBook'),
            "enterpriseValue": info.get('enterpriseValue'),
            "enterpriseToRevenue": info.get('enterpriseToRevenue'),
            "enterpriseToEbitda": info.get('enterpriseToEbitda'),
            
            # Financial Highlights
            "profitMargins": info.get('profitMargins'),
            "operatingMargins": info.get('operatingMargins'),
            "returnOnAssets": info.get('returnOnAssets'),
            "returnOnEquity": info.get('returnOnEquity'),
            "totalRevenue": info.get('totalRevenue'),
            "revenueGrowth": info.get('revenueGrowth'),
            "grossMargins": info.get('grossMargins'),
            "ebitda": info.get('ebitda'),
            "netIncomeToCommon": info.get('netIncomeToCommon'),
            "trailingEps": info.get('trailingEps'),
            "forwardEps": info.get('forwardEps'),
            
            # Balance Sheet
            "totalCash": info.get('totalCash'),
            "totalDebt": info.get('totalDebt'),
            "debtToEquity": info.get('debtToEquity'),
            "currentRatio": info.get('currentRatio'),
            "bookValue": info.get('bookValue'),
            
            # Dividends
            "dividendRate": info.get('dividendRate'),
            "dividendYield": info.get('dividendYield'),
            "payoutRatio": info.get('payoutRatio'),
            
            # Price History
            "fiftyTwoWeekHigh": info.get('fiftyTwoWeekHigh'),
            "fiftyTwoWeekLow": info.get('fiftyTwoWeekLow'),
            "fiftyDayAverage": info.get('fiftyDayAverage'),
            "twoHundredDayAverage": info.get('twoHundredDayAverage'),
            
            # Share Statistics
            "sharesOutstanding": info.get('sharesOutstanding'),
            "floatShares": info.get('floatShares'),
            "heldPercentInsiders": info.get('heldPercentInsiders'),
            "heldPercentInstitutions": info.get('heldPercentInstitutions'),
            
            # General Info
            "sector": info.get('sector'),
            "industry": info.get('industry'),
            "longBusinessSummary": info.get('longBusinessSummary')[:500] if info.get('longBusinessSummary') else None, # Truncate summary if needed
            "fullTimeEmployees": info.get('fullTimeEmployees'),
            "website": info.get('website'),
            "currency": info.get('currency'),
            "shortName": info.get('shortName'),
            "longName": info.get('longName')
        }
        
        # Clean None values if desired, but DB handles nulls. 
        # DataStore expects a dict.
        
        db = DataStore()
        db.save_fundamentals(fundamentals, symbol)
        # print(f"Fundamentals stored for {symbol}")
        
    except Exception as e:
        print(f"Error fetching fundamentals for {symbol}: {e}")

if __name__ == "__main__":
    # Test
    fetch_and_store_fundamentals("TCS.NS")
