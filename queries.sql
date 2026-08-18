-- ====================================================================
-- Stock Market Data Analytics - Analytical SQL Queries (queries.sql)
-- Target Database: SQLite (stocks.db, table: prices)
-- ====================================================================

-- --------------------------------------------------------------------
-- QUERY 1: Overall Return per Stock (Ranked Highest to Lowest)
-- Formula: (Last Close - First Close) / First Close * 100
-- --------------------------------------------------------------------
WITH FirstLastDates AS (
    SELECT 
        Ticker,
        Sector,
        MIN(Date) as StartDate,
        MAX(Date) as EndDate
    FROM prices
    GROUP BY Ticker, Sector
),
StartPrices AS (
    SELECT p.Ticker, p.Close as StartClose
    FROM prices p
    JOIN FirstLastDates f ON p.Ticker = f.Ticker AND p.Date = f.StartDate
),
EndPrices AS (
    SELECT p.Ticker, p.Close as EndClose
    FROM prices p
    JOIN FirstLastDates f ON p.Ticker = f.Ticker AND p.Date = f.EndDate
)
SELECT 
    f.Ticker,
    f.Sector,
    s.StartClose,
    e.EndClose,
    ROUND(((e.EndClose - s.StartClose) / s.StartClose) * 100.0, 2) AS Overall_Return_Pct,
    RANK() OVER (ORDER BY ((e.EndClose - s.StartClose) / s.StartClose) DESC) AS Performance_Rank
FROM FirstLastDates f
JOIN StartPrices s ON f.Ticker = s.Ticker
JOIN EndPrices e ON f.Ticker = e.Ticker
ORDER BY Performance_Rank;

-- --------------------------------------------------------------------
-- QUERY 2: 20-Day Moving Average per Stock using Window Function
-- --------------------------------------------------------------------
SELECT 
    Date,
    Ticker,
    Close,
    ROUND(AVG(Close) OVER (
        PARTITION BY Ticker 
        ORDER BY Date 
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ), 2) AS Moving_Avg_20
FROM prices
ORDER BY Ticker, Date;

-- --------------------------------------------------------------------
-- QUERY 3: Day-over-Day Return using LAG() Window Function
-- --------------------------------------------------------------------
SELECT 
    Date,
    Ticker,
    Close,
    LAG(Close, 1) OVER (PARTITION BY Ticker ORDER BY Date) AS Prev_Close,
    ROUND(
        ((Close - LAG(Close, 1) OVER (PARTITION BY Ticker ORDER BY Date)) / 
        LAG(Close, 1) OVER (PARTITION BY Ticker ORDER BY Date)) * 100.0, 
        2
    ) AS Calculated_Daily_Return_Pct
FROM prices
ORDER BY Ticker, Date;

-- --------------------------------------------------------------------
-- QUERY 4: Volatility (Standard Deviation of Daily_Return_Pct) per Stock (Ranked)
-- --------------------------------------------------------------------
SELECT 
    Ticker,
    Sector,
    COUNT(*) AS Trading_Days,
    ROUND(AVG(Daily_Return_Pct), 4) AS Mean_Daily_Return_Pct,
    ROUND(
        SQRT(
            (AVG(Daily_Return_Pct * Daily_Return_Pct) - (AVG(Daily_Return_Pct) * AVG(Daily_Return_Pct))) 
            * COUNT(*) / (COUNT(*) - 1)
        ), 4
    ) AS Volatility_StdDev_Pct,
    RANK() OVER (
        ORDER BY SQRT(
            (AVG(Daily_Return_Pct * Daily_Return_Pct) - (AVG(Daily_Return_Pct) * AVG(Daily_Return_Pct))) 
            * COUNT(*) / (COUNT(*) - 1)
        ) DESC
    ) AS Volatility_Rank
FROM prices
GROUP BY Ticker, Sector
ORDER BY Volatility_Rank;

-- --------------------------------------------------------------------
-- QUERY 5: Average Daily Return and Volatility by Sector (Grouped & Ranked)
-- --------------------------------------------------------------------
SELECT 
    Sector,
    COUNT(DISTINCT Ticker) AS Stock_Count,
    ROUND(AVG(Daily_Return_Pct), 4) AS Avg_Daily_Return_Pct,
    ROUND(
        SQRT(
            (AVG(Daily_Return_Pct * Daily_Return_Pct) - (AVG(Daily_Return_Pct) * AVG(Daily_Return_Pct))) 
            * COUNT(*) / (COUNT(*) - 1)
        ), 4
    ) AS Sector_Volatility_StdDev,
    RANK() OVER (ORDER BY AVG(Daily_Return_Pct) DESC) AS Sector_Rank
FROM prices
GROUP BY Sector
ORDER BY Sector_Rank;

-- --------------------------------------------------------------------
-- QUERY 6: Single Best and Single Worst Trading Day per Stock
-- --------------------------------------------------------------------
WITH RankedReturns AS (
    SELECT 
        Ticker,
        Date,
        Daily_Return_Pct,
        ROW_NUMBER() OVER (PARTITION BY Ticker ORDER BY Daily_Return_Pct DESC) as RankBest,
        ROW_NUMBER() OVER (PARTITION BY Ticker ORDER BY Daily_Return_Pct ASC) as RankWorst
    FROM prices
)
SELECT 
    b.Ticker,
    b.Date AS Best_Day_Date,
    ROUND(b.Daily_Return_Pct, 2) AS Best_Day_Return_Pct,
    w.Date AS Worst_Day_Date,
    ROUND(w.Daily_Return_Pct, 2) AS Worst_Day_Return_Pct
FROM RankedReturns b
JOIN RankedReturns w ON b.Ticker = w.Ticker AND w.RankWorst = 1
WHERE b.RankBest = 1
ORDER BY b.Ticker;

-- --------------------------------------------------------------------
-- QUERY 7: Correlation-Ready Data Extraction
-- --------------------------------------------------------------------
SELECT 
    Date,
    Ticker,
    ROUND(Daily_Return_Pct, 4) AS Daily_Return_Pct
FROM prices
ORDER BY Date, Ticker;

-- --------------------------------------------------------------------
-- QUERY 8: 2-Year Price Range & Peak Drawdown Analysis
-- --------------------------------------------------------------------
WITH RangeStats AS (
    SELECT 
        Ticker,
        MIN(Low) AS Period_Low,
        MAX(High) AS Period_High,
        MIN(Date) AS Start_Date,
        MAX(Date) AS Latest_Date
    FROM prices
    GROUP BY Ticker
),
LatestPrice AS (
    SELECT p.Ticker, p.Close AS Current_Close
    FROM prices p
    JOIN RangeStats r ON p.Ticker = r.Ticker AND p.Date = r.Latest_Date
)
SELECT 
    r.Ticker,
    ROUND(r.Period_Low, 2) AS Two_Year_Low,
    ROUND(r.Period_High, 2) AS Two_Year_High,
    ROUND(l.Current_Close, 2) AS Latest_Close,
    ROUND(((l.Current_Close - r.Period_High) / r.Period_High) * 100.0, 2) AS Pct_From_Peak
FROM RangeStats r
JOIN LatestPrice l ON r.Ticker = l.Ticker
ORDER BY Pct_From_Peak DESC;

-- --------------------------------------------------------------------
-- QUERY 9: Monthly Sector Average Performance
-- --------------------------------------------------------------------
SELECT 
    strftime('%Y-%m', Date) AS Year_Month,
    Sector,
    ROUND(AVG(Daily_Return_Pct), 4) AS Monthly_Avg_Daily_Return
FROM prices
GROUP BY Year_Month, Sector
ORDER BY Year_Month, Sector;

-- --------------------------------------------------------------------
-- QUERY 10: Top 5 Highest Single-Day Market Gainers Across All Stocks
-- --------------------------------------------------------------------
SELECT 
    Date,
    Ticker,
    Sector,
    ROUND(Daily_Return_Pct, 2) AS Daily_Return_Pct,
    ROUND(Close, 2) AS Close_Price
FROM prices
ORDER BY Daily_Return_Pct DESC
LIMIT 5;
