# Intel (INTC) Valuation Model

A scenario-based valuation of Intel Corporation in pure Python: DCF (bear/base/bull) with a reverse DCF, sum-of-the-parts, relative valuation against peers, and a Monte Carlo layer, combined into a football field chart and a short investment memo.

Intel is quite difficult to value. Free cash flow has been negative because of foundry capex. Earnings are volatile or negative (so P/E cannot be used), and the capital structure has changed recently (including a $23bn equity raise in 2026). The point of the project is to make and defend those judgement calls. It will not produce a "correct" price target.

> **Status:** work in progress. Sections marked *(planned)* are not built yet.

## Methods

| Method | Purpose | Status |
|---|---|---|
| Data pipeline (SEC EDGAR, yfinance, FRED) | Reproducible inputs from free sources | Done |
| Historical analysis | Margins, capex intensity, FCF, net debt | Done (pre-2016 revenue gap and pre-2022 net debt open) |
| WACC (CAPM) | Discount rate range from several beta windows | Done |
| Scenario DCF | Bear / base / bull, WACC x g grid, tornado | Built; draft assumptions, terminal D&A/capex fix pending |
| Reverse DCF | Revenue CAGR, terminal margin and WACC needed to justify the market price | Written, not yet run |
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
├── config/
│   └── assumptions.yaml    # scenario assumptions and equity bridge inputs
├── src/                    # reusable logic
│   ├── data_loader.py      # SEC / yfinance / FRED pulls
│   ├── wacc.py             # beta (paired_returns), CAPM, WACC
│   ├── dcf.py              # DCF engine, sensitivity grid
│   ├── reverse_dcf.py      # bisection solvers for implied drivers
│   ├── sotp.py             # (planned)
│   ├── comps.py            # (planned)
│   └── montecarlo.py       # (planned)
├── scripts/                # run in order; each prints tables and saves outputs
│   ├── step1_historicals.py
│   ├── step2_wacc.py
│   ├── step3_dcf.py
│   ├── step4_reverse_dcf.py
│   └── step5 ... step8     # (planned: SOTP, comps, Monte Carlo, football field)
├── tests/
│   ├── test_wacc.py
│   ├── test_dcf.py
│   └── test_reverse_dcf.py
├── data/
│   ├── raw/                # cached downloads (gitignored)
│   ├── processed/          # cleaned CSVs derived from public filings
│   └── manual/             # hand-entered inputs: segments.csv, capex_financed.csv
├── knowledge_base/         # notes (financial_terms.md)
├── outputs/                # tables, charts, Excel export
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
   - `python scripts/step3_dcf.py` - three scenarios, sensitivity grid, tornado
   - `python scripts/step4_reverse_dcf.py [--price 65.76]` - what the market price implies
   - later steps *(planned)*
6. Run the tests: `pip install pytest` then `pytest`

To force fresh market data, delete the files in `data/raw/` (or pass `refresh=True` to the loader functions). Cached files never expire on their own (cache expiry is on the to-do list).

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
7. Estimate beta by regressing INTC returns on SPY over several windows (2y/3y/5y weekly, 5y monthly), using aligned return windows.
8. Cost of equity by CAPM using the 10Y Treasury yield and Damodaran's implied ERP.
9. Cost of debt as risk-free rate plus a credit spread for Intel's rating (see limitations).
10. Present a WACC range, not a single number, and cross-check against Yahoo's beta and an industry beta relevered at Intel's leverage.

### Phase 3: DCF
11. `assumptions.yaml` holds bear/base/bull scenarios (revenue growth, EBIT margin path, D&A, capex, tax rate, terminal growth), each with a written rationale **before** looking at output.
12. `dcf.py` is unit tested against hand-calculated cases.
13. Run the three scenarios, a WACC vs terminal growth grid, and a tornado chart.
14. Sanity checks: terminal value share of EV, implied exit multiple, terminal growth below the risk-free rate, **terminal capex at least D&A**.
15. Equity bridge: EV plus cash and short-term investments, minus debt, minus non-controlling interest, divided by shares outstanding.
16. Reverse DCF: solve for the revenue CAGR, terminal EBIT margin and WACC that equate DCF value to the market price. Assumptions are never tuned to hit the price.

### Phase 4: SOTP and comps *(planned)*
17. Value Intel Products against fabless peers and Intel Foundry against foundry peers, add equity stakes, subtract net debt.
18. Compare EV/Sales, EV/EBITDA and P/B against peers.

### Phase 5: Monte Carlo *(planned)*
19. Sample growth, terminal margin, WACC and terminal growth with correlations and a fixed seed (10,000+ draws). Report median, 10th-90th percentile and probability of value exceeding the current price.

### Phase 6: Synthesis *(planned)*
20. Football field chart across all methods, an Excel export for auditability, and `memo.md` with the thesis and what would prove it wrong.
21. Run every script from a clean checkout and commit per phase.

## Data sources and as-of dates

| Input | Source | As of |
|---|---|---|
| Financial statements | SEC EDGAR XBRL company facts | FY2025 10-K |
| Latest balance sheet | SEC EDGAR, tied to the Q3 2026 results release | 30 Oct 2026 |
| Shares outstanding | 10-Q cover page: 5,315m (5,310m at 26 Sep 2026) | late Oct 2026 |
| Share price | yfinance (scraped; spot-check before use): 65.76 | 30 Oct 2026, after Q3 results |
| Risk-free rate | FRED DGS10: 4.98% | *confirm date of the cached file* |
| Equity risk premium | Damodaran implied ERP: 4.20% | 1 Oct 2026 (check for update) |
| Credit spread | Damodaran BBB spread table: 1.11% (table undated) | confirm Moody's level and any post-Q3 action |
| Peer multiples | yfinance (scraped; spot-check before use) | *update on refresh* |

*Update the market-data rows each time the caches are refreshed.*

### Balance sheet tie-out (Q3 2026, USD millions)

| Item | Value | Note |
|---|---|---|
| Cash and equivalents | 21,846 | |
| Short-term investments | 32,159 | equals `afs_investments` |
| Total debt | 50,134 | 3,817 short-term + 46,317 long-term |
| Non-controlling interest | 16,642 | |
| Intel stockholders' equity | 114,914 | 131,556 including NCI; loader `total_equity` excludes NCI |
| Shares outstanding | 5,315m | |

The $23bn equity raise (22.6bn net) explains the jump in liquidity.

### WACC

Inputs: risk-free 4.98%, ERP 4.20%, cost of debt = risk-free + 1.11%.

| Beta window | Beta |
|---|---|
| 2y weekly | 2.10 |
| 3y weekly | 2.15 |
| 5y weekly | 1.63 |
| 5y monthly | 2.42 |

The WACC range across windows is 10.9-13.8%. The base case uses **11.5%**, consistent with a Blume-adjusted beta of about 1.7-1.8.

## Results so far

Draft assumptions, WACC 11.5%, **before** the terminal D&A/capex fix (base case expected to fall once D&A fades below terminal capex):

| Scenario | Value per share | vs 65.76 |
|---|---|---|
| Bear | 8.05 | -88% |
| Base | 23.47 | -64% |
| Bull | 38.66 | -41% |

Even the bull case is below the market price, so the market EV (about 362bn) requires far more than the base case. Reverse DCF output goes here once `step4_reverse_dcf.py` has been run.

## Limitations

- Cost of debt uses a generic BBB spread rather than Intel's own traded yields.
- Capex funded through partner arrangements appears in the financing section of the cash flow statement; `data/manual/capex_financed.csv` (FY2024, FY2025 10-Ks) is still to be filled, so historical capex and FCF may be flattered.
- Pre-2016 revenue uses a different XBRL tag (`SalesRevenueNet`, to be added); pre-2022 net debt is not reconciled.
- The FY2026 growth rate is a placeholder pending 9M revenue and Q4 guidance.
- Scraped market data (yfinance) should be spot-checked. LSEG data, if used, stays in a git-ignored restricted folder until licence terms are confirmed.