# Financial terms glossary

Plain-English definitions of the terms used in this project, grouped by topic.
Where helpful there's a formula and an Intel example from the project's own data.

**The big picture in one paragraph:** A company is worth the cash it will generate in the
future, adjusted for the fact that money later is worth less than money now (and
risky money is worth less than safe money). Step 1 looks at the cash Intel has
generated historically. Step 2 works out the "discount rate" (WACC) investors
demand. A future step (DCF) combines the two into a value per share, and a
comparables step sanity-checks it against similar companies.

---

## 1. Data sources and filings

| Term | Meaning |
|---|---|
| **SEC** | U.S. Securities and Exchange Commission — the regulator. Every U.S.-listed company must file its financial reports with it. |
| **EDGAR** | The SEC's public database of all company filings (edgar.sec.gov). Free to use. |
| **XBRL** | A machine-readable tagging format for financial statements. Each number in a filing carries a tag like `Revenues` or `NetIncomeLoss`, so software can extract it without reading the PDF. |
| **companyfacts API** | An SEC endpoint that returns every XBRL number a company has ever filed, as one big JSON file. This is what `data_loader.py` downloads. |
| **us-gaap / dei** | Two families of XBRL tags. `us-gaap` = accounting numbers (revenue, debt…). `dei` = "document and entity information" (company name, share count on the cover page). |
| **GAAP** | Generally Accepted Accounting Principles — the U.S. accounting rulebook. "Non-GAAP" numbers are company-adjusted figures that exclude some items. |
| **CIK** | Central Index Key — the SEC's ID number for a company. Intel's is `0000050863`. |
| **10-K** | Annual report (audited). The main source for yearly financials. **10-K/A** is an amended version. |
| **10-Q** | Quarterly report (unaudited). Used for the latest balance sheet. |
| **8-K** | Report of a significant event between quarterly reports (acquisition, share issuance, CEO change…). |
| **Cover page** | First page of a 10-K/10-Q; states the number of shares outstanding on a recent date. |
| **Fiscal year** | The company's 12-month accounting year. Intel's ends on the last Saturday of December, which is why dates like `2018-12-29` appear. |
| **yfinance** | A Python library that pulls stock data from Yahoo Finance. Unofficial — convenient but should be spot-checked. |
| **FRED** | Federal Reserve Economic Data, run by the St. Louis Fed. Free economic time series (interest rates, inflation, GDP…). |
| **DGS10** | The FRED series code for the 10-year U.S. Treasury yield. |
| **Ticker** | Short stock-market code for a company: INTC = Intel, SPY = S&P 500 ETF, etc. |

## 2. Market and index terms

| Term | Meaning |
|---|---|
| **S&P 500** | Index of ~500 large U.S. companies; the standard proxy for "the stock market". |
| **SPY** | An exchange-traded fund (ETF) that tracks the S&P 500. Used here as "the market" when measuring beta. |
| **ETF** | Exchange-traded fund — a basket of stocks that trades like a single share. |
| **Adjusted close / auto_adjust** | Share prices adjusted for dividends and stock splits so that returns over time are comparable. |
| **Return** | % change in price over a period: (price_end ÷ price_start) − 1. The project uses weekly and monthly returns. |
| **Market capitalization (market cap)** | Share price × shares outstanding. What the stock market says the equity is worth. |
| **Shares outstanding** | Number of shares held by all investors. Intel's has changed a lot recently (new share issuances), hence the "verify against latest 10-Q/8-K" warning. |
| **Peers / comparables (comps)** | Similar companies used for comparison. Here: AMD, NVIDIA (NVDA), TSMC (TSM), Qualcomm (QCOM), Broadcom (AVGO), Texas Instruments (TXN), Micron (MU), GlobalFoundries (GFS). |

## 3. Income statement (performance over a year)

Shows money earned and spent over a period. Read top to bottom:

```
Revenue
 − Cost of goods sold
 = Gross profit
 − Operating expenses (R&D, sales, admin)
 = Operating income
 − Interest, ± other items
 − Income tax
 = Net income
```

| Term | Meaning |
|---|---|
| **Revenue** (sales, "top line") | Total money from selling products/services. |
| **Cost of goods sold (COGS)** | Direct cost of making what was sold (materials, factory costs). |
| **Gross profit** | Revenue − COGS. **Gross margin** = gross profit ÷ revenue. |
| **R&D expense** | Research and development spending. Large for chip companies. |
| **Operating income** (EBIT, roughly) | Profit from the core business before interest and taxes. |
| **Operating margin** | Operating income ÷ revenue. How many cents of operating profit each dollar of sales produces. *Intel 2019: 22,035 ÷ 71,965 ≈ **30.6%**.* |
| **EBIT** | Earnings Before Interest and Taxes. Close to operating income. |
| **EBITDA** | EBIT + Depreciation + Amortization. A rough proxy for cash profit; popular for comparing companies. |
| **Interest expense** | Cost of borrowing on the company's debt. |
| **Income tax expense** | Taxes charged against profits for the year. |
| **Net income** ("bottom line", earnings) | Profit left for shareholders after everything. |
| **EPS** | Earnings per share = net income ÷ shares. |

## 4. Depreciation, amortization and capex

| Term | Meaning |
|---|---|
| **Capex** (capital expenditure) | Cash spent on long-lived assets — for Intel, mainly chip factories ("fabs") and equipment. Shown in the cash-flow statement as "payments to acquire property, plant and equipment". |
| **PP&E** | Property, Plant & Equipment — buildings, factories, machines. |
| **Depreciation** | Spreading the cost of PP&E over its useful life. A $10bn fab used for 10 years shows ~$1bn of depreciation expense per year, even though the cash left in year 1. Non-cash expense. |
| **Amortization** | The same idea for intangible assets (patents, acquired technology). |
| **D&A** | Depreciation + amortization. |
| **Capex % of revenue** | Capex ÷ revenue. Shows capital intensity. Intel's has risen sharply as it builds new fabs. |

## 5. Cash flow statement

Profit isn't cash (because of depreciation, timing of payments, etc.). This statement
tracks actual cash in and out, in three sections: operating, investing, financing.

| Term | Meaning |
|---|---|
| **Cash flow from operations (CFO / OCF)** | Cash generated by running the business. In the code: `cfo`. |
| **Cash flow from investing** | Cash spent on/received from capex, acquisitions, buying/selling investments. |
| **Cash flow from financing** | Cash from/to lenders and shareholders: borrowing, repaying debt, dividends, buybacks, issuing shares. |
| **Free cash flow (FCF)** | CFO − capex. Cash left after keeping and growing the asset base — what's genuinely available to investors. *Intel 2019: 33,145 − 16,213 = **$16.9bn**.* The core input to a DCF. |
| **Unlevered FCF (FCFF)** | Free cash flow to the firm — before interest payments, i.e. available to both debt and equity holders. This is what gets discounted at WACC. |

## 6. Balance sheet (snapshot at a date)

What the company owns and owes at one moment. **Assets = Liabilities + Equity.**
In the code these are "instant" values (a point in time), vs. income/cash-flow items
which are "flow" values (over a period).

| Term | Meaning |
|---|---|
| **Cash and cash equivalents** | Cash in the bank plus very short-term, very safe investments. |
| **Short-term investments** | Liquid investments maturing within a year. |
| **Available-for-sale (AFS) securities** | Debt securities (bonds) the company holds and could sell. Treated like cash in net debt. |
| **Trading assets / securities** | Securities held to trade in the short term. Also treated like cash here. |
| **Current debt** | Debt due within 12 months. |
| **Long-term debt** | Debt due after 12 months. |
| **Stockholders' equity** (book equity) | Assets − liabilities, according to the accounts. Different from market cap. |
| **Book value** | Same as stockholders' equity. **Price-to-book (P/B)** = market cap ÷ book value. |
| **Non-controlling interest (minority interest)** | The part of a subsidiary owned by outsiders. Intel has sold stakes in units (e.g. Mobileye, fab joint ventures), so this matters for Intel. |
| **Net debt** | Total debt − cash and liquid investments. Negative = more cash than debt. |

## 7. Valuation multiples

Quick ways to compare companies of different sizes.

| Term | Meaning |
|---|---|
| **Enterprise value (EV)** | Market cap + net debt (+ non-controlling interest, etc.). The value of the whole business, regardless of how it's financed — what you'd pay to buy all of it, taking on its debt and keeping its cash. |
| **EV / Sales** | EV ÷ revenue. Useful when profits are low or negative (Intel's case recently). *INTC snapshot: ≈ 6.0×.* |
| **EV / EBITDA** | EV ÷ EBITDA. Most common multiple in comps analysis. Only meaningful when EBITDA is positive (the code excludes negatives). |
| **P/E (price-to-earnings)** | Share price ÷ EPS. **Trailing P/E** uses the last 12 months' earnings; blank when earnings are negative. |
| **Forward** multiple | Uses next year's forecast numbers instead of past ones. |

## 8. Cost of capital and WACC (Step 2)

| Term | Meaning |
|---|---|
| **Cost of capital** | The return investors require to fund the company. Used as the discount rate. |
| **Risk-free rate (rf)** | Return on a "riskless" investment — the 10-year U.S. Treasury yield. |
| **Treasury yield** | Annual interest return on U.S. government bonds. |
| **Beta (β)** | How much a stock moves relative to the market. β = 1 moves with the market; β = 2 moves twice as much (riskier); β = 0.5 half as much. Calculated as covariance(stock returns, market returns) ÷ variance(market returns). *Yahoo shows INTC β ≈ 2.2.* |
| **Covariance / variance** | Statistics: covariance measures how two series move together; variance measures how much one series moves. |
| **Equity risk premium (ERP)** | Extra annual return investors expect from stocks over risk-free bonds. The project assumes **4.2%** — a judgement call; typical estimates are 4–6%. |
| **CAPM** | Capital Asset Pricing Model: **cost of equity = rf + β × ERP**. |
| **Cost of equity (Ke)** | Return shareholders require. From CAPM. |
| **Cost of debt (Kd)** | Interest rate the company pays to borrow. The project assumes **6%** pre-tax. |
| **After-tax cost of debt** | Kd × (1 − tax rate). Interest is tax-deductible, so debt is cheaper than its headline rate. This saving is the **tax shield**. |
| **Tax rate** | 21% = U.S. federal corporate tax rate (Intel's actual effective rate varies year to year). |
| **Capital structure** | The mix of debt and equity funding a company. |
| **WACC** | Weighted Average Cost of Capital: the blended required return across shareholders and lenders, weighted by how much of each the company uses. |

**WACC formula:**

```
         E                 D
WACC = ───── × Ke   +   ───── × Kd × (1 − tax)
       E + D             E + D
```

E = market value of equity (market cap), D = debt.

*Toy example:* rf 4%, β 1.5, ERP 5% → Ke = 4% + 1.5 × 5% = 11.5%.
With E = 100, D = 100 and after-tax Kd = 4% → WACC = 0.5 × 11.5% + 0.5 × 4% = 7.75%.

**Why several beta windows?** Beta depends on the period and frequency used. 2-year
weekly reflects recent behaviour; 5-year monthly is smoother. Seeing the range shows
how sensitive WACC is to that choice.

## 9. Valuation methods (coming next)

| Term | Meaning |
|---|---|
| **Intrinsic value** | What a business is worth based on its own cash flows, independent of the current share price. |
| **DCF (Discounted Cash Flow)** | Forecast future free cash flows for ~5–10 years, discount each back to today at the WACC, add a terminal value, then subtract net debt to get equity value. Divide by shares → value per share. |
| **Discounting / present value** | $100 received in 1 year at a 10% discount rate is worth 100 ÷ 1.10 ≈ $90.9 today. |
| **Terminal value** | The value of all cash flows beyond the forecast period, usually assuming steady growth forever: FCF_next ÷ (WACC − g). |
| **Perpetual growth rate (g)** | Assumed long-run growth rate in the terminal value; typically 2–3% (around inflation/GDP). |
| **Comparables analysis** | Value a company by applying peers' multiples (e.g. median EV/EBITDA) to its own numbers. |
| **Sum-of-the-parts (SOTP)** | Value each business segment separately and add them up — relevant for Intel's Products vs Foundry split. |
| **Upside / downside** | (Estimated value ÷ current price) − 1. |

## 10. Intel / semiconductor-specific terms

| Term | Meaning |
|---|---|
| **Semiconductor / chip** | Electronic component made on silicon wafers — processors, memory, etc. |
| **Fab** | Semiconductor fabrication plant. Extremely expensive (often $10–20bn+ each). |
| **Foundry** | A company that manufactures chips designed by others (e.g. TSMC, GlobalFoundries). Intel is building this business as "Intel Foundry". |
| **Fabless** | A chip company that designs but doesn't manufacture (AMD, NVIDIA, Qualcomm, Broadcom). |
| **IDM** | Integrated Device Manufacturer — designs *and* makes its own chips (Intel, Texas Instruments, Micron). |
| **Segments** | The business units a company reports separately. Intel's: **Intel Products** (the chips it sells — PCs, data-centre), **Intel Foundry** (manufacturing), **All Other** (e.g. Mobileye, Altera). |

## 11. Units and conventions in the code

- Raw SEC values are in **US dollars**; scripts divide by `1e6` ($ millions) or `1e9` ($ billions) for display.
- Percentages are stored as decimals (0.306 = 30.6%).
- "Flow" items (revenue, capex…) are taken only from 10-K periods of ~12 months (350–380 days).
- "Instant" items (cash, debt…) are point-in-time values from 10-Ks and 10-Qs.
