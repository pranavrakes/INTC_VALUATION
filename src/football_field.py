"""Football field: value-per-share ranges from every method against the market price.

build_rows() turns the CSVs the step scripts already write into one tidy table; plot_football_field()
draws it. Place in src/football_field.py.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

COLUMNS = ["method", "low", "mid", "high", "kind"]
KIND_COLOURS = {"intrinsic": "#4C78A8", "relative": "#F58518", "mixed": "#54A24B"}
KIND_LABELS = {"intrinsic": "Intrinsic (cash flows)", "relative": "Relative (peer multiples)",
               "mixed": "Sum of the parts"}


def build_rows(dcf: pd.DataFrame, mc_values, comps: pd.DataFrame, sotp: pd.DataFrame,
               include_pb: bool = False) -> pd.DataFrame:
    """One row per method: low / mid / high per share.

    dcf   : outputs/dcf_scenarios.csv   (columns scenario, per_share)
    mc    : outputs/mc_values.csv       (one value per Monte Carlo draw)
    comps : outputs/comps_implied.csv   (index EV/Sales, EV/EBITDA, P/B; columns low, median, high)
    sotp  : outputs/sotp_cases.csv      (index Low, Mid, High, Integrated; column per_share)
    """
    d = dcf.set_index("scenario")["per_share"]
    v = np.asarray(mc_values, dtype=float)
    rows = [
        ("DCF: bear to bull", d["bear"], d["base"], d["bull"], "intrinsic"),
        ("Monte Carlo: 10th-90th percentile", *np.percentile(v, [10, 50, 90]), "intrinsic"),
    ]
    comps_rows = [("EV/EBITDA", "Comps: EV/EBITDA (peer 25th-75th pct)"),
                  ("EV/Sales", "Comps: EV/Sales (peer 25th-75th pct)")]
    if include_pb:
        comps_rows.append(("P/B", "Comps: P/B (peer 25th-75th pct)"))
    for key, label in comps_rows:
        r = comps.loc[key]
        rows.append((label, r["low"], r["median"], r["high"], "relative"))
    ps = sotp["per_share"]
    rows.append(("SOTP: integrated to high", ps.min(), sotp.loc["Mid", "per_share"], ps.max(), "mixed"))

    df = pd.DataFrame(rows, columns=COLUMNS)
    df[["low", "mid", "high"]] = df[["low", "mid", "high"]].astype(float)
    bad = df[~((df["low"] <= df["mid"]) & (df["mid"] <= df["high"]))]
    if len(bad):
        raise ValueError(f"low <= mid <= high violated for: {list(bad['method'])}")
    df["low"] = df["low"].clip(lower=0.0)       # equity cannot be worth less than zero
    return df


def plot_football_field(df: pd.DataFrame, price: float, path, excluded_note: str | None = None) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    fig, ax = plt.subplots(figsize=(10, 4.8))
    n = len(df)
    xmax = max(df["high"].max(), price) * 1.12
    for i, r in enumerate(df.itertuples()):
        ax.barh(i, r.high - r.low, left=r.low, height=0.5, color=KIND_COLOURS[r.kind])
        ax.plot([r.mid, r.mid], [i - 0.25, i + 0.25], color="black", lw=2)
        if r.low < xmax * 0.015:    # bar starts at ~zero: put its low label inside the bar
            ax.text(r.low + xmax * 0.008, i, f"{r.low:,.0f}", ha="left", va="center",
                    fontsize=9, color="white")
        else:
            ax.text(r.low - xmax * 0.008, i, f"{r.low:,.0f}", ha="right", va="center", fontsize=9)
        ax.text(r.high + xmax * 0.008, i, f"{r.high:,.0f}", ha="left", va="center", fontsize=9)
    ax.axvline(price, color="#D62728", lw=2)
    ax.text(price, -0.72, f"Price {price:.2f}", color="#D62728", ha="center", va="center", fontsize=10,
            bbox=dict(facecolor="white", edgecolor="none", pad=2), zorder=5)
    ax.set_yticks(range(n))
    ax.set_yticklabels(df["method"], fontsize=10)
    ax.invert_yaxis()
    ax.set_xlim(0, xmax)
    ax.set_ylim(n - 0.5, -1.0)
    ax.set_xlabel("Value per share ($).  Black tick = base / median / mid case")
    ax.set_title("INTC value per share by method", loc="left", fontsize=12)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(handles=[Patch(color=KIND_COLOURS[k], label=KIND_LABELS[k])
                       for k in KIND_COLOURS if k in set(df["kind"])],
              loc="upper right", frameon=False, fontsize=9)
    if excluded_note:
        fig.text(0.01, 0.01, excluded_note, fontsize=8, color="#555555", ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, dpi=150)
    plt.close(fig)