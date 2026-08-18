import sqlite3
import pandas as pd
import json
import re

QUERY_NAMES = [
    "1. Overall Return per Stock (Ranked)",
    "2. 20-Day Moving Average per Stock",
    "3. Day-over-Day Return using LAG() Window Function",
    "4. Volatility (Standard Deviation of Daily_Return_Pct) per Stock",
    "5. Average Daily Return & Volatility by Sector",
    "6. Single Best and Single Worst Trading Day per Stock",
    "7. Correlation-Ready Data Extraction",
    "8. 2-Year Price Range & Peak Drawdown Analysis",
    "9. Monthly Sector Average Performance",
    "10. Top 5 Single-Day Market Gainers Across All Stocks"
]

def run_queries():
    """
    Parses queries.sql, executes each query against stocks.db via pandas.read_sql_query,
    prints formatted query results to terminal, and saves insights to insights.json.
    """
    print("==================================================")
    print("Step 4: Executing Analytical SQL Queries")
    print("==================================================")
    
    db_file = "stocks.db"
    sql_file = "queries.sql"

    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        print(f"ERROR: Cannot connect to {db_file}: {e}")
        return

    try:
        with open(sql_file, "r") as f:
            full_sql_script = f.read()
    except Exception as e:
        print(f"ERROR: Cannot read {sql_file}: {e}")
        return

    # Split script into individual queries by semicolon
    raw_blocks = full_sql_script.split(";")
    valid_queries = []
    
    for block in raw_blocks:
        # Strip whitespace
        cleaned = block.strip()
        if not cleaned:
            continue
        # Remove standalone comment blocks
        lines = [line for line in cleaned.splitlines() if not line.strip().startswith("--")]
        query_text = "\n".join(lines).strip()
        if query_text:
            valid_queries.append(cleaned)

    insights_data = {}

    for idx, sql in enumerate(valid_queries):
        name = QUERY_NAMES[idx] if idx < len(QUERY_NAMES) else f"Query {idx + 1}"

        print(f"\n==================================================")
        print(f" {name} ")
        print(f"==================================================")
        
        try:
            df = pd.read_sql_query(sql, conn)
            
            # Print preview (full table for short results <= 15 rows, head for long results)
            if len(df) <= 15:
                print(df.to_string(index=False))
            else:
                print(df.head(10).to_string(index=False))
                print(f"... ({len(df) - 10} more rows)")
                
            insights_data[name] = df.to_dict(orient="records")

        except Exception as e:
            print(f"ERROR executing query '{name}': {e}")
            insights_data[name] = {"error": str(e)}

    conn.close()

    # Save output to insights.json
    output_json = "insights.json"
    with open(output_json, "w") as f:
        json.dump(insights_data, f, indent=2)
        
    print(f"\n==================================================")
    print(f"All {len(valid_queries)} query results successfully saved to '{output_json}'")
    print(f"==================================================\n")

if __name__ == "__main__":
    run_queries()
