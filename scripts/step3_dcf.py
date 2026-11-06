import argparse
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")                       # never block on a window
import matplotlib.pyplot as plt
import pandas as pd
import yaml

from src.dcf import DCFInputs, run_dcf, sensitivity_grid

OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)


def load_assumptions(path=ROOT / "config" / "assumptions.yaml"):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_inputs(cfg: dict, scenario: str) -> DCFInputs:
    s, b = cfg["scenarios"][scenario], cfg["bridge"]
    return DCFInputs(
        revenue0=cfg["revenue0"], growth=s["growth"], ebit_margin=s["ebit_margin"],
        tax_rate=cfg["tax_rate"], da_pct=s["da_pct"], capex_pct=s["capex_pct"],
        nwc_pct_of_delta_rev=cfg["nwc_pct_of_delta_rev"], wacc=cfg["wacc"],
        terminal_growth=s["terminal_growth"],
        cash=b["cash"] + b["short_term_investments"], debt=b["debt"], nci=b["nci"],
        shares=cfg["shares"])


def run_scenario(cfg, scenario):
    return run_dcf(build_inputs(cfg, scenario))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--price", type=float, default=65.76, help="current INTC price")
    args = ap.parse_args()
    cfg = load_assumptions()
    price = args.price

    # 1. Scenarios
    rows, results = [], {}
    for name in ("bear", "base", "bull"):
        r = run_scenario(cfg, name)
        results[name] = r
        rows.append(dict(scenario=name, ev=r.enterprise_value, equity=r.equity_value,
                         per_share=r.per_share, vs_price=r.per_share / price - 1,
                         tv_share_of_ev=r.tv_share_of_ev,
                         fcf_y1=r.years[0]["fcf"], fcf_final=r.years[-1]["fcf"]))
    sc = pd.DataFrame(rows).set_index("scenario")
    sc.to_csv(OUT / "dcf_scenarios.csv")
    print(f"\nINTC DCF  |  price {price:.2f}  |  WACC {cfg['wacc']:.1%}  |  $m except per share")
    print(sc.round({"ev": 0, "equity": 0, "per_share": 2, "vs_price": 3,
                    "tv_share_of_ev": 3, "fcf_y1": 0, "fcf_final": 0}).to_string())

    base = results["base"]
    print("\nBase-case forecast ($m):")
    print(pd.DataFrame(base.years)[["year", "revenue", "ebit", "ebitda", "capex", "fcf"]]
          .round(0).to_string(index=False))

    # 2. WACC x terminal growth grid (base)
    base_in = build_inputs(cfg, "base")
    waccs = [0.100, 0.105, 0.110, 0.115, 0.120, 0.125, 0.130, 0.135]
    gs = [0.015, 0.020, 0.025, 0.030, 0.035]
    grid = sensitivity_grid(base_in, waccs, gs)
    gdf = pd.DataFrame(grid, index=[f"{w:.1%}" for w in waccs], columns=[f"{g:.1%}" for g in gs])
    gdf.index.name = "WACC \\ g"
    gdf.to_csv(OUT / "dcf_sensitivity_base.csv")
    print("\nBase per-share value, WACC (rows) x terminal growth (cols):")
    print(gdf.round(1).to_string())

    # 3. Tornado (base): low/high per driver
    capex_base = base_in.capex_pct
    def val(inp):
        return run_dcf(inp).per_share
    mid = val(base_in)
    shift = lambda xs, d: [x + d for x in xs]
    tests = {
        "WACC +/-1.5pt":            (replace(base_in, wacc=base_in.wacc + .015), replace(base_in, wacc=base_in.wacc - .015), None, None),
        "Terminal growth +/-0.5pt": (replace(base_in, terminal_growth=base_in.terminal_growth - .005), replace(base_in, terminal_growth=base_in.terminal_growth + .005), None, None),
        "EBIT margin +/-3pt":       (replace(base_in, ebit_margin=shift(base_in.ebit_margin, -.03)), replace(base_in, ebit_margin=shift(base_in.ebit_margin, .03)), None, None),
        "Revenue growth +/-2pt":    (replace(base_in, growth=shift(base_in.growth, -.02)), replace(base_in, growth=shift(base_in.growth, .02)), None, None),
        "Capex % rev -/+2pt":       (replace(base_in, capex_pct=shift(capex_base, .02)), replace(base_in, capex_pct=shift(capex_base, -.02)), None, None),
        "Cash tax +/-5pt":          (replace(base_in, tax_rate=base_in.tax_rate + .05), replace(base_in, tax_rate=base_in.tax_rate - .05), None, None),
        "NCI x2 / x0.5":            (replace(base_in, nci=base_in.nci * 2), replace(base_in, nci=base_in.nci * .5), None, None),
    }
    trows = []
    for k, (lo_in, hi_in, _, _) in tests.items():
        lo, hi = val(lo_in), val(hi_in)
        trows.append(dict(driver=k, low=lo, high=hi, swing=abs(hi - lo)))
    t = pd.DataFrame(trows).sort_values("swing").set_index("driver")
    t.to_csv(OUT / "dcf_tornado.csv")
    print(f"\nTornado (base {mid:.2f}/share):")
    print(t.sort_values("swing", ascending=False).round(2).to_string())

    # 4. Charts
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for i, (d, r) in enumerate(t.iterrows()):
        ax.barh(i, r["low"] - mid, left=mid, color="#c0504d")
        ax.barh(i, r["high"] - mid, left=mid, color="#4f81bd")
    ax.set_yticks(range(len(t)), t.index)
    ax.axvline(mid, color="k", lw=1)
    ax.axvline(price, color="gray", ls="--", lw=1, label=f"price {price:.2f}")
    ax.set_xlabel("Value per share ($)")
    ax.set_title(f"INTC base-case DCF sensitivity (base {mid:.2f})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "dcf_tornado.png", dpi=150)
    plt.close(fig)
    print(f"\nSaved to {OUT}")


if __name__ == "__main__":
    main()