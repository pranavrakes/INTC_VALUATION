"""Step 8: football field. Reads the CSVs saved by steps 3, 5, 6 and 7 in outputs/.

Run steps 3, 5, 6 and 7 first (each saves its CSV). Nothing is recomputed here, so the chart
always shows exactly what those scripts printed.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.football_field import build_rows, plot_football_field   # noqa: E402

OUT = ROOT / "outputs"
NEEDS = {
    "dcf_scenarios.csv": "step3_dcf.py",
    "mc_values.csv": "step7_montecarlo.py",
    "comps_implied.csv": "step5_comps.py",
    "sotp_cases.csv": "step6_sotp.py",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--price", type=float, default=65.76)
    ap.add_argument("--include-pb", action="store_true", help="also show the P/B comps bar")
    args = ap.parse_args()

    missing = [f"{f} (run {s})" for f, s in NEEDS.items() if not (OUT / f).exists()]
    if missing:
        raise FileNotFoundError("Missing in outputs/: " + "; ".join(missing))

    df = build_rows(
        dcf=pd.read_csv(OUT / "dcf_scenarios.csv"),
        mc_values=pd.read_csv(OUT / "mc_values.csv")["value_per_share"],
        comps=pd.read_csv(OUT / "comps_implied.csv", index_col=0),
        sotp=pd.read_csv(OUT / "sotp_cases.csv", index_col=0),
        include_pb=args.include_pb,
    )

    print(f"\nINTC football field  |  price {args.price:.2f}  |  value per share")
    show = df.copy()
    show["mid_vs_price"] = (show["mid"] / args.price - 1).map(lambda x: f"{x:+.0%}")
    print(show.round(1).to_string(index=False))
    n_above = int((df["high"] > args.price).sum())
    print(f"\n{n_above} of {len(df)} ranges reach the market price at their high end; "
          f"{int((df['mid'] > args.price).sum())} have a mid point above it.")

    note = None if args.include_pb else "P/B comps (about 146-324 per share) excluded: least comparable. Use --include-pb to show."
    df.to_csv(OUT / "football_field.csv", index=False)
    plot_football_field(df, args.price, OUT / "football_field.png", excluded_note=note)
    print(f"\nSaved football_field.csv and football_field.png to {OUT}")


if __name__ == "__main__":
    main()