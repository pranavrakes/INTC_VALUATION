# Restructuring plan (proposal — not implemented yet)

A proposal for turning the current scripts into a clean, self-contained `uv` project
that is easy to run, easy to test, and can value companies other than Intel.
Nothing here changes the analysis itself — it's about structure.

Background on what exists today: [knowledge-base/project_overview.md](knowledge-base/project_overview.md).

---

## 1. Goals

1. **One-command setup and run** — `uv sync`, then `uv run valuation ...`.
2. **A README** that tells a newcomer what the project does, how to run it, and what output to expect.
3. **A clear folder structure** where each module has one job.
4. **No hard-coded company or assumption values in code** — move them to configuration so the same code can value AMD, Micron, etc.
5. **Reliable** — tests that don't need the internet, pinned dependencies, predictable outputs.

## 2. What I found in the current code

| # | Observation | Where |
|---|---|---|
| F1 | No `pyproject.toml` / `requirements.txt` — dependencies have to be guessed and installed by hand. | repo root |
| F2 | No README. | repo root |
| F3 | `data_loader.py` does ~6 jobs: HTTP downloads, caching, XBRL parsing, derived metrics, price/peer fetching, writing a template CSV. | `src/data_loader.py` |
| F4 | Intel-specific values are in code: CIK, peer list, segment names, SEC/FRED URLs, start year. | `src/data_loader.py:41-44`, `:236` |
| F5 | Valuation assumptions are in code: ERP 4.2%, tax 21%, cost of debt 6%, benchmark `SPY`. | `scripts/step2_wacc.py:10-11,23,32` |
| F6 | Folders are created as a side effect of *importing* the module. | `src/data_loader.py:38-39` |
| F7 | Scripts and tests edit `sys.path` so `from src...` works. A proper package install removes the need. | `scripts/*.py:1-4`, `tests/test_wacc.py:1-3` |
| F8 | `avg_debt` is computed but never used; the printed message says cost of debt should be checked against interest expense, but `kd` is a fixed 6%. Looks like an unfinished idea. | `scripts/step2_wacc.py:22-24` |
| F9 | Step 1 ends with `plt.show()`, which blocks until the window is closed, and has a leftover debug print after saving. | `scripts/step1_historicals.py:28-29` |
| F10 | Cache never expires — old prices/peer data are reused silently until `--refresh` is passed. | `src/data_loader.py` (all `load_*`) |
| F11 | `load_financials(min_year=2013)` but the CSV starts in 2016 — earlier years drop out because the revenue tag doesn't match. Worth investigating (add the older XBRL tag). | `src/data_loader.py:47-48,131` |
| F12 | Output goes through `print`; no logging levels. | everywhere |
| F13 | Only 2 tests, none for the data parsing — the part most likely to break. | `tests/` |
| F14 | `wacc()` has no docstrings / input checks (e.g. equity + debt = 0). | `src/wacc.py` |
| F15 | `data/processed/financials_annual.csv` and `outputs/historicals.png` are committed while `data/raw/` is ignored — no clear policy on generated files. | `.gitignore` |

None of these are bugs in the analysis; they're the normal state of a project that grew
step by step. F11 is the closest to a data issue.

## 3. Rationale — the design principles behind the proposal

Each principle below explains *why* a change is worth making, and which findings it addresses.

### 3.1 Single responsibility

Every module and function should have exactly one reason to change. A module that
downloads data shouldn't also need editing when the free-cash-flow formula changes.
Small, focused pieces are easier to read, test and fix in isolation.
*Addresses F3, F9.*

### 3.2 Modularity and separation of concerns

Group the code into layers that each handle one concern — **fetching data**,
**calculating**, **presenting results**, and **orchestrating a step** — with dependencies
flowing in one direction only (analysis → calculations → data). Pure calculations never
touch the network or the file system. This keeps the financial logic independent of
where the data comes from: if Yahoo Finance changes, only one module is affected.
*Addresses F3, F6, F7.*

### 3.3 Reusability — company-agnostic by design

Nothing about the method is specific to Intel; only the inputs are. Writing the code
once, generically, and feeding it a company profile means the same pipeline can value
AMD, Micron or any other SEC filer — and peers can be analysed with identical logic
for a fair comparison.
*Addresses F4.*

### 3.4 Configuration over code (externalised settings and environment variables)

Values that are expected to change — company identifiers, peer lists, URLs, valuation
assumptions — belong in configuration files, not in source code. Changing an assumption
like the equity risk premium then means editing one clearly labelled file, not hunting
through scripts. Personal or sensitive values (the SEC contact string) live in
environment variables so they're never committed to git.
*Addresses F4, F5.*

### 3.5 Reproducible environment and runtime

Anyone, on any machine, should get the same libraries and the same results with one
command. Declared dependencies plus a lock file eliminate "works on my machine"
problems; a single command-line entry point replaces remembering which script to run
from which folder; predictable caching rules mean you know how fresh the data is.
*Addresses F1, F7, F10.*

### 3.6 Clear documentation

Code tells you *how*; documentation tells you *what* and *why*. A README for running the
project, docstrings for functions, and the knowledge base for concepts mean either of
you can pick the project up after a break — and a new collaborator can get started
without help.
*Addresses F2, F14.*

### 3.7 Observability and graceful error handling

When something goes wrong (a website is down, a ticker is missing, a tag doesn't match),
the program should say clearly what happened and what to do about it — not show a long
stack trace. Structured logging with levels lets normal runs stay quiet while a
`--verbose` run shows every detail when debugging.
*Addresses F10, F12.*

### 3.8 Testability and trust in the numbers

A valuation is only as good as its inputs. Automated tests that run in seconds, without
the internet, give confidence that a refactor or a library upgrade didn't silently change
the results. Data-quality checks catch missing or stale values before they flow into
the valuation.
*Addresses F8, F11, F13, F15.*

## 4. Proposed changes

### 4.1 Make it a `uv` project

*Principles: 3.5.* Same approach as the `helloworld` project:

```bash
uv init --package --name valuation   # creates pyproject.toml, src/valuation/
uv add pandas numpy requests yfinance matplotlib
uv add --dev pytest ruff
```

Resulting `pyproject.toml` (sketch):

```toml
[project]
name = "valuation"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["pandas>=3.1", "numpy>=2.5", "requests>=2.34", "yfinance>=1.7", "matplotlib>=3.11"]

[project.scripts]
valuation = "valuation.cli:main"      # gives the `uv run valuation` command

[dependency-groups]
dev = ["pytest>=9.2", "ruff>=0.14"]

[build-system]
requires = ["uv_build>=0.13.6,<0.14.0"]
build-backend = "uv_build"
```

- Commit `uv.lock` so both of you get identical library versions.
- Add a `.python-version` file (`3.12`) so `uv` picks the right Python automatically.
- Installing the project as a package removes the `sys.path` workarounds (F7).

### 4.2 Folder structure

*Principles: 3.1, 3.2, 3.3.*

```
intc_valuation/
├── pyproject.toml
├── uv.lock
├── .python-version
├── README.md
├── RESTRUCTURING_PLAN.md
├── .env.example                 # template for SEC_USER_AGENT (real .env is git-ignored)
│
├── config/
│   ├── settings.toml            # global: URLs, XBRL tag map, cache expiry
│   └── companies/
│       ├── intc.toml            # Intel: CIK, peers, segments, assumptions
│       └── amd.toml             # example of adding another company
│
├── src/valuation/
│   ├── __init__.py
│   ├── cli.py                   # command-line entry point (only argument parsing)
│   ├── config.py                # load settings + company config + env vars
│   ├── paths.py                 # all folder locations, created on demand
│   ├── cache.py                 # read/write cached files, expiry check
│   ├── sources/                 # one module per external data source — fetch only, no maths
│   │   ├── sec.py               # SEC companyfacts download
│   │   ├── market.py            # yfinance: prices, peer snapshot
│   │   └── fred.py              # FRED risk-free rate
│   ├── financials.py            # XBRL JSON → clean annual table, derived metrics (FCF, net debt)
│   ├── wacc.py                  # pure formulas: beta, CAPM, cost of debt, WACC
│   ├── analysis/                # each step = one module, uses the pieces above
│   │   ├── historicals.py       # step 1
│   │   └── cost_of_capital.py   # step 2
│   └── charts.py                # matplotlib plotting
│
├── data/
│   └── intc/                    # one folder per company
│       ├── raw/                 # downloads (git-ignored)
│       ├── processed/           # cleaned CSVs (git-ignored, regenerated)
│       └── manual/              # hand-entered data, e.g. segments.csv (committed)
├── outputs/
│   └── intc/                    # charts and reports
│
├── tests/
│   ├── fixtures/                # small saved samples of SEC/FRED/yfinance responses
│   ├── test_wacc.py
│   ├── test_financials.py       # XBRL parsing against fixtures — no internet needed
│   └── test_config.py
│
└── knowledge-base/              # documentation for humans
```

Old → new mapping:

| Today | Moves to |
|---|---|
| `src/data_loader.py` — `get_sec_facts` | `sources/sec.py` |
| `src/data_loader.py` — `_series_from_tags`, `load_financials`, `load_balance_sheet_latest`, `load_share_count` | `financials.py` |
| `src/data_loader.py` — `load_prices`, `load_peer_snapshot` | `sources/market.py` |
| `src/data_loader.py` — `load_risk_free` | `sources/fred.py` |
| `src/data_loader.py` — `FLOW_TAGS`, `INSTANT_TAGS`, URLs | `config/settings.toml` |
| `src/data_loader.py` — `INTC_CIK`, `PEERS`, segment names | `config/companies/intc.toml` |
| `src/data_loader.py` — `write_segments_template` | `financials.py` (or a `cli.py init` command) |
| `src/data_loader.py` — `build_all` | `cli.py fetch` |
| `src/wacc.py` | `wacc.py` (unchanged, plus docstrings) |
| `scripts/step1_historicals.py` | `analysis/historicals.py` + `charts.py` |
| `scripts/step2_wacc.py` | `analysis/cost_of_capital.py` |

### 4.3 Module responsibilities

*Principles: 3.1, 3.2.* Rules of thumb for where code goes:

- **Sources fetch, they don't calculate.** `sources/*` return raw data; nothing else talks to the internet.
- **Calculations are pure functions.** `financials.py` and `wacc.py` take data in and return results, with no file or network access — which makes them easy to test.
- **Analysis modules orchestrate.** They call sources → calculations → charts, for one step.
- **The command-line module only parses arguments** and calls an analysis function.
- **Configuration is loaded once** at startup and passed down, rather than each module reading globals or environment variables.
- **No side effects on import.** Creating folders, reading environment variables, downloading — only inside functions (F6).
- **Keep it simple.** Plain functions plus small data containers (`dataclasses`) are idiomatic Python; avoid deep class hierarchies.

### 4.4 Configuration and environment variables

*Principles: 3.3, 3.4.* Three layers, from least to most specific:

1. **`config/settings.toml`** — the same for every company: SEC/FRED URL templates, the XBRL tag lists, cache expiry, default benchmark index.
2. **`config/companies/<ticker>.toml`** — everything company-specific.
3. **Environment variables / `.env`** — personal or sensitive values that must never be committed: `SEC_USER_AGENT`. Optionally overrides like `VALUATION_DATA_DIR`.

Example `config/companies/intc.toml`:

```toml
[company]
ticker = "INTC"
name = "Intel Corporation"
cik = "0000050863"
peers = ["AMD", "NVDA", "TSM", "QCOM", "AVGO", "TXN", "MU", "GFS"]
segments = ["Intel Products", "Intel Foundry", "All Other"]

[history]
start_date = "2013-01-01"
min_fiscal_year = 2013

[market]
benchmark = "SPY"
risk_free_series = "DGS10"

[assumptions]
equity_risk_premium = 0.042
tax_rate = 0.21
pre_tax_cost_of_debt = 0.06
```

- Per-company XBRL tag overrides can go in the company file too (some companies use different tags for the same line item).
- Python reads TOML with the built-in `tomllib`, so no extra library is needed.
- For `.env`, use `uv run --env-file .env ...` (built into uv) or `python-dotenv`.
- Adding a new company becomes: copy `intc.toml` → `amd.toml`, change the values, run `uv run valuation all --company amd`.

### 4.5 Command-line interface

*Principles: 3.5.* One entry point instead of separate scripts:

```bash
uv run valuation fetch        --company intc [--refresh]   # download + cache all data
uv run valuation historicals  --company intc [--show]      # step 1 (saves chart; --show opens it)
uv run valuation wacc         --company intc               # step 2
uv run valuation all          --company intc               # everything in order
```

Standard-library `argparse` is enough; `typer` is a friendlier option. Making the
chart window opt-in (`--show`) fixes the blocking `plt.show()` (F9).

### 4.6 Documentation

*Principles: 3.6.*

README outline:

1. What this project is (one paragraph) and current status (steps done / planned).
2. Prerequisites: `uv` installed. That's it — uv installs Python itself.
3. Setup: `git clone`, `uv sync`, `cp .env.example .env` and fill in `SEC_USER_AGENT`.
4. Run: the commands from 4.5.
5. **What to expect**: sample console output for each step, where files land (`data/intc/...`, `outputs/intc/...`), how long the first download takes vs. cached runs.
6. Configuration: how to change assumptions and add a company.
7. Development: `uv run pytest`, `uv run ruff check`, `uv run ruff format`.
8. Data caveats: yfinance is scraped; verify share count against the latest 10-Q/8-K; segments are entered by hand.
9. Link to `knowledge-base/`.

Also: a short docstring on every public function (F14), and keep `knowledge-base/` updated as new steps (DCF, comparables) are added.

### 4.7 Logging and error handling

*Principles: 3.7.*

- Replace `print` with Python's built-in `logging` module (F12): `INFO` for normal progress, `DEBUG` for detail, `WARNING` for suspicious data. A `--verbose` flag switches on debug output.
- Clear, actionable error messages for: missing `SEC_USER_AGENT`, network failures, unknown tickers, a company whose XBRL tags don't match.
- **Cache expiry** (F10): e.g. prices refresh after 1 day, SEC facts after 7 days, configurable in `settings.toml`; record the download time alongside each cached file and log its age.
- Write each step's results (e.g. the WACC table) to CSV/Markdown in `outputs/`, not just the console, so runs can be compared over time.

### 4.8 Testing and data quality

*Principles: 3.8.*

- Save small trimmed samples of the SEC JSON, FRED CSV and price data under `tests/fixtures/` and test the parsing against them — fast and no internet needed (F13).
- Mark the few real-network tests with `@pytest.mark.network` so they're skipped by default.
- Data-quality checks: warn when key fields are empty for a year (e.g. 2016 has no operating cash flow), when the share count looks stale, or when the history is shorter than requested (F11).
- Decide the cost-of-debt approach — fixed input or derived from interest expense ÷ average debt (F8).

### 4.9 Code quality and collaboration

*Principles: 3.5, 3.6.*

- **`ruff`** for linting and formatting — one tool that keeps both your coding styles consistent.
- **Type hints** everywhere (partly done already); PyCharm uses them for autocomplete and warnings.
- **Git policy for generated files** (F15): ignore `raw/`, `processed/` and `outputs/`; commit only hand-entered data (`manual/`) and perhaps a few reference charts.
- **GitHub Actions** to run `ruff` + `pytest` automatically on every push / pull request.
- **pre-commit hook** to run ruff before each commit.
- **Branch + pull-request workflow** — one feature per branch, review each other's changes.
- **Optional `notebooks/` folder** for exploratory Jupyter work, keeping the package code clean.
- **Leave room for the next analytical steps:** `analysis/dcf.py`, `analysis/comparables.py`, `analysis/sensitivity.py` (WACC × growth grid).

## 5. Suggested order of work

Each phase is a small, separately reviewable change; the analysis keeps working after each one.

1. **uv project** (4.1) — `pyproject.toml`, `uv.lock`, `.python-version`, README first draft. No code moves.
2. **Package + linting** (4.2) — move code into `src/valuation/`, drop `sys.path` workarounds, add `ruff`; behaviour identical. Check outputs match the old ones.
3. **Split `data_loader.py`** (4.2, 4.3) into `sources/`, `financials.py`, `cache.py`, `paths.py`.
4. **Configuration** (4.4) — `settings.toml` + `companies/intc.toml` + `.env.example`; remove hard-coded values.
5. **Command line** (4.5) — `valuation fetch/historicals/wacc/all`; retire `scripts/`.
6. **Hardening** (4.7, 4.8, 4.9) — logging, cache expiry, fixture-based tests, data checks, CI.
7. **Prove it generalises** — add a second company config and run end-to-end.

## 6. Open questions to decide together

- Package/project name: keep `intc_valuation` or go generic (`valuation`, `equity_valuation`) since it will support other companies?
- Commit generated data/charts or regenerate them? (Proposal: regenerate; commit only `manual/`.)
- Should cost of debt stay a fixed input, or be derived from interest expense ÷ average debt (which `avg_debt` in step 2 hints at)?
- `argparse` or `typer` for the command line?
- Fix the pre-2016 revenue gap (F11) as part of this work or separately?
