# Indian Stock Market AI Decision System 📈🤖

A customized AI-powered financial dashboard that evaluates Indian stocks (NSE) and calculates a **Buying Possibility Score (0–99%)** along with dynamic **Risk Categorization** (Low, Moderate, High Risk). The system integrates real-time stock prices, NLP-based news sentiment, company fundamentals, and explainable Machine Learning models.

---

## 🚀 Key Features

* **Real-time Market Data**: Fetches live stock prices and historical data using `yfinance`.
* **NLP News Sentiment**: Scrapes financial news using `BeautifulSoup` & `feedparser`, evaluating sentiment scores with `vaderSentiment` and `textblob`.
* **Fundamental Indicators**: Analyzes key company health metrics (P/E Ratio, ROE, Debt-to-Equity, etc.).
* **Buying Possibility Score (0-99%)**: Replaces generic "BUY/SELL/HOLD" signals with a precise probability score indicating the strength of a buying opportunity, powered by **XGBoost**, **LightGBM**, and **LSTM** networks.
* **Risk Categorization**: Automatically classifies stocks based on their Buying Possibility:
  * 🟢 **Low Risk**: Score $\ge$ 76%
  * 🟡 **Moderate Risk**: 36% $\le$ Score < 76%
  * 🔴 **High Risk**: Score < 36%
* **Sniper Mode**: A filter that displays only high-probability setups (Buying Possibility Score > 80%) while hiding weaker signals.
* **Explainable AI (XAI)**: Generates SHAP (SHapley Additive exPlanations) waterfall plots to explain *which* specific factors (e.g. RSI, news sentiment, valuation) are driving the final score up or down.
* **Paper Trading Simulator**: Includes a mock trading account with fund management to test your strategies.

---

## 🔍 Detailed Feature Walkthrough

### 1. Real-time Market Data Pipeline
* **Data Source**: Fetches live quotes and historical daily candle bars from the National Stock Exchange (NSE) using `yfinance`.
* **Database Caching**: Stored in a local SQLite database (`data/market_data.db`) to enable fast loading, offline analytics, and reduce network overhead.
* **Live Refresh**: Automatically checks prices in a background daemon thread (`update_data_loop`) and pushes real-time price updates and percentage changes directly to the UI.

### 2. NLP News Sentiment Engine
* **Scraping**: Uses `feedparser` to parse RSS feeds and `BeautifulSoup4` to extract article descriptions from financial news portals.
* **Dual-Core Sentiment Analysis**:
  * **VADER Sentiment (70% Weight)**: Evaluates short headline text, capitalization cues (e.g., "SOARING PROFITS"), and punctuation intensity.
  * **TextBlob (30% Weight)**: Evaluates semantic structure to verify polarity.
* **Sentiment Metric**: Produces a normalized sentiment score between `-1.0` (strong bearish news) and `+1.0` (strong bullish news), which is fed directly into the prediction model.

### 3. Buying Possibility Engine (ML & Safety Overrides)
* **ML Predictions**: Generates a **Buying Possibility Score (0-99%)** showing how strong the current buying opportunity is. Powered by an ensemble of **XGBoost** and **LightGBM** classifiers trained on technical indicators (RSI, SMA, Volume) and sentiment data.
* **Technical Overrides**: For safety, the AI models are checked against strict boundary constraints:
  * **Oversold Booster**: If the Relative Strength Index (RSI) drops below 30, the score is automatically boosted (up to 99%) due to a strong technical rebound opportunity.
  * **Overbought Penalty**: If the RSI exceeds 70, the score is capped (down to 15%) to prevent buying at local market peaks.

### 4. Dynamic Risk Categorization
* Based on the calculated Buying Possibility Score, the dashboard categorizes the risk level:
  * 🟢 **Low Risk (Score $\ge$ 76%)**: Setup has strong technical supports, positive sentiment, and low valuations.
  * 🟡 **Moderate Risk (36% $\le$ Score < 76%)**: Conflicting metrics (e.g., strong sentiment but overbought chart).
  * 🔴 **High Risk (Score < 36%)**: Bearish technical patterns or negative sentiment news alerts.

### 5. Explainable AI (SHAP Explainer)
* To remove the "black box" aspect of Machine Learning, the system runs local **SHAP (SHapley Additive exPlanations)** analysis on the active predictions.
* When a user opens a stock card, the app renders a **SHAP waterfall chart** showing exactly how much each feature (such as Volume, RSI, or News Sentiment) contributed to the final score.
* A natural language explanation translates the complex math: e.g. *"The Buying Possibility score is 87% primarily because RSI is increasing the confidence."*

### 6. Paper Trading Simulator
* **Interactive Account**: Offers a mock trading environment starting with a virtual budget of ₹1,00,000.
* **Mock Trades**: Buy and sell tracked stocks at live market prices.
* **Portfolio Tracker**: Displays average buy price, current price, quantity, total investment, current market value, and unrealized profit/loss (PnL) in real-time.
* **Account Functions**: Deposit or withdraw virtual funds to simulate realistic account growth.

### 7. Sniper Mode Filter
* Easily toggled on/off in the header bar. 
* Once enabled, it applies a client-side filter that hides all weak signals and displays only high-probability setups (Buying Possibility Score $> 80\%$), allowing users to focus on high-conviction trades.

---


## 🛠️ Tech Stack

* **Backend**: Flask (Python)
* **Frontend**: HTML5, Vanilla CSS, JS (Interactive Plotly & ApexCharts)
* **Database**: SQLite (local) / PostgreSQL (production)
* **Data Processing**: Pandas, NumPy, Ta (Technical Analysis Library)
* **Machine Learning**: Scikit-Learn, XGBoost, LightGBM, SHAP
* **Sentiment Analysis**: VADER Sentiment, TextBlob

---

## 📁 Project Structure

```text
├── data/                  # SQLite DB, cash balance, settings, and cached analysis
├── notebooks/             # Jupyter notebooks for model training and EDA (empty/optional)
├── scripts/               # Python utility scripts for database inspection and bulk updates
├── src/
│   ├── data/              # Data collection scripts (Yahoo news, fundamentals)
│   ├── features/          # Feature engineering & technical indicators calculation
│   ├── models/            # ML model prediction and SHAP explainability
│   └── web/               # Flask routing, UI templates, and paper trading API
├── tests/                 # Unit test suite for data collection and NLP sentiment
├── run.py                 # Main entry point to launch the application
├── requirements.txt       # Python package dependencies
└── STARTUP_GUIDE.md       # Guide on auto-starting the app on Windows
```

---

## 💻 Getting Started

### Prerequisites
* Python 3.8 or higher installed.

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/stock-market-ai.git
   cd stock-market-ai
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Launch the application:
   ```bash
   python run.py
   ```
   Open `http://127.0.0.1:5004` in your browser.

---

## 📊 Model Explainability (SHAP)
Instead of acting as a "black box," the system uses **SHAP values** to explain how individual indicators (e.g., RSI, News Sentiment, MACD) influence the model's decision:

* **Positive SHAP Value**: Features driving the recommendation toward a higher **Buying Possibility**.
* **Negative SHAP Value**: Features lowering the score and pushing it toward **High Risk**.

---

## 📝 License
This project is licensed under the MIT License - see the LICENSE file for details.
