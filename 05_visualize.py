import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Segoe UI, DejaVu Sans, Arial'
plt.rcParams['axes.edgecolor'] = '#cbd5e1'
plt.rcParams['axes.linewidth'] = 0.8

CHARTS_DIR = "charts"

def ensure_charts_dir():
    if not os.path.exists(CHARTS_DIR):
        os.makedirs(CHARTS_DIR)

def create_visualizations():
    """
    Generates and saves 6 high-quality analytical charts for the expanded dataset.
    """
    ensure_charts_dir()
    print("==================================================")
    print("Step 5: Generating Analytical Visualizations (Expanded Dataset)")
    print("==================================================")
    
    clean_csv = "stock_data_clean.csv"
    df = pd.read_csv(clean_csv)
    df['Date'] = pd.to_datetime(df['Date'])

    # --------------------------------------------------------------------
    # Chart 1: Headline Normalized Price Trend (Indexed to 100)
    # --------------------------------------------------------------------
    print("Generating Chart 1: Normalized Price Trend...")
    pivot_close = df.pivot(index='Date', columns='Ticker', values='Close')
    normalized_prices = pivot_close.div(pivot_close.iloc[0]) * 100.0

    # Determine top 3 and bottom 3 overall performers
    first_prices = df.groupby('Ticker')['Close'].first()
    last_prices = df.groupby('Ticker')['Close'].last()
    total_returns = ((last_prices - first_prices) / first_prices) * 100.0
    
    top3 = total_returns.nlargest(3).index.tolist()
    bottom3 = total_returns.nsmallest(3).index.tolist()
    featured_tickers = set(top3 + bottom3)

    fig, ax = plt.subplots(figsize=(16, 8), dpi=300)
    for ticker in normalized_prices.columns:
        if ticker in top3:
            ax.plot(normalized_prices.index, normalized_prices[ticker], label=f"{ticker} (Top)", linewidth=2.2, alpha=0.95)
        elif ticker in bottom3:
            ax.plot(normalized_prices.index, normalized_prices[ticker], label=f"{ticker} (Bottom)", linewidth=2.0, linestyle='--', alpha=0.85)
        else:
            ax.plot(normalized_prices.index, normalized_prices[ticker], color='#cbd5e1', linewidth=0.8, alpha=0.4)

    ax.axhline(100, color='#334155', linestyle=':', linewidth=1.5, label='Baseline (100)')
    ax.set_title(f'5-Year Normalized Stock Performance Across {df["Ticker"].nunique()} Equities (Base = 100)', fontsize=16, fontweight='bold', pad=15)
    ax.set_xlabel('Date', fontsize=12, labelpad=10)
    ax.set_ylabel('Indexed Price (Start = 100)', fontsize=12, labelpad=10)
    ax.legend(bbox_to_anchor=(1.01, 1), loc='upper left', frameon=True, facecolor='#ffffff', edgecolor='#cbd5e1')
    plt.tight_layout()
    chart1_path = os.path.join(CHARTS_DIR, "normalized_price_trend.png")
    plt.savefig(chart1_path)
    plt.close()
    print(f"  [SAVED] {chart1_path}")

    # --------------------------------------------------------------------
    # Chart 2: 20-Day Moving Average for Best Performing Stock
    # --------------------------------------------------------------------
    best_ticker = total_returns.idxmax()
    best_return = total_returns.max()

    best_df = df[df['Ticker'] == best_ticker].sort_values('Date').copy()
    best_df['MA20'] = best_df['Close'].rolling(window=20).mean()

    fig, ax = plt.subplots(figsize=(14, 6), dpi=300)
    ax.plot(best_df['Date'], best_df['Close'], label=f'{best_ticker} Daily Close', color='#0284c7', linewidth=1.5)
    ax.plot(best_df['Date'], best_df['MA20'], label='20-Day Moving Average', color='#f59e0b', linewidth=2.0, linestyle='--')
    
    ax.set_title(f'Price & 20-Day MA: Top Performer ({best_ticker} +{best_return:.2f}%)', fontsize=16, fontweight='bold', pad=15)
    ax.set_xlabel('Date', fontsize=12, labelpad=10)
    ax.set_ylabel('Stock Price (INR)', fontsize=12, labelpad=10)
    ax.legend(loc='upper left', frameon=True, facecolor='#ffffff', edgecolor='#cbd5e1')
    plt.tight_layout()
    chart2_path = os.path.join(CHARTS_DIR, "best_performing_ma20.png")
    plt.savefig(chart2_path)
    plt.close()
    print(f"  [SAVED] {chart2_path}")

    # --------------------------------------------------------------------
    # Chart 3: Total Return % by Stock (Sorted Descending)
    # --------------------------------------------------------------------
    print("Generating Chart 3: Total Return % by Stock...")
    returns_df = total_returns.reset_index()
    returns_df.columns = ['Ticker', 'Total_Return_Pct']
    returns_df = returns_df.sort_values(by='Total_Return_Pct', ascending=False)

    fig, ax = plt.subplots(figsize=(16, 7), dpi=300)
    bar_colors = ['#10b981' if x >= 0 else '#ef4444' for x in returns_df['Total_Return_Pct']]
    bars = ax.bar(returns_df['Ticker'], returns_df['Total_Return_Pct'], color=bar_colors, edgecolor='#1e293b', width=0.65)

    ax.axhline(0, color='#334155', linewidth=1)
    ax.set_title(f'5-Year Total Percentage Return Across {len(returns_df)} Stocks', fontsize=16, fontweight='bold', pad=15)
    ax.set_xlabel('Ticker', fontsize=12, labelpad=10)
    ax.set_ylabel('Total Return (%)', fontsize=12, labelpad=10)
    plt.xticks(rotation=60, ha='right', fontsize=9)
    plt.tight_layout()
    chart3_path = os.path.join(CHARTS_DIR, "total_return_by_stock.png")
    plt.savefig(chart3_path)
    plt.close()
    print(f"  [SAVED] {chart3_path}")

    # --------------------------------------------------------------------
    # Chart 4: Volatility by Stock
    # --------------------------------------------------------------------
    print("Generating Chart 4: Volatility by Stock...")
    vol_df = df.groupby('Ticker')['Daily_Return_Pct'].std().reset_index()
    vol_df.columns = ['Ticker', 'Volatility_StdDev']
    vol_df = vol_df.sort_values(by='Volatility_StdDev', ascending=False)

    fig, ax = plt.subplots(figsize=(16, 7), dpi=300)
    bars = ax.bar(vol_df['Ticker'], vol_df['Volatility_StdDev'], color='#8b5cf6', edgecolor='#4c1d95', width=0.65)

    ax.set_title(f'Daily Return Volatility (Standard Deviation %) across {len(vol_df)} Equities', fontsize=16, fontweight='bold', pad=15)
    ax.set_xlabel('Ticker', fontsize=12, labelpad=10)
    ax.set_ylabel('Daily Return Std Dev (%)', fontsize=12, labelpad=10)
    plt.xticks(rotation=60, ha='right', fontsize=9)
    plt.tight_layout()
    chart4_path = os.path.join(CHARTS_DIR, "volatility_by_stock.png")
    plt.savefig(chart4_path)
    plt.close()
    print(f"  [SAVED] {chart4_path}")

    # --------------------------------------------------------------------
    # Chart 5: Average Daily Return by Sector
    # --------------------------------------------------------------------
    print("Generating Chart 5: Average Daily Return by Sector...")
    sector_df = df.groupby('Sector')['Daily_Return_Pct'].mean().reset_index()
    sector_df.columns = ['Sector', 'Avg_Daily_Return_Pct']
    sector_df = sector_df.sort_values(by='Avg_Daily_Return_Pct', ascending=False)

    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
    sec_colors = ['#059669' if x >= 0 else '#dc2626' for x in sector_df['Avg_Daily_Return_Pct']]
    bars = ax.bar(sector_df['Sector'], sector_df['Avg_Daily_Return_Pct'], color=sec_colors, edgecolor='#1e293b', width=0.55)

    for bar in bars:
        height = bar.get_height()
        va = 'bottom' if height >= 0 else 'top'
        ax.annotate(f'{height:+.4f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3 if height >= 0 else -10),
                    textcoords="offset points",
                    ha='center', va=va, fontsize=9, fontweight='bold')

    ax.axhline(0, color='#334155', linewidth=1)
    ax.set_title('Average Daily Return Percentage by Sector', fontsize=16, fontweight='bold', pad=15)
    ax.set_xlabel('Sector', fontsize=12, labelpad=10)
    ax.set_ylabel('Mean Daily Return (%)', fontsize=12, labelpad=10)
    plt.xticks(rotation=30, ha='right')
    plt.tight_layout()
    chart5_path = os.path.join(CHARTS_DIR, "average_return_by_sector.png")
    plt.savefig(chart5_path)
    plt.close()
    print(f"  [SAVED] {chart5_path}")

    # --------------------------------------------------------------------
    # Chart 6: Correlation Heatmap of Daily Returns Across Equities
    # --------------------------------------------------------------------
    print("Generating Chart 6: Correlation Heatmap...")
    pivot_returns = df.pivot(index='Date', columns='Ticker', values='Daily_Return_Pct')
    corr_matrix = pivot_returns.corr()

    fig, ax = plt.subplots(figsize=(14, 12), dpi=300)
    sns.heatmap(corr_matrix, annot=False, cmap='vlag', vmin=-1, vmax=1,
                linewidths=0.2, cbar_kws={'label': 'Pearson Correlation'}, ax=ax)

    ax.set_title(f'Cross-Equity Daily Return Correlation Heatmap ({len(corr_matrix)} Stocks)', fontsize=16, fontweight='bold', pad=15)
    plt.xticks(rotation=90, fontsize=8)
    plt.yticks(rotation=0, fontsize=8)
    plt.tight_layout()
    chart6_path = os.path.join(CHARTS_DIR, "correlation_heatmap.png")
    plt.savefig(chart6_path)
    plt.close()
    print(f"  [SAVED] {chart6_path}")

    print("\n==================================================")
    print("All 6 visualization charts generated successfully!")
    print("==================================================\n")

if __name__ == "__main__":
    create_visualizations()
