from __future__ import annotations

import numpy as np
import pandas as pd

MULTIPLES = {
    "ev_to_sales": "EV/Sales",
    "ev_to_ebitda": "EV/EBITDA",
    "price_to_book": "P/B",
}
EV_MCAP_BOUNDS = (0.5, 2.0)   # EV/market cap outside this band => mixed currencies or bad scrape


def add_multiples(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ev_to_sales"] = out["enterpriseValue"] / out["totalRevenue"]
    out["ev_to_ebitda"] = out["enterpriseValue"] / out["ebitda"].where(out["ebitda"] > 0)
    out["price_to_book"] = out["priceToBook"].where(out["priceToBook"] > 0)
    out["ev_to_mcap"] = out["enterpriseValue"] / out["marketCap"]
    return out


def screen_peers(df: pd.DataFrame, target: str = "INTC") -> tuple[pd.DataFrame, dict[str, str]]:
    """Drop the target and any peer whose data fails basic consistency checks.

    Returns (clean peers, {ticker: reason}).
    """
    df = add_multiples(df)
    excluded: dict[str, str] = {}
    keep = []
    lo, hi = EV_MCAP_BOUNDS
    for t, r in df.drop(index=target, errors="ignore").iterrows():
        if pd.isna(r["enterpriseValue"]) or pd.isna(r["marketCap"]) or pd.isna(r["totalRevenue"]):
            excluded[t] = "missing EV, market cap or revenue"
        elif not lo <= r["ev_to_mcap"] <= hi:
            excluded[t] = (f"EV/market cap = {r['ev_to_mcap']:.1f}x: likely mixed currencies "
                           "(foreign filer) or bad scrape")
        else:
            keep.append(t)
    return df.loc[keep], excluded


def peer_stats(peers: pd.DataFrame) -> pd.DataFrame:
    """n, min, 25th pct, median, 75th pct, max for each multiple."""
    rows = {}
    for col, label in MULTIPLES.items():
        s = peers[col].dropna()
        rows[label] = dict(n=len(s), min=s.min(), p25=s.quantile(0.25), median=s.median(),
                           p75=s.quantile(0.75), max=s.max()) if len(s) else dict(n=0)
    return pd.DataFrame(rows).T


def implied_per_share(stats: pd.DataFrame, revenue: float, ebitda: float, book_equity: float,
                      cash: float, debt: float, nci: float, shares: float,
                      extra_claims: float = 0.0) -> pd.DataFrame:
    """Intel value per share at the peer 25th pct / median / 75th pct for each multiple ($m)."""
    metric = {"EV/Sales": revenue, "EV/EBITDA": ebitda, "P/B": book_equity}
    rows = {}
    for label, m in metric.items():
        row = {}
        for k, name in (("p25", "low"), ("median", "median"), ("p75", "high")):
            mult = stats.loc[label, k]
            if label == "P/B":
                equity = mult * m
            else:
                equity = mult * m + cash - debt - nci - extra_claims
            row[name] = equity / shares
        rows[label] = row
    return pd.DataFrame(rows).T


def intel_vs_peers(df: pd.DataFrame, stats: pd.DataFrame, target: str = "INTC") -> pd.DataFrame:
    """Intel's own multiples against the peer median (premium > 0 means Intel is dearer)."""
    d = add_multiples(df).loc[target]
    rows = {}
    for col, label in MULTIPLES.items():
        med = stats.loc[label, "median"]
        rows[label] = dict(intel=d[col], peer_median=med, premium=d[col] / med - 1)
    return pd.DataFrame(rows).T


def margin_adjusted_ev_sales(peers: pd.DataFrame, intel_margin: float, min_n: int = 5) -> dict | None:
    """EV/Sales explained by operating margin (peers only). Indicative: tiny sample."""
    d = peers[["ev_to_sales", "operatingMargins"]].dropna()
    if len(d) < min_n:
        return None
    slope, intercept = np.polyfit(d["operatingMargins"], d["ev_to_sales"], 1)
    pred = intercept + slope * d["operatingMargins"]
    ss_res = float(((d["ev_to_sales"] - pred) ** 2).sum())
    ss_tot = float(((d["ev_to_sales"] - d["ev_to_sales"].mean()) ** 2).sum())
    return dict(n=len(d), slope=slope, intercept=intercept,
                r2=1 - ss_res / ss_tot if ss_tot else float("nan"),
                implied_multiple=intercept + slope * intel_margin)