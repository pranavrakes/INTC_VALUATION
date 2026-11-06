import math
import sys
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.dcf import (DCFInputs, project_fcf, run_dcf, sensitivity_grid,
                     terminal_value_gordon)


def flat_inputs(**kw):
    """Zero growth, 100 FCF every year: EBIT 100/(1-t) offsets nothing else."""
    base = dict(revenue0=1000.0, growth=[0.0] * 5, ebit_margin=[0.10] * 5,
                tax_rate=0.0, da_pct=0.0, capex_pct=0.0, nwc_pct_of_delta_rev=0.0,
                wacc=0.10, terminal_growth=0.0, mid_year=False, shares=10.0)
    base.update(kw)
    return DCFInputs(**base)


def test_project_fcf_known_values():
    inp = DCFInputs(revenue0=100.0, growth=[0.10], ebit_margin=[0.20], tax_rate=0.25,
                    da_pct=0.05, capex_pct=0.08, nwc_pct_of_delta_rev=0.10,
                    wacc=0.1, terminal_growth=0.02)
    r = project_fcf(inp)[0]
    assert r["revenue"] == pytest.approx(110.0)
    assert r["ebit"] == pytest.approx(22.0)
    assert r["nopat"] == pytest.approx(16.5)
    # 16.5 + 5.5 (D&A) - 8.8 (capex) - 1.0 (dNWC) = 12.2
    assert r["fcf"] == pytest.approx(12.2)


def test_flat_perpetuity_equals_fcf_over_wacc():
    res = run_dcf(flat_inputs())
    assert res.enterprise_value == pytest.approx(1000.0)      # 100 / 0.10


def test_mid_year_scales_ev_by_half_year_of_growth():
    end = run_dcf(flat_inputs(mid_year=False)).enterprise_value
    mid = run_dcf(flat_inputs(mid_year=True)).enterprise_value
    assert mid / end == pytest.approx(1.10 ** 0.5)


def test_equity_bridge():
    res = run_dcf(flat_inputs(cash=200.0, debt=300.0, nci=50.0, extra_claims=10.0))
    assert res.equity_value == pytest.approx(1000 + 200 - 300 - 50 - 10)
    assert res.per_share == pytest.approx(res.equity_value / 10.0)


def test_exit_multiple_used_when_set():
    res = run_dcf(flat_inputs(exit_multiple=8.0))
    assert res.terminal_value == pytest.approx(100.0 * 8.0)   # EBITDA = EBIT here


def test_wacc_must_exceed_growth():
    with pytest.raises(ValueError):
        terminal_value_gordon(100.0, 0.03, 0.03)
    with pytest.raises(ValueError):
        run_dcf(flat_inputs(wacc=0.02, terminal_growth=0.03))


def test_mismatched_lengths_rejected():
    with pytest.raises(ValueError):
        run_dcf(flat_inputs(ebit_margin=[0.1] * 4))


def test_sensitivity_grid_monotonic_and_nan_guard():
    inp = flat_inputs()
    grid = sensitivity_grid(inp, [0.08, 0.10, 0.12], [0.00, 0.02, 0.10])
    assert grid[0][0] > grid[1][0] > grid[2][0]               # higher WACC, lower value
    assert grid[1][1] > grid[1][0]                            # higher g, higher value
    assert math.isnan(grid[1][2])                             # g=10% == WACC=10%
    assert math.isnan(grid[0][2])                             # 8% WACC < 10% g: invalid


def test_capex_path_per_year_matches_flat_when_constant():
    flat = run_dcf(flat_inputs(capex_pct=0.05)).enterprise_value
    path = run_dcf(flat_inputs(capex_pct=[0.05] * 5)).enterprise_value
    assert path == pytest.approx(flat)
    with pytest.raises(ValueError):
        run_dcf(flat_inputs(capex_pct=[0.05] * 4))