from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src.comps import (implied_per_share, intel_vs_peers,        # noqa: E402
                       margin_adjusted_ev_sales, peer_stats, screen_peers)
from src.data_loader import load_peer_snapshot                    # noqa: E402
from step3_dcf import build_inputs, load_assumptions              # noqa: E402

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)
M = 1e6   # snapshot is in dollars; the model is in $m


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-pull the peer snapshot from yfinance")
    ap.add_argument("--price", type=float, default=65.76)
    args = ap.parse_args()

    snap = load_peer_snapshot(refresh=args.refresh)
    peers, excluded = screen_peers(snap)
    stats = peer_stats(peers)

    inp = build_inputs(load_assumptions(), "base")       # bridge only; scenario does not matter
    intel = snap.loc["INTC"]
    revenue, ebitda = intel["totalRevenue"] / M, intel["ebitda"] / M
    book_equity = intel["marketCap"] / intel["priceToBook"] / M

    print(f"\nINTC comps  |  price {args.price:.2f}  |  $m except per share  |  trailing figures (yfinance)")
    print(f"Peers used ({len(peers)}): {', '.join(peers.index)}")
    for t, why in excluded.items():
        print(f"Excluded {t}: {why}")

    print("\nPeer multiples:")
    cols = ["marketCap", "ev_to_sales", "ev_to_ebitda", "price_to_book", "operatingMargins"]
    show = peers[cols].copy()
    show["marketCap"] = (show["marketCap"] / 1e9).round(0)
    print(show.rename(columns={"marketCap": "mcap_$bn"}).round(2).to_string())

    print("\nPeer statistics:")
    print(stats.round(2).to_string())

    print("\nIntel vs peer median:")
    print(intel_vs_peers(snap, stats).round(2).to_string())

    implied = implied_per_share(stats, revenue, ebitda, book_equity,
                                cash=inp.cash, debt=inp.debt, nci=inp.nci, shares=inp.shares,
                                extra_claims=inp.extra_claims)
    implied["vs_price_median"] = implied["median"] / args.price - 1
    print(f"\nImplied INTC value per share at peer multiples "
          f"(bridge: cash {inp.cash:,.0f}, debt {inp.debt:,.0f}, NCI {inp.nci:,.0f}, shares {inp.shares:,.0f}m):")
    print(implied.round(2).to_string())

    adj = margin_adjusted_ev_sales(peers, intel["operatingMargins"])
    if adj:
        ev = adj["implied_multiple"] * revenue
        eq = ev + inp.cash - inp.debt - inp.nci - inp.extra_claims
        print(f"\nMargin-adjusted EV/Sales (indicative, n={adj['n']}, R2={adj['r2']:.2f}): "
              f"Intel at {intel['operatingMargins']:.1%} margin -> {adj['implied_multiple']:.1f}x "
              f"-> {eq / inp.shares:.2f} per share")

    out = ROOT / "outputs"
    out.mkdir(exist_ok=True)
    stats.to_csv(out / "comps_peer_stats.csv")
    implied.to_csv(out / "comps_implied.csv")
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()