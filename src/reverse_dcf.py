"""Reverse DCF: solve for the single driver that makes DCF value per share equal the market price.

Pure functions on DCFInputs / run_dcf. Place in src/reverse_dcf.py.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Callable

from src.dcf import DCFInputs, run_dcf


def _bisect(f: Callable[[float], float], lo: float, hi: float,
            tol: float = 1e-7, max_iter: int = 200) -> float | None:
    try:
        flo, fhi = f(lo), f(hi)
    except ValueError:
        return None
    if flo != flo or fhi != fhi or flo * fhi > 0:
        return None
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if abs(fm) < tol or (hi - lo) < 1e-12:
            return mid
        if flo * fm <= 0:
            hi = mid
        else:
            lo, flo = mid, fm
    return 0.5 * (lo + hi)


def cagr(start: float, end: float, years: int) -> float:
    return (end / start) ** (1.0 / years) - 1.0


def margin_path(m_start: float, m_end: float, n: int) -> list[float]:
    if n == 1:
        return [m_end]
    return [m_start + (m_end - m_start) * t / (n - 1) for t in range(n)]


def summarise(inp: DCFInputs) -> dict:
    res = run_dcf(inp)
    last = res.years[-1]
    n = len(inp.growth)
    return dict(
        per_share=res.per_share,
        rev_cagr=cagr(inp.revenue0, last["revenue"], n),
        rev_final=last["revenue"],
        ebit_final=last["ebit"],
        ebit_margin_final=last["ebit"] / last["revenue"],
        fcf_final=last["fcf"],
        tv_share=res.tv_share_of_ev,
    )


def solve_revenue_cagr(inp: DCFInputs, price: float,
                       lo: float = -0.10, hi: float = 0.60) -> dict | None:
    n = len(inp.growth)

    def f(g: float) -> float:
        return run_dcf(replace(inp, growth=[g] * n)).per_share - price

    g = _bisect(f, lo, hi)
    if g is None:
        return None
    return summarise(replace(inp, growth=[g] * n))


def solve_terminal_margin(inp: DCFInputs, price: float, growth: list[float] | None = None,
                          lo: float = 0.0, hi: float = 0.80) -> dict | None:
    n = len(inp.growth)
    base = replace(inp, growth=growth) if growth is not None else inp
    m0 = inp.ebit_margin[0]

    def f(m: float) -> float:
        return run_dcf(replace(base, ebit_margin=margin_path(m0, m, n))).per_share - price

    m = _bisect(f, lo, hi)
    if m is None:
        return None
    return summarise(replace(base, ebit_margin=margin_path(m0, m, n)))


def solve_wacc(inp: DCFInputs, price: float, hi: float = 0.40) -> float | None:
    lo = inp.terminal_growth + 0.005

    def f(w: float) -> float:
        return run_dcf(replace(inp, wacc=w)).per_share - price

    return _bisect(f, lo, hi)


def frontier(inp: DCFInputs, price: float, cagrs: list[float]) -> list[dict]:
    n = len(inp.growth)
    out = []
    for g in cagrs:
        r = solve_terminal_margin(inp, price, growth=[g] * n)
        out.append(dict(rev_cagr=g,
                        rev_final=inp.revenue0 * (1 + g) ** n,
                        margin_needed=None if r is None else r["ebit_margin_final"],
                        ebit_final=None if r is None else r["ebit_final"]))
    return out