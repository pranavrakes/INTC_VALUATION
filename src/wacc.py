import numpy as np
import pandas as pd

def paired_returns(asset_close: pd.Series, bench_close: pd.Series,
                   freq: str, drop_partial_last: bool = False) -> tuple [pd.Series, pd.Series]:
    px = pd.concat({"asset":asset_close, "bench":bench_close}, axis=1).dropna()
    r = px.resample(freq).last().pct_change().dropna()
    if drop_partial_last:
        r = r.iloc[:-1]
    return r["asset"], r["bench"]


def estimate_beta(stock_returns: pd.Series, market_returns: pd.Series) -> float:
    df = pd.concat([stock_returns, market_returns], axis=1).dropna()
    cov = np.cov(df.iloc[:, 0], df.iloc[:, 1])
    return cov[0, 1] / cov[1, 1]

def cost_of_equity(rf: float, beta: float, erp: float) -> float:
    return rf + beta * erp

def after_tax_cost_of_debt(pre_tax: float, tax_rate: float) -> float:
    return pre_tax * (1 - tax_rate)

def wacc(equity: float, debt: float, ke: float, kd_after_tax: float) -> float:
    total = equity + debt
    return equity / total * ke + debt / total * kd_after_tax





