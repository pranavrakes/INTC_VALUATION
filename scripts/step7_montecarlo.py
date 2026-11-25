from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402
import numpy as np                # noqa: E402
import pandas as pd               # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src.dcf import run_dcf                                           # noqa: E402
from src.montecarlo import MCSpec, rank_correlations, simulate, summarise  # noqa: E402
from step3_dcf import build_inputs, load_assumptions                  # noqa: E402

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--price", type=float, default=65.76)
    ap.add_argument("--n", type=int, default=20_000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    cfg = load_assumptions()
    inputs = {sc: build_inputs(cfg, sc) for sc in ("bear", "base", "bull")}
    det = {sc: run_dcf(i).per_share for sc, i in inputs.items()}
    spec = MCSpec(n=args.n, seed=args.seed)

    print(f"\nINTC Monte Carlo  |  {args.n:,} draws, seed {args.seed}  |  price {args.price:.2f}")
    print("Deterministic scenarios: " + ", ".join(f"{k} {v:.2f}" for k, v in det.items()))
    print("Driver spreads (1 sd): growth {:.1%}, terminal margin {:.1%}, capex {:.1%}, "
          "WACC {:.1%}, terminal growth {:.1%}".format(*spec.sd))

    # Main run: centred on base
    main_run = simulate(inputs["base"], spec)
    s = summarise(main_run["values"], args.price,
                  refs={"bear": det["bear"], "bull": det["bull"]})
    print("\nBase-centred distribution (value per share):")
    print("  " + "  ".join(f"{k} {s[k]:.1f}" for k in ("p5", "p10", "p25", "p50", "p75", "p90", "p95")))
    print(f"  mean {s['mean']:.1f}   max {s['max']:.1f}")
    print(f"  P(value > {args.price:.2f}) = {s['prob_above_price']:.2%}   "
          f"(price sits at the {s['price_percentile']:.1f}th percentile)")
    print(f"  P(value > bull deterministic {det['bull']:.1f}) = {s['prob_above_bull']:.1%}")

    print("\nWhat drives the spread (Spearman rank correlation with value per share):")
    rc = rank_correlations(main_run["shocks"], main_run["values"])
    print("  " + "  ".join(f"{k} {v:+.2f}" for k, v in sorted(rc.items(), key=lambda kv: -abs(kv[1]))))

    # Robustness: three centres x two spreads
    rows = {}
    for centre in ("bear", "base", "bull"):
        for label, k in (("1x spreads", 1.0), ("2x spreads (wide)", 2.0)):
            r = simulate(inputs[centre], spec.scaled(k))
            ss = summarise(r["values"], args.price)
            rows[(centre, label)] = dict(p10=ss["p10"], median=ss["p50"], p90=ss["p90"],
                                         prob_above_price=ss["prob_above_price"])
    rob = pd.DataFrame(rows).T
    rob.index.names = ["centre", "spreads"]
    rob["prob_above_price"] = rob["prob_above_price"].map(lambda x: f"{x:.2%}")
    print("\nRobustness: does the conclusion depend on where we centre and how wide we draw?")
    print(rob.round(1).to_string())

    out = ROOT / "outputs"
    out.mkdir(exist_ok=True)
    pd.Series(main_run["values"], name="value_per_share").to_csv(out / "mc_values.csv", index=False)
    rob.to_csv(out / "mc_robustness.csv")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    vals = main_run["values"]
    ax.hist(vals, bins=80, color="#4C78A8", alpha=0.85)
    ax.axvline(args.price, color="#D62728", lw=2, label=f"Price {args.price:.2f}")
    for sc, col in (("bear", "#7F7F7F"), ("base", "#2CA02C"), ("bull", "#7F7F7F")):
        ax.axvline(det[sc], color=col, lw=1.2, ls="--", label=f"{sc} DCF {det[sc]:.1f}")
    ax.set_xlabel("DCF value per share ($)")
    ax.set_ylabel("Draws")
    ax.set_title(f"INTC Monte Carlo (base-centred, n={args.n:,}): P(value > price) = {s['prob_above_price']:.2%}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "mc_hist.png", dpi=150)
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()