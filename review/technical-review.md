# Technical review: Intel valuation

**Date:** 25 Nov 2026
**Reviewed:** `master` at commit `eb16d15`
**Scope:** how the project is built and run. The finance logic is covered in [functional-review.md](functional-review.md).
**Standard:** a finance student's analysis project, not production software.

No project code was changed for this review.

## Verdict

For a university project **the code is in good shape**:

- Each method has its own module in `src/`.
- Assumptions live in `config/assumptions.yaml`.
- Charts don't block (except step 1).
- The 39 automated tests all pass.

Most items below are about **whether someone else can run it and get the same numbers**.

## Must fix: someone else can't reproduce it today

| # | Issue | Why it matters |
|---|---|---|
| T1 | **No list of required libraries.** The README says `pip install -r requirements.txt` (`README.md:73`), but that file doesn't exist. The project needs pandas, numpy, requests, yfinance, matplotlib, pyyaml and pytest. | The README's first setup step fails. |
| T2 | **README describes files that don't exist:** `requirements.txt`, `docs/`, `scripts/check_tags.py` and `data/manual/capex_financed.csv` (`README.md:26-69`). The folder is also named `PythonProject1/`. | An examiner following the README hits dead ends. |
| T3 | **The memo's chart is missing.** `docs/football_field.png` (`memo.md:34`, `README.md:233`) was never committed, and step 8 saves into `outputs/`, which Git ignores. | The memo's main picture appears broken on GitHub. |
| T4 | **No end-to-end run from a fresh download.** The README's own last step says to do this. It's a check rather than a patch. | It proves T1 to T3 are fixed. |

## Should fix: the same input is entered in several places

| # | Issue | Why it matters |
|---|---|---|
| T5 | **The share price ($65.76) is typed into 6 scripts:** steps 3 to 8, each in its `--price` default. | Updating the price means editing 6 files, and missing one silently mixes prices. It belongs in `assumptions.yaml` with its date. |
| T6 | **WACC inputs are split up.** Step 2 hard-codes the risk premium, credit spread and a 21% tax rate (`scripts/step2_wacc.py:13-18`), while the DCF uses 18% and a hand-typed 11.5% WACC (`config/assumptions.yaml:37-39`). | The tax rates disagree, which was a functional finding. Move the inputs to the config and keep 11.5% as a stated judgement. |
| T7 | **Results are copied by hand into the README and memo.** | The functional fixes will change many numbers, so it's easy to miss one. Have step 8 write a summary table to copy from, or use a checklist. |
| T8 | **Steps 4 to 7 borrow setup code from the step 3 script** (`from step3_dcf import build_inputs, load_assumptions`). | A change to step 3 can break other steps. Move the shared code into `src/`. |
| T9 | **Leftover instructions in the code:** "Place in src/..." in `src/reverse_dcf.py`, `src/sotp.py`, `src/montecarlo.py` and `src/football_field.py`, and "Run from PyCharm like step3" in `scripts/step4_reverse_dcf.py` and `scripts/step6_sotp.py`. | They look like copied notes, and an examiner may notice. |
| T10 | **Step 1 still opens a chart window and waits**, and still has a stray debug print (`scripts/step1_historicals.py:28-29`). | Running all steps in one go stops at step 1. Other steps already avoid this. |
| T11 | **The beta calculation has no test.** `tests/test_wacc.py` checks only the formulas, not `estimate_beta` or `paired_returns`. | A test with made-up data where beta is known to be 2.0 would protect the main WACC input. |
| T12 | **Two versions of the knowledge-base folder.** The `knowledge-base-plus-plan` branch was never merged, and `master` now has `knowledge_base/`, with an underscore. | Decide what to keep: put the useful docs in `knowledge_base/` and retire the old restructuring plan. |

## Nice to have

| # | Issue |
|---|---|
| T13 | `outputs/historicals.png` is still in Git even though `outputs/` is now ignored. |
| T14 | If the DCF is given no forecast years, it fails with a confusing error before its own clearer check runs (`src/dcf.py:74-82`). |
| T15 | Downloaded data never refreshes by itself. The README already lists this, so a note is enough for a student project. |
| T16 | The download step creates folders as soon as it's loaded (`src/data_loader.py:38-39`), and nothing tests how it reads SEC data. This is acceptable at this level. |

## What happened to the earlier restructuring plan

| Earlier idea | Status | Recommendation for a university project |
|---|---|---|
| README | Done by Pranav | Fix the mismatches (T2) |
| Config instead of hard-coded values | Partly done (`assumptions.yaml`) | Finish for price and WACC inputs (T5, T6) |
| Tests | Mostly done (39 passing) | Add the beta test (T11) |
| Proper setup with a dependency list | Not done | `requirements.txt` is enough (T1); uv is optional |
| Splitting the download code, one command to run everything, logging, automatic GitHub checks | Not done | **Skip.** Too much effort for the benefit here. |
| Support for other companies | Not done | **Skip.** The project is about Intel. |

## Suggested patch areas

Each area can be one small patch for Pranav to review and commit:

1. **Setup and README:** T1, T2, T3
2. **Single inputs:** T5, T6, T7
3. **Cleanup:** T8, T9, T10, T14
4. **Tests:** T11
5. **Git tidying:** T12, T13

T4 is a final check after the patches. T15 and T16 need no change.
