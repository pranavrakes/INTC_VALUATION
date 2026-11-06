"""
data_loader.py -- data ingestion for the INTC valuation project.

Sources
-------
* SEC EDGAR XBRL "companyfacts" API  -> annual financials, balance sheet, share count
* yfinance                           -> price history, peer multiple snapshot
* FRED (public CSV endpoint)         -> 10-year Treasury yield (risk-free rate)

Files land in data/raw/ (cached) and data/processed/ (clean CSVs).

Setup
-----
SEC requires a descriptive User-Agent with contact info:

    export SEC_USER_AGENT="Your Name your.email@example.com"

Usage
-----
    python src/data_loader.py            # pull everything
    python src/data_loader.py --refresh  # ignore cache, re-download
"""
from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
MANUAL = ROOT / "data" / "manual"
for p in (RAW, PROCESSED, MANUAL):
    p.mkdir(parents=True, exist_ok=True)

INTC_CIK = "0000050863"
SEC_FACTS_URL = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{INTC_CIK}.json"
FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
PEERS = ["AMD", "NVDA", "TSM", "QCOM", "AVGO", "TXN", "MU", "GFS"]

# XBRL tag names vary across filings/years; try each in order, first hit wins.
FLOW_TAGS = {
    "revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"],
    "gross_profit": ["GrossProfit"],
    "operating_income": ["OperatingIncomeLoss"],
    "net_income": ["NetIncomeLoss"],
    "depreciation": ["Depreciation"],
    "amortization": ["AmortizationOfIntangibleAssets"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],  # gross, not netted
    "cfo": ["NetCashProvidedByUsedInOperatingActivities"],
    "rd_expense": ["ResearchAndDevelopmentExpense"],
    "interest_expense": ["InterestExpense", "InterestExpenseNonoperating"],
    "income_tax": ["IncomeTaxExpenseBenefit"],
}
INSTANT_TAGS = {
    "cash": ["CashAndCashEquivalentsAtCarryingValue"],
    "short_term_investments": ["ShortTermInvestments"],
    "debt_current": ["DebtCurrent", "LongTermDebtCurrent"],
    "debt_long_term": ["LongTermDebtNoncurrent", "LongTermDebt"],
    "total_equity": ["StockholdersEquity"],
    "afs_investments": ["AvailableForSaleSecuritiesDebtSecuritiesCurrent"],
    "trading_assets": ["TradingSecuritiesCurrent", "TradingSecurities"],
    "noncontrolling_interest": ["MinorityInterest"],
}


def _sec_headers() -> dict:
    ua = os.environ.get("SEC_USER_AGENT")
    if not ua:
        raise EnvironmentError("Set SEC_USER_AGENT='Your Name your@email.com' before running.")
    return {"User-Agent": ua}


def get_sec_facts(refresh: bool = False) -> dict:
    cache = RAW / "sec_companyfacts.json"
    if not refresh and cache.exists():
        return json.loads(cache.read_text())
    resp = requests.get(SEC_FACTS_URL, headers=_sec_headers(), timeout=60)
    resp.raise_for_status()
    cache.write_text(resp.text)
    return resp.json()


def _series_from_tags(facts: dict, tags: list[str], unit: str, instant: bool) -> pd.Series:
    """Pull one metric's time series from a list of candidate XBRL tags.

    instant=False: annual (~12mo) durations from 10-Ks, indexed by period end.
    instant=True:  point-in-time balance-sheet values from 10-Ks and 10-Qs.
    """
    combined = pd.Series(dtype="float64", index=pd.DatetimeIndex([]))
    for tag in tags:
        try:
            rows = facts["facts"]["us-gaap"][tag]["units"][unit]
        except KeyError:
            continue
        df = pd.DataFrame(rows)
        if df.empty:
            continue
        df["end"] = pd.to_datetime(df["end"])
        df["filed"] = pd.to_datetime(df["filed"])
        if instant:
            df = df[df["form"].isin(["10-K", "10-K/A", "10-Q"])]
            if "start" in df:
                df = df[df["start"].isna()]
        else:
            if "start" not in df:
                continue
            df["start"] = pd.to_datetime(df["start"])
            days = (df["end"] - df["start"]).dt.days
            df = df[df["form"].isin(["10-K", "10-K/A"]) & days.between(350, 380)]
        if df.empty:
            continue
        s = df.sort_values("filed").drop_duplicates("end", keep="last").set_index("end")["val"]
        combined = combined.combine_first(s)  # earlier tags in the list win on overlap
    return combined.sort_index()


def load_financials(refresh: bool = False, min_year: int = 2013) -> pd.DataFrame:
    """One row per fiscal year: income statement, cash flow, balance sheet, plus derived FCF/net debt."""
    facts = get_sec_facts(refresh)
    cols = {name: _series_from_tags(facts, tags, "USD", instant=False) for name, tags in FLOW_TAGS.items()}
    cols.update({name: _series_from_tags(facts, tags, "USD", instant=True) for name, tags in INSTANT_TAGS.items()})

    df = pd.DataFrame(cols).sort_index()
    df.index = pd.to_datetime(df.index)
    df = df[df.index.year >= min_year].dropna(subset=["revenue"])
    df.index.name = "fiscal_year_end"

    df["d_and_a"] = df["depreciation"].fillna(0) + df["amortization"].fillna(0)
    df["operating_margin"] = df["operating_income"] / df["revenue"]
    df["capex_pct_revenue"] = df["capex"] / df["revenue"]
    df["fcf"] = df["cfo"] - df["capex"]
    df["net_debt"] = (df["debt_current"].fillna(0) + df["debt_long_term"].fillna(0)
                      - df["cash"].fillna(0) - df["short_term_investments"].fillna(0)
                      - df["afs_investments"].fillna(0) - df["trading_assets"].fillna(0))
    df.to_csv(PROCESSED / "financials_annual.csv")
    return df


def load_balance_sheet_latest(refresh: bool = False) -> pd.Series:
    """Most recent balance sheet items. Drops any item whose latest value is >120 days
    older than the newest item."""
    facts = get_sec_facts(refresh)
    latest = {}
    for name, tags in INSTANT_TAGS.items():
        s = _series_from_tags(facts, tags, "USD", instant=True)
        if not s.empty:
            latest[name] = (s.index[-1], s.iloc[-1])
    newest = max(d for d, _ in latest.values())
    out = {n: v for n, (d, v) in latest.items() if (newest - d).days < 120}
    return pd.Series(out, name="latest_balance_sheet")


def load_share_count(refresh: bool = False) -> dict:
    """Latest cover-page shares outstanding. Cross-check against the latest 10-Q/8-K by hand --
    Intel's share count has moved a lot recently."""
    facts = get_sec_facts(refresh)
    rows = facts["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"]
    df = pd.DataFrame(rows)
    df["end"] = pd.to_datetime(df["end"])
    df["filed"] = pd.to_datetime(df["filed"])
    latest = df.sort_values(["end", "filed"]).iloc[-1]
    return {
        "shares_outstanding": float(latest["val"]),
        "cover_page_date": latest["end"].date().isoformat(),
        "form": latest["form"],
    }


def load_prices(ticker: str = "INTC", start: str = "2013-01-01", refresh: bool = False) -> pd.DataFrame:
    import yfinance as yf
    cache = RAW / f"prices_{ticker}.csv"
    if not refresh and cache.exists():
        return pd.read_csv(cache, index_col=0, parse_dates=True)
    df = yf.Ticker(ticker).history(start=start, auto_adjust=True)
    if df.empty:
        raise ValueError(f"No price data for {ticker}.")
    df.index = df.index.tz_localize(None)
    df.to_csv(cache)
    return df


def load_peer_snapshot(tickers: list[str] | None = None, refresh: bool = False) -> pd.DataFrame:
    """Current multiples for INTC + peers via yfinance .info. Scraped data -- spot-check before use,
    especially for foreign filers like TSM."""
    import yfinance as yf
    tickers = ["INTC"] + (tickers or PEERS)
    cache = RAW / "peer_snapshot.csv"
    if not refresh and cache.exists():
        return pd.read_csv(cache, index_col=0)

    fields = ["marketCap", "enterpriseValue", "totalRevenue", "ebitda", "operatingMargins",
              "priceToBook", "trailingPE", "beta", "totalDebt", "totalCash"]
    rows = {}
    for t in tickers:
        try:
            info = yf.Ticker(t).info
        except Exception as exc:
            print(f"[warn] {t}: {exc}")
            info = {}
        rows[t] = {f: info.get(f) for f in fields}

    df = pd.DataFrame(rows).T.apply(pd.to_numeric, errors="coerce")
    df["ev_to_sales"] = df["enterpriseValue"] / df["totalRevenue"]
    df["ev_to_ebitda"] = df["enterpriseValue"] / df["ebitda"].where(df["ebitda"] > 0)
    df.index.name = "ticker"
    df.to_csv(cache)
    return df


def load_risk_free(series: str = "DGS10", refresh: bool = False) -> dict:
    """Latest 10Y Treasury yield from FRED's public CSV endpoint (no API key needed)."""
    cache = RAW / f"fred_{series}.csv"
    if refresh or not cache.exists():
        resp = requests.get(FRED_CSV_URL.format(series=series), timeout=30)
        resp.raise_for_status()
        cache.write_text(resp.text)
    df = pd.read_csv(io.StringIO(cache.read_text()))
    df.columns = ["date", "value"]
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    last = df.dropna().iloc[-1]
    return {"rate": float(last["value"]) / 100, "date": str(last["date"]), "series": series}


def write_segments_template() -> Path:
    """Segment (Products/Foundry) data isn't in the XBRL API -- enter it by hand from the
    10-K segment note into this CSV, in USD millions."""
    path = MANUAL / "segments.csv"
    if not path.exists():
        cols = ["fiscal_year", "segment", "revenue", "operating_income", "source_note"]
        rows = [(None, seg, None, None, "") for seg in ("Intel Products", "Intel Foundry", "All Other")]
        pd.DataFrame(rows, columns=cols).to_csv(path, index=False)
    return path


def build_all(refresh: bool = False) -> None:
    fin = load_financials(refresh)
    print(f"Financials: {len(fin)} fiscal years, {fin.index.min().date()} -> {fin.index.max().date()}")

    sh = load_share_count()
    print(f"Shares outstanding: {sh['shares_outstanding']:,.0f} as of {sh['cover_page_date']} "
          "-- verify against latest 10-Q/8-K")

    px = load_prices(refresh=refresh)
    print(f"INTC last close: {px['Close'].iloc[-1]:.2f} on {px.index.max().date()}")

    load_peer_snapshot(refresh=refresh)
    rf = load_risk_free(refresh=refresh)
    print(f"10Y UST: {rf['rate']:.2%} on {rf['date']}")

    seg_path = write_segments_template()
    print(f"Segment template at {seg_path} -- fill in by hand from the 10-K")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pull data for the INTC valuation project.")
    parser.add_argument("--refresh", action="store_true")
    build_all(parser.parse_args().refresh)