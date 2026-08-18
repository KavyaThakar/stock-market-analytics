import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# Set page configuration
st.set_page_config(
    page_title="Stock Market Data Analytics Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.0rem;
        color: #475569;
        margin-bottom: 1.5rem;
        line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load cleaned stock price data and pre-computed insights."""
    csv_file = "stock_data_clean.csv"
    json_file = "insights.json"
    
    df = pd.read_csv(csv_file)
    df['Date'] = pd.to_datetime(df['Date'])
    
    insights = {}
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            insights = json.load(f)
            
    return df, insights

df, insights = load_data()

# --------------------------------------------------------------------
# Sidebar Controls
# --------------------------------------------------------------------
st.sidebar.image("https://img.icons8.com/color/96/000000/line-chart.png", width=64)
st.sidebar.title("Dashboard Controls")

all_tickers = sorted(df['Ticker'].unique().tolist())
all_sectors = sorted(df['Sector'].dropna().unique().tolist())

# Sector filter dropdown
selected_sectors = st.sidebar.multiselect(
    "Filter by Sector",
    options=all_sectors,
    default=all_sectors
)

# Filter tickers based on sector selection
available_tickers = df[df['Sector'].isin(selected_sectors)]['Ticker'].unique().tolist()

# Smart default ticker selection (Top liquid benchmarks for clean initial presentation)
preferred_defaults = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "BHARTIARTL.NS", "TRENT.NS"]
default_selected_tickers = [t for t in preferred_defaults if t in available_tickers]
if not default_selected_tickers:
    default_selected_tickers = available_tickers[:5]

selected_tickers = st.sidebar.multiselect(
    "Select Stocks to Analyze",
    options=available_tickers,
    default=default_selected_tickers
)

if not selected_tickers:
    st.warning("Please select at least one ticker from the sidebar.")
    st.stop()

# Filter dataset
filtered_df = df[df['Ticker'].isin(selected_tickers)].copy()

# --------------------------------------------------------------------
# Title and Description
# --------------------------------------------------------------------
st.markdown('<div class="main-title">📈 Stock Market Data Analytics Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">'
    'An interactive financial analytics dashboard analyzing 5 years of daily OHLCV market data for major National Stock Exchange (NSE) equities fetched via <code>yfinance</code>. '
    'Use the sidebar controls to filter tickers, compare relative growth, evaluate sector trends, and explore return correlations.'
    '</div>',
    unsafe_allow_html=True
)

# --------------------------------------------------------------------
# KPI Metrics Row
# --------------------------------------------------------------------
start_prices = filtered_df.groupby('Ticker')['Close'].first()
end_prices = filtered_df.groupby('Ticker')['Close'].last()
total_returns = ((end_prices - start_prices) / start_prices) * 100.0
volatilities = filtered_df.groupby('Ticker')['Daily_Return_Pct'].std()

best_ticker = total_returns.idxmax()
best_return = total_returns.max()

worst_ticker = total_returns.idxmin()
worst_return = total_returns.min()

most_volatile_ticker = volatilities.idxmax()
most_volatile_val = volatilities.max()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Stocks Selected",
        value=f"{len(selected_tickers)} Equities",
        delta=f"Out of {len(all_tickers)} Available"
    )

with col2:
    st.metric(
        label="Best Performer",
        value=best_ticker,
        delta=f"+{best_return:.2f}% Return" if best_return >= 0 else f"{best_return:.2f}% Return"
    )

with col3:
    st.metric(
        label="Worst Performer",
        value=worst_ticker,
        delta=f"{worst_return:.2f}% Return",
        delta_color="inverse"
    )

with col4:
    st.metric(
        label="Most Volatile Stock",
        value=most_volatile_ticker,
        delta=f"{most_volatile_val:.2f}% Std Dev",
        delta_color="off"
    )

st.markdown("---")

# --------------------------------------------------------------------
# Interactive Normalized Price Trend Chart (Base = 100)
# --------------------------------------------------------------------
st.subheader("📊 Normalized Price Performance Trend (Indexed to 100)")
st.caption("Normalizing close prices to 100 on the start date allows direct percentage-based growth comparison across equities.")

pivot_close = filtered_df.pivot(index='Date', columns='Ticker', values='Close')
normalized_prices = pivot_close.div(pivot_close.iloc[0]) * 100.0
normalized_df = normalized_prices.reset_index().melt(id_vars=['Date'], var_name='Ticker', value_name='Indexed_Price')

fig_trend = px.line(
    normalized_df,
    x='Date',
    y='Indexed_Price',
    color='Ticker',
    labels={"Indexed_Price": "Indexed Price (Base = 100)", "Date": "Date"},
    template="plotly_white"
)
fig_trend.add_hline(y=100, line_dash="dash", line_color="#64748b", annotation_text="Baseline (100)")

# Clean Layout: Place legend on the right side with ample top margin to prevent overlapping title
fig_trend.update_layout(
    title=dict(text="Cumulative Stock Price Growth (Baseline = 100)", y=0.98, x=0.01),
    margin=dict(t=50, b=40, l=50, r=120),
    hovermode="x unified",
    legend=dict(
        orientation="v",
        yanchor="top",
        y=1.0,
        xanchor="left",
        x=1.02,
        title=dict(text="Ticker")
    )
)
st.plotly_chart(fig_trend, use_container_width=True)

# --------------------------------------------------------------------
# Performance & Sector Analysis (2 Columns)
# --------------------------------------------------------------------
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("🥇 Total Return % by Stock")
    returns_df = total_returns.reset_index()
    returns_df.columns = ['Ticker', 'Total_Return_Pct']
    returns_df = returns_df.sort_values(by='Total_Return_Pct', ascending=False)
    
    fig_returns = px.bar(
        returns_df,
        x='Ticker',
        y='Total_Return_Pct',
        color='Total_Return_Pct',
        color_continuous_scale=px.colors.diverging.RdYlGn,
        text_auto='.1f' if len(selected_tickers) <= 15 else False,
        template="plotly_white"
    )
    fig_returns.update_layout(
        title=dict(text="Overall Return (%) per Selected Equity", y=0.95),
        coloraxis_showscale=False,
        yaxis_title="Total Return (%)",
        margin=dict(t=50, b=40, l=40, r=40)
    )
    st.plotly_chart(fig_returns, use_container_width=True)

with chart_col2:
    st.subheader("🏢 Average Daily Return by Sector")
    sector_df = filtered_df.groupby('Sector')['Daily_Return_Pct'].mean().reset_index()
    sector_df.columns = ['Sector', 'Avg_Daily_Return_Pct']
    sector_df = sector_df.sort_values(by='Avg_Daily_Return_Pct', ascending=False)
    
    fig_sector = px.bar(
        sector_df,
        x='Sector',
        y='Avg_Daily_Return_Pct',
        color='Avg_Daily_Return_Pct',
        color_continuous_scale=px.colors.sequential.Greens,
        text_auto='.4f',
        template="plotly_white"
    )
    fig_sector.update_layout(
        title=dict(text="Mean Daily Return (%) across Sectors", y=0.95),
        coloraxis_showscale=False,
        yaxis_title="Avg Daily Return (%)",
        margin=dict(t=50, b=40, l=40, r=40)
    )
    st.plotly_chart(fig_sector, use_container_width=True)

# --------------------------------------------------------------------
# Cross-Asset Return Correlation Heatmap
# --------------------------------------------------------------------
st.subheader("🔥 Daily Returns Cross-Stock Correlation Heatmap")
st.caption("Pearson correlation matrix of daily returns for selected equities.")

pivot_returns = filtered_df.pivot(index='Date', columns='Ticker', values='Daily_Return_Pct')
corr_matrix = pivot_returns.corr()

fig_heatmap = px.imshow(
    corr_matrix,
    text_auto='.2f' if len(selected_tickers) <= 12 else False,
    color_continuous_scale='RdBu_r',
    zmin=-1.0,
    zmax=1.0,
    template="plotly_white",
    aspect="auto"
)
fig_heatmap.update_layout(
    title=dict(text="Daily Return Correlation Matrix", y=0.96),
    height=650 if len(selected_tickers) > 15 else 500,
    margin=dict(t=50, b=50, l=50, r=50)
)
st.plotly_chart(fig_heatmap, use_container_width=True)

# --------------------------------------------------------------------
# Raw Data Inspector Footer
# --------------------------------------------------------------------
with st.expander("🔍 Inspect Raw Clean Data Table"):
    st.dataframe(filtered_df.sort_values(by=['Date', 'Ticker'], ascending=[False, True]), use_container_width=True)
