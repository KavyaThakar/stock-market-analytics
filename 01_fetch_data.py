import pandas as pd
import yfinance as yf
import sys

# Expanded selection of 40 major NSE equities across 8 key sectors
TICKERS = [
    # Energy & Infra
    "RELIANCE.NS", "LT.NS", "NTPC.NS", "POWERGRID.NS", "ONGC.NS", "COALINDIA.NS", "ADANIENT.NS",
    # IT
    "TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS", "LTIM.NS",
    # Banking & Financial Services
    "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS",
    # FMCG
    "ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS", "TATACONSUM.NS",
    # Telecom
    "BHARTIARTL.NS",
    # Auto & Manufacturing
    "MARUTI.NS", "M&M.NS", "TATAMOTORS.NS", "HEROMOTOCO.NS", "EICHERMOT.NS", "BAJAJ-AUTO.NS",
    # Pharma & Healthcare
    "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "APOLLOHOSP.NS", "DIVISLAB.NS",
    # Consumer, Materials & Retail
    "ASIANPAINT.NS", "TITAN.NS", "ULTRACEMCO.NS", "GRASIM.NS", "PIDILITIND.NS", "TRENT.NS"
]

def fetch_stock_data(tickers, period="5y"):
    """
    Downloads 5 years of daily OHLCV data for 40 major NSE stocks using yfinance.
    Combines them into a single long-format DataFrame and saves to stock_data_raw.csv.
    """
    print("==================================================")
    print(f"Step 1: Fetching 5 Years of Stock Market Data for {len(tickers)} Tickers (yfinance)")
    print("==================================================")
    
    all_dfs = []
    success_counts = {}

    for ticker in tickers:
        try:
            print(f"Fetching data for {ticker} (Period: {period})...")
            t = yf.Ticker(ticker)
            df = t.history(period=period, auto_adjust=False)
            
            if df.empty:
                print(f"  [WARNING] No data returned for {ticker}. Skipping.")
                continue

            df = df.reset_index()
            
            # Standardize date column
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
            else:
                print(f"  [WARNING] 'Date' column not found for {ticker}. Skipping.")
                continue
                
            df['Ticker'] = ticker
            
            # Select required columns
            required_cols = ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_cols:
                if col not in df.columns:
                    df[col] = None
                    
            df_subset = df[required_cols].copy()
            all_dfs.append(df_subset)
            success_counts[ticker] = len(df_subset)
            print(f"  [SUCCESS] Downloaded {len(df_subset)} rows for {ticker}.")

        except Exception as e:
            print(f"  [ERROR] Failed to download {ticker}: {e}")
            continue

    print("\n--- Download Summary ---")
    for tkr, count in success_counts.items():
        print(f"{tkr:<15}: {count} rows")

    if not all_dfs:
        print("ERROR: No data fetched for any ticker. Exiting.")
        sys.exit(1)

    combined_df = pd.concat(all_dfs, ignore_index=True)
    raw_csv = "stock_data_raw.csv"
    combined_df.to_csv(raw_csv, index=False)
    print(f"\nSaved expanded raw data to '{raw_csv}' with total {len(combined_df)} rows.\n")
    return combined_df

if __name__ == "__main__":
    fetch_stock_data(TICKERS, period="5y")
