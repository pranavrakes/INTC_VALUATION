# Project overview — what has been built so far

Goal: estimate what Intel (ticker **INTC**) is worth, using public data and standard
valuation methods. The work is organised as numbered steps; steps 1 and 2 are done.

See also: [python_env.md](python_env.md) for the libraries, and
[financial_terms.md](financial_terms.md) for the vocabulary, and
[git_and_github.md](git_and_github.md) for how we share code.

## Current layout

```
intc_valuation/
├── src/
│   ├── data_loader.py      # downloads + cleans all data (SEC, yfinance, FRED)
│   └── wacc.py             # beta, cost of equity, cost of debt, WACC formulas
├── scripts/
│   ├── step1_historicals.py  # prints historical financials, saves a chart
│   └── step2_wacc.py         # estimates beta and WACC over several windows
├── tests/
│   └── test_wacc.py        # two sanity tests for the WACC formulas
├── data/
│   ├── raw/                # cached downloads (git-ignored)
│   ├── processed/          # financials_annual.csv (committed)
│   └── manual/             # segments.csv — to be filled in by hand
└── outputs/
    └── historicals.png     # chart produced by step 1
```

## Step 0 — data loading (`src/data_loader.py`)

Pulls data from three free sources and caches it under `data/raw/` so repeat runs are
fast and don't hit the websites again (use `--refresh` to force a re-download).

| Source | What it provides | Function |
|---|---|---|
| SEC EDGAR (XBRL "companyfacts" API) | Yearly income statement, cash flow and balance sheet; shares outstanding | `load_financials`, `load_balance_sheet_latest`, `load_share_count` |
| yfinance (Yahoo Finance) | Daily price history; current multiples for INTC and 8 peers | `load_prices`, `load_peer_snapshot` |
| FRED (St. Louis Fed) | 10-year US Treasury yield (the "risk-free rate") | `load_risk_free` |

What it computes on top of the raw numbers:

- **D&A** = depreciation + amortization
- **Operating margin** = operating income ÷ revenue
- **Capex % of revenue** = capex ÷ revenue
- **Free cash flow (FCF)** = cash from operations − capex
- **Net debt** = total debt − cash − short-term investments − other liquid securities

Output: `data/processed/financials_annual.csv` — one row per fiscal year (2016 onward).

It also creates `data/manual/segments.csv`, a blank template. Intel reports
"Intel Products" and "Intel Foundry" separately, but that split is not in the SEC API,
so it has to be typed in by hand from the 10-K annual report.

Peers used for comparison: AMD, NVDA, TSM, QCOM, AVGO, TXN, MU, GFS.

## Step 1 — historicals (`scripts/step1_historicals.py`)

Answers "what has Intel's business looked like over the last decade?"

- Prints revenue, operating income, net income, D&A, capex, cash from operations,
  FCF and net debt per year (in $ millions).
- Prints operating margin and capex-as-%-of-revenue.
- Prints the latest balance sheet.
- Saves three charts to `outputs/historicals.png`: revenue, operating margin,
  capex vs. operating cash flow — and opens a chart window (close it to finish).

## Step 2 — WACC (`scripts/step2_wacc.py`, `src/wacc.py`)

Answers "what annual return do investors demand from Intel?" — this becomes the
discount rate for a future DCF valuation.

1. Risk-free rate from FRED (10-year Treasury).
2. Market value of equity = latest share price × shares outstanding.
3. Debt from the latest balance sheet.
4. **Beta** measured against SPY (S&P 500 ETF) over four windows: 2y, 3y, 5y weekly
   returns and 5y monthly returns — beta varies with the window, so seeing several helps.
5. Cost of equity via CAPM, then WACC.

Fixed assumptions in the script: equity risk premium **4.2%**, tax rate **21%**,
pre-tax cost of debt **6%**.

## Tests

`tests/test_wacc.py` checks the WACC and CAPM formulas against hand-calculated
toy numbers. Run with `pytest`.

## Not done yet (likely next steps)

- Fill in `data/manual/segments.csv` from the 10-K.
- A **DCF** (discounted cash flow) model: project future free cash flows and discount
  them at the WACC to get a value per share.
- A **comparables** analysis using the peer snapshot (EV/Sales, EV/EBITDA, P/E).
- Compare the resulting value per share with the current market price.

## Git history at the time of writing

```
56be236 Added Wacc
285ddac SEC, yfinance, FRED, data loader and historicals
```
