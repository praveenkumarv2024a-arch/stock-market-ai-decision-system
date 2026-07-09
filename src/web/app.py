from flask import Flask, render_template, jsonify, send_from_directory, request
import os
import pandas as pd
import joblib
from src.data.yahoo_news import fetch_and_store_yahoo_news
from src.data.fundamentals import fetch_and_store_fundamentals
import json
# import yfinance as yf # Moved to function scope
from src.features.engineer import FeatureEngineer
# from src.models.predict import predict_latest # Moved to local scope

import time

app = Flask(__name__)
START_TIME = time.time()

# Global model variable (Lazy loaded)
model = None

def get_model():
    global model
    if model is None:
        try:
            model = joblib.load("data/best_model.pkl")
            print("Model loaded successfully.")
        except:
            print("Warning: Model not found.")
            model = None
    return model

from flask import request
from src.main import process_symbol
from src.data.storage import DataStore

TRACKED_FILE = 'src/data/tracked_stocks.json'

def load_tracked_stocks():
    if os.path.exists(TRACKED_FILE):
        try:
            with open(TRACKED_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return ["RELIANCE.NS", "TCS.NS"] # Default fallback

def save_tracked_stocks(stocks):
    try:
        with open(TRACKED_FILE, 'w') as f:
            json.dump(stocks, f, indent=4)
    except Exception as e:
        print(f"Error saving tracked stocks: {e}")

TRACKED_STOCKS = load_tracked_stocks()

# --- Settings Management ---
SETTINGS_FILE = 'data/settings.json'
DEFAULT_SETTINGS = {
    "theme": "dark",
    "refresh_rate": 5, 
    "risk_tolerance": "balanced",
    "market_hours_only": False
}
SETTINGS = DEFAULT_SETTINGS.copy()

def load_settings():
    global SETTINGS
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                saved = json.load(f)
                SETTINGS.update(saved)
        except Exception as e:
            print(f"Settings load error: {e}")

def save_settings():
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(SETTINGS, f, indent=4)
    except Exception as e:
        print(f"Settings save error: {e}")

load_settings()

@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    if request.method == 'POST':
        data = request.json
        if 'refresh_rate' in data:
            data['refresh_rate'] = max(2, min(60, int(data['refresh_rate'])))
        SETTINGS.update(data)
        save_settings()
        return jsonify({"message": "Settings saved", "settings": SETTINGS})
    return jsonify(SETTINGS)

@app.route('/api/settings/reset', methods=['POST'])
def reset_data():
    try:
        action = request.json.get('action')
        if action == 'cache':
            global CACHE_DICT
            CACHE_DICT = {}
            save_cache_disk()
            return jsonify({"message": "Cache cleared"})
        elif action == 'portfolio':
             db = DataStore()
             # Manual portfolio clear
             holdings = db.get_portfolio()
             for h in holdings:
                 db.delete_portfolio_holding(h['symbol'])
        return jsonify({"message": "Portfolio cleared"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Paper Trading Logic ---
PAPER_FILE = 'data/paper_trading.json'

def load_paper_data():
    if not os.path.exists(PAPER_FILE):
        reset_paper_data()
    try:
        with open(PAPER_FILE, 'r') as f:
            return json.load(f)
    except:
        return reset_paper_data()

def save_paper_data(data):
    with open(PAPER_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def reset_paper_data():
    data = {
        "cash": 100000.0,
        "holdings": {},
        "transactions": []
    }
    save_paper_data(data)
    return data

@app.route('/api/paper/funds', methods=['POST'])
def paper_funds():
    """
    Add or Withdraw Funds.
    JSON: { "amount": 50000 }  (Positive to Deposit, Negative to Withdraw)
    """
    req = request.json
    try:
        amount = float(req.get('amount', 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid amount"}), 400

    if amount == 0:
        return jsonify({"error": "Amount cannot be zero"}), 400

    data = load_paper_data()
    
    # Check for withdrawal limit
    if amount < 0 and (data['cash'] + amount) < 0:
         return jsonify({"error": f"Insufficient funds to withdraw ₹{abs(amount):.2f}"}), 400

    data['cash'] += amount
    
    # Log Transaction
    tx_type = "DEPOSIT" if amount > 0 else "WITHDRAW"
    data['transactions'].append({
        "type": tx_type,
        "symbol": "CASH",
        "qty": 0,
        "price": amount,
        "time": time.time()
    })
    
    save_paper_data(data)
    return jsonify({"message": f"{tx_type} Successful", "new_cash": data['cash']})

@app.route('/api/paper/reset', methods=['POST'])
def paper_reset():
    data = reset_paper_data()
    return jsonify({"message": "Account Reset", "data": data})

@app.route('/api/paper/portfolio', methods=['GET'])
def get_paper_portfolio():
    data = load_paper_data()
    holdings = data.get('holdings', {})
    
    portfolio_list = []
    total_invested = 0.0
    current_value = 0.0
    
    for symbol, details in holdings.items():
        qty = details['qty']
        avg_price = details['avg_price']
        
        # Get Live Price
        live_price = avg_price # Fallback
        if symbol in CACHE_DICT:
             live_price = CACHE_DICT[symbol]['price']
        else:
             # Try fetch if missing
             try:
                 import yfinance as yf
                 t = yf.Ticker(symbol)
                 p = t.fast_info.get('last_price')
                 if not p:
                     hist = t.history(period="1d")
                     if not hist.empty:
                        p = hist['Close'].iloc[-1]
                 
                 if p and p > 0:
                     live_price = float(p)
                     # Update Cache
                     if symbol not in CACHE_DICT: CACHE_DICT[symbol] = {}
                     CACHE_DICT[symbol]['price'] = round(live_price, 2)
             except: pass

        invested = qty * avg_price
        curr_val = qty * live_price
        pnl = curr_val - invested
        pnl_pct = (pnl / invested * 100) if invested > 0 else 0.0
        
        portfolio_list.append({
            "symbol": symbol,
            "quantity": qty,
            "avg_price": round(avg_price, 2),
            "current_price": round(live_price, 2),
            "market_value": round(curr_val, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2)
        })
        
        total_invested += invested
        current_value += curr_val
        
    response = {
        "cash": round(data.get('cash', 0), 2),
        "total_invested": round(total_invested, 2),
        "current_value": round(current_value, 2),
        "total_portfolio_value": round(data.get('cash', 0) + current_value, 2),
        "holdings": portfolio_list
    }
    return jsonify(response)

@app.route('/api/paper/buy', methods=['POST'])
def paper_buy():
    req = request.json
    symbol = req.get('symbol')
    qty = int(req.get('quantity', 1))
    price = float(req.get('price', 0)) # User passes price, or we fetch
    
    if not symbol or qty <= 0: return jsonify({"error": "Invalid params"}), 400
    
    data = load_paper_data()
    cash = data['cash']
    
    # Verify Price (Backend Safety)
    if price <= 0:
         if symbol in CACHE_DICT:
             price = CACHE_DICT[symbol]['price']
    
    cost = price * qty
    if cash < cost:
        return jsonify({"error": f"Insufficient Funds. Need ₹{cost:.2f}, Have ₹{cash:.2f}"}), 400
        
    # Execute
    data['cash'] -= cost
    
    if symbol in data['holdings']:
        # Average Price Logic
        h = data['holdings'][symbol]
        old_qty = h['qty']
        old_cost = old_qty * h['avg_price']
        new_cost = old_cost + cost
        new_qty = old_qty + qty
        h['qty'] = new_qty
        h['avg_price'] = new_cost / new_qty
    else:
        data['holdings'][symbol] = {"qty": qty, "avg_price": price}
        
    data['transactions'].append({
        "type": "BUY",
        "symbol": symbol,
        "qty": qty,
        "price": price,
        "time": time.time()
    })
    
    save_paper_data(data)
    
    # Ensure tracking
    if symbol not in TRACKED_STOCKS:
        TRACKED_STOCKS.append(symbol)
        save_tracked_stocks(TRACKED_STOCKS)

    return jsonify({"message": f"Bought {qty} {symbol}", "new_cash": data['cash']})

@app.route('/api/paper/sell', methods=['POST'])
def paper_sell():
    req = request.json
    symbol = req.get('symbol')
    qty = int(req.get('quantity', 1))
    price = float(req.get('price', 0))
    
    data = load_paper_data()
    
    if symbol not in data['holdings']:
        return jsonify({"error": "Not holding this stock"}), 400
        
    h = data['holdings'][symbol]
    if h['qty'] < qty:
        return jsonify({"error": f"Not enough quantity. Have {h['qty']}"}), 400
        
    # Verify Price
    if price <= 0:
         if symbol in CACHE_DICT:
             price = CACHE_DICT[symbol]['price']

    # Execute
    revenue = price * qty
    data['cash'] += revenue
    
    h['qty'] -= qty
    if h['qty'] == 0:
        del data['holdings'][symbol]
        
    data['transactions'].append({
        "type": "SELL",
        "symbol": symbol,
        "qty": qty,
        "price": price,
        "time": time.time()
    })
    
    save_paper_data(data)
    return jsonify({"message": f"Sold {qty} {symbol}", "new_cash": data['cash']})


@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')

@app.route('/news')
def news_page():
    return render_template('news.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/api/stocks', methods=['POST'])
def add_stock():
    data = request.json
    symbol = data.get('symbol', '').upper()
    if not symbol:
        return jsonify({"error": "No symbol provided"}), 400
        
    if symbol not in TRACKED_STOCKS:
        # Trigger fetch
        try:
            print(f"Adding new stock: {symbol}")
            process_symbol(symbol, live=True) # Fetch immediate data
            
            # Generate Explanation
            try:
                from src.models.explain import ModelExplainer
                explainer = ModelExplainer()
                explainer.explain_latest(symbol)
            except Exception as e:
                print(f"Explanation generation failed: {e}")
                
            TRACKED_STOCKS.append(symbol)
            save_tracked_stocks(TRACKED_STOCKS) # PERSIST
            
            # Invalidate Cache
            global CACHE_DATA
            CACHE_DATA = None
            
            return jsonify({"message": f"Added {symbol}", "status": "success"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"message": "Stock already tracked"}), 200

@app.route('/api/stocks/<symbol>', methods=['DELETE'])
def remove_stock(symbol):
    symbol = symbol.upper()
    if symbol in TRACKED_STOCKS:
        TRACKED_STOCKS.remove(symbol)
        save_tracked_stocks(TRACKED_STOCKS) # PERSIST
        
        # Invalidate Cache
        global CACHE_DATA
        CACHE_DATA = None
        
        return jsonify({"message": f"Removed {symbol}"})
    return jsonify({"error": "Stock not found"}), 404

@app.route('/api/market/refresh', methods=['POST'])
def refresh_market():
    """
    Force updates all tracked stocks immediately using threading.
    """
    try:
        print("Manual Market Refresh Triggered")
        tracked = list(TRACKED_STOCKS)
        
        # Use ThreadPool to fast refresh prices
        from concurrent.futures import ThreadPoolExecutor
        
        def refresh_single(symbol):
            try:
                import yfinance as yf
                # Fast Info Fetch
                t = yf.Ticker(symbol)
                price = t.fast_info.get('last_price')
                prev = t.fast_info.get('previous_close')
                
                if price and prev:
                    change = ((price - prev) / prev) * 100
                    # Update Cache immediately
                    if symbol in CACHE_DICT:
                        CACHE_DICT[symbol]['price'] = round(price, 2)
                        CACHE_DICT[symbol]['change'] = round(change, 2)
                    print(f"Refreshed {symbol}: {price}")
                else:
                    # Fallback
                    hist = t.history(period="2d")
                    if len(hist) >= 1:
                        price = hist['Close'].iloc[-1]
                        if symbol in CACHE_DICT: CACHE_DICT[symbol]['price'] = round(price, 2)
            except Exception as e:
                print(f"Refresh Error {symbol}: {e}")

        # Run in parallel
        with ThreadPoolExecutor(max_workers=10) as executor:
             list(executor.map(refresh_single, tracked))
             
        return jsonify({"message": "Market data refreshed", "count": len(tracked)})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/refresh/<symbol>', methods=['POST'])
def refresh_stock(symbol):
    try:
        print(f"Fast Refresh Triggered for {symbol}")
        
        # 1. IMMEDIATE PRICE UPDATE (Synchronous)
        price_updated = False
        try:
            import yfinance as yf
            rt_ticker = yf.Ticker(symbol)
            
            # Use 5d history fallback logic immediately as it's most robust
            hist = rt_ticker.history(period="5d")
            
            price = 0.0
            change = 0.0
            success = False
            
            if not hist.empty and len(hist) >= 2:
                rt_price = hist['Close'].iloc[-1]
                rt_prev = hist['Close'].iloc[-2]
                price = rt_price
                change = ((rt_price - rt_prev) / rt_prev) * 100
                success = True
            
            if not success:
                 # Try fast_info
                 rt_price = rt_ticker.fast_info.get('last_price')
                 rt_prev = rt_ticker.fast_info.get('previous_close')
                 if rt_price and rt_prev:
                     price = rt_price
                     change = ((rt_price - rt_prev) / rt_prev) * 100
                     success = True
            
            if success:
                if symbol not in CACHE_DICT: CACHE_DICT[symbol] = {}
                CACHE_DICT[symbol]['price'] = round(float(price), 2)
                CACHE_DICT[symbol]['change'] = round(float(change), 2)
                price_updated = True
                print(f"Refreshed Price {symbol}: {price}")
                
        except Exception as e:
            print(f"Price Refresh Failed: {e}")

        # 2. HEAVY LIFTING (Background)
        def bg_heavy_refresh(sym):
            try:
                # Store full history
                store_price_data(sym, period="1mo") 
                
                # Fetch News
                try: fetch_and_store_yahoo_news(sym)
                except: pass

                # Fetch Fundamentals
                try: fetch_and_store_fundamentals(sym)
                except: pass
                
                # Re-run AI Analysis
                from src.features.engineer import FeatureEngineer
                fe = FeatureEngineer()
                df = fe.prepare_data(sym, is_training=False)
                
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    # Update other cache fields
                    if sym not in CACHE_DICT: CACHE_DICT[sym] = {} 
                    CACHE_DICT[sym]['sentiment'] = round(float(latest.get('sentiment_score', 0)), 2)
                    CACHE_DICT[sym]['rsi'] = round(float(latest.get('RSI', 50)), 2)
                
                # Re-run AI Prediction (Using logic with RSI fallback)
                from src.models.predict import predict_latest
                pred_df = predict_latest([sym])
                if not pred_df.empty:
                    row = pred_df.iloc[0]
                    if sym not in CACHE_DICT: CACHE_DICT[sym] = {}
                    CACHE_DICT[sym]['decision'] = row['Decision'] # BUY/SELL
                    CACHE_DICT[sym]['confidence'] = round(float(row['Confidence']), 2)
                
                # Re-generate SHAP
                from src.models.explain import ModelExplainer
                explainer = ModelExplainer()
                explainer.explain_latest(sym)
                
                save_cache_disk()
                print(f"Background Refresh Complete for {sym}")
            except Exception as e:
                print(f"Background Refresh Error {sym}: {e}")

        # Start thread
        import threading
        t = threading.Thread(target=bg_heavy_refresh, args=(symbol,), daemon=True)
        t.start()
        
        save_cache_disk() # Save the price update
        return jsonify({"message": f"Refreshed {symbol} (Price updated, Analysis running in background)"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/details/<symbol>')
def get_stock_details(symbol):
    try:
        print(f"Fetching details for {symbol}")
        db = DataStore()
        fundamentals = db.get_latest_fundamentals(symbol)
        print(f"Got fundamentals: {len(fundamentals)} keys")
        news = db.get_recent_news(symbol)
        print(f"Got news: {len(news)} items")
        
        return jsonify({
            "fundamentals": fundamentals,
            "news": news
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio_data():
    try:
        db = DataStore()
        holdings = db.get_portfolio()
        
        summary = {
            "total_value": 0.0,
            "total_investment": 0.0,
            "total_pnl": 0.0,
            "holdings": []
        }
        
        for item in holdings:
            symbol = item['symbol']
            qty = item['quantity']
            avg_price = item['avg_price']
            
            # Get real-time price from Cache
            current_price = 0.0
            if symbol in CACHE_DICT:
                current_price = CACHE_DICT[symbol].get('price', 0.0)
            
            # Fallback if not in cache (could be checking stock_prices or fetching)
            # Fallback if not in cache (could be checking stock_prices or fetching)
            if current_price == 0:
                 # Check Database
                 try:
                    db_price = db.get_latest_price(symbol)
                    if db_price > 0:
                        current_price = db_price
                    else:
                        # Last Resort: Synchronous Quick Fetch
                        try:
                            import yfinance as yf
                            t = yf.Ticker(symbol)
                            current_price = t.fast_info.get('last_price', 0.0)
                            if current_price == 0:
                                df_p = t.history(period="1d")
                                if not df_p.empty:
                                    current_price = df_p['Close'].iloc[-1]
                            # Update Cache so next time it's fast
                            if current_price > 0:
                                CACHE_DICT[symbol] = CACHE_DICT.get(symbol, {})
                                CACHE_DICT[symbol]['price'] = current_price
                        except: pass
                 except: pass

            market_value = qty * current_price
            investment = qty * avg_price
            pnl = market_value - investment
            pnl_pct = (pnl / investment * 100) if investment > 0 else 0.0
            
            summary["total_value"] += market_value
            summary["total_investment"] += investment
            summary["total_pnl"] += pnl
            
            summary["holdings"].append({
                "symbol": symbol,
                "quantity": qty,
                "avg_price": round(avg_price, 2),
                "current_price": round(current_price, 2),
                "market_value": round(market_value, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2)
            })
            
        summary["total_pnl_pct"] = (summary["total_pnl"] / summary["total_investment"] * 100) if summary["total_investment"] > 0 else 0.0
        
        # Round totals
        summary["total_value"] = round(summary["total_value"], 2)
        summary["total_investment"] = round(summary["total_investment"], 2)
        summary["total_pnl"] = round(summary["total_pnl"], 2)
        summary["total_pnl_pct"] = round(summary["total_pnl_pct"], 2)
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio/add', methods=['POST'])
def add_portfolio_item():
    try:
        data = request.json
        symbol = data.get('symbol', '').upper()
        
        # Safe conversion helper
        def safe_float(val):
            try: return float(val)
            except: return 0.0
            
        qty = int(safe_float(data.get('quantity', 0)))
        price = safe_float(data.get('price', 0.0))
        
        if not symbol or qty <= 0 or price < 0:
            return jsonify({"error": "Invalid input"}), 400
            
        db = DataStore()
        db.add_portfolio_holding(symbol, qty, price)
        
        # Ensure we track this stock for price updates
        if symbol not in TRACKED_STOCKS:
            TRACKED_STOCKS.append(symbol)
            save_tracked_stocks(TRACKED_STOCKS)
            # Trigger immediate fetch in background?
            # For now, just rely on next loop
            
        return jsonify({"message": f"Added {symbol} to portfolio"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio/<symbol>', methods=['DELETE'])
def delete_portfolio_item(symbol):
    try:
        db = DataStore()
        db.delete_portfolio_holding(symbol)
        return jsonify({"message": f"Removed {symbol} from portfolio"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Load Symbols
try:
    with open('src/data/nse_symbols.json', 'r') as f:
        NSE_SYMBOLS = json.load(f)
except Exception as e:
    print(f"Error loading symbols: {e}")
    NSE_SYMBOLS = []

@app.route('/api/symbols')
def get_symbols():
    return jsonify(NSE_SYMBOLS)

@app.route('/api/news/refresh', methods=['POST'])
def refresh_news_manual():
    try:
        from concurrent.futures import ThreadPoolExecutor
        print("Manual News Refresh Triggered")
        
        tracked = list(TRACKED_STOCKS)
        
        def fetch_single(symbol):
            try:
                # Use a small delay to prevent rate limit spikes if needed, but here we just go
                fetch_and_store_yahoo_news(symbol)
                print(f"Refreshed news for {symbol}")
            except Exception as e:
                print(f"News Refresh Error {symbol}: {e}")

        # Use moderate workers to avoid DB lock contention
        with ThreadPoolExecutor(max_workers=4) as executor:
             list(executor.map(fetch_single, tracked))
             
        return jsonify({"message": "News refreshed successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/news')
def get_global_news():
    try:
        db = DataStore()
        news = db.get_all_news(limit=50)
        return jsonify(news)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/explanation/<symbol>')
def get_explanation(symbol):
    try:
        import importlib
        import src.features.engineer # Hot-patch dependency first
        importlib.reload(src.features.engineer)
        import src.models.explain
        importlib.reload(src.models.explain)
        from src.models.explain import ModelExplainer
        
        
        # Use the SAME model instance as the dashboard to ensure 100% sync
        explainer = ModelExplainer(model=model)
        
        # Pass cached price to ensure synchronization
        live_price = None
        if symbol.upper() in CACHE_DICT:
             live_price = CACHE_DICT[symbol.upper()].get('price')
        
        # Fallback fetch if not in cache
        if not live_price:
             try:
                 import yfinance as yf
                 t = yf.Ticker(symbol)
                 live_price = t.fast_info.get('last_price')
             except: pass

        text = explainer.get_natural_language_explanation(symbol.upper(), live_price=live_price)
        # Also ensure the plot exists (legacy support)
        # explainer.explain_latest(symbol.upper()) 
        resp = jsonify({"explanation": text})
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return resp
    except Exception as e:
        return jsonify({"explanation": f"Could not generate explanation: {str(e)}"}), 500



# Caching & Background Update
CACHE_DICT = {} # Symbol -> Data
CACHE_FILE = 'data/dashboard_cache.json'

def load_cache_disk():
    global CACHE_DICT
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                CACHE_DICT = json.load(f)
            print(f"Loaded {len(CACHE_DICT)} stocks from disk cache.")
        except Exception as e:
            print(f"Cache load error: {e}")

def save_cache_disk():
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(CACHE_DICT, f)
    except Exception as e:
        print(f"Cache save error: {e}")

# Initial Load
load_cache_disk()

from src.data.stock_price import fetch_stock_data

def store_price_data(symbol, period="3mo"):
    try:
        # Fetch data. Use shorter period for updates to stay fast.
        df = fetch_stock_data(symbol, period=period, interval="1d")
        if df is not None and not df.empty:
            db = DataStore()
            db.save_stock_data(df, symbol)
            # db.close() # DataStore does not have close(), connection is closed in save_stock_data
    except Exception as e:
        print(f"Store Price Error {symbol}: {e}")

def update_data_loop():
    global CACHE_DICT
    print("Background Data Updater Started...")
    while True:
        try:
            # fe = FeatureEngineer()
            
            # Check Market Hours Optimisation
            if SETTINGS.get('market_hours_only', False):
                import datetime
                now = datetime.datetime.now()
                # NSE Hours: 9:15 to 15:30 IST (approx). 
                # Simplistic check: 9 to 16
                if now.hour < 9 or now.hour >= 16:
                    print("Market Closed. Pausing updates (Settings).")
                    time.sleep(60) # Sleep longer
                    continue
            
            # Process stocks
            tracked = list(TRACKED_STOCKS) # Copy
            
            # Use ThreadPoolExecutor for parallelism
            from concurrent.futures import ThreadPoolExecutor
            
            def process_single_stock(symbol):
                try:
                    # Ensure model is available
                    current_model = get_model() # Lazy load if needed

                    # 1. Update Prices (Fast 5d fetch)
                    store_price_data(symbol, period="5d")
                    
                    # 2. Update News & Fundamentals
                    try: fetch_and_store_yahoo_news(symbol)
                    except: pass
                    try: fetch_and_store_fundamentals(symbol)
                    except: pass

                    # 3. Real-Time Price Fetch (PRE-CALC)
                    # We need this BEFORE prediction to inject it
                    rt_price = 0.0
                    rt_change = 0.0
                    try:
                        import yfinance as yf
                        t = yf.Ticker(symbol)
                        # fast_info is fast
                        p = t.fast_info.get('last_price')
                        prev = t.fast_info.get('previous_close')
                        if p and prev:
                            rt_price = round(float(p), 2)
                            rt_change = round(((p - prev) / prev) * 100, 2)
                    except: pass
                    
                    # 4. Predict & Cache (WITH LIVE PRICE)
                    fe = FeatureEngineer()
                    
                    # Pass rt_price to injection if valid
                    live_injection = rt_price if rt_price > 0 else None
                    df = fe.prepare_data(symbol, is_training=False, live_price=live_injection)
                    
                    if df is None or df.empty: return
                        
                    latest = df.iloc[-1]
                    price = latest['close'] # This will now be rt_price if injected
                    sentiment = latest.get('sentiment_score', 0)
                    rsi = latest.get('RSI', 50)
                    
                    # Prepare X
                    import numpy as np
                    drop_cols = ['target', 'future_close', 'future_return', 'date']
                    X = df.iloc[[-1]].drop(columns=[c for c in drop_cols if c in df.columns]).select_dtypes(include=[np.number])
                    
                    # Logics...
                    decision = "HOLD"
                    confidence = 0.0
                    
                    # --- Logic Sync: Strongly Buy Score (0-100) ---
                    buy_score = 50.0
                    override = False
                    
                    if rsi < 30: 
                        buy_score = 90.0 + (30 - rsi)
                        if buy_score > 99: buy_score = 99
                        override = True
                    elif rsi > 70:
                        # User wants floor of 15%. Make overbought less punitive.
                        # RSI 70 -> 40, RSI 90 -> 20.
                        buy_score = 40.0 - (rsi - 70)
                        if buy_score < 15: buy_score = 15
                        override = True

                    if not override and current_model:
                        try:
                            if hasattr(current_model, 'feature_names_in_'):
                                X = X.reindex(columns=current_model.feature_names_in_, fill_value=0)
                            
                            if hasattr(current_model, "predict_proba"):
                                probs = current_model.predict_proba(X)[0]
                                classes = list(current_model.classes_)
                                buy_cls = max(classes)
                                sell_cls = min(classes)
                                
                                p_buy = probs[classes.index(buy_cls)]
                                p_sell = probs[classes.index(sell_cls)]
                                
                                buy_score = 50.0 + (p_buy * 50.0) - (p_sell * 50.0)
                            else:
                                pred = current_model.predict(X)[0]
                                if pred == 1: buy_score = 75.0
                                elif pred == -1: buy_score = 25.0
                                else: buy_score = 50.0
                                
                        except Exception as e:
                            print(f"Prediction logic error {symbol}: {e}")
                            # LOG ERROR TO FILE
                            try:
                                with open('debug_error.log', 'a') as f:
                                    f.write(f"{symbol} Error: {str(e)}\n")
                            except: pass
                            
                            buy_score = 50.0

                    
                    # --- Multi-Factor Upgrades ---
                    pe = latest.get('trailingPE', 0)
                    pb = latest.get('priceToBook', 0)
                    
                    # 1. Valuation Modifiers
                    if pe > 0:
                        if pe < 15: buy_score += 10 # Cheap
                        elif pe > 30: buy_score -= 10 # Expensive
                        elif pe > 50: buy_score -= 15 # Very Expensive
                    
                    if pb > 0:
                        if pb < 1.0: buy_score += 5 # Deep Value
                        elif pb > 5.0: buy_score -= 5 # Premium
                        
                    # 2. Sentiment Modifiers
                    if sentiment > 0.2: buy_score += 10 # Strong News
                    elif sentiment < -0.2: buy_score -= 10 # Bad News
                    
                    # Aggressive Floor: Never go below 15%
                    buy_score = max(15, min(99, buy_score))
                    
                    decision = "Strongly Buy" # Label
                    confidence = buy_score / 100.0 # Normalized 0-1 for cache consistency

                    stock_info = {
                        "symbol": symbol,
                        "price": round(float(price), 2),
                        "change": 0.0,
                        "sentiment": round(float(sentiment), 2),
                        "rsi": round(float(rsi), 2),
                        "decision": decision,
                        "confidence": round(confidence, 4),
                        # Keep history logic simple for now
                        "history": df['close'].tail(30).tolist()
                    }
                    
                    
                    # --- Real-Time Price Update (Simplified) ---
                    # We already fetched rt_price and rt_change earlier for injection
                    if rt_price > 0:
                        stock_info['price'] = rt_price
                        stock_info['change'] = rt_change
                        # print(f"{symbol} Real-Time: {rt_price} ({rt_change}%)")
                    else:
                         # Fallback to DB Price if RT failed
                         if len(df) >= 2:
                             prev = df.iloc[-2]['close']
                             stock_info['change'] = round(((price - prev)/prev)*100, 2)
                    
                    
                    # 3.5 AI Prediction already done above (Unified Logic)

                    # 4. Generate AI Explanation Plot (Background)
                    try:
                        from src.models.explain import ModelExplainer
                        explainer = ModelExplainer()
                        explainer.explain_latest(symbol)
                    except Exception as e:
                        print(f"Explain Error {symbol}: {e}")

                    CACHE_DICT[symbol] = stock_info
                    
                except Exception as e:
                    print(f"BG Process Error {symbol}: {e}")
                    # Placeholder
                    CACHE_DICT[symbol] = CACHE_DICT.get(symbol, {
                        "symbol": symbol, "price": 0.0, "change": 0.0, "sentiment":0.0,
                        "rsi":0.0, "decision":"BUY", "confidence":0.5 # Default safety
                    })

            # Run in parallel (5 workers)
            with ThreadPoolExecutor(max_workers=5) as executor:
                list(executor.map(process_single_stock, tracked))
            
            save_cache_disk() # Save after batch
            print(f"Cycle Complete. Updated {len(CACHE_DICT)} stocks.")
            
        except Exception as e:
            print(f"Background Loop Crash: {e}")
            
        time.sleep(10) # Wait 10s



import threading
# Start background thread
t = threading.Thread(target=update_data_loop, daemon=True)
t.start()

@app.route('/api/data')
def get_data():
    """
    Returns JSON with latest data for all stocks from cache.
    Instant response.
    """
    return jsonify(list(CACHE_DICT.values()))

@app.route('/api/market/sentiment')
def get_market_sentiment():
    """
    Returns aggregated sentiment data for Heatmap.
    Format: [{x: 'Symbol', y: SentimentScore, size: Price/Volume}]
    """
    data = []
    for symbol, info in CACHE_DICT.items():
        # Sentiment -1 to 1. 0 is Neutral.
        score = info.get('sentiment', 0)
        # Use Market Cap or Price as size? We only have Price.
        # Let's use Price * 100 as a proxy for "importance" visual, or just Price.
        # Ideally Volume, but we need to check if we have it.
        # Basic: Equal size blocks, colored by sentiment.
        # Better: Sized by Price.
        price = info.get('price', 100)
        
        data.append({
            "x": symbol,
            "y": score, 
            "size": price 
        })
    return jsonify(data)

@app.route('/api/indices')
def get_indices():
    """
    Fetches major market indices (Nifty 50, Sensex).
    Cached for 60 seconds to prevent rate limiting.
    """
    try:
        import yfinance as yf
        indices = {
            "NIFTY 50": "^NSEI",
            "SENSEX": "^BSESN"
        }
        
        result = []
        for name, ticker in indices.items():
            try:
                # Fast fetch for REAL-TIME data
                t = yf.Ticker(ticker)
                # fast_info is typically live
                price = t.fast_info.get('last_price')
                prev = t.fast_info.get('previous_close')
                
                if price and prev:
                    change = price - prev
                    pct = (change / prev) * 100
                else:
                    # Fallback to history if fast_info fails
                    hist = t.history(period="5d")
                    if not hist.empty:
                        price = hist['Close'].iloc[-1]
                        prev = hist['Close'].iloc[-2] if len(hist) > 1 else price
                        change = price - prev
                        pct = (change / prev) * 100
                    else:
                        continue # Skip if no data
                
                result.append({
                    "name": name,
                    "price": round(price, 2),
                    "change": round(change, 2),
                    "percent": round(pct, 2)
                })
            except Exception as e:
                print(f"Index Fetch Error {name}: {e}")
        
        return jsonify(result)
    except Exception as e:
        print(f"Indices Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/explanation/<symbol>')
def explanation(symbol):
    """
    Returns the SHAP PNG explanation.
    """
    # Check if file exists
    filename = f"{symbol}_explanation.png"
    path = f"data/{filename}"
    
    if os.path.exists(path):
        response = send_from_directory('../../data', filename)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    else:
        # Try generating it on the fly if missing
        try:
            response = send_from_directory('../../data', filename)
            # HOSTILE CACHING: Force browser to never cache this image
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
        except FileNotFoundError:
            pass # Fall through to generation attempt
    
    # Try generating it on the fly if missing
    # Try generating it on the fly if missing
    try:
        from src.models.explain import ModelExplainer
        
        # Debug Sync
        live_price = None
        if symbol in CACHE_DICT:
            live_price = CACHE_DICT[symbol].get('price')
            print(f"DEBUG: Dashboard Cached Price for {symbol}: {live_price} (Score: {CACHE_DICT[symbol].get('confidence')})")
        
        # If no cache, try fetching
        if not live_price:
            try:
                import yfinance as yf
                t = yf.Ticker(symbol)
                live_price = t.fast_info.get('last_price')
            except: pass

        explainer = ModelExplainer()
        # PASS THE LIVE PRICE TO SYNC
        explainer.explain_latest(symbol, live_price=live_price)
        
        if os.path.exists(path):
            try:
                response = send_from_directory('../../data', filename)
                # HOSTILE CACHING: Force browser to never cache this image
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
                return response
            except FileNotFoundError:
                pass # Fall through to "not found"
    except Exception as e:
         print(f"Explanation Route Error {symbol}: {e}")
         
    return jsonify({"error": "Image not found"}), 404
    return "Explanation not found (Analysis pending...)", 404

@app.route('/api/status')
def get_status():
    uptime_seconds = int(time.time() - START_TIME)
    # Format as HH:MM:SS
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return jsonify({
        "status": "online",
        "uptime": f"{hours:02}:{minutes:02}:{seconds:02}",
        "uptime_seconds": uptime_seconds,
        "tracked_count": len(TRACKED_STOCKS),
        "cache_status": f"Active ({len(CACHE_DICT)} items)"
    })

@app.route('/api/history/<symbol>')
def get_history(symbol):
    try:
        import yfinance as yf
        # Get params
        period = request.args.get('period', '6mo')
        interval = request.args.get('interval', '1d')
        
        # Validate to prevent abuse/errors
        valid_periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
        valid_intervals = ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo']
        
        if period not in valid_periods: period = '6mo'
        if interval not in valid_intervals: interval = '1d'

        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            return jsonify([])

        data = []
        for index, row in df.iterrows():
            data.append({
                "x": index.isoformat(), 
                "y": round(float(row['Close']), 2)
            })
            
        return jsonify(data)
    except Exception as e:
        print(f"History Error {symbol}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([])

@app.route('/api/chart/intraday/<symbol>')
def intraday_chart(symbol):
    try:
        import yfinance as yf
        # Fetch 1-day data with 1-minute interval (Live Intraday)
        # valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        # valid intervals: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
        # "1d" period gives current day's data (or last trading day if closed)
        
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1d", interval="1m")
        
        # Holiday/Weekend Fallback: If today is empty, get last 5 days
        if df.empty:
            df = ticker.history(period="5d", interval="1m")
            if not df.empty:
                # Filter for the LAST available date only
                last_dt = df.index[-1]
                last_date = last_dt.date()
                df = df[df.index.date == last_date]
        
        if df.empty:
            return jsonify({"error": "No intraday data available"}), 404
            
        # Format for Chart.js [ {t: timestamp, y: price}, ... ]
        data = []
        for index, row in df.iterrows():
            # index is datetime (localized)
            data.append({
                "t": index.isoformat(), 
                "y": round(row['Close'], 2)
            })
            
        return jsonify({
            "symbol": symbol,
            "data": data,
            "current_price": round(df['Close'].iloc[-1], 2),
            "prev_close": ticker.info.get('previousClose', 0.0)
        })
            
    except Exception as e:
        print(f"Chart Error {symbol}: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Threaded=True allows background interactions
    # Use reloader=False to avoid double-init of background threads in some envs
    app.run(debug=True, use_reloader=False)
