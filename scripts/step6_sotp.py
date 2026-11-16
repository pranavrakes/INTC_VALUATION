"""Step 6: sum-of-the-parts. Intel Products + Intel Foundry + All Other - corporate costs.

Run from PyCharm like step3-5. The bridge (cash, debt, NCI, shares) comes from the same
assumptions.yaml as the DCF; peer multiples from the same snapshot as step 5.

Every multiple below is a JUDGEMENT, set at the top of this file so you can change it and
defend it in the memo. Nothing is tuned to the share price.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src.data_loader import load_peer_snapshot                    # noqa: E402
from src.sotp import (Case, check_ties, load_segments, peer_ev_ebit,  # noqa: E402
                      run_rate, value_case)
from step3_dcf import build_inputs, load_assumptions              # noqa: E402

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)

SEGMENTS_CSV = ROOT / "data" / "manual" / "segments.csv"
FABLESS = ["AMD", "NVDA", "QCOM", "AVGO"]   # Products' economic peers (GAAP EV/EBIT, trailing)
FOUNDRY_PEER = "GFS"                         # TSM excluded: its snapshot row mixes currencies
CORP_MULTIPLE = 10.0                         # capitalise corporate costs at 10x (judgement)
OTHER_VS_PRODUCTS = 0.5                      # All Other (small, incl. Mobileye) at half Products' multiple
FOUNDRY_MID_DISCOUNT = 0.5                   # Foundry mid case = 50% of GFS EV/Sales (it loses money)
EQUITY_STAKES = 0.0                          # $m: Altera 49% stake etc. -- enter from the 10-K/10-Q


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--price", type=float, default=65.76)
    ap.add_argument("--period", default="9M-2026", help="period used for segment run-rate")
    ap.add_argument("--factor", type=float, default=4 / 3, help="annualisation factor (9M: 4/3, quarter: 4)")
    args = ap.parse_args()

    seg = load_segments(SEGMENTS_CSV)
    print("\nSegment sum checks (gaps should be 0):")
    for p in sorted(seg["period"].unique()):
        print("  ", check_ties(seg, p))

    snap = load_peer_snapshot()
    fab = peer_ev_ebit(snap, FABLESS)
    q = fab.quantile([0.25, 0.5, 0.75])
    gfs = snap.loc[FOUNDRY_PEER, "enterpriseValue"] / snap.loc[FOUNDRY_PEER, "totalRevenue"]

    # Corporate costs on the latest-quarter run-rate: the 9M figure includes large items to verify.
    rr = run_rate(seg, args.period, args.factor, corp_period="Q3-2026", corp_factor=4)
    rr9 = run_rate(seg, args.period, args.factor)
    inp = build_inputs(load_assumptions(), "base")
    bridge = dict(cash=inp.cash, debt=inp.debt, nci=inp.nci, shares=inp.shares,
                  extra_claims=inp.extra_claims)

    print(f"\nINTC SOTP  |  price {args.price:.2f}  |  $m except per share")
    print(f"Run-rate ({args.period} x {args.factor:.2f}): Products EBIT {rr.products_ebit:,.0f}, "
          f"Foundry EBIT {rr.foundry_ebit:,.0f} on revenue {rr.foundry_rev:,.0f} (mostly internal), "
          f"All Other EBIT {rr.other_ebit:,.0f}")
    print(f"Corporate unallocated + eliminations: {rr.corp_ebit:,.0f} (Q3 x4); "
          f"{rr9.corp_ebit:,.0f} on the {args.period} basis")
    print(f"Fabless EV/EBIT ({', '.join(fab.index)}): "
          + ", ".join(f"{t} {m:.1f}x" for t, m in fab.items())
          + f"  | p25 {q[.25]:.1f}x, median {q[.5]:.1f}x, p75 {q[.75]:.1f}x")
    print(f"Foundry peer {FOUNDRY_PEER} EV/Sales: {gfs:.1f}x")

    cases = [
        Case("Low", q[.25], 0.0, q[.25] * OTHER_VS_PRODUCTS, CORP_MULTIPLE, 0.0, EQUITY_STAKES),
        Case("Mid", q[.5], gfs * FOUNDRY_MID_DISCOUNT, q[.5] * OTHER_VS_PRODUCTS, CORP_MULTIPLE, 0.0, EQUITY_STAKES),
        Case("High", q[.75], gfs, q[.75] * OTHER_VS_PRODUCTS, CORP_MULTIPLE, 0.0, EQUITY_STAKES),
        Case("Integrated", q[.5], 0.0, q[.5] * OTHER_VS_PRODUCTS, CORP_MULTIPLE, 1.0, EQUITY_STAKES),
    ]
    rows = {}
    for c in cases:
        r = value_case(rr, c, **bridge)
        rows[c.name] = {**r["parts"], "EV": r["ev"], "equity": r["equity"],
                        "per_share": r["per_share"], "vs_price": r["per_share"] / args.price - 1}
    table = pd.DataFrame(rows).T
    print("\nSOTP by case (Integrated = Products carries 100% of Foundry's loss, Foundry given no value):")
    print(table.round(2).to_string())

    # The key judgement: how much of Foundry's loss is really Products' wafer cost?
    mults = [20.0, round(q[.5], 1), 30.0]
    grid = {}
    for m in mults:
        grid[f"{m:.1f}x"] = [
            value_case(rr, replace(cases[1], products_ev_ebit=m, foundry_loss_burden=b), **bridge)["per_share"]
            for b in (0.0, 0.25, 0.5, 0.75, 1.0)]
    sens = pd.DataFrame(grid, index=["0%", "25%", "50%", "75%", "100%"])
    sens.index.name = "Foundry loss charged to Products"
    print("\nValue per share: share of Foundry loss charged to Products (rows) x Products EV/EBIT (cols), "
          "Foundry at mid multiple:")
    print(sens.round(1).to_string())

    out = ROOT / "outputs"
    out.mkdir(exist_ok=True)
    table.to_csv(out / "sotp_cases.csv")
    sens.to_csv(out / "sotp_burden_sensitivity.csv")
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()