# Portfolio Rebalancer — Regime-Based Macro Strategy

Automated portfolio rebalancing tool using FRED macroeconomic data and Yahoo Finance prices.
Implements a 50/30/20 allocation strategy driven by macro regime classification.

## Setup

```bash
# 1. Clone / copy files into a directory
# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
streamlit run app.py
```

## FRED API Key
Get a free key at: https://fred.stlouisfed.org/docs/api/api_key.html
Enter it in the sidebar when the app loads.

## Regime Logic

| Regime       | GDP    | Inflation | Favored Sectors        | Hedges        |
|--------------|--------|-----------|------------------------|---------------|
| Stagflation  | < 2%   | > 3%      | XLE, VEGI, XLV, XLP   | REK, SH, GLD  |
| Goldilocks   | > 3%   | < 2%      | XLK, XLY, XLC, XLF    | GLD, PSQ, SH  |
| Late Cycle   | Slowing| Rising    | XLP, XLU, XLV, XLE    | SARK, REK, GLD|
| Neutral      | ≥ 2%   | ≥ 2%      | XLK, XLF, XLI, XLV    | GLD, SH, PSQ  |
| Transitional | Mixed  | Mixed     | XLV, XLP, XLE, XLK    | GLD, SH, REK  |

## Portfolio Structure

- **Core (50%)**: VOO — broad market anchor
- **Sector Tilts (30%)**: 5–6 sector ETFs favored by current regime
- **Hedges (20%)**: 3–4 inverse ETFs (-1x only) or GLD

## Modules

- `get_macro_data(fred_api_key)` — pulls GDP, CPI, Fed Funds, USD Index from FRED
- `determine_regime(macro)` — classifies macro regime from indicator values
- `calculate_allocations(regime, price_df, total_capital)` — builds the 50/30/20 portfolio
- `calculate_drift(alloc_df, price_df, total_capital)` — compares current to target weights

## Disclaimer
Not financial advice. For research and educational purposes only.
