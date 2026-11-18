import numpy as np
import pytest

from src.dcf import DCFInputs, run_dcf
from src.montecarlo import (MCSpec, apply_shock, draw_shocks, rank_correlations, simulate,
                            summarise)


def make() -> DCFInputs:
    n = 10
    return DCFInputs(
        revenue0=50_000, growth=[0.15] + [0.06] * 9,
        ebit_margin=[0.05 + 0.015 * t for t in range(n)],
        tax_rate=0.18, da_pct=[0.18 - 0.005 * t for t in range(n)],
        capex_pct=[0.27 - 0.013 * t for t in range(n)], nwc_pct_of_delta_rev=0.10,
        wacc=0.115, terminal_growth=0.025, cash=50_000, debt=50_000, nci=15_000, shares=5_000)


def test_seeded_and_reproducible():
    a = draw_shocks(MCSpec(n=500, seed=1))
    b = draw_shocks(MCSpec(n=500, seed=1))
    c = draw_shocks(MCSpec(n=500, seed=2))
    assert np.array_equal(a, b) and not np.array_equal(a, c)


def test_zero_spread_reproduces_the_scenario():
    inp = make()
    out = simulate(inp, MCSpec(n=50, sd=(0, 0, 0, 0, 0)))
    assert np.allclose(out["values"], run_dcf(inp).per_share)


def test_sample_correlation_matches_target():
    spec = MCSpec(n=60_000, seed=3)
    s = draw_shocks(spec)
    corr = np.corrcoef(s.T)
    assert corr[0, 1] == pytest.approx(0.5, abs=0.02)      # growth-margin
    assert corr[3, 4] == pytest.approx(0.3, abs=0.02)      # wacc-terminal growth
    assert s[:, 0].std() == pytest.approx(0.02, rel=0.03)


def test_bad_correlation_matrix_rejected():
    bad = np.ones((5, 5)) * 2 - np.eye(5)                  # off-diagonals of 2: not a correlation matrix
    with pytest.raises(ValueError):
        draw_shocks(MCSpec(n=10, corr=bad))


def test_shock_keeps_year1_growth_and_floors_capex_at_da():
    inp = make()
    spec = MCSpec()
    shocked = apply_shock(inp, np.array([0.05, 0.0, -0.20, 0.0, 0.0]), spec)   # huge capex cut
    assert shocked.growth[0] == inp.growth[0]
    assert shocked.growth[1] == pytest.approx(inp.growth[1] + 0.05)
    assert all(c >= d for c, d in zip(shocked.capex_pct, shocked.da_pct))


def test_wacc_and_terminal_growth_constraints():
    inp = make()
    spec = MCSpec()
    s = apply_shock(inp, np.array([0, 0, 0, -0.10, 0.10]), spec)               # extreme both ways
    assert s.wacc == spec.wacc_bounds[0]
    assert s.wacc - s.terminal_growth >= spec.min_wacc_g_spread - 1e-12


def test_higher_wacc_lowers_value_and_rank_corr_signs():
    inp = make()
    out = simulate(inp, MCSpec(n=3_000, seed=5))
    rc = rank_correlations(out["shocks"], out["values"])
    assert rc["wacc"] < 0 and rc["margin"] > 0 and rc["growth"] > 0


def test_summarise_probabilities():
    v = np.arange(100, dtype=float)
    s = summarise(v, price=89.5, refs={"ref": 49.5})
    assert s["prob_above_price"] == pytest.approx(0.10)
    assert s["prob_above_ref"] == pytest.approx(0.50)