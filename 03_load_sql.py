import sqlite3
import pandas as pd

def load_sql():
    """
    Loads stock_data_clean.csv into SQLite database 'stocks.db'
    in table 'prices' and creates indices on Ticker and Date.
    """
    print("==================================================")
    print("Step 3: Loading Clean Data into SQLite Database")
    print("==================================================")
    
    clean_csv = "stock_data_clean.csv"
    db_file = "stocks.db"

    try:
        df = pd.read_csv(clean_csv)
    except Exception as e:
        print(f"ERROR: Unable to read {clean_csv}: {e}")
        return

    print(f"Loaded {len(df)} records from '{clean_csv}'.")

    # Connect to SQLite database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Write to table 'prices'
    df.to_sql('prices', conn, if_exists='replace', index=False)
    print(f"Successfully populated table 'prices' in '{db_file}'.")

    # Create explicit indices
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prices_ticker ON prices(Ticker);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prices_date ON prices(Date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prices_ticker_date ON prices(Ticker, Date);")
    
    conn.commit()
    print("Indices created successfully on 'Ticker', 'Date', and '(Ticker, Date)'.")
    
    # Verify table schema & row count
    cursor.execute("SELECT COUNT(*) FROM prices;")
    count = cursor.fetchone()[0]
    print(f"Verification: 'prices' table contains {count} rows.")

    conn.close()
    print("Database loading complete.\n")

if __name__ == "__main__":
    load_sql()
