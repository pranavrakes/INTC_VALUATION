import pandas as pd
import pytest

from src.comps import (add_multiples, implied_per_share, intel_vs_peers,
                       margin_adjusted_ev_sales, peer_stats, screen_peers)


def snapshot() -> pd.DataFrame:
    rows = {
        "INTC": dict(marketCap=300, enterpriseValue=330, totalRevenue=60, ebitda=20, priceToBook=3.0, operatingMargins=0.15),
        "A":    dict(marketCap=100, enterpriseValue=100, totalRevenue=10, ebitda=5, priceToBook=5.0, operatingMargins=0.30),
        "B":    dict(marketCap=200, enterpriseValue=210, totalRevenue=20, ebitda=10, priceToBook=8.0, operatingMargins=0.40),
        "C":    dict(marketCap=300, enterpriseValue=300, totalRevenue=20, ebitda=-1, priceToBook=9.0, operatingMargins=0.10),
        "FX":   dict(marketCap=100, enterpriseValue=900, totalRevenue=10, ebitda=5, priceToBook=70.0, operatingMargins=0.50),
        "D":    dict(marketCap=100, enterpriseValue=110, totalRevenue=10, ebitda=4, priceToBook=4.0, operatingMargins=0.20),
        "E":    dict(marketCap=150, enterpriseValue=150, totalRevenue=15, ebitda=6, priceToBook=6.0, operatingMargins=0.25),
    }
    return pd.DataFrame(rows).T.astype(float)


def test_negative_ebitda_gives_nan():
    assert pd.isna(add_multiples(snapshot()).loc["C", "ev_to_ebitda"])


def test_screen_excludes_target_and_currency_mismatch():
    peers, excluded = screen_peers(snapshot())
    assert "INTC" not in peers.index
    assert list(excluded) == ["FX"]
    assert set(peers.index) == {"A", "B", "C", "D", "E"}


def test_stats_and_implied_value():
    peers, _ = screen_peers(snapshot())
    stats = peer_stats(peers)
    assert stats.loc["EV/Sales", "median"] == pytest.approx(10.5)      # sorted: 10, 10, 10.5, 11, 15
    assert stats.loc["EV/EBITDA", "n"] == 4                            # C dropped
    out = implied_per_share(stats, revenue=60, ebitda=20, book_equity=100,
                            cash=50, debt=40, nci=10, shares=10)
    # EV 10.5 x 60 = 630; + 50 - 40 - 10 = 630 equity -> 63/share
    assert out.loc["EV/Sales", "median"] == pytest.approx(63.0)
    # P/B median 6.0 x 100 = 600 equity -> 60/share, bridge not applied
    assert out.loc["P/B", "median"] == pytest.approx(60.0)


def test_intel_premium_sign():
    peers, _ = screen_peers(snapshot())
    stats = peer_stats(peers)
    cmp_ = intel_vs_peers(snapshot(), stats)
    assert cmp_.loc["EV/Sales", "intel"] == pytest.approx(5.5)
    assert cmp_.loc["EV/Sales", "premium"] < 0


def test_margin_regression_needs_enough_peers():
    peers, _ = screen_peers(snapshot())
    assert margin_adjusted_ev_sales(peers.iloc[:3], 0.15) is None
    assert margin_adjusted_ev_sales(peers, 0.15) is not None