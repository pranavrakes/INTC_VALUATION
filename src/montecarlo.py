"""Monte Carlo around a DCF scenario.

Each draw shocks five drivers of a base scenario (DCFInputs) with fixed correlations, runs the
normal DCF engine, and records value per share. Reproducible (seeded). Place in src/montecarlo.py.

Shocks are ADDITIVE shifts to the scenario paths, so the scenario's own shape is preserved:
  growth   -> added to years 2..N (year 1, FY2026, is largely known from reported revenue + guidance)
  margin   -> added to the EBIT margin, ramped linearly from 0 in year 1 to the full shock in year N
  capex    -> added to capex % of revenue, same ramp, never below D&A
  wacc     -> added to WACC, clipped to bounds
  terminal growth -> added, clipped, and kept at least `min_wacc_g_spread` below WACC
The spreads are judgements (see MCSpec); they are NOT fitted to the share price.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np

from src.dcf import DCFInputs, run_dcf

DRIVERS = ["growth", "margin", "capex", "wacc", "terminal_growth"]

# Correlations (order = DRIVERS). Growth and margin move together (scale, operating leverage);
# faster growth needs more capex; WACC and terminal growth are mildly linked via the rate level.
DEFAULT_CORR = np.array([
    [1.0, 0.5, 0.3, 0.0, 0.0],
    [0.5, 1.0, -0.2, 0.0, 0.0],
    [0.3, -0.2, 1.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 1.0, 0.3],
    [0.0, 0.0, 0.0, 0.3, 1.0],
])


@dataclass
class MCSpec:
    n: int = 20_000
    seed: int = 42
    sd: tuple = (0.02, 0.05, 0.015, 0.010, 0.005)    # std dev of each driver's shift
    corr: np.ndarray = field(default_factory=lambda: DEFAULT_CORR.copy())
    wacc_bounds: tuple = (0.08, 0.15)
    tg_bounds: tuple = (0.01, 0.035)
    margin_bounds: tuple = (-0.05, 0.60)
    min_wacc_g_spread: float = 0.04

    def scaled(self, k: float) -> "MCSpec":
        """Same correlations, every spread multiplied by k (k=2 is a deliberately wide test)."""
        return replace(self, sd=tuple(s * k for s in self.sd))


def _as_list(x, n: int) -> list[float]:
    return list(x) if isinstance(x, list) else [x] * n


def draw_shocks(spec: MCSpec) -> np.ndarray:
    """(n, 5) array of correlated driver shifts."""
    c = np.asarray(spec.corr, dtype=float)
    if c.shape != (5, 5) or not np.allclose(c, c.T) or np.linalg.eigvalsh(c).min() < -1e-9:
        raise ValueError("corr must be a symmetric positive semi-definite 5x5 matrix")
    chol = np.linalg.cholesky(c + 1e-12 * np.eye(5))
    z = np.random.default_rng(spec.seed).standard_normal((spec.n, 5))
    return (z @ chol.T) * np.asarray(spec.sd)


def apply_shock(inp: DCFInputs, shock: np.ndarray, spec: MCSpec) -> DCFInputs:
    dg, dm, dc, dw, dt = shock
    n = len(inp.growth)
    ramp = [t / (n - 1) if n > 1 else 1.0 for t in range(n)]
    da = _as_list(inp.da_pct, n)
    capex = _as_list(inp.capex_pct, n)
    lo_m, hi_m = spec.margin_bounds
    wacc = float(np.clip(inp.wacc + dw, *spec.wacc_bounds))
    tg = float(np.clip(inp.terminal_growth + dt, *spec.tg_bounds))
    tg = min(tg, wacc - spec.min_wacc_g_spread)
    return replace(
        inp,
        growth=[inp.growth[0]] + [g + dg for g in inp.growth[1:]],
        ebit_margin=[float(np.clip(m + dm * r, lo_m, hi_m)) for m, r in zip(inp.ebit_margin, ramp)],
        da_pct=da,
        capex_pct=[max(c + dc * r, d) for c, d, r in zip(capex, da, ramp)],
        wacc=wacc,
        terminal_growth=tg,
    )


def simulate(inp: DCFInputs, spec: MCSpec) -> dict:
    shocks = draw_shocks(spec)
    values = np.empty(spec.n)
    tv_share = np.empty(spec.n)
    for i in range(spec.n):
        res = run_dcf(apply_shock(inp, shocks[i], spec))
        values[i] = res.per_share
        tv_share[i] = res.tv_share_of_ev
    return dict(values=values, shocks=shocks, tv_share=tv_share)


def summarise(values: np.ndarray, price: float,
              refs: dict[str, float] | None = None) -> dict:
    """Percentiles, mean, and the probability of beating the price (and any reference values)."""
    pct = {f"p{p}": float(np.percentile(values, p)) for p in (5, 10, 25, 50, 75, 90, 95)}
    out = dict(mean=float(values.mean()), prob_above_price=float((values > price).mean()),
               price_percentile=float((values < price).mean() * 100), max=float(values.max()), **pct)
    for name, v in (refs or {}).items():
        out[f"prob_above_{name}"] = float((values > v).mean())
    return out


def rank_correlations(shocks: np.ndarray, values: np.ndarray) -> dict[str, float]:
    """Spearman rank correlation of value per share with each driver shift."""
    def ranks(x):
        return np.argsort(np.argsort(x)).astype(float)
    rv = ranks(values)
    return {d: float(np.corrcoef(ranks(shocks[:, j]), rv)[0, 1]) for j, d in enumerate(DRIVERS)}