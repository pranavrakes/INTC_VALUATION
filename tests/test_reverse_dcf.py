from dataclasses import replace

import pytest

from src.dcf import DCFInputs, run_dcf
from src.reverse_dcf import solve_revenue_cagr, solve_terminal_margin, solve_wacc


def make() -> DCFInputs:
    n = 10
    return DCFInputs(
        revenue0=50_000, growth=[0.08] * n, ebit_margin=[0.05 + 0.015 * t for t in range(n)],
        tax_rate=0.15, da_pct=0.12, capex_pct=0.14, nwc_pct_of_delta_rev=0.10,
        wacc=0.115, terminal_growth=0.025, cash=50_000, debt=50_000, nci=15_000, shares=5_000,
    )


def test_wacc_round_trip():
    inp = make()
    target = run_dcf(replace(inp, wacc=0.09)).per_share
    assert solve_wacc(inp, target) == pytest.approx(0.09, abs=1e-5)


def test_cagr_round_trip():
    inp = make()
    target = run_dcf(replace(inp, growth=[0.15] * 10)).per_share
    r = solve_revenue_cagr(inp, target)
    assert r["rev_cagr"] == pytest.approx(0.15, abs=1e-5)


def test_margin_hits_target():
    inp = make()
    r = solve_terminal_margin(inp, 30.0)
    assert r is not None
    assert r["per_share"] == pytest.approx(30.0, abs=1e-3)


def test_unreachable_returns_none():
    assert solve_revenue_cagr(make(), 1e9) is None