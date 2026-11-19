import numpy as np
import pandas as pd
import pytest

from src.football_field import build_rows, plot_football_field


def inputs():
    dcf = pd.DataFrame({"scenario": ["bear", "base", "bull"], "per_share": [1.0, 18.0, 34.0]})
    mc = np.arange(1, 101, dtype=float)
    comps = pd.DataFrame({"low": [60, 45, 140], "median": [150, 85, 260], "high": [190, 100, 320]},
                         index=["EV/Sales", "EV/EBITDA", "P/B"])
    sotp = pd.DataFrame({"per_share": [75, 85, 107, 38]}, index=["Low", "Mid", "High", "Integrated"])
    return dcf, mc, comps, sotp


def test_rows_order_and_values():
    df = build_rows(*inputs())
    assert list(df["method"])[0].startswith("DCF") and list(df["method"])[-1].startswith("SOTP")
    assert len(df) == 5                                       # P/B excluded by default
    dcf_row = df.iloc[0]
    assert (dcf_row["low"], dcf_row["mid"], dcf_row["high"]) == (1.0, 18.0, 34.0)
    sotp_row = df.iloc[-1]
    assert (sotp_row["low"], sotp_row["mid"], sotp_row["high"]) == (38, 85, 107)   # min, Mid, max
    mc_row = df.iloc[1]
    assert mc_row["low"] == pytest.approx(10.9) and mc_row["high"] == pytest.approx(90.1)


def test_include_pb_adds_a_row():
    assert len(build_rows(*inputs(), include_pb=True)) == 6


def test_negative_low_is_floored_at_zero():
    dcf, mc, comps, sotp = inputs()
    dcf.loc[0, "per_share"] = -4.0
    assert build_rows(dcf, mc, comps, sotp).iloc[0]["low"] == 0.0


def test_inverted_range_rejected():
    dcf, mc, comps, sotp = inputs()
    comps.loc["EV/EBITDA", "low"] = 120
    with pytest.raises(ValueError):
        build_rows(dcf, mc, comps, sotp)


def test_plot_writes_a_file(tmp_path):
    out = tmp_path / "ff.png"
    plot_football_field(build_rows(*inputs()), 65.76, out)
    assert out.exists() and out.stat().st_size > 5_000