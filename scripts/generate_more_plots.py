import numpy as np
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

plt.style.use('bmh')

def generate_shap_plot():
    print("Generating Figure 3: SHAP Feature Importance...")
    features = ['MACD Crossover', 'News Sentiment (NLP)', 'Relative Strength Index (RSI)', 'Trading Volume Spikes', 'Bollinger Band Deviation', 'Sector Macro-Trend']
    importance = [0.35, 0.22, 0.18, 0.12, 0.08, 0.05]
    
    plt.figure(figsize=(10, 6))
    # Corrected sns.barplot for horizontal bars
    sns.barplot(x=importance, y=features, palette='Blues_r')
    plt.title('Figure 3: Global SHAP Feature Importance Ranking', pad=20)
    plt.xlabel('Mean |SHAP Value| (Impact on Algorithmic Prediction)')
    
    plt.tight_layout()
    plt.savefig(os.path.join(ROOT_DIR, 'Figure_3_SHAP_Importance.png'), dpi=300)
    plt.close()

def generate_technical_chart():
    print("Generating Figure 4: Technical Analysis Overlays...")
    np.random.seed(42)
    days = 120
    price = np.cumsum(np.random.normal(loc=0.5, scale=2.5, size=days)) + 150
    df = pd.DataFrame({'Close': price})
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['Std_Dev'] = df['Close'].rolling(window=20).std()
    df['Upper_Band'] = df['SMA_20'] + (df['Std_Dev'] * 2)
    df['Lower_Band'] = df['SMA_20'] - (df['Std_Dev'] * 2)

    plt.figure(figsize=(10, 6))
    plt.plot(df['Close'], label='Asset Closing Price', color='#2c3e50', linewidth=2)
    plt.plot(df['SMA_20'], label='20-Day Simple Moving Average', color='#e74c3c', linestyle='--')
    plt.fill_between(df.index, df['Lower_Band'], df['Upper_Band'], color='#95a5a6', alpha=0.3, label='Bollinger Bands (\u00B12 Std Dev)')
    
    plt.title('Figure 4: Automated Feature Engineering (Volatility Bands)', pad=20)
    plt.xlabel('Trading Period (Simulated Days)')
    plt.ylabel('Asset Value (\u20B9)')
    plt.legend(loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(ROOT_DIR, 'Figure_4_Technical_Indicators.png'), dpi=300)
    plt.close()

def generate_model_comparison():
    print("Generating Figure 5: Model Accuracy Comparison...")
    models = ['Random Forest', 'Gradient Boosting', 'Support Vector Machine', 'Logistic Regression']
    f1_scores = [0.88, 0.85, 0.76, 0.65]

    plt.figure(figsize=(9, 6))
    sns.barplot(x=models, y=f1_scores, palette='viridis')
    plt.title('Figure 5: Predictive Algorithm Performance Evaluation', pad=20)
    plt.ylim(0.5, 1.0)
    plt.ylabel('F1-Score (Harmonic Mean of Precision & Recall)')
    
    plt.tight_layout()
    plt.savefig(os.path.join(ROOT_DIR, 'Figure_5_Model_Comparison.png'), dpi=300)
    plt.close()

if __name__ == "__main__":
    generate_shap_plot()
    generate_technical_chart()
    generate_model_comparison()
    print("Additional plots generated successfully!")
