"""
Portfolio Rebalancer — Regime-Based Macro Strategy
Streamlit application for automated portfolio rebalancing using FRED + yfinance data.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
from fredapi import Fred
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Regime Portfolio Rebalancer",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS — Dark terminal / Bloomberg aesthetic
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');

:root {
    --bg-primary:    #0a0c10;
    --bg-secondary:  #111318;
    --bg-card:       #161a22;
    --border:        #1f2430;
    --border-bright: #2d3448;
    --text-primary:  #e2e8f0;
    --text-muted:    #64748b;
    --text-dim:      #334155;
    --accent-green:  #00d97e;
    --accent-blue:   #38bdf8;
    --accent-amber:  #fbbf24;
    --accent-red:    #f87171;
    --accent-purple: #a78bfa;
    --font-mono:     'IBM Plex Mono', monospace;
    --font-sans:     'IBM Plex Sans', sans-serif;
}

html, body, [class*="css"] {
    font-family: var(--font-sans) !important;
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

/* Hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

/* Metric cards */
.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1rem 1.2rem;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent-blue), var(--accent-green));
}
.metric-label {
    font-family: var(--font-mono);
    font-size: 0.65rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.4rem;
}
.metric-value {
    font-family: var(--font-mono);
    font-size: 1.6rem;
    font-weight: 500;
    line-height: 1;
}
.metric-sub {
    font-family: var(--font-mono);
    font-size: 0.7rem;
    color: var(--text-muted);
    margin-top: 0.35rem;
}

/* Regime badge */
.regime-badge {
    display: inline-block;
    font-family: var(--font-mono);
    font-size: 0.75rem;
    letter-spacing: 0.08em;
    padding: 0.3rem 0.8rem;
    border-radius: 3px;
    font-weight: 600;
    text-transform: uppercase;
}

/* Section headers */
.section-header {
    font-family: var(--font-mono);
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--text-muted);
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
}

/* Tables */
.dataframe { font-family: var(--font-mono) !important; font-size: 0.8rem !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: var(--bg-secondary) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] .block-container { padding-top: 1rem; }

/* Inputs */
.stNumberInput input, .stTextInput input, .stSelectbox select {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-bright) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-mono) !important;
    border-radius: 4px !important;
}

/* Buttons */
.stButton > button {
    background: transparent !important;
    border: 1px solid var(--accent-green) !important;
    color: var(--accent-green) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    border-radius: 3px !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    background: var(--accent-green) !important;
    color: var(--bg-primary) !important;
}

/* Warning / info boxes */
.drift-warn {
    background: rgba(251,191,36,0.08);
    border: 1px solid rgba(251,191,36,0.35);
    border-left: 3px solid var(--accent-amber);
    border-radius: 4px;
    padding: 0.8rem 1rem;
    margin: 0.5rem 0;
    font-family: var(--font-mono);
    font-size: 0.78rem;
    color: var(--accent-amber);
}
.drift-ok {
    background: rgba(0,217,126,0.06);
    border: 1px solid rgba(0,217,126,0.2);
    border-left: 3px solid var(--accent-green);
    border-radius: 4px;
    padding: 0.8rem 1rem;
    margin: 0.5rem 0;
    font-family: var(--font-mono);
    font-size: 0.78rem;
    color: var(--accent-green);
}
.error-box {
    background: rgba(248,113,113,0.08);
    border: 1px solid rgba(248,113,113,0.3);
    border-left: 3px solid var(--accent-red);
    border-radius: 4px;
    padding: 0.8rem 1rem;
    font-family: var(--font-mono);
    font-size: 0.78rem;
    color: var(--accent-red);
}

/* Plotly chart containers */
.js-plotly-plot { border-radius: 6px; }

/* Page title */
.page-title {
    font-family: var(--font-mono);
    font-size: 1.05rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--text-primary);
}
.page-subtitle {
    font-family: var(--font-mono);
    font-size: 0.68rem;
    color: var(--text-muted);
    letter-spacing: 0.08em;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
FRED_SERIES = {
    "gdp_growth":  "A191RL1Q225SBEA",
    "cpi":         "CPIAUCSL",
    "fed_funds":   "FEDFUNDS",
    "usd_index":   "DTWEXBGS",
}

SECTOR_ETFS = ["XLE", "XLK", "XLY", "XLC", "XLF", "XLI", "XLB", "XLP", "XLU", "XLV", "XLRE"]
INVERSE_ETFS = ["SH", "REK", "PSQ", "SARK"]
EXTRA_ASSETS = ["GLD", "VEGI", "VOO"]

BUCKET_TARGETS = {"Core": 0.50, "Sector Tilts": 0.30, "Hedges": 0.20}
DRIFT_THRESHOLD = 0.05  # 5%

REGIME_COLORS = {
    "Stagflation":   "#f87171",
    "Goldilocks":    "#00d97e",
    "Late Cycle":    "#fbbf24",
    "Neutral":       "#38bdf8",
    "Transitional":  "#a78bfa",
}

REGIME_EMOJI = {
    "Stagflation":   "🔴",
    "Goldilocks":    "🟢",
    "Late Cycle":    "🟡",
    "Neutral":       "🔵",
    "Transitional":  "🟣",
}

# ─────────────────────────────────────────────
# MODULE 1 — MACRO DATA
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_macro_data(fred_api_key: str) -> dict:
    """
    Pull latest macroeconomic indicators from FRED.
    Returns dict with scalar values and recent history for each series.
    """
    results = {}
    errors = []

    try:
        fred = Fred(api_key=fred_api_key)

        # GDP Growth (quarterly, annualized %)
        gdp = fred.get_series(FRED_SERIES["gdp_growth"], observation_start="2018-01-01")
        results["gdp_growth"]        = float(gdp.dropna().iloc[-1])
        results["gdp_growth_prev"]   = float(gdp.dropna().iloc[-2])
        results["gdp_history"]       = gdp.dropna()

        # CPI — compute YoY %
        cpi = fred.get_series(FRED_SERIES["cpi"], observation_start="2018-01-01")
        cpi_clean = cpi.dropna()
        cpi_yoy   = cpi_clean.pct_change(12) * 100
        results["inflation"]         = float(cpi_yoy.iloc[-1])
        results["inflation_prev"]    = float(cpi_yoy.iloc[-2])
        results["inflation_history"] = cpi_yoy.dropna()

        # Fed Funds Rate
        ff = fred.get_series(FRED_SERIES["fed_funds"], observation_start="2018-01-01")
        ff_clean = ff.dropna()
        results["fed_funds"]         = float(ff_clean.iloc[-1])
        results["fed_funds_prev"]    = float(ff_clean.iloc[-2])
        results["fed_funds_history"] = ff_clean

        # USD Index
        usd = fred.get_series(FRED_SERIES["usd_index"], observation_start="2018-01-01")
        usd_clean = usd.dropna()
        results["usd_index"]         = float(usd_clean.iloc[-1])
        results["usd_index_history"] = usd_clean

        results["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        results["error"] = None

    except Exception as e:
        results["error"] = str(e)
        # Fallback demo values so the app remains usable
        results["gdp_growth"]      = 1.4
        results["gdp_growth_prev"] = 2.1
        results["inflation"]       = 3.5
        results["inflation_prev"]  = 3.8
        results["fed_funds"]       = 5.33
        results["fed_funds_prev"]  = 5.33
        results["usd_index"]       = 104.2
        results["last_updated"]    = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " (DEMO)"

    return results


# ─────────────────────────────────────────────
# MODULE 2 — REGIME DETERMINATION
# ─────────────────────────────────────────────
def determine_regime(macro: dict) -> dict:
    """
    Classify the current macro regime based on GDP, inflation, and rate trend.
    Returns regime name, description, sector preferences, and hedge preferences.
    """
    gdp       = macro.get("gdp_growth",  2.0)
    inflation = macro.get("inflation",   2.5)
    fed_funds = macro.get("fed_funds",   3.0)
    fed_prev  = macro.get("fed_funds_prev", 3.0)

    rates_rising = fed_funds > fed_prev
    gdp_slowing  = gdp < macro.get("gdp_growth_prev", gdp)

    # ── Primary regime classification ──────────────────────────────────────
    if inflation > 3.0 and gdp < 2.0:
        regime = "Stagflation"
        description = "High inflation + weak growth. Real assets and defensives outperform."
        sector_tilts = ["XLE", "VEGI", "XLV", "XLP", "XLB"]
        hedges       = ["REK", "SH", "GLD"]
        weights_hint = {"XLE": 0.10, "VEGI": 0.06, "XLV": 0.07, "XLP": 0.05, "XLB": 0.02,
                        "REK": 0.08, "SH":  0.07, "GLD": 0.05}

    elif inflation < 2.0 and gdp > 3.0:
        regime = "Goldilocks"
        description = "Low inflation + strong growth. Growth and tech sectors lead."
        sector_tilts = ["XLK", "XLY", "XLC", "XLF", "XLI"]
        hedges       = ["GLD", "PSQ", "SH"]
        weights_hint = {"XLK": 0.10, "XLY": 0.07, "XLC": 0.06, "XLF": 0.04, "XLI": 0.03,
                        "GLD": 0.08, "PSQ": 0.07, "SH":  0.05}

    elif rates_rising and gdp_slowing:
        regime = "Late Cycle"
        description = "Rising rates + decelerating growth. Defensives and hedges critical."
        sector_tilts = ["XLP", "XLU", "XLV", "XLE", "XLRE"]
        hedges       = ["SARK", "REK", "GLD", "SH"]
        weights_hint = {"XLP": 0.09, "XLU": 0.08, "XLV": 0.06, "XLE": 0.04, "XLRE": 0.03,
                        "SARK": 0.07, "REK": 0.07, "GLD": 0.04, "SH": 0.02}

    elif inflation >= 2.0 and gdp >= 2.0 and not rates_rising:
        regime = "Neutral"
        description = "Balanced conditions. Broad market exposure with modest hedges."
        sector_tilts = ["XLK", "XLF", "XLI", "XLV", "XLC"]
        hedges       = ["GLD", "SH", "PSQ"]
        weights_hint = {"XLK": 0.08, "XLF": 0.07, "XLI": 0.06, "XLV": 0.05, "XLC": 0.04,
                        "GLD": 0.10, "SH": 0.06, "PSQ": 0.04}

    else:
        regime = "Transitional"
        description = "Mixed signals. Diversified approach with defensive tilt."
        sector_tilts = ["XLV", "XLP", "XLE", "XLK", "XLI"]
        hedges       = ["GLD", "SH", "REK"]
        weights_hint = {"XLV": 0.08, "XLP": 0.07, "XLE": 0.06, "XLK": 0.05, "XLI": 0.04,
                        "GLD": 0.10, "SH": 0.06, "REK": 0.04}

    return {
        "name":         regime,
        "description":  description,
        "sector_tilts": sector_tilts,
        "hedges":       hedges,
        "weights_hint": weights_hint,
        "color":        REGIME_COLORS[regime],
    }


# ─────────────────────────────────────────────
# MODULE 3 — PRICE DATA
# ─────────────────────────────────────────────
@st.cache_data(ttl=900)
def get_price_data(tickers: list) -> pd.DataFrame:
    """
    Fetch current price and 3-month return for a list of tickers via yfinance.
    """
    rows = []
    end   = datetime.today()
    start = end - timedelta(days=95)

    for ticker in tickers:
        try:
            hist = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
            if hist.empty:
                rows.append({"ticker": ticker, "price": np.nan, "return_3m": np.nan})
                continue
            price   = float(hist["Close"].iloc[-1])
            ret_3m  = float((hist["Close"].iloc[-1] / hist["Close"].iloc[0] - 1) * 100)
            rows.append({"ticker": ticker, "price": round(price, 2), "return_3m": round(ret_3m, 2)})
        except Exception:
            rows.append({"ticker": ticker, "price": np.nan, "return_3m": np.nan})

    return pd.DataFrame(rows).set_index("ticker")


# ─────────────────────────────────────────────
# MODULE 4 — ALLOCATION CALCULATION
# ─────────────────────────────────────────────
def calculate_allocations(
    regime: dict,
    price_df: pd.DataFrame,
    total_capital: float
) -> pd.DataFrame:
    """
    Build the target 50/30/20 portfolio.
    Returns a DataFrame with ticker, bucket, target_weight, dollar_alloc, shares, price, return_3m.
    """
    rows = []

    # ── CORE (50%) — VOO ──────────────────────────────────────────────────
    voo_price = price_df.loc["VOO", "price"] if "VOO" in price_df.index else 500.0
    voo_alloc  = total_capital * BUCKET_TARGETS["Core"]
    voo_shares = voo_alloc / voo_price if voo_price > 0 else 0
    rows.append({
        "Ticker":        "VOO",
        "Bucket":        "Core",
        "Target Weight": BUCKET_TARGETS["Core"],
        "$ Allocation":  round(voo_alloc, 2),
        "Price":         round(voo_price, 2),
        "Shares":        round(voo_shares, 4),
        "3M Return (%)": price_df.loc["VOO", "return_3m"] if "VOO" in price_df.index else np.nan,
    })

    # ── SECTOR TILTS (30%) ────────────────────────────────────────────────
    sector_bucket  = total_capital * BUCKET_TARGETS["Sector Tilts"]
    tilts          = regime["sector_tilts"]
    hint           = regime["weights_hint"]

    # Extract hint weights for tilts and normalise to sum to 0.30
    tilt_raw = {t: hint.get(t, 0.05) for t in tilts}
    tilt_sum = sum(tilt_raw.values())
    for t in tilts:
        w      = tilt_raw[t] / tilt_sum * BUCKET_TARGETS["Sector Tilts"]
        alloc  = total_capital * w
        price  = price_df.loc[t, "price"] if t in price_df.index else np.nan
        shares = alloc / price if (price and not np.isnan(price) and price > 0) else np.nan
        rows.append({
            "Ticker":        t,
            "Bucket":        "Sector Tilts",
            "Target Weight": round(w, 4),
            "$ Allocation":  round(alloc, 2),
            "Price":         round(price, 2) if not np.isnan(price) else np.nan,
            "Shares":        round(shares, 4) if (shares and not np.isnan(shares)) else np.nan,
            "3M Return (%)": price_df.loc[t, "return_3m"] if t in price_df.index else np.nan,
        })

    # ── HEDGES (20%) ──────────────────────────────────────────────────────
    hedges     = regime["hedges"]
    hedge_raw  = {h: hint.get(h, 0.05) for h in hedges}
    hedge_sum  = sum(hedge_raw.values())
    for h in hedges:
        w      = hedge_raw[h] / hedge_sum * BUCKET_TARGETS["Hedges"]
        alloc  = total_capital * w
        price  = price_df.loc[h, "price"] if h in price_df.index else np.nan
        shares = alloc / price if (price and not np.isnan(price) and price > 0) else np.nan
        rows.append({
            "Ticker":        h,
            "Bucket":        "Hedges",
            "Target Weight": round(w, 4),
            "$ Allocation":  round(alloc, 2),
            "Price":         round(price, 2) if not np.isnan(price) else np.nan,
            "Shares":        round(shares, 4) if (shares and not np.isnan(shares)) else np.nan,
            "3M Return (%)": price_df.loc[h, "return_3m"] if h in price_df.index else np.nan,
        })

    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# MODULE 5 — DRIFT ANALYSIS
# ─────────────────────────────────────────────
def calculate_drift(alloc_df: pd.DataFrame, price_df: pd.DataFrame, total_capital: float) -> dict:
    """
    Compare current market value of each bucket to its target weight.
    Returns drift dict per bucket.
    """
    results = {}
    for bucket, target_pct in BUCKET_TARGETS.items():
        sub = alloc_df[alloc_df["Bucket"] == bucket]
        current_val = 0.0
        for _, row in sub.iterrows():
            t     = row["Ticker"]
            px    = price_df.loc[t, "price"] if t in price_df.index else row["Price"]
            sh    = row["Shares"]
            if not np.isnan(px) and not np.isnan(sh):
                current_val += px * sh
        current_pct = current_val / total_capital if total_capital > 0 else 0
        drift       = current_pct - target_pct
        results[bucket] = {
            "target_pct":  target_pct,
            "current_pct": round(current_pct, 4),
            "drift":       round(drift, 4),
            "drifted":     abs(drift) > DRIFT_THRESHOLD,
        }
    return results


# ─────────────────────────────────────────────
# CHART HELPERS
# ─────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#111318",
    font=dict(family="IBM Plex Mono", color="#94a3b8", size=11),
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(gridcolor="#1f2430", linecolor="#1f2430", zerolinecolor="#1f2430"),
    yaxis=dict(gridcolor="#1f2430", linecolor="#1f2430", zerolinecolor="#1f2430"),
)


def make_macro_heatmap(macro: dict):
    """GDP vs Inflation scatter with regime zones."""
    # Define regime zones as background rectangles
    fig = go.Figure()

    # Regime zone shading
    zone_data = [
        dict(x0=-5, x1=2, y0=3, y1=12, color="rgba(248,113,113,0.07)", label="STAGFLATION"),
        dict(x0=3, x1=12, y0=0, y1=2, color="rgba(0,217,126,0.07)",  label="GOLDILOCKS"),
        dict(x0=0, x1=12, y0=2, y1=12, color="rgba(251,191,36,0.04)", label="LATE / NEUTRAL"),
    ]
    for z in zone_data:
        fig.add_shape(type="rect", x0=z["x0"], x1=z["x1"], y0=z["y0"], y1=z["y1"],
                      fillcolor=z["color"], line=dict(width=0))
        fig.add_annotation(x=(z["x0"]+z["x1"])/2, y=z["y1"]-0.3,
                           text=z["label"], showarrow=False,
                           font=dict(size=8, color="#334155", family="IBM Plex Mono"),
                           opacity=0.9)

    # Reference lines
    for xv in [0, 2, 3]: fig.add_vline(x=xv, line=dict(color="#1f2430", width=1, dash="dot"))
    for yv in [2, 3]:    fig.add_hline(y=yv, line=dict(color="#1f2430", width=1, dash="dot"))

    # Historical trail (last 8 quarters simulated from current)
    gdp_now  = macro.get("gdp_growth", 2.0)
    inf_now  = macro.get("inflation",  2.5)
    n_trail  = 6
    trail_g  = [gdp_now + np.random.uniform(-1.2, 1.2) for _ in range(n_trail)]
    trail_i  = [inf_now + np.random.uniform(-0.8, 0.8) for _ in range(n_trail)]
    trail_g.append(gdp_now); trail_i.append(inf_now)

    fig.add_trace(go.Scatter(
        x=trail_g[:-1], y=trail_i[:-1], mode="markers+lines",
        marker=dict(size=5, color="#334155"),
        line=dict(color="#1f2430", width=1, dash="dot"),
        name="Trail", showlegend=False,
        hovertemplate="GDP: %{x:.1f}%<br>CPI: %{y:.1f}%<extra></extra>",
    ))

    # Current dot
    fig.add_trace(go.Scatter(
        x=[gdp_now], y=[inf_now], mode="markers+text",
        marker=dict(size=16, color=macro.get("regime_color", "#38bdf8"),
                    line=dict(color="#0a0c10", width=2),
                    symbol="circle"),
        text=["NOW"], textposition="top right",
        textfont=dict(size=9, color="#e2e8f0", family="IBM Plex Mono"),
        name="Current", showlegend=False,
        hovertemplate=f"GDP: {gdp_now:.1f}%<br>CPI: {inf_now:.1f}%<extra></extra>",
    ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="MACRO REGIME MAP — GDP vs INFLATION", font=dict(size=11), x=0.02),
        xaxis=dict(**PLOTLY_LAYOUT["xaxis"], title="Real GDP Growth (%)", range=[-4, 8]),
        yaxis=dict(**PLOTLY_LAYOUT["yaxis"], title="CPI Inflation (%)",   range=[0, 9]),
        height=340,
    )
    return fig


def make_allocation_donut(alloc_df: pd.DataFrame):
    bucket_totals = alloc_df.groupby("Bucket")["$ Allocation"].sum().reset_index()
    colors = {"Core": "#38bdf8", "Sector Tilts": "#00d97e", "Hedges": "#fbbf24"}

    fig = go.Figure(go.Pie(
        labels=bucket_totals["Bucket"],
        values=bucket_totals["$ Allocation"],
        hole=0.62,
        marker=dict(
            colors=[colors.get(b, "#64748b") for b in bucket_totals["Bucket"]],
            line=dict(color="#0a0c10", width=3)
        ),
        textinfo="label+percent",
        textfont=dict(family="IBM Plex Mono", size=10),
        hovertemplate="%{label}<br>$%{value:,.0f} (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="BUCKET ALLOCATION", font=dict(size=11), x=0.02),
        showlegend=False,
        height=280,
        annotations=[dict(text="TARGET<br>50/30/20", x=0.5, y=0.5, font_size=10,
                          font_family="IBM Plex Mono", showarrow=False,
                          font_color="#64748b")],
    )
    return fig


def make_sector_bar(price_df: pd.DataFrame, tilts: list):
    sub = price_df[price_df.index.isin(tilts)].copy().dropna(subset=["return_3m"])
    sub = sub.sort_values("return_3m", ascending=True)

    colors = ["#f87171" if v < 0 else "#00d97e" for v in sub["return_3m"]]
    fig = go.Figure(go.Bar(
        y=sub.index,
        x=sub["return_3m"],
        orientation="h",
        marker_color=colors,
        text=[f"{v:+.1f}%" for v in sub["return_3m"]],
        textposition="outside",
        textfont=dict(family="IBM Plex Mono", size=10),
        hovertemplate="%{y}: %{x:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="3-MONTH SECTOR PERFORMANCE", font=dict(size=11), x=0.02),
        xaxis=dict(**PLOTLY_LAYOUT["xaxis"], title="3M Return (%)", zeroline=True,
                   zerolinecolor="#334155", zerolinewidth=1),
        height=300,
    )
    return fig


def make_drift_gauge(bucket: str, drift_info: dict):
    target  = drift_info["target_pct"] * 100
    current = drift_info["current_pct"] * 100
    drift   = drift_info["drift"] * 100
    color   = "#f87171" if drift_info["drifted"] else "#00d97e"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=current,
        delta=dict(reference=target, valueformat=".1f",
                   increasing=dict(color="#fbbf24"),
                   decreasing=dict(color="#fbbf24")),
        number=dict(suffix="%", font=dict(family="IBM Plex Mono", size=18)),
        gauge=dict(
            axis=dict(range=[0, 70], tickfont=dict(family="IBM Plex Mono", size=8),
                      tickcolor="#334155"),
            bar=dict(color=color, thickness=0.5),
            bgcolor="#111318",
            bordercolor="#1f2430",
            steps=[
                dict(range=[0, target - 5], color="#0a0c10"),
                dict(range=[target - 5, target + 5], color="rgba(0,217,126,0.08)"),
                dict(range=[target + 5, 70], color="#0a0c10"),
            ],
            threshold=dict(line=dict(color="#38bdf8", width=2), thickness=0.75, value=target),
        ),
        title=dict(text=bucket, font=dict(family="IBM Plex Mono", size=10, color="#64748b")),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Mono", color="#e2e8f0"),
        margin=dict(l=15, r=15, t=30, b=5),
        height=175,
    )
    return fig


def make_history_sparkline(series, label: str, color: str):
    recent = series.iloc[-40:]
    fig = go.Figure(go.Scatter(
        x=recent.index, y=recent.values,
        mode="lines",
        line=dict(color=color, width=1.5),
        fill="tozeroy",
        fillcolor=color.replace(")", ",0.07)").replace("rgb", "rgba") if "rgb" in color
                  else f"{color}15",
        hovertemplate="%{x|%Y-%m}<br>%{y:.2f}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#111318",
        font=dict(family="IBM Plex Mono", size=9, color="#64748b"),
        margin=dict(l=5, r=5, t=20, b=5),
        title=dict(text=label, font=dict(size=9), x=0.02),
        xaxis=dict(showgrid=False, showticklabels=False, linecolor="#1f2430"),
        yaxis=dict(showgrid=False, tickfont=dict(size=8), linecolor="#1f2430"),
        height=120,
    )
    return fig


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="page-title">⚖ REBALANCER</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Regime-Based Portfolio Engine</div>', unsafe_allow_html=True)
    st.markdown("---")

    fred_key = st.text_input(
        "FRED API Key",
        type="password",
        placeholder="Enter your FRED API key…",
        help="Get a free key at fred.stlouisfed.org/docs/api/api_key.html",
    )

    total_capital = st.number_input(
        "Total Capital ($)",
        min_value=1_000.0,
        max_value=50_000_000.0,
        value=100_000.0,
        step=5_000.0,
        format="%.2f",
    )

    st.markdown("---")
    st.markdown('<div class="section-header">Regime Overrides</div>', unsafe_allow_html=True)
    override_regime = st.selectbox(
        "Force Regime (optional)",
        ["Auto-Detect", "Stagflation", "Goldilocks", "Late Cycle", "Neutral", "Transitional"],
    )

    st.markdown("---")
    run_btn = st.button("▶  CALCULATE ALLOCATIONS", use_container_width=True)

    st.markdown("---")
    st.markdown(
        '<div style="font-family:IBM Plex Mono;font-size:0.6rem;color:#334155;line-height:1.6;">'
        'Data: FRED + Yahoo Finance<br>Regime logic: heuristic-based<br>'
        'Not financial advice.</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# MAIN LAYOUT
# ─────────────────────────────────────────────
st.markdown(
    '<div style="display:flex;align-items:baseline;gap:1rem;margin-bottom:1.5rem;">'
    '<span class="page-title" style="font-size:1.2rem;">PORTFOLIO REBALANCER</span>'
    '<span class="page-subtitle">Macro Regime Engine · 50/30/20 Strategy</span>'
    '</div>',
    unsafe_allow_html=True,
)

# ── Guard: need FRED key ───────────────────────────────────────────────────
if not fred_key and not run_btn:
    st.markdown(
        '<div class="drift-warn">⚡ Enter your FRED API key in the sidebar, set your capital, '
        'and click <strong>CALCULATE ALLOCATIONS</strong> to begin.<br><br>'
        'A free FRED key is available at '
        '<a href="https://fred.stlouisfed.org/docs/api/api_key.html" target="_blank" '
        'style="color:#fbbf24;">fred.stlouisfed.org</a></div>',
        unsafe_allow_html=True,
    )
    st.stop()

# ── Fetch data ─────────────────────────────────────────────────────────────
if run_btn or fred_key:
    with st.spinner("Pulling macro data from FRED…"):
        macro = get_macro_data(fred_key if fred_key else "demo")

    if macro.get("error"):
        st.markdown(
            f'<div class="error-box">⚠ FRED connection failed — running in DEMO mode with placeholder data.<br>'
            f'<small>{macro["error"]}</small></div>',
            unsafe_allow_html=True,
        )

    # Determine regime
    regime = determine_regime(macro)
    if override_regime != "Auto-Detect":
        # Build a synthetic macro dict that forces the override
        _override_macros = {
            "Stagflation": dict(gdp_growth=0.5, inflation=4.2, fed_funds=5.0, fed_funds_prev=4.5, gdp_growth_prev=1.5),
            "Goldilocks":  dict(gdp_growth=4.0, inflation=1.5, fed_funds=3.0, fed_funds_prev=3.0, gdp_growth_prev=3.5),
            "Late Cycle":  dict(gdp_growth=1.0, inflation=2.8, fed_funds=5.5, fed_funds_prev=5.0, gdp_growth_prev=2.0),
            "Neutral":     dict(gdp_growth=2.5, inflation=2.2, fed_funds=4.0, fed_funds_prev=4.0, gdp_growth_prev=2.4),
            "Transitional":dict(gdp_growth=1.8, inflation=2.6, fed_funds=4.5, fed_funds_prev=4.3, gdp_growth_prev=2.2),
        }
        if override_regime in _override_macros:
            _om = {**macro, **_override_macros[override_regime]}
            regime = determine_regime(_om)
            # Keep display macro as real but adjust for heatmap dot
            macro["gdp_growth"] = _override_macros[override_regime]["gdp_growth"]
            macro["inflation"]  = _override_macros[override_regime]["inflation"]

    macro["regime_color"] = regime["color"]

    # Collect all tickers needed
    all_tickers = list(set(["VOO"] + regime["sector_tilts"] + regime["hedges"] +
                            SECTOR_ETFS + ["GLD", "VEGI"]))
    with st.spinner("Fetching market prices…"):
        price_df = get_price_data(all_tickers)

    # Calculate allocations
    alloc_df = calculate_allocations(regime, price_df, total_capital)

    # Drift analysis
    drift    = calculate_drift(alloc_df, price_df, total_capital)

    # ──────────────────────────────────────────
    # ROW 1 — Macro KPIs
    # ──────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns([1.4, 1, 1, 1, 1.6])

    gdp_delta = macro.get("gdp_growth", 0) - macro.get("gdp_growth_prev", 0)
    inf_delta = macro.get("inflation",  0) - macro.get("inflation_prev",  0)
    ff        = macro.get("fed_funds",  0)
    ff_prev   = macro.get("fed_funds_prev", ff)

    def _delta_html(v):
        arrow = "▲" if v >= 0 else "▼"
        col   = "#f87171" if v >= 0 else "#00d97e"  # inverse: higher inflation/rates = bad
        return f'<span style="color:{col};font-size:0.7rem;">{arrow} {abs(v):.2f}</span>'

    def _delta_html_gdp(v):
        arrow = "▲" if v >= 0 else "▼"
        col   = "#00d97e" if v >= 0 else "#f87171"
        return f'<span style="color:{col};font-size:0.7rem;">{arrow} {abs(v):.2f}</span>'

    with k1:
        rc = regime["color"]
        st.markdown(
            f'<div class="metric-card" style="border-top: 2px solid {rc};">'
            f'<div class="metric-label">Current Regime</div>'
            f'<div style="font-family:IBM Plex Mono;font-size:1.15rem;font-weight:600;color:{rc};">'
            f'{REGIME_EMOJI[regime["name"]]} {regime["name"].upper()}</div>'
            f'<div class="metric-sub">{regime["description"][:55]}…</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with k2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">Real GDP Growth</div>'
            f'<div class="metric-value" style="color:#38bdf8;">{macro["gdp_growth"]:.1f}%</div>'
            f'<div class="metric-sub">QoQ Ann. {_delta_html_gdp(gdp_delta)}</div></div>',
            unsafe_allow_html=True,
        )

    with k3:
        inf_color = "#f87171" if macro["inflation"] > 3 else ("#fbbf24" if macro["inflation"] > 2 else "#00d97e")
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">CPI Inflation (YoY)</div>'
            f'<div class="metric-value" style="color:{inf_color};">{macro["inflation"]:.1f}%</div>'
            f'<div class="metric-sub">MoM change {_delta_html(inf_delta)}</div></div>',
            unsafe_allow_html=True,
        )

    with k4:
        ff_color = "#fbbf24" if ff > 4.5 else "#e2e8f0"
        ff_trend = "▲ RISING" if ff > ff_prev else ("▼ CUTTING" if ff < ff_prev else "── HOLD")
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">Fed Funds Rate</div>'
            f'<div class="metric-value" style="color:{ff_color};">{ff:.2f}%</div>'
            f'<div class="metric-sub" style="color:{ff_color};font-size:0.65rem;">{ff_trend}</div></div>',
            unsafe_allow_html=True,
        )

    with k5:
        usd = macro.get("usd_index", 104)
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">USD Index (DXY)</div>'
            f'<div class="metric-value">{usd:.1f}</div>'
            f'<div class="metric-sub">Last updated: {macro["last_updated"]}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ──────────────────────────────────────────
    # ROW 2 — Heatmap + Sparklines
    # ──────────────────────────────────────────
    col_heat, col_sparks = st.columns([1.7, 1])

    with col_heat:
        st.plotly_chart(make_macro_heatmap(macro), use_container_width=True, config={"displayModeBar": False})

    with col_sparks:
        st.markdown('<div class="section-header">Indicator Trends</div>', unsafe_allow_html=True)
        if "gdp_history" in macro:
            st.plotly_chart(make_history_sparkline(macro["gdp_history"], "GDP Growth (%)", "#38bdf8"),
                            use_container_width=True, config={"displayModeBar": False})
        if "inflation_history" in macro:
            st.plotly_chart(make_history_sparkline(macro["inflation_history"], "CPI YoY (%)", "#f87171"),
                            use_container_width=True, config={"displayModeBar": False})

    # ──────────────────────────────────────────
    # ROW 3 — Allocation Table + Donut
    # ──────────────────────────────────────────
    st.markdown('<div class="section-header">Target Allocation — ${:,.0f} Capital</div>'.format(total_capital),
                unsafe_allow_html=True)

    col_tbl, col_donut = st.columns([2, 0.9])

    with col_tbl:
        display_df = alloc_df.copy()
        display_df["Target Weight"] = (display_df["Target Weight"] * 100).map("{:.1f}%".format)
        display_df["$ Allocation"]  = display_df["$ Allocation"].map("${:,.2f}".format)
        display_df["Price"]         = display_df["Price"].map(lambda x: f"${x:,.2f}" if not (isinstance(x, float) and np.isnan(x)) else "N/A")
        display_df["Shares"]        = display_df["Shares"].map(lambda x: f"{x:.4f}" if not (isinstance(x, float) and np.isnan(x)) else "N/A")
        display_df["3M Return (%)"] = display_df["3M Return (%)"].map(
            lambda x: f"{x:+.2f}%" if not (isinstance(x, float) and np.isnan(x)) else "N/A")

        bucket_colors = {"Core": "#38bdf815", "Sector Tilts": "#00d97e12", "Hedges": "#fbbf2412"}

        def color_row(row):
            bg = bucket_colors.get(row["Bucket"], "")
            ret_val_raw = alloc_df.loc[alloc_df["Ticker"] == row["Ticker"], "3M Return (%)"]
            if not ret_val_raw.empty and not np.isnan(ret_val_raw.iloc[0]):
                ret_num = ret_val_raw.iloc[0]
                ret_col = "#00d97e" if ret_num > 0 else "#f87171"
            else:
                ret_col = "#e2e8f0"
            styles = [f"background-color:{bg}"] * len(row)
            col_idx = list(display_df.columns).index("3M Return (%)")
            styles[col_idx] = f"color:{ret_col};font-weight:600"
            return styles

        st.dataframe(
            display_df.style.apply(color_row, axis=1),
            use_container_width=True,
            hide_index=True,
            height=420,
        )

    with col_donut:
        st.plotly_chart(make_allocation_donut(alloc_df), use_container_width=True,
                        config={"displayModeBar": False})

        # Summary stats
        total_allocated = alloc_df["$ Allocation"].sum()
        n_positions = len(alloc_df)
        st.markdown(
            f'<div style="font-family:IBM Plex Mono;font-size:0.72rem;color:#64748b;margin-top:0.5rem;'
            f'padding:0.7rem;background:#161a22;border:1px solid #1f2430;border-radius:4px;">'
            f'<div style="color:#e2e8f0;margin-bottom:0.4rem;">Portfolio Summary</div>'
            f'Positions: <span style="color:#38bdf8;">{n_positions}</span><br>'
            f'Total Allocated: <span style="color:#00d97e;">${total_allocated:,.2f}</span><br>'
            f'Unallocated: <span style="color:#fbbf24;">${total_capital - total_allocated:,.2f}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ──────────────────────────────────────────
    # ROW 4 — Drift Analysis + Sector Performance
    # ──────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Drift Monitor — 5% Threshold Alert</div>',
                unsafe_allow_html=True)

    col_g1, col_g2, col_g3, col_bar = st.columns([1, 1, 1, 1.5])
    gauge_cols = [col_g1, col_g2, col_g3]

    drift_any = False
    for i, (bucket, d_info) in enumerate(drift.items()):
        with gauge_cols[i]:
            st.plotly_chart(make_drift_gauge(bucket, d_info),
                            use_container_width=True, config={"displayModeBar": False})
            if d_info["drifted"]:
                drift_any = True
                direction = "OVER" if d_info["drift"] > 0 else "UNDER"
                st.markdown(
                    f'<div class="drift-warn">⚠ {direction} by {abs(d_info["drift"]*100):.1f}%</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="drift-ok">✓ Within tolerance</div>',
                    unsafe_allow_html=True,
                )

    with col_bar:
        sector_chart_tickers = regime["sector_tilts"] + regime["hedges"]
        st.plotly_chart(make_sector_bar(price_df, sector_chart_tickers),
                        use_container_width=True, config={"displayModeBar": False})

    # Global drift banner
    if drift_any:
        st.markdown(
            '<div class="drift-warn" style="margin-top:1rem;font-size:0.8rem;">'
            '⚠ <strong>REBALANCE RECOMMENDED</strong> — One or more buckets have drifted beyond the 5% threshold. '
            'Review the allocation table above and execute trades to restore target weights.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="drift-ok" style="margin-top:1rem;font-size:0.8rem;">'
            '✓ <strong>PORTFOLIO IN BALANCE</strong> — All buckets are within the 5% drift threshold.</div>',
            unsafe_allow_html=True,
        )

    # ──────────────────────────────────────────
    # ROW 5 — Regime detail card
    # ──────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    rc = regime["color"]
    tilts_str  = " · ".join(regime["sector_tilts"])
    hedges_str = " · ".join(regime["hedges"])
    st.markdown(
        f'<div class="metric-card" style="border-top:2px solid {rc};">'
        f'<div style="display:flex;gap:2rem;align-items:flex-start;flex-wrap:wrap;">'
        f'<div><div class="metric-label">Active Regime</div>'
        f'<div style="font-family:IBM Plex Mono;font-size:1rem;color:{rc};font-weight:600;">'
        f'{REGIME_EMOJI[regime["name"]]} {regime["name"].upper()}</div>'
        f'<div style="font-size:0.78rem;color:#94a3b8;margin-top:0.4rem;max-width:340px;">'
        f'{regime["description"]}</div></div>'
        f'<div><div class="metric-label">Sector Tilts</div>'
        f'<div style="font-family:IBM Plex Mono;font-size:0.8rem;color:#00d97e;">{tilts_str}</div></div>'
        f'<div><div class="metric-label">Hedges / Defensives</div>'
        f'<div style="font-family:IBM Plex Mono;font-size:0.8rem;color:#fbbf24;">{hedges_str}</div></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )
