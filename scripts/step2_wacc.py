import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data_loader import (load_financials, load_balance_sheet_latest,
                             load_share_count, load_prices, load_risk_free)
from src.wacc import estimate_beta, cost_of_equity, after_tax_cost_of_debt, wacc

ERP = 0.042
TAX_RATE = 0.21

rf = load_risk_free()["rate"]
price = load_prices("INTC")["Close"].iloc[-1]
shares =  load_share_count()["shares_outstanding"]
equity = price * shares

bs = load_balance_sheet_latest()
debt = bs.get("debt_current", 0) + bs.get("debt_long_term", 0)

SPREAD = 0.02
kd = rf + SPREAD
print(f"Pre-tax cost of debt: {kd:.2%} (risk-free {rf:.2%} + spread {SPREAD:.2%})")

def returns(ticker, freq):
    return load_prices(ticker)["Close"].resample(freq).last().pct_change().dropna()

print(f"\n RF {rf: .2%} | ERP {ERP: .2%} | Equity {equity/1e9: .1f}bn | Debt {debt/1e9: .1f}bn")
print(f"{'Window':<14}{'Beta':>7}{'Ke':>9}{'WACC':>9}")

intc_w, spy_w = returns("INTC", "W-FRI"), returns("SPY", "W-FRI")
windows = [("2y weekly", intc_w.tail(104), spy_w.tail(104)),
           ("3y weekly", intc_w.tail(156), spy_w.tail(156)),
           ("5y weekly", intc_w.tail(260), spy_w.tail(260))]
intc_m, spy_m = returns("INTC", "ME"), returns("SPY", "ME")
windows.append(("5y monthly", intc_m.tail(60), spy_m.tail(60)))

for label, i, s in windows:
    beta = estimate_beta(i, s)
    ke = cost_of_equity(rf, beta, ERP)
    w = wacc(equity, debt, ke, after_tax_cost_of_debt(kd, TAX_RATE))
    print(f"{label:<14}{beta:>7.2f}{ke:>9.2%}{w:>9.2%}")
