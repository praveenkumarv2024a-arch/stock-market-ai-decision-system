# Indian Stock Market AI Decision System 📈🤖

A customized AI-powered financial dashboard that provides **BUY**, **SELL**, or **HOLD** recommendations for Indian stocks (NSE). The system integrates real-time stock prices, news sentiment analysis, company fundamentals, and explainable Machine Learning models.

---

## 🚀 Key Features

* **Real-time Market Data**: Fetches live stock prices and historical data using `yfinance`.
* **NLP News Sentiment**: Scrapes financial news using `BeautifulSoup` & `feedparser`, evaluating sentiment scores with `vaderSentiment` and `textblob`.
* **Fundamental Indicators**: Analyzes key company health metrics (P/E Ratio, ROE, Debt-to-Equity, etc.).
* **Hybrid ML/AI Predictions**: Leverages state-of-the-art predictive algorithms including **XGBoost**, **LightGBM**, and **LSTM** networks.
* **Explainable AI (XAI)**: Generates SHAP (SHapley Additive exPlanations) plots to explain *why* the model makes a specific decision.
* **Paper Trading Simulator**: Includes a mock trading account with fund management to test your AI strategies.

---

## 🛠️ Tech Stack

* **Backend**: Flask (Python)
* **Frontend**: HTML5, Vanilla CSS, JS (Interactive Plotly Charts)
* **Database**: SQLite (local) / PostgreSQL (production)
* **Data Processing**: Pandas, NumPy, Ta (Technical Analysis)
* **Machine Learning**: Scikit-Learn, XGBoost, LightGBM, SHAP
* **Sentiment Analysis**: VADER Sentiment, TextBlob

---

## 📁 Project Structure

```text
├── data/                  # SQLite DB, cash balance, settings, and cached analysis
├── src/
│   ├── data/              # Data collection scripts (Yahoo news, fundamentals)
│   ├── features/          # Feature engineering & technical indicators calculation
│   ├── models/            # ML model prediction and SHAP explainability
│   └── web/               # Flask routing, UI templates, and paper trading API
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

* **Positive SHAP Value**: Features driving the recommendation toward a **BUY**.
* **Negative SHAP Value**: Features driving the recommendation toward a **SELL**.

---

## 📝 License
This project is licensed under the MIT License - see the LICENSE file for details.
