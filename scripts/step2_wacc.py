import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

from src.data_loader import (load_financials, load_balance_sheet_latest,
                             load_share_count, load_prices, load_risk_free)
from src.wacc import (estimate_beta, cost_of_equity, after_tax_cost_of_debt,
                      wacc, paired_returns)

ERP = 0.042
TAX_RATE = 0.21

# Rating-based spread: BBB (S&P/Fitch, Fitch outlook negative).
# Damodaran ratings table, Baa2/BBB = 1.11% (table undated; checked 3 Nov 2026).
SPREAD = 0.0111

rf = load_risk_free()["rate"]
intc_px = load_prices("INTC")["Close"]
spy_px = load_prices("SPY")["Close"]
print(f"Prices end {intc_px.index[-1].date()} (INTC), {spy_px.index[-1].date()} (SPY)")

price = intc_px.iloc[-1]
shares = load_share_count()["shares_outstanding"]
equity = price * shares

bs = load_balance_sheet_latest()
debt = bs.get("debt_current", 0) + bs.get("debt_long_term", 0)

kd = rf + SPREAD
print(f"Pre-tax cost of debt: {kd:.2%} (risk-free {rf:.2%} + spread {SPREAD:.2%})")

intc_w, spy_w = paired_returns(intc_px, spy_px, "W-FRI")
partial = intc_px.index[-1].to_period("M") == pd.Timestamp.today().to_period("M")
intc_m, spy_m = paired_returns(intc_px, spy_px, "ME", drop_partial_last=partial)

print(f"\n RF {rf: .2%} | ERP {ERP: .2%} | Equity {equity/1e9: .1f}bn | Debt {debt/1e9: .1f}bn")
print(f"{'Window':<14}{'Beta':>7}{'Ke':>9}{'WACC':>9}")

windows = [("2y weekly", intc_w.tail(104), spy_w.tail(104)),
           ("3y weekly", intc_w.tail(156), spy_w.tail(156)),
           ("5y weekly", intc_w.tail(260), spy_w.tail(260)),
           ("5y monthly", intc_m.tail(60), spy_m.tail(60))]

for label, i, s in windows:
    beta = estimate_beta(i, s)
    ke = cost_of_equity(rf, beta, ERP)
    w = wacc(equity, debt, ke, after_tax_cost_of_debt(kd, TAX_RATE))
    print(f"{label:<14}{beta:>7.2f}{ke:>9.2%}{w:>9.2%}")