# Intel (INTC) Valuation Model

A scenario-based valuation of Intel Corporation in pure Python: DCF (bear/base/bull), sum-of-the-parts, relative valuation against peers, and a Monte Carlo layer, combined into a football field chart and a short investment memo.

Intel is quite difficult to value. Free cash flow has been negative because of foundry capex. Earnings are pretty volatile or negative (so P/E cannot be used), and the capital structure has changed recently. The point of the project is to make and defend those judgement calls. It will not produce a "correct" price target.

> **Status:** work in progress. Sections marked *(planned)* are not built yet.

## Methods

| Method | Purpose | Status |
|---|---|---|
| Data pipeline (SEC EDGAR, yfinance, FRED) | Reproducible inputs from free sources | Done |
| Historical analysis | Margins, capex intensity, FCF, net debt | Done |
| WACC (CAPM) | Discount rate range from several beta windows | Done (inputs to be refreshed) |
| Scenario DCF | Bear / base / bull, sensitivity grid, tornado chart | *(planned)* |
| Sum-of-the-parts | Intel Products vs Intel Foundry plus stakes | *(planned)* |
| Comps | EV/Sales, EV/EBITDA, P/B against peers | *(planned)* |
| Monte Carlo | Correlated draws, fixed seed, value distribution | *(planned)* |
| Football field and memo | Combine all methods, state what would prove the thesis wrong | *(planned)* |

## Project layout

```
PythonProject1/
├── README.md
├── requirements.txt
├── .gitignore
├── src/                    # reusable logic
│   ├── data_loader.py      # SEC / yfinance / FRED pulls
│   ├── wacc.py             # beta, CAPM, WACC
│   ├── dcf.py              # (planned)
│   ├── sotp.py             # (planned)
│   ├── comps.py            # (planned)
│   └── montecarlo.py       # (planned)
├── scripts/                # run in order; each prints tables and saves charts
│   ├── step1_historicals.py
│   ├── step2_wacc.py
│   └── step3_dcf.py ... step7_football_field.py   # (planned)
├── tests/
│   └── test_wacc.py
├── data/
│   ├── raw/                # cached downloads (gitignored)
│   ├── processed/          # cleaned CSVs derived from public filings
│   └── manual/             # hand-entered inputs, e.g. segments.csv
├── outputs/                # charts and Excel export
└── memo.md                 # (planned) thesis and falsification criteria
```

## How to run

1. Install dependencies: `pip install -r requirements.txt`
2. SEC requires a contact User-Agent. In PowerShell:
   `$env:SEC_USER_AGENT="Your Name your.email@example.com"`
   (macOS/Linux: `export SEC_USER_AGENT="..."`)
3. Pull data: `python src/data_loader.py`
4. Fill in `data/manual/segments.csv` from the latest 10-K segment note (USD millions, with a source note per row).
5. Run the scripts in order:
   - `python scripts/step1_historicals.py` - historical tables and chart
   - `python scripts/step2_wacc.py` - beta, cost of equity and WACC by window
   - `python scripts/step3_dcf.py` ... `step7_football_field.py` *(planned)*
6. Run the tests: `pip install pytest` then `pytest`

To force fresh market data, delete the files in `data/raw/` (or pass `refresh=True` to the loader functions). Cached files never expire on their own.

## Step-by-step plan

### Phase 0: Setup
1. Create the folder structure and `.gitignore` (`.venv/`, `.idea/`, `__pycache__/`, `data/raw/`, `data/lseg/`).
2. Run `data_loader.py` and confirm it prints financials, shares outstanding, last close, 10Y yield and the segment template path.
3. Fill in `segments.csv` from the 10-K.

### Phase 1: Understand the business
4. Run `step1_historicals.py`. Check revenue and operating income against the 10-K for two or three years. Make sure no column is NaN.
5. Reconcile the latest balance sheet against the latest 10-Q (cash, short-term investments, debt, equity, non-controlling interest).
6. Record valuation-date inputs: price, shares outstanding, debt, cash and investments, non-controlling interest.

### Phase 2: Cost of capital
7. Estimate beta by regressing INTC returns on SPY over several windows (2y/3y/5y weekly, 5y monthly).
8. Cost of equity by CAPM using the 10Y Treasury yield and Damodaran's implied ERP.
9. Cost of debt as risk-free rate plus a credit spread for Intel's rating (see limitations).
10. Present a WACC range, not a single number, and cross-check against Yahoo's beta and an industry beta relevered at Intel's leverage.

### Phase 3: DCF *(planned)*
11. Write `assumptions.yaml` with bear/base/bull scenarios (revenue growth, target operating margin, capex % of revenue, tax rate, terminal growth), each with a written rationale **before** looking at output.
12. Build `dcf.py` with a unit test against a hand-calculated toy case.
13. Run the three scenarios, a WACC vs terminal growth grid, and a tornado chart.
14. Sanity checks: terminal value share of EV, implied exit multiple, terminal growth below the risk-free rate.
15. Equity bridge: EV minus debt, plus cash and short-term investments, minus non-controlling interest, divided by diluted shares.

### Phase 4: SOTP and comps *(planned)*
16. Value Intel Products against fabless peers and Intel Foundry against foundry peers, add equity stakes, subtract net debt.
17. Compare EV/Sales, EV/EBITDA and P/B with peers after spot-checking the scraped Yahoo data (especially foreign filers such as TSM).

### Phase 5: Monte Carlo *(planned)*
18. Sample growth, terminal margin, WACC and terminal growth with correlations and a fixed seed (10,000+ draws). Report median, 10th-90th percentile and probability of value exceeding the current price.

### Phase 6: Synthesis *(planned)*
19. Football field chart across all methods, an Excel export for auditability, and `memo.md` with the thesis and what would prove it wrong.
20. Run every script from a clean checkout and commit per phase.

## Data sources and as-of dates

| Input | Source | As of |
|---|---|---|
| Financial statements | SEC EDGAR XBRL company facts | FY2025 10-K |
| Latest balance sheet | SEC EDGAR, tied to the Q2 2026 10-Q | 27 Jun 2026 |
| Shares outstanding | 10-Q cover page / balance sheet (about 5.04bn) | Jul 2026 |
| Risk-free rate | FRED DGS10 (5.12%) | 20 Oct 2026 |
| Equity risk premium | Damodaran implied ERP (4.20%) | 1 Oct 2026 |
| Prices and peer multiples | yfinance (scraped; spot-check before use) | cached 22 Oct 2026 |

*Update the market-data rows each time the caches are refreshed.*
