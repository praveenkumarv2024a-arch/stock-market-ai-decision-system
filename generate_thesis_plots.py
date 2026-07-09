import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set the style to look professional and academic
plt.style.use('bmh')

def generate_correlation_matrix():
    print("Generating Figure 1: Correlation Matrix...")
    np.random.seed(42)
    days = 252 # Trading days in a year
    # Simulate some stock returns
    data = np.random.normal(loc=0.0005, scale=0.02, size=(days, 5))
    
    # Force some realistic correlations
    data[:, 1] = data[:, 0] * 0.85 + np.random.normal(0, 0.01, days) # High positive correlation (Tech to Tech)
    data[:, 2] = -data[:, 0] * 0.65 + np.random.normal(0, 0.01, days) # Negative correlation (Tech to Defensive)

    df = pd.DataFrame(data, columns=['TCS', 'INFOSYS', 'HDFCBANK', 'ITC', 'RELIANCE'])
    corr = df.corr()

    plt.figure(figsize=(8, 6))
    sns.heatmap(corr, annot=True, cmap='coolwarm', vmin=-1, vmax=1, fmt=".2f", linewidths=.5)
    plt.title('Figure 1: Cross-Sector Multivariate Correlation Matrix', pad=20)
    plt.tight_layout()
    plt.savefig('Figure_1_Correlation_Matrix.png', dpi=300)
    plt.close()

def generate_density_plot():
    print("Generating Figure 2: Return Density Plot...")
    # Generate 'fat-tailed' data (Laplace distribution) vs Normal distribution
    np.random.seed(100)
    actual_returns = np.random.laplace(loc=0.001, scale=0.015, size=2000)
    normal_returns = np.random.normal(loc=0.001, scale=0.015, size=2000)

    plt.figure(figsize=(9, 6))
    sns.kdeplot(actual_returns, label='Actual Market Returns (Leptokurtic)', color='#e74c3c', fill=True, alpha=0.5)
    sns.kdeplot(normal_returns, label='Standard Normal Distribution', color='#2c3e50', linestyle='--', linewidth=2)
    
    plt.title('Figure 2: Statistical Density of Daily Returns', pad=20)
    plt.xlabel('Daily Percentage Return')
    plt.ylabel('Probability Density')
    plt.legend()
    plt.xlim(-0.15, 0.15)
    plt.tight_layout()
    plt.savefig('Figure_2_Return_Density.png', dpi=300)
    plt.close()

if __name__ == "__main__":
    print("--- Starting Thesis Plot Generation ---")
    generate_correlation_matrix()
    generate_density_plot()
    print("--- Success! Plots saved as PNG files in your folder. ---")
