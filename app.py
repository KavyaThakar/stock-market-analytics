import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os

# ════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="NSE Stock Market Analytics Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ════════════════════════════════════════════════════════════════════════
# CUSTOM CSS — Premium styling with Google Fonts + theme-aware colors
# ════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Global font override */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    .main-title {
        font-family: 'Inter', sans-serif;
        font-size: 2.4rem;
        font-weight: 800;
        color: var(--text-color);
        margin-bottom: 0.1rem;
        letter-spacing: -0.02em;
    }
    .sub-title {
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        color: var(--text-color);
        opacity: 0.7;
        margin-bottom: 1.2rem;
        line-height: 1.6;
    }
    .section-header {
        font-family: 'Inter', sans-serif;
        font-size: 1.15rem;
        font-weight: 600;
        color: var(--text-color);
        margin-top: 0.5rem;
        margin-bottom: 0.3rem;
        letter-spacing: -0.01em;
    }
    .insight-card {
        background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(59,130,246,0.05));
        border-left: 4px solid #6366f1;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 12px;
        font-family: 'Inter', sans-serif;
        font-size: 0.88rem;
        color: var(--text-color);
        line-height: 1.55;
    }
    .metric-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.78rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-color);
        opacity: 0.55;
    }
    .metric-value {
        font-family: 'Inter', sans-serif;
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--text-color);
    }
    .positive { color: #10b981 !important; }
    .negative { color: #ef4444 !important; }
    .neutral  { color: #f59e0b !important; }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.9rem;
        letter-spacing: -0.01em;
    }
    
    /* Sidebar polish */
    section[data-testid="stSidebar"] {
        font-family: 'Inter', sans-serif;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1rem;
    }

    /* Divider */
    .gradient-divider {
        height: 3px;
        background: linear-gradient(90deg, #6366f1, #3b82f6, #06b6d4, #10b981);
        border: none;
        border-radius: 2px;
        margin: 0.8rem 0 1.2rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════
# PLOTLY THEME TEMPLATE
# ════════════════════════════════════════════════════════════════════════
PLOTLY_LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Inter, sans-serif", size=12),
    margin=dict(t=50, b=40, l=50, r=50),
    hovermode="x unified",
    hoverlabel=dict(font_size=12, font_family="Inter"),
)

ACCENT_COLORS = [
    "#6366f1", "#3b82f6", "#06b6d4", "#10b981", "#f59e0b",
    "#ef4444", "#ec4899", "#8b5cf6", "#14b8a6", "#f97316",
    "#84cc16", "#e11d48"
]


# ════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ════════════════════════════════════════════════════════════════════════
@st.cache_data
def load_data():
    """Load cleaned stock price data and pre-computed SQL insights."""
    df = pd.read_csv("stock_data_clean.csv")
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(['Ticker', 'Date']).reset_index(drop=True)

    insights = {}
    if os.path.exists("insights.json"):
        with open("insights.json", "r") as f:
            insights = json.load(f)

    return df, insights


@st.cache_data
def compute_technicals(df):
    """Pre-compute technical indicators per ticker."""
    out = []
    for ticker, grp in df.groupby('Ticker'):
        g = grp.copy().sort_values('Date')
        # Moving averages
        g['MA20'] = g['Close'].rolling(20).mean()
        g['MA50'] = g['Close'].rolling(50).mean()
        g['MA200'] = g['Close'].rolling(200).mean()
        # Bollinger Bands (20-day)
        g['BB_Mid'] = g['MA20']
        g['BB_Std'] = g['Close'].rolling(20).std()
        g['BB_Upper'] = g['BB_Mid'] + 2 * g['BB_Std']
        g['BB_Lower'] = g['BB_Mid'] - 2 * g['BB_Std']
        # RSI (14-day)
        delta = g['Close'].diff()
        gain = delta.where(delta > 0, 0.0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        g['RSI'] = 100.0 - (100.0 / (1.0 + rs))
        # MACD
        ema12 = g['Close'].ewm(span=12, adjust=False).mean()
        ema26 = g['Close'].ewm(span=26, adjust=False).mean()
        g['MACD'] = ema12 - ema26
        g['MACD_Signal'] = g['MACD'].ewm(span=9, adjust=False).mean()
        g['MACD_Hist'] = g['MACD'] - g['MACD_Signal']
        # Cumulative return
        g['Cum_Return'] = (1 + g['Daily_Return_Pct'] / 100.0).cumprod() - 1
        # Running max / drawdown
        g['Running_Max'] = g['Close'].cummax()
        g['Drawdown_Pct'] = ((g['Close'] - g['Running_Max']) / g['Running_Max']) * 100.0
        # Rolling volatility (21-day annualized)
        g['Rolling_Vol_21'] = g['Daily_Return_Pct'].rolling(21).std() * np.sqrt(252)
        # Rolling Sharpe (63-day ≈ 3 month, assuming 0% risk-free)
        roll_mean = g['Daily_Return_Pct'].rolling(63).mean() * 252
        roll_std = g['Daily_Return_Pct'].rolling(63).std() * np.sqrt(252)
        g['Rolling_Sharpe_63'] = roll_mean / roll_std.replace(0, np.nan)
        out.append(g)
    return pd.concat(out, ignore_index=True)


df, insights = load_data()
tech_df = compute_technicals(df)


# ════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════
st.sidebar.image("https://img.icons8.com/color/96/000000/line-chart.png", width=64)
st.sidebar.markdown("### 🎛️ Analytics Controls")

all_tickers = sorted(df['Ticker'].unique().tolist())
all_sectors = sorted(df['Sector'].dropna().unique().tolist())

selected_sectors = st.sidebar.multiselect(
    "Filter by Sector",
    options=all_sectors,
    default=all_sectors,
    help="Narrow down stocks by their market sector."
)

available_tickers = sorted(df[df['Sector'].isin(selected_sectors)]['Ticker'].unique().tolist())

preferred_defaults = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "BHARTIARTL.NS", "TRENT.NS"]
default_tickers = [t for t in preferred_defaults if t in available_tickers]
if not default_tickers:
    default_tickers = available_tickers[:5]

selected_tickers = st.sidebar.multiselect(
    "Select Stocks",
    options=available_tickers,
    default=default_tickers,
    help="Choose equities for analysis."
)

if not selected_tickers:
    st.warning("⚠️ Please select at least one stock from the sidebar to begin analysis.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"<div style='font-size:0.75rem;opacity:0.5;font-family:Inter,sans-serif;'>"
    f"📅 Data range: {df['Date'].min().strftime('%b %Y')} – {df['Date'].max().strftime('%b %Y')}<br>"
    f"📊 {len(all_tickers)} equities · {len(df):,} records"
    f"</div>",
    unsafe_allow_html=True
)

# Filtered datasets
filtered_df = tech_df[tech_df['Ticker'].isin(selected_tickers)].copy()
filtered_raw = df[df['Ticker'].isin(selected_tickers)].copy()


# ════════════════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════════════════
st.markdown('<div class="main-title">📈 NSE Stock Market Analytics Platform</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">'
    'Advanced financial analytics platform analyzing 5 years of daily OHLCV data for major NSE equities. '
    'Features technical indicators (RSI, MACD, Bollinger Bands), risk analytics (drawdown, VaR, Sharpe), '
    'sector intelligence, and cross-asset correlation analysis.'
    '</div>',
    unsafe_allow_html=True
)
st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════════════════════════
tab_overview, tab_technical, tab_risk, tab_sector, tab_data = st.tabs([
    "📊 Overview",
    "🔬 Technical Analysis",
    "⚡ Risk Analytics",
    "🏢 Sector Intelligence",
    "🗃️ Data Explorer"
])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1: OVERVIEW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_overview:
    # KPI Row
    start_prices = filtered_raw.groupby('Ticker')['Close'].first()
    end_prices = filtered_raw.groupby('Ticker')['Close'].last()
    total_returns = ((end_prices - start_prices) / start_prices) * 100.0
    volatilities = filtered_raw.groupby('Ticker')['Daily_Return_Pct'].std()
    avg_vol = filtered_raw.groupby('Ticker')['Volume'].mean()

    best_ticker = total_returns.idxmax()
    best_return = total_returns.max()
    worst_ticker = total_returns.idxmin()
    worst_return = total_returns.min()
    most_volatile = volatilities.idxmax()
    most_volatile_val = volatilities.max()
    highest_vol_ticker = avg_vol.idxmax()

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.metric("Stocks Selected", f"{len(selected_tickers)}", f"of {len(all_tickers)} available")
    with k2:
        st.metric("🏆 Best Performer", best_ticker.replace('.NS', ''),
                  f"+{best_return:.1f}%" if best_return >= 0 else f"{best_return:.1f}%")
    with k3:
        st.metric("📉 Worst Performer", worst_ticker.replace('.NS', ''),
                  f"{worst_return:.1f}%", delta_color="inverse")
    with k4:
        st.metric("⚡ Most Volatile", most_volatile.replace('.NS', ''),
                  f"{most_volatile_val:.2f}% σ", delta_color="off")
    with k5:
        st.metric("📊 Highest Volume", highest_vol_ticker.replace('.NS', ''),
                  f"{avg_vol.max()/1e6:.1f}M avg", delta_color="off")

    st.markdown("---")

    # ── Normalized Price Trend ──
    st.markdown('<div class="section-header">📈 Normalized Price Performance (Base = 100)</div>', unsafe_allow_html=True)
    st.caption("All stock prices indexed to 100 at the start date for direct percentage growth comparison.")

    pivot_close = filtered_raw.pivot(index='Date', columns='Ticker', values='Close')
    normalized = pivot_close.div(pivot_close.iloc[0]) * 100.0
    norm_melted = normalized.reset_index().melt(id_vars='Date', var_name='Ticker', value_name='Indexed')

    fig_trend = px.line(norm_melted, x='Date', y='Indexed', color='Ticker',
                        color_discrete_sequence=ACCENT_COLORS)
    fig_trend.add_hline(y=100, line_dash="dash", line_color="#94a3b8",
                        annotation_text="Baseline 100", annotation_position="bottom right")
    fig_trend.update_layout(**PLOTLY_LAYOUT,
                            title=dict(text="Cumulative Growth (Indexed to 100)", y=0.97, x=0.01),
                            yaxis_title="Indexed Price",
                            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02))
    st.plotly_chart(fig_trend, use_container_width=True)

    # ── Two-column: Returns + Volatility ──
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-header">🥇 Total Return % by Stock</div>', unsafe_allow_html=True)
        ret_df = total_returns.reset_index()
        ret_df.columns = ['Ticker', 'Return']
        ret_df = ret_df.sort_values('Return', ascending=True)
        fig_ret = px.bar(ret_df, x='Return', y='Ticker', orientation='h',
                         color='Return', color_continuous_scale='RdYlGn',
                         text_auto='.1f')
        fig_ret.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False,
                              xaxis_title="Total Return (%)", yaxis_title="",
                              height=max(350, len(selected_tickers) * 35))
        st.plotly_chart(fig_ret, use_container_width=True)

    with c2:
        st.markdown('<div class="section-header">⚡ Annualized Volatility by Stock</div>', unsafe_allow_html=True)
        vol_df = (volatilities * np.sqrt(252)).reset_index()
        vol_df.columns = ['Ticker', 'AnnVol']
        vol_df = vol_df.sort_values('AnnVol', ascending=True)
        fig_vol = px.bar(vol_df, x='AnnVol', y='Ticker', orientation='h',
                         color='AnnVol', color_continuous_scale='YlOrRd',
                         text_auto='.1f')
        fig_vol.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False,
                              xaxis_title="Annualized Volatility (%)", yaxis_title="",
                              height=max(350, len(selected_tickers) * 35))
        st.plotly_chart(fig_vol, use_container_width=True)

    # ── Risk-Return Scatter ──
    st.markdown('<div class="section-header">🎯 Risk-Return Profile (Efficient Frontier View)</div>', unsafe_allow_html=True)
    st.caption("Each dot is a stock. The further right = more volatile; the higher up = better return. Best stocks are top-left.")
    scatter_df = pd.DataFrame({
        'Ticker': total_returns.index,
        'Return': total_returns.values,
        'Volatility': (volatilities * np.sqrt(252)).values,
        'Sector': [filtered_raw[filtered_raw['Ticker']==t]['Sector'].iloc[0] for t in total_returns.index]
    })
    fig_scatter = px.scatter(scatter_df, x='Volatility', y='Return', color='Sector',
                             text='Ticker', size=abs(scatter_df['Return']) + 10,
                             color_discrete_sequence=ACCENT_COLORS)
    fig_scatter.update_traces(textposition='top center', textfont_size=10)
    fig_scatter.update_layout(**PLOTLY_LAYOUT,
                              xaxis_title="Annualized Volatility (%)",
                              yaxis_title="Total Return (%)",
                              height=500)
    fig_scatter.add_hline(y=0, line_dash="dash", line_color="#94a3b8", opacity=0.5)
    st.plotly_chart(fig_scatter, use_container_width=True)

    # ── Correlation Heatmap ──
    st.markdown('<div class="section-header">🔥 Cross-Stock Return Correlation Matrix</div>', unsafe_allow_html=True)
    st.caption("Pearson correlation of daily returns. High correlation = move together; negative = diversification benefit.")

    pivot_ret = filtered_raw.pivot(index='Date', columns='Ticker', values='Daily_Return_Pct')
    corr = pivot_ret.corr()
    fig_hm = px.imshow(corr, text_auto='.2f' if len(selected_tickers) <= 12 else False,
                       color_continuous_scale='RdBu_r', zmin=-1, zmax=1, aspect='auto')
    fig_hm.update_layout(**PLOTLY_LAYOUT, height=max(450, len(selected_tickers) * 40))
    st.plotly_chart(fig_hm, use_container_width=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 2: TECHNICAL ANALYSIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_technical:
    st.markdown('<div class="section-header">🔬 Technical Analysis Dashboard</div>', unsafe_allow_html=True)
    st.caption("Select a single stock below for detailed candlestick charting with Bollinger Bands, RSI, and MACD indicators.")

    ta_ticker = st.selectbox("Select Stock for Technical Analysis",
                             options=selected_tickers,
                             index=0,
                             key="ta_ticker")

    ta_data = filtered_df[filtered_df['Ticker'] == ta_ticker].copy()

    if len(ta_data) < 30:
        st.warning("Not enough data points for meaningful technical analysis.")
    else:
        # ── Candlestick + Bollinger Bands + Volume (subplots) ──
        fig_candle = make_subplots(
            rows=4, cols=1, shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.45, 0.15, 0.20, 0.20],
            subplot_titles=(
                f"{ta_ticker} — Candlestick + Bollinger Bands",
                "Volume",
                "RSI (14-day)",
                "MACD (12, 26, 9)"
            )
        )

        # Candlestick
        fig_candle.add_trace(go.Candlestick(
            x=ta_data['Date'], open=ta_data['Open'], high=ta_data['High'],
            low=ta_data['Low'], close=ta_data['Close'],
            increasing_line_color='#10b981', decreasing_line_color='#ef4444',
            name='OHLC', showlegend=False
        ), row=1, col=1)

        # Bollinger Bands
        fig_candle.add_trace(go.Scatter(
            x=ta_data['Date'], y=ta_data['BB_Upper'], mode='lines',
            line=dict(width=1, color='rgba(99,102,241,0.3)'),
            name='BB Upper', showlegend=False
        ), row=1, col=1)
        fig_candle.add_trace(go.Scatter(
            x=ta_data['Date'], y=ta_data['BB_Lower'], mode='lines',
            fill='tonexty', fillcolor='rgba(99,102,241,0.06)',
            line=dict(width=1, color='rgba(99,102,241,0.3)'),
            name='BB Lower', showlegend=False
        ), row=1, col=1)
        # MA20 line
        fig_candle.add_trace(go.Scatter(
            x=ta_data['Date'], y=ta_data['MA20'], mode='lines',
            line=dict(width=1.5, color='#f59e0b', dash='dot'),
            name='MA20'
        ), row=1, col=1)
        # MA50 line
        fig_candle.add_trace(go.Scatter(
            x=ta_data['Date'], y=ta_data['MA50'], mode='lines',
            line=dict(width=1.5, color='#3b82f6', dash='dash'),
            name='MA50'
        ), row=1, col=1)

        # Volume bars
        vol_colors = ['#10b981' if c >= o else '#ef4444'
                      for c, o in zip(ta_data['Close'], ta_data['Open'])]
        fig_candle.add_trace(go.Bar(
            x=ta_data['Date'], y=ta_data['Volume'],
            marker_color=vol_colors, name='Volume', showlegend=False
        ), row=2, col=1)

        # RSI
        fig_candle.add_trace(go.Scatter(
            x=ta_data['Date'], y=ta_data['RSI'], mode='lines',
            line=dict(width=1.5, color='#8b5cf6'), name='RSI', showlegend=False
        ), row=3, col=1)
        fig_candle.add_hline(y=70, line_dash="dash", line_color="#ef4444", line_width=1, row=3, col=1)
        fig_candle.add_hline(y=30, line_dash="dash", line_color="#10b981", line_width=1, row=3, col=1)
        fig_candle.add_hrect(y0=30, y1=70, fillcolor="rgba(99,102,241,0.04)", line_width=0, row=3, col=1)

        # MACD
        hist_colors = ['#10b981' if v >= 0 else '#ef4444' for v in ta_data['MACD_Hist'].fillna(0)]
        fig_candle.add_trace(go.Bar(
            x=ta_data['Date'], y=ta_data['MACD_Hist'],
            marker_color=hist_colors, name='MACD Hist', showlegend=False
        ), row=4, col=1)
        fig_candle.add_trace(go.Scatter(
            x=ta_data['Date'], y=ta_data['MACD'], mode='lines',
            line=dict(width=1.5, color='#3b82f6'), name='MACD'
        ), row=4, col=1)
        fig_candle.add_trace(go.Scatter(
            x=ta_data['Date'], y=ta_data['MACD_Signal'], mode='lines',
            line=dict(width=1.5, color='#f97316', dash='dash'), name='Signal'
        ), row=4, col=1)

        fig_candle.update_layout(
            height=900,
            font=dict(family="Inter, sans-serif", size=11),
            margin=dict(t=40, b=30, l=50, r=30),
            xaxis_rangeslider_visible=False,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            hovermode="x unified"
        )
        fig_candle.update_yaxes(title_text="Price (₹)", row=1, col=1)
        fig_candle.update_yaxes(title_text="Vol", row=2, col=1)
        fig_candle.update_yaxes(title_text="RSI", row=3, col=1, range=[0, 100])
        fig_candle.update_yaxes(title_text="MACD", row=4, col=1)

        st.plotly_chart(fig_candle, use_container_width=True)

        # ── Technical Summary Card ──
        latest = ta_data.iloc[-1]
        prev = ta_data.iloc[-2] if len(ta_data) > 1 else latest

        rsi_val = latest['RSI']
        rsi_signal = "Overbought 🔴" if rsi_val > 70 else ("Oversold 🟢" if rsi_val < 30 else "Neutral ⚪")
        macd_signal = "Bullish 🟢" if latest['MACD'] > latest['MACD_Signal'] else "Bearish 🔴"
        bb_pos = "Above Upper Band ⚠️" if latest['Close'] > latest['BB_Upper'] else (
            "Below Lower Band ⚠️" if latest['Close'] < latest['BB_Lower'] else "Within Bands ✅")
        ma_trend = "Bullish (Price > MA50) 🟢" if latest['Close'] > latest['MA50'] else "Bearish (Price < MA50) 🔴"

        st.markdown(
            f'<div class="insight-card">'
            f'<b>Technical Summary for {ta_ticker}</b> (Latest: {latest["Date"].strftime("%d %b %Y")})<br><br>'
            f'📊 <b>Close:</b> ₹{latest["Close"]:,.2f} &nbsp;|&nbsp; '
            f'📈 <b>RSI(14):</b> {rsi_val:.1f} — {rsi_signal} &nbsp;|&nbsp; '
            f'📉 <b>MACD:</b> {macd_signal}<br>'
            f'📐 <b>Bollinger:</b> {bb_pos} &nbsp;|&nbsp; '
            f'🔄 <b>Trend:</b> {ma_trend}'
            f'</div>',
            unsafe_allow_html=True
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 3: RISK ANALYTICS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_risk:
    st.markdown('<div class="section-header">⚡ Risk Analytics Dashboard</div>', unsafe_allow_html=True)
    st.caption("Drawdown analysis, rolling volatility, Sharpe ratios, Value at Risk, and return distributions.")

    # ── Drawdown Chart ──
    st.markdown('<div class="section-header">📉 Drawdown from All-Time High (%)</div>', unsafe_allow_html=True)
    st.caption("Shows how far each stock has fallen from its peak at each point in time. Deeper drawdowns = higher risk.")

    fig_dd = go.Figure()
    for i, ticker in enumerate(selected_tickers):
        td = filtered_df[filtered_df['Ticker'] == ticker]
        fig_dd.add_trace(go.Scatter(
            x=td['Date'], y=td['Drawdown_Pct'], mode='lines',
            name=ticker, line=dict(width=1.5, color=ACCENT_COLORS[i % len(ACCENT_COLORS)]),
            fill='tozeroy', fillcolor=f'rgba({int(ACCENT_COLORS[i % len(ACCENT_COLORS)][1:3], 16)},{int(ACCENT_COLORS[i % len(ACCENT_COLORS)][3:5], 16)},{int(ACCENT_COLORS[i % len(ACCENT_COLORS)][5:7], 16)},0.05)'
        ))
    fig_dd.update_layout(**PLOTLY_LAYOUT, yaxis_title="Drawdown (%)", height=400,
                         title=dict(text="Peak-to-Trough Drawdown", y=0.97))
    st.plotly_chart(fig_dd, use_container_width=True)

    # ── Max Drawdown Summary ──
    max_dd = filtered_df.groupby('Ticker')['Drawdown_Pct'].min().sort_values()
    dd_df = max_dd.reset_index()
    dd_df.columns = ['Ticker', 'Max_Drawdown']

    r1, r2 = st.columns(2)
    with r1:
        st.markdown('<div class="section-header">🕳️ Maximum Drawdown by Stock</div>', unsafe_allow_html=True)
        fig_mdd = px.bar(dd_df, x='Max_Drawdown', y='Ticker', orientation='h',
                         color='Max_Drawdown', color_continuous_scale='Reds_r',
                         text_auto='.1f')
        fig_mdd.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False,
                              xaxis_title="Max Drawdown (%)", yaxis_title="",
                              height=max(350, len(selected_tickers) * 35))
        st.plotly_chart(fig_mdd, use_container_width=True)

    with r2:
        st.markdown('<div class="section-header">📊 Rolling Volatility (21-Day Annualized)</div>', unsafe_allow_html=True)
        fig_rv = go.Figure()
        for i, ticker in enumerate(selected_tickers):
            td = filtered_df[filtered_df['Ticker'] == ticker]
            fig_rv.add_trace(go.Scatter(
                x=td['Date'], y=td['Rolling_Vol_21'], mode='lines',
                name=ticker, line=dict(width=1.5, color=ACCENT_COLORS[i % len(ACCENT_COLORS)])
            ))
        fig_rv.update_layout(**PLOTLY_LAYOUT, yaxis_title="Annualized Vol (%)",
                             height=max(350, len(selected_tickers) * 35))
        st.plotly_chart(fig_rv, use_container_width=True)

    # ── Rolling Sharpe Ratio ──
    st.markdown('<div class="section-header">📐 Rolling Sharpe Ratio (63-Day / 3-Month Window)</div>', unsafe_allow_html=True)
    st.caption("Sharpe Ratio = (Return / Volatility). Higher = better risk-adjusted return. >1 is good, >2 is excellent.")

    fig_sharpe = go.Figure()
    for i, ticker in enumerate(selected_tickers):
        td = filtered_df[filtered_df['Ticker'] == ticker]
        fig_sharpe.add_trace(go.Scatter(
            x=td['Date'], y=td['Rolling_Sharpe_63'], mode='lines',
            name=ticker, line=dict(width=1.5, color=ACCENT_COLORS[i % len(ACCENT_COLORS)])
        ))
    fig_sharpe.add_hline(y=0, line_dash="dash", line_color="#94a3b8", opacity=0.5)
    fig_sharpe.add_hline(y=1, line_dash="dot", line_color="#10b981", opacity=0.3,
                         annotation_text="Sharpe = 1", annotation_position="bottom right")
    fig_sharpe.update_layout(**PLOTLY_LAYOUT, yaxis_title="Sharpe Ratio", height=400)
    st.plotly_chart(fig_sharpe, use_container_width=True)

    # ── VaR & Return Distribution ──
    st.markdown('<div class="section-header">🎲 Value at Risk (VaR) & Return Distribution</div>', unsafe_allow_html=True)

    var_data = []
    for ticker in selected_tickers:
        rets = filtered_raw[filtered_raw['Ticker'] == ticker]['Daily_Return_Pct'].dropna()
        var_95 = np.percentile(rets, 5)
        var_99 = np.percentile(rets, 1)
        cvar_95 = rets[rets <= var_95].mean()
        var_data.append({
            'Ticker': ticker,
            'VaR 95%': round(var_95, 3),
            'VaR 99%': round(var_99, 3),
            'CVaR 95%': round(cvar_95, 3),
            'Mean Return': round(rets.mean(), 4),
            'Skewness': round(rets.skew(), 3),
            'Kurtosis': round(rets.kurtosis(), 3)
        })
    var_table = pd.DataFrame(var_data)
    st.dataframe(var_table.style.format({
        'VaR 95%': '{:.3f}%', 'VaR 99%': '{:.3f}%', 'CVaR 95%': '{:.3f}%',
        'Mean Return': '{:.4f}%'
    }), use_container_width=True, hide_index=True)

    # Return distribution histogram for selected stocks
    st.markdown('<div class="section-header">📊 Daily Return Distribution</div>', unsafe_allow_html=True)
    dist_ticker = st.selectbox("Select stock for distribution", selected_tickers, key="dist_ticker")
    dist_rets = filtered_raw[filtered_raw['Ticker'] == dist_ticker]['Daily_Return_Pct'].dropna()

    fig_dist = go.Figure()
    fig_dist.add_trace(go.Histogram(
        x=dist_rets, nbinsx=80, marker_color='#6366f1', opacity=0.7, name='Returns'
    ))
    var95_val = np.percentile(dist_rets, 5)
    fig_dist.add_vline(x=var95_val, line_dash="dash", line_color="#ef4444",
                       annotation_text=f"VaR 95%: {var95_val:.2f}%")
    fig_dist.add_vline(x=dist_rets.mean(), line_dash="dash", line_color="#10b981",
                       annotation_text=f"Mean: {dist_rets.mean():.3f}%")
    fig_dist.update_layout(**PLOTLY_LAYOUT, xaxis_title="Daily Return (%)",
                           yaxis_title="Frequency", height=350,
                           title=dict(text=f"{dist_ticker} — Daily Return Distribution", y=0.97))
    st.plotly_chart(fig_dist, use_container_width=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 4: SECTOR INTELLIGENCE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_sector:
    st.markdown('<div class="section-header">🏢 Sector Intelligence Dashboard</div>', unsafe_allow_html=True)
    st.caption("Sector-level performance, rotation analysis, and comparative metrics across market segments.")

    # ── Sector Avg Daily Return ──
    s1, s2 = st.columns(2)
    with s1:
        st.markdown('<div class="section-header">📊 Average Daily Return by Sector</div>', unsafe_allow_html=True)
        sec_ret = filtered_raw.groupby('Sector')['Daily_Return_Pct'].mean().sort_values(ascending=True).reset_index()
        sec_ret.columns = ['Sector', 'AvgReturn']
        fig_sr = px.bar(sec_ret, x='AvgReturn', y='Sector', orientation='h',
                        color='AvgReturn', color_continuous_scale='Greens',
                        text_auto='.4f')
        fig_sr.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False,
                             xaxis_title="Avg Daily Return (%)", yaxis_title="", height=400)
        st.plotly_chart(fig_sr, use_container_width=True)

    with s2:
        st.markdown('<div class="section-header">⚡ Sector Volatility Comparison</div>', unsafe_allow_html=True)
        sec_vol = (filtered_raw.groupby('Sector')['Daily_Return_Pct'].std() * np.sqrt(252)).sort_values(ascending=True).reset_index()
        sec_vol.columns = ['Sector', 'AnnVol']
        fig_sv = px.bar(sec_vol, x='AnnVol', y='Sector', orientation='h',
                        color='AnnVol', color_continuous_scale='YlOrRd',
                        text_auto='.1f')
        fig_sv.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False,
                             xaxis_title="Annualized Volatility (%)", yaxis_title="", height=400)
        st.plotly_chart(fig_sv, use_container_width=True)

    # ── Monthly Sector Performance Heatmap ──
    st.markdown('<div class="section-header">🗓️ Monthly Sector Performance Heatmap</div>', unsafe_allow_html=True)
    st.caption("Average monthly return by sector over time — reveals sector rotation patterns and seasonal trends.")

    monthly = filtered_raw.copy()
    monthly['YearMonth'] = monthly['Date'].dt.to_period('M').astype(str)
    monthly_sector = monthly.groupby(['YearMonth', 'Sector'])['Daily_Return_Pct'].mean().reset_index()
    monthly_pivot = monthly_sector.pivot(index='Sector', columns='YearMonth', values='Daily_Return_Pct')

    # Show last 24 months for readability
    if monthly_pivot.shape[1] > 24:
        monthly_pivot = monthly_pivot.iloc[:, -24:]

    fig_mh = px.imshow(monthly_pivot, color_continuous_scale='RdYlGn',
                       aspect='auto', text_auto='.2f' if monthly_pivot.shape[1] <= 18 else False)
    fig_mh.update_layout(**PLOTLY_LAYOUT, height=350,
                         title=dict(text="Sector × Month Return Heatmap (Last 24 Months)", y=0.97),
                         xaxis_title="Month", yaxis_title="")
    st.plotly_chart(fig_mh, use_container_width=True)

    # ── Sector Cumulative Performance ──
    st.markdown('<div class="section-header">📈 Sector Cumulative Performance</div>', unsafe_allow_html=True)
    sector_cum = filtered_raw.groupby(['Date', 'Sector'])['Daily_Return_Pct'].mean().reset_index()
    sector_cum = sector_cum.sort_values(['Sector', 'Date'])
    sector_cum['Cum_Return'] = sector_cum.groupby('Sector')['Daily_Return_Pct'].transform(
        lambda x: (1 + x / 100).cumprod() - 1) * 100

    fig_sc = px.line(sector_cum, x='Date', y='Cum_Return', color='Sector',
                     color_discrete_sequence=ACCENT_COLORS)
    fig_sc.update_layout(**PLOTLY_LAYOUT, yaxis_title="Cumulative Return (%)", height=400)
    st.plotly_chart(fig_sc, use_container_width=True)

    # ── Sector Composition Treemap ──
    st.markdown('<div class="section-header">🌳 Portfolio Sector Composition</div>', unsafe_allow_html=True)
    avg_vol_sector = filtered_raw.groupby(['Sector', 'Ticker'])['Volume'].mean().reset_index()
    fig_tree = px.treemap(avg_vol_sector, path=['Sector', 'Ticker'], values='Volume',
                          color='Volume', color_continuous_scale='Blues')
    fig_tree.update_layout(**PLOTLY_LAYOUT, height=450, coloraxis_showscale=False)
    st.plotly_chart(fig_tree, use_container_width=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 5: DATA EXPLORER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_data:
    st.markdown('<div class="section-header">🗃️ Data Explorer</div>', unsafe_allow_html=True)
    st.caption("Browse, filter, and download the underlying clean dataset. All computed technical indicators are included.")

    # Date range filter
    d1, d2 = st.columns(2)
    with d1:
        start_date = st.date_input("Start Date", value=filtered_df['Date'].min().date(),
                                   min_value=filtered_df['Date'].min().date(),
                                   max_value=filtered_df['Date'].max().date(),
                                   key="data_start")
    with d2:
        end_date = st.date_input("End Date", value=filtered_df['Date'].max().date(),
                                 min_value=filtered_df['Date'].min().date(),
                                 max_value=filtered_df['Date'].max().date(),
                                 key="data_end")

    mask = (filtered_df['Date'].dt.date >= start_date) & (filtered_df['Date'].dt.date <= end_date)
    display_df = filtered_df[mask].sort_values(['Date', 'Ticker'], ascending=[False, True])

    st.markdown(f"**Showing {len(display_df):,} rows** for {len(selected_tickers)} stocks "
                f"from {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}")

    # Column selector
    all_cols = display_df.columns.tolist()
    default_cols = ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume', 'Sector',
                    'Daily_Return_Pct', 'MA20', 'MA50', 'RSI', 'MACD']
    show_cols = st.multiselect("Select columns to display", all_cols,
                               default=[c for c in default_cols if c in all_cols],
                               key="data_cols")

    if show_cols:
        st.dataframe(display_df[show_cols], use_container_width=True, height=500, hide_index=True)

        # Download button
        csv_data = display_df[show_cols].to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv_data,
            file_name=f"stock_analytics_{start_date}_{end_date}.csv",
            mime="text/csv"
        )
    else:
        st.info("Select at least one column to display data.")

    # ── SQL Insights from Pipeline ──
    if insights:
        st.markdown("---")
        st.markdown('<div class="section-header">🧠 Pre-Computed SQL Analytics Insights</div>', unsafe_allow_html=True)
        st.caption("These insights were generated by the SQL analytical pipeline (04_run_queries.py).")

        insight_keys = list(insights.keys())
        selected_insight = st.selectbox("Select Insight Query", insight_keys, key="insight_select")

        if selected_insight:
            data = insights[selected_insight]
            if isinstance(data, list) and len(data) > 0:
                st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
            else:
                st.json(data)


# ════════════════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(
    '<div style="text-align:center;opacity:0.5;font-size:0.78rem;font-family:Inter,sans-serif;padding:0.5rem 0;">'
    '📈 NSE Stock Market Analytics Platform &nbsp;·&nbsp; '
    'Built with Streamlit + Plotly &nbsp;·&nbsp; '
    'Data via yfinance &nbsp;·&nbsp; '
    f'{len(df):,} records across {len(all_tickers)} equities'
    '</div>',
    unsafe_allow_html=True
)
