from __future__ import annotations
import warnings
from dataclasses import dataclass, field


@dataclass
class DCFInputs:
    revenue0: float                      # last actual fiscal-year revenue
    growth: list[float]                  # revenue growth per forecast year
    ebit_margin: list[float]             # EBIT / revenue per forecast year
    tax_rate: float                      # cash tax rate on EBIT
    da_pct: float  | list[float]                    # D&A as % of revenue
    capex_pct: float | list[float]       # capex as % of revenue (one value, or one per year)
    nwc_pct_of_delta_rev: float          # change in NWC as % of change in revenue
    wacc: float
    terminal_growth: float
    cash: float = 0.0                    # cash + short-term investments
    debt: float = 0.0
    nci: float = 0.0                     # non-controlling interests
    shares: float = 1.0
    mid_year: bool = True
    exit_multiple: float | None = None   # EV/EBITDA; if set, used instead of Gordon growth
    extra_claims: float = 0.0            # leases, pensions, etc. subtracted in the bridge


@dataclass
class DCFResult:
    years: list[dict] = field(default_factory=list)
    pv_fcf: float = 0.0
    terminal_value: float = 0.0
    pv_terminal: float = 0.0
    enterprise_value: float = 0.0
    equity_value: float = 0.0
    per_share: float = 0.0
    tv_share_of_ev: float = 0.0


def project_fcf(inp: DCFInputs) -> list[dict]:
    """Revenue -> EBIT -> NOPAT -> unlevered FCF for each forecast year."""
    n = len(inp.growth)
    if len(inp.ebit_margin) != n:
        raise ValueError("growth and ebit_margin must be the same length")
    if isinstance(inp.capex_pct, list) and len(inp.capex_pct) != n:
        raise ValueError("capex_pct list must match the forecast length")
    rows, prev_rev = [], inp.revenue0
    for t in range(n):
        rev = prev_rev * (1 + inp.growth[t])
        ebit = rev * inp.ebit_margin[t]
        nopat = ebit * (1 - inp.tax_rate)
        dp = inp.da_pct[t] if isinstance(inp.da_pct, list) else inp.da_pct
        da = rev * dp
        cp = inp.capex_pct[t] if isinstance(inp.capex_pct, list) else inp.capex_pct
        capex = rev * cp
        d_nwc = (rev - prev_rev) * inp.nwc_pct_of_delta_rev
        fcf = nopat + da - capex - d_nwc
        rows.append(dict(year=t + 1, revenue=rev, ebit=ebit, nopat=nopat,
                         da=da, capex=capex, d_nwc=d_nwc, ebitda=ebit + da, fcf=fcf))
        prev_rev = rev
    return rows


def discount_factor(rate: float, t: float) -> float:
    return 1.0 / (1.0 + rate) ** t


def terminal_value_gordon(fcf_last: float, wacc: float, g: float) -> float:
    if wacc <= g:
        raise ValueError(f"WACC ({wacc:.2%}) must exceed terminal growth ({g:.2%})")
    return fcf_last * (1 + g) / (wacc - g)


def run_dcf(inp: DCFInputs) -> DCFResult:
    rows = project_fcf(inp)
    last = rows[-1]
    if last["capex"] < last["da"]:
        warnings.warn(
            f"Terminal capex ({last['capex']:,.0f}) < D&A ({last['da']:,.0f}): "
            "terminal value overstated"
        )
    n = len(rows)
    if n == 0:
        raise ValueError("need at least one forecast year")
    shift = 0.5 if inp.mid_year else 0.0

    pv_fcf = 0.0
    for r in rows:
        r["discount_factor"] = discount_factor(inp.wacc, r["year"] - shift)
        r["pv_fcf"] = r["fcf"] * r["discount_factor"]
        pv_fcf += r["pv_fcf"]

    if inp.exit_multiple is not None:
        tv = rows[-1]["ebitda"] * inp.exit_multiple
        pv_tv = tv * discount_factor(inp.wacc, n)            # exit multiple: end of year N
    else:
        tv = terminal_value_gordon(rows[-1]["fcf"], inp.wacc, inp.terminal_growth)
        pv_tv = tv * discount_factor(inp.wacc, n - shift)    # Gordon follows cash-flow timing

    ev = pv_fcf + pv_tv
    equity = ev + inp.cash - inp.debt - inp.nci - inp.extra_claims
    return DCFResult(years=rows, pv_fcf=pv_fcf, terminal_value=tv, pv_terminal=pv_tv,
                     enterprise_value=ev, equity_value=equity,
                     per_share=equity / inp.shares, tv_share_of_ev=pv_tv / ev if ev else float("nan"))


def sensitivity_grid(inp: DCFInputs, waccs: list[float], growths: list[float]) -> list[list[float]]:
    from dataclasses import replace
    grid = []
    for w in waccs:
        row = []
        for g in growths:
            try:
                row.append(run_dcf(replace(inp, wacc=w, terminal_growth=g)).per_share)
            except ValueError:
                row.append(float("nan"))
        grid.append(row)
    return grid