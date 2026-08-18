import pandas as pd

SECTOR_MAP = {
    # Energy & Infra
    "RELIANCE.NS": "Energy&Infra",
    "LT.NS": "Energy&Infra",
    "NTPC.NS": "Energy&Infra",
    "POWERGRID.NS": "Energy&Infra",
    "ONGC.NS": "Energy&Infra",
    "COALINDIA.NS": "Energy&Infra",
    "ADANIENT.NS": "Energy&Infra",
    # IT
    "TCS.NS": "IT",
    "INFY.NS": "IT",
    "HCLTECH.NS": "IT",
    "WIPRO.NS": "IT",
    "TECHM.NS": "IT",
    "LTIM.NS": "IT",
    # Banking & Financial Services
    "HDFCBANK.NS": "Banking",
    "ICICIBANK.NS": "Banking",
    "SBIN.NS": "Banking",
    "KOTAKBANK.NS": "Banking",
    "AXISBANK.NS": "Banking",
    "BAJFINANCE.NS": "Banking",
    "BAJAJFINSV.NS": "Banking",
    # FMCG
    "ITC.NS": "FMCG",
    "HINDUNILVR.NS": "FMCG",
    "NESTLEIND.NS": "FMCG",
    "BRITANNIA.NS": "FMCG",
    "TATACONSUM.NS": "FMCG",
    # Telecom
    "BHARTIARTL.NS": "Telecom",
    # Auto & Manufacturing
    "MARUTI.NS": "Auto",
    "M&M.NS": "Auto",
    "TATAMOTORS.NS": "Auto",
    "HEROMOTOCO.NS": "Auto",
    "EICHERMOT.NS": "Auto",
    "BAJAJ-AUTO.NS": "Auto",
    # Pharma & Healthcare
    "SUNPHARMA.NS": "Pharma",
    "DRREDDY.NS": "Pharma",
    "CIPLA.NS": "Pharma",
    "APOLLOHOSP.NS": "Pharma",
    "DIVISLAB.NS": "Pharma",
    # Consumer & Retail
    "ASIANPAINT.NS": "Consumer",
    "TITAN.NS": "Consumer",
    "ULTRACEMCO.NS": "Consumer",
    "GRASIM.NS": "Consumer",
    "PIDILITIND.NS": "Consumer",
    "TRENT.NS": "Consumer"
}

def clean_stock_data():
    """
    Loads stock_data_raw.csv, audits missing values & duplicates,
    forward-fills missing price data per ticker, adds Sector mapping,
    computes Daily_Return_Pct per ticker, and saves to stock_data_clean.csv.
    """
    print("==================================================")
    print("Step 2: Cleaning Data & Engineering Features")
    print("==================================================")
    
    raw_file = "stock_data_raw.csv"
    try:
        df = pd.read_csv(raw_file)
    except Exception as e:
        print(f"ERROR: Unable to read {raw_file}: {e}")
        return None

    print(f"Initial raw record count: {len(df)}")
    
    # 1. Audit Missing Values
    print("\n--- Missing Values Audit ---")
    missing_sum = df.isnull().sum()
    for col, count in missing_sum.items():
        print(f"  Column '{col}': {count} missing values")
        
    # 2. Audit & Remove Duplicates
    print("\n--- Duplicate Pairs Audit ---")
    dup_count = df.duplicated(subset=['Date', 'Ticker']).sum()
    print(f"  Duplicate (Date, Ticker) pairs found: {dup_count}")
    if dup_count > 0:
        df = df.drop_duplicates(subset=['Date', 'Ticker'], keep='first')
        print(f"  Removed {dup_count} duplicate rows.")

    # 3. Sort by Ticker and Date
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by=['Ticker', 'Date']).reset_index(drop=True)

    # 4. Forward Fill Missing Price Data per Ticker
    print("\n--- Forward-Filling Price Gaps per Ticker ---")
    price_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    df[price_cols] = df.groupby('Ticker')[price_cols].transform(lambda group: group.ffill().bfill())

    # 5. Add Sector Column
    print("\n--- Mapping Sector Information ---")
    df['Sector'] = df['Ticker'].map(SECTOR_MAP).fillna("Other")

    # 6. Compute Daily_Return_Pct per Ticker
    print("\n--- Computing Day-over-Day Return Percentage ---")
    df['Daily_Return_Pct'] = df.groupby('Ticker')['Close'].pct_change() * 100.0
    df['Daily_Return_Pct'] = df['Daily_Return_Pct'].fillna(0.0)

    # Re-format Date to standard string YYYY-MM-DD
    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')

    clean_file = "stock_data_clean.csv"
    df.to_csv(clean_file, index=False)
    print(f"\nData cleaning & feature engineering complete.")
    print(f"Saved clean dataset to '{clean_file}' with {len(df)} rows across {df['Ticker'].nunique()} equities.")
    print(f"Columns in clean dataset: {list(df.columns)}\n")
    return df

if __name__ == "__main__":
    clean_stock_data()
