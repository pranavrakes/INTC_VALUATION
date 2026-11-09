"""Step 4: reverse DCF. What do you have to believe to justify the market price?

Run from PyCharm like step3. Needs step3_dcf.py to keep its work under
`if __name__ == "__main__":` (otherwise importing it re-runs step 3).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src.dcf import run_dcf                                   # noqa: E402
from src.reverse_dcf import (frontier, solve_revenue_cagr,   # noqa: E402
                             solve_terminal_margin, solve_wacc, summarise)
from step3_dcf import build_inputs, load_assumptions         # noqa: E402

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--price", type=float, default=65.76, help="market price per share")
    args = ap.parse_args()
    price = args.price

    cfg = load_assumptions()
    out_dir = ROOT / "outputs"
    out_dir.mkdir(exist_ok=True)

    rows = []
    for sc in ("bear", "base", "bull"):
        inp = build_inputs(cfg, sc)
        cur = summarise(inp)
        rows.append(dict(scenario=sc, solve="as modelled", value=None, per_share=cur["per_share"],
                         rev_cagr=cur["rev_cagr"], rev_final=cur["rev_final"],
                         ebit_margin_final=cur["ebit_margin_final"], ebit_final=cur["ebit_final"]))

        r = solve_revenue_cagr(inp, price)
        rows.append(dict(scenario=sc, solve="revenue CAGR to hit price", value=None if r is None else r["rev_cagr"],
                         per_share=price if r else None,
                         rev_cagr=None if r is None else r["rev_cagr"],
                         rev_final=None if r is None else r["rev_final"],
                         ebit_margin_final=None if r is None else r["ebit_margin_final"],
                         ebit_final=None if r is None else r["ebit_final"]))

        r = solve_terminal_margin(inp, price)
        rows.append(dict(scenario=sc, solve="final-yr EBIT margin to hit price",
                         value=None if r is None else r["ebit_margin_final"],
                         per_share=price if r else None,
                         rev_cagr=None if r is None else r["rev_cagr"],
                         rev_final=None if r is None else r["rev_final"],
                         ebit_margin_final=None if r is None else r["ebit_margin_final"],
                         ebit_final=None if r is None else r["ebit_final"]))

        w = solve_wacc(inp, price)
        rows.append(dict(scenario=sc, solve=f"WACC to hit price (model {inp.wacc:.1%})", value=w,
                         per_share=price if w else None, rev_cagr=cur["rev_cagr"],
                         rev_final=cur["rev_final"], ebit_margin_final=cur["ebit_margin_final"],
                         ebit_final=cur["ebit_final"]))

    df = pd.DataFrame(rows)
    print(f"\nINTC reverse DCF  |  target price {price:.2f}  |  $m except per share")
    print("(None = no solution inside the search bounds)\n")
    fmt = df.copy()
    for c in ("value", "rev_cagr", "ebit_margin_final"):
        fmt[c] = fmt[c].map(lambda x: "n/a" if x is None or x != x else f"{x:.1%}")
    for c in ("rev_final", "ebit_final"):
        fmt[c] = fmt[c].map(lambda x: "n/a" if x is None or x != x else f"{x:,.0f}")
    fmt["per_share"] = fmt["per_share"].map(lambda x: "n/a" if x is None or x != x else f"{x:.2f}")
    print(fmt.to_string(index=False))

    base = build_inputs(cfg, "base")
    fr = pd.DataFrame(frontier(base, price, [0.05, 0.08, 0.10, 0.12, 0.15, 0.20, 0.25]))
    print("\nBase case: final-year EBIT margin needed for each revenue CAGR (margin ramps linearly from year 1)")
    fr_fmt = fr.copy()
    fr_fmt["rev_cagr"] = fr_fmt["rev_cagr"].map(lambda x: f"{x:.0%}")
    fr_fmt["rev_final"] = fr_fmt["rev_final"].map(lambda x: f"{x:,.0f}")
    fr_fmt["margin_needed"] = fr_fmt["margin_needed"].map(lambda x: "none <=80%" if pd.isna(x) else f"{x:.1%}")
    fr_fmt["ebit_final"] = fr_fmt["ebit_final"].map(lambda x: "n/a" if pd.isna(x) else f"{x:,.0f}")
    print(fr_fmt.to_string(index=False))

    df.to_csv(out_dir / "reverse_dcf.csv", index=False)
    fr.to_csv(out_dir / "reverse_dcf_frontier.csv", index=False)
    print(f"\nSaved to {out_dir}")


if __name__ == "__main__":
    main()