import pandas as pd
import pytest

from src.sotp import (CONSOL, CORP, ELIM, FOUNDRY, OTHER, PRODUCTS, Case, check_ties,
                      peer_ev_ebit, run_rate, sensitivity, value_case)


def seg() -> pd.DataFrame:
    rows = [
        ("P", PRODUCTS, 100, 30), ("P", FOUNDRY, 40, -10), ("P", OTHER, 10, 2),
        ("P", CORP, None, -6), ("P", ELIM, -45, 1), ("P", CONSOL, 105, 17),
    ]
    return pd.DataFrame(rows, columns=["period", "segment", "revenue", "operating_income"])


def test_ties_pass_and_fail():
    assert check_ties(seg(), "P") == dict(period="P", revenue_gap=0.0, op_income_gap=0.0)
    bad = seg()
    bad.loc[bad.segment == FOUNDRY, "operating_income"] = -11
    assert check_ties(bad, "P")["op_income_gap"] == -1.0


def test_run_rate_annualises_and_nets_eliminations_into_corporate():
    rr = run_rate(seg(), "P", 2.0)
    assert rr.products_ebit == 60 and rr.foundry_ebit == -20
    assert rr.corp_ebit == (-6 + 1) * 2


def test_value_case_hand_calc():
    rr = run_rate(seg(), "P", 1.0)
    c = Case("t", products_ev_ebit=10, foundry_ev_sales=2, other_ev_ebit=5, corp_multiple=8)
    r = value_case(rr, c, cash=50, debt=20, nci=10, shares=10)
    # 300 + 80 + 10 - 40 = 350 EV; equity 350 + 50 - 20 - 10 = 370 -> 37/share
    assert r["ev"] == pytest.approx(350)
    assert r["per_share"] == pytest.approx(37.0)


def test_foundry_loss_burden_reduces_products_value():
    rr = run_rate(seg(), "P", 1.0)
    base = Case("t", 10, 0, 0, 0)
    full = Case("t", 10, 0, 0, 0, foundry_loss_burden=1.0)
    a = value_case(rr, base, 0, 0, 0, 1)["ev"]
    b = value_case(rr, full, 0, 0, 0, 1)["ev"]
    assert a - b == pytest.approx(100)          # 10 of Foundry loss x 10x


def test_peer_ev_ebit_drops_negative_and_extreme():
    snap = pd.DataFrame({
        "enterpriseValue": [100, 100, 100, 1000],
        "totalRevenue": [10, 10, 10, 10],
        "operatingMargins": [0.5, -0.1, 0.01, 0.5],
    }, index=["A", "B", "C", "D"])
    out = peer_ev_ebit(snap, ["A", "B", "C", "D"], max_multiple=60)
    assert list(out.index) == ["A"]             # B negative EBIT, C = 1000x, D = 200x
    assert out["A"] == pytest.approx(20.0)


def test_sensitivity_monotonic():
    rr = run_rate(seg(), "P", 1.0)
    g = sensitivity(rr, Case("t", 10, 1, 0, 5), [10, 20], [0.0, 1.0], 0, 0, 0, 1)
    assert g.loc[20, 0.0] > g.loc[10, 0.0]
    assert g.loc[10, 1.0] > g.loc[10, 0.0]