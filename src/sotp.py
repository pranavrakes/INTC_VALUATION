from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

PRODUCTS, FOUNDRY, OTHER = "Intel Products", "Intel Foundry", "All Other"
CORP, ELIM, CONSOL = "Corporate unallocated", "Intersegment eliminations", "Consolidated"
REQUIRED_COLUMNS = {"period", "segment", "revenue", "operating_income"}


def load_segments(path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"period": str})
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"segments file missing columns: {sorted(missing)}")
    return df


def _get(seg: pd.DataFrame, period: str, segment: str, col: str) -> float:
    r = seg[(seg["period"] == period) & (seg["segment"] == segment)][col]
    if len(r) != 1 or pd.isna(r.iloc[0]):
        raise ValueError(f"need exactly one {col} value for {segment!r} in {period!r}")
    return float(r.iloc[0])


def check_ties(seg: pd.DataFrame, period: str) -> dict:
    """Segment rows must sum to the consolidated row (catches transcription errors)."""
    rev = sum(_get(seg, period, s, "revenue") for s in (PRODUCTS, FOUNDRY, OTHER, ELIM))
    oi = sum(_get(seg, period, s, "operating_income") for s in (PRODUCTS, FOUNDRY, OTHER, CORP, ELIM))
    return dict(period=period,
                revenue_gap=rev - _get(seg, period, CONSOL, "revenue"),
                op_income_gap=oi - _get(seg, period, CONSOL, "operating_income"))


@dataclass(frozen=True)
class RunRate:
    products_rev: float
    products_ebit: float
    foundry_rev: float
    foundry_ebit: float
    other_rev: float
    other_ebit: float
    corp_ebit: float        # corporate unallocated + intersegment eliminations (negative = cost)


def run_rate(seg: pd.DataFrame, period: str, factor: float,
             corp_period: str | None = None, corp_factor: float | None = None) -> RunRate:
    cp, cf = corp_period or period, corp_factor or factor
    return RunRate(
        products_rev=_get(seg, period, PRODUCTS, "revenue") * factor,
        products_ebit=_get(seg, period, PRODUCTS, "operating_income") * factor,
        foundry_rev=_get(seg, period, FOUNDRY, "revenue") * factor,
        foundry_ebit=_get(seg, period, FOUNDRY, "operating_income") * factor,
        other_rev=_get(seg, period, OTHER, "revenue") * factor,
        other_ebit=_get(seg, period, OTHER, "operating_income") * factor,
        corp_ebit=(_get(seg, cp, CORP, "operating_income") + _get(seg, cp, ELIM, "operating_income")) * cf,
    )


def peer_ev_ebit(snap: pd.DataFrame, tickers: list[str], max_multiple: float = 60.0) -> pd.Series:
    d = snap.loc[tickers]
    ebit = d["operatingMargins"] * d["totalRevenue"]
    m = d["enterpriseValue"] / ebit.where(ebit > 0)
    return m[m <= max_multiple].dropna()


@dataclass(frozen=True)
class Case:
    name: str
    products_ev_ebit: float
    foundry_ev_sales: float
    other_ev_ebit: float
    corp_multiple: float             # applied to the (negative) corporate run-rate
    foundry_loss_burden: float = 0.0   # share of Foundry's operating loss charged to Products EBIT
    stakes: float = 0.0                # equity stakes not in segment results ($m)


def value_case(rr: RunRate, case: Case, cash: float, debt: float, nci: float,
               shares: float, extra_claims: float = 0.0) -> dict:
    products_ebit = rr.products_ebit + case.foundry_loss_burden * rr.foundry_ebit
    parts = {
        PRODUCTS: products_ebit * case.products_ev_ebit,
        FOUNDRY: rr.foundry_rev * case.foundry_ev_sales,
        OTHER: rr.other_ebit * case.other_ev_ebit,
        "Corporate costs": rr.corp_ebit * case.corp_multiple,
        "Equity stakes": case.stakes,
    }
    ev = sum(parts.values())
    equity = ev + cash - debt - nci - extra_claims
    return dict(parts=parts, ev=ev, equity=equity, per_share=equity / shares)


def sensitivity(rr: RunRate, base: Case, products_mults: list[float], foundry_mults: list[float],
                cash: float, debt: float, nci: float, shares: float,
                extra_claims: float = 0.0) -> pd.DataFrame:
    from dataclasses import replace
    grid = {}
    for fm in foundry_mults:
        grid[fm] = [value_case(rr, replace(base, products_ev_ebit=pm, foundry_ev_sales=fm),
                               cash, debt, nci, shares, extra_claims)["per_share"]
                    for pm in products_mults]
    return pd.DataFrame(grid, index=products_mults)