# Functional review: Intel valuation

**Date:** 22 Nov 2026
**Reviewed:** `master` at commit `eb16d15`
**Scope:** the finance logic and the memo's conclusions. The technical review (code structure, setup) is separate.
**Standard:** a university project, not a production system.

No project code, assumptions or results were changed for this review.

## Verdict

**This is strong work for a university project.** The method is complete and the main numbers reproduce. Four gaps are worth fixing before submission, and two of them weaken the claim that peer comparisons support today's share price.

## What the project does

The project asks: **is Intel's $65.76 share price justified?** It answers in five ways:

| Method | Plain-English question | Value per share |
|---|---|---|
| **Cash flow forecast (DCF)** | What are Intel's future profits worth today? | $1 bad case, **$18 base**, $34 good case |
| **Reverse DCF** | What must happen to justify $65.76? | About 24% revenue growth for 10 years |
| **Peer comparison** | What if Intel were priced like similar companies? | About $86 on the main measure (EV/EBITDA) |
| **Sum of the parts (SOTP)** | What is each Intel business worth separately? | $39 to $108, **mid case $85** |
| **Simulation (Monte Carlo)** | What if the forecasts vary 20,000 ways? | Mostly $7 to $33 |

**The memo's conclusion:** Intel's own cash flows don't support the price, so the market is betting on a recovery, especially in its chip-manufacturing business (Foundry).

## What's especially good

- Assumptions were written down before seeing the results, so they weren't tuned to reach the price.
- The reverse DCF turns the price into something concrete that can be judged.
- The memo lists the signals that would prove it wrong.
- It spots that internal pricing between Intel's businesses can distort their reported profits.
- It is open about its limitations and weak data.

## Major gaps

### Gap 1: SOTP mid case needs reframing

**Where:** `scripts/step6_sotp.py:33`, `:57`, `:76`, `:89-96`

The memo already shows the Foundry loss sensitivity and an Integrated case, so this is mainly about framing.

| Case | Treatment | Value per share |
|---|---|---:|
| **Foundry recovery** (memo's mid case) | Foundry loss excluded, Foundry valued at $38bn | $85.03 |
| Memo's 100% row | Loss charged to Products, Foundry's $38bn **kept** | $45.89 |
| Integrated | Loss charged to Products, Foundry at zero | $38.66 |
| **Losses persist** | Whole-company EBIT of $6.6bn at 24.5x | $27.95 |

**Suggested changes:**

- Label $85 as the **Foundry recovery case** and show about **$28** as the **losses persist case**.
- Fix the sensitivity table: it charges Foundry's loss to Products but keeps Foundry's $38bn value. Its 100% row should tie to the Integrated case ($39).
- Recheck the 49% breakeven. It becomes about 31% if Foundry is set to zero; a sliding Foundry value would land in between.
- Justify or align corporate costs: they use 10x against 24.5x for Products, and the Q3 run-rate (-$4.5bn a year) rather than the nine-month pace (-$9.5bn a year).

### Gap 2: Reconcile Intel's EBITDA

**Where:** `scripts/step5_comps.py:35`

Yahoo isn't necessarily wrong, but its **$19.2bn** is about $4.6bn above a filings-based estimate of **$14.6bn**, and that difference is unexplained.

| Filings-based estimate, last 12 months | $bn |
|---|---:|
| Operating profit (1.18 for 9M 2026 + -2.21 for FY2025 + 2.79 to remove 9M 2025) | 1.76 |
| D&A (9.59 for 9M 2026 + **estimated** 3.2 for Q4 2025) | 12.79 |
| **Estimated EBITDA** | **14.55** |

| Intel EBITDA | Peer group and multiple | Value per share |
|---|---|---:|
| Yahoo $19.2bn | All 7 peers, 24.4x | $85.8 |
| Filings estimate $14.6bn | All 7 peers, 24.4x | $64.4 |
| Yahoo $19.2bn (sensitivity only) | Factory owners TXN, MU, GFS, 11.3x | about $38 |

**Suggested changes:**

- Replace the estimated Q4 2025 D&A with the actual figure.
- Identify which one-offs explain the difference from Yahoo. The nine-month corporate cost (-$7.6bn) is the first place to check.
- Until then, show **$64 to $86** rather than $86 alone.
- Keep Intel and peers on the same EBITDA basis.
- Show the factory-owning peer group as a sensitivity only, since it has just three companies.

### Gap 3: The headline claim is too strong

**Where:** `memo.md:7`, `memo.md:62`

The memo says the price isn't supported "under any plausible assumptions." But the reverse DCF mostly changes **one assumption at a time**, and real recoveries move several together.

| Combined test | Year-10 revenue | Value per share |
|---|---:|---:|
| Good case as modelled | $130bn | $34.5 |
| Good case with 10.9% required return | $130bn | $37.8 |
| Plus 28% margin | $130bn | $41.2 |
| Plus 2 points more growth | $153bn | $47.2 |
| 3 points more growth, 30% margin, 10.5% required return (about 12% growth a year) | $166bn | **$58.3** |

That's still below the price, but far above the memo's $34 top case. A 30% margin is within Intel's 2016-21 range of 22-33%. Whether $166bn of revenue is realistic is a judgement, as it is about twice Intel's 2021 peak.

The simulation's "0% chance" also only reflects the ranges it was given. It isn't a real-world probability.

**Suggested direction:** a safer headline is *"The price needs growth, margins and risk to all improve together."*

### Gap 4: The forecast uses the wrong starting date

**Where:** `src/dcf.py:83-96`, `config/assumptions.yaml:35-45`

The model values Intel as of December 2025 but compares it with an October 2026 price. It also counts nine months of 2026 cash flow that are already reflected in the September balance sheet.

| Scenario | As modelled | Date-corrected |
|---|---:|---:|
| Bad | $1.14 | $2.24 |
| Base | $18.09 | $20.41 |
| Good | $34.46 | $37.85 |

The correction keeps only the last quarter of FY2026 and discounts from the 26 Sep 2026 balance sheet. The conclusion doesn't change, but it's an easy error for an examiner to spot.

## Smaller items

- **Missing chart:** the memo's main chart, `docs/football_field.png`, isn't in the repo, so it will appear broken.
- **Unvalued investments:** about $8.5bn of private investments in the Sep 2026 10-Q are left out, worth roughly $1.60 per share. Check whether this overlaps with the Altera stake.
- **Long-term factory spending:** keeping factory assets in line with sales after year 10 would lower the base case by roughly $1 to $2. This is approximate, because the cached SEC data has no asset figure after 2022.
- **EV/Sales on the main chart** (`src/football_field.py:32-33`): the memo calls this measure flattering for Intel, yet its $61-190 range helps support "every peer-based range spans the price." Drop it from the chart, or use the margin-adjusted EV/Sales the project already calculates (`scripts/step5_comps.py:63-69`).
- **Q4 2026 profit** (`config/assumptions.yaml:58`): the base case implies about $1.9bn of Q4 operating profit, which looks high against guidance of about $0.10 earnings per share. The effect on value is small, and the README already lists this as an open item.
- **Tax rate:** the WACC step uses 21% (`scripts/step2_wacc.py:14`) and the DCF uses 18% (`config/assumptions.yaml:37`). The effect is tiny, but one rate should be used throughout.
- **Football field after fixes:** it reads the CSVs saved by earlier steps, so rerun steps 3 to 8 after any change.
- **Fine to leave as stated limitations:** the 18% tax rate itself, and the 30 Oct share price (now almost four weeks old).

## What the story becomes

**The core conclusion survives:** Intel's standalone cash flows are well below the share price. What changes is the second half: peer methods give **weaker support** for $65.76 than the memo suggests, and the price depends more clearly on a Foundry recovery.

Suggested order of fixes:

1. Gap 1: sum-of-the-parts treatment of Foundry
2. Gap 2: verify Intel's EBITDA
3. Gap 4: correct the valuation date
4. Gap 3: rewrite the headline using the updated numbers
5. Restore the missing chart, then rerun steps 3 to 8

## How this was checked

- Recalculated the DCF, reverse DCF, peer comparison and sum of the parts from the project's own code and cached data. The results match the memo and README, including $18.09, 24.4%, 69%, 5.7% and $85.03.
- All 39 automated tests pass.
- The alternative figures above come from a separate review script and were not added to the project.
- Filing figures come from the project's cached SEC data and `data/manual/segments.csv`. They weren't re-checked against the original PDFs.
- Peer data is the Yahoo snapshot cached on 1 Nov 2026.

**Not verified:**

- Segment figures (`data/manual/segments.csv`) and the balance sheet tie-out against the original 10-Q. A spot check is worth doing.
- The beta estimates. The S&P 500 price cache wasn't available locally, so only the arithmetic of the 11.5% WACC was checked.

This review covers the project's reasoning. It isn't investment advice.
