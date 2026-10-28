import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
from src.data_loader import load_financials, load_balance_sheet_latest

OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

fin = load_financials()
fin.index = fin.index.year
bs = (load_balance_sheet_latest() / 1e6).round(0).to_string()

money = ["revenue", "operating_income", "net_income", "d_and_a", "capex", "cfo", "fcf", "net_debt"]
print((fin[money]/1e6).round(0).to_string())
print(fin[["operating_margin", "capex_pct_revenue"]].round(3).to_string())

print(f"\nLatest balance sheet ($m):\n{bs}")

fig, axes = plt.subplots(1, 3, figsize=(15, 4))
(fin["revenue"] / 1e9).plot(kind="bar", ax=axes[0], title="Revenue ($bn)")
(fin["operating_margin"] * 100).plot(ax=axes[1], marker="o", title="Operating margin (%)")
(fin[["capex", "cfo"]] / 1e9).plot(ax=axes[2], marker="o", title="Capex vs operating cash flow ($bn)")
plt.tight_layout()
fig.savefig(OUT / "historicals.png", dpi=150)
print((fin[["short_term_investments", "afs_investments", "trading_assets"]] / 1e6).round(0).to_string())
plt.show()
