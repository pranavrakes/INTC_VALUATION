# Python environment

What the project needs to run, and what each important library does. Use this as the
starting point for a proper `uv` project (`pyproject.toml` + `uv.lock`), the same way
the `helloworld` project is set up.

## Python version

Tested with **Python 3.12** (via `uv venv --python 3.12`). The code also works on 3.9+,
but there's no reason to use anything older than 3.12.

## Third-party libraries (need installing)

| Library | Used in | What it does here |
|---|---|---|
| **pandas** | everywhere | The workhorse. Holds the financial data as tables (`DataFrame`) and time series (`Series`), reads/writes CSV, resamples daily prices to weekly/monthly, computes % changes. Think of it as "Excel inside Python". |
| **numpy** | `src/wacc.py` | Fast maths on arrays. Used for the covariance calculation behind beta. pandas is built on top of numpy. |
| **requests** | `src/data_loader.py` | Makes HTTP calls. Downloads the SEC companyfacts JSON and the FRED CSV. |
| **yfinance** | `src/data_loader.py` | Unofficial Yahoo Finance client. Fetches daily share prices (INTC, SPY) and a snapshot of company stats (market cap, EV, P/E, beta…) for INTC and peers. It scrapes Yahoo, so it can occasionally break or return gaps. |
| **matplotlib** | `scripts/step1_historicals.py` | Draws charts. Produces `outputs/historicals.png`. |
| **pytest** | `tests/` | Test runner. Finds functions named `test_*` and reports pass/fail. A dev-only dependency — not needed to run the analysis. |

### Pulled in automatically (you don't install these directly)

yfinance brings `curl-cffi` (HTTP client that looks like a browser),
`beautifulsoup4` + `lxml` (HTML parsing), `peewee` (small local cache DB),
`platformdirs`, `protobuf`, `websockets`. matplotlib brings `pillow` (images),
`fonttools`, `kiwisolver`, `contourpy`. pandas brings `python-dateutil`, `pytz`, `tzdata`.

## Standard library modules used (built into Python)

| Module | What it's for |
|---|---|
| `pathlib.Path` | File paths that work on any OS (`ROOT / "data" / "raw"`). |
| `json` | Parse the SEC JSON cache file. |
| `io` | Wrap a text string so pandas can read it like a file. |
| `os` | Read environment variables (`SEC_USER_AGENT`). |
| `argparse` | Command-line flags (`--refresh`). |
| `sys` | The scripts add the project root to `sys.path` so `from src...` imports work. |
| `__future__.annotations` | Lets newer type-hint syntax (`list[str] \| None`) work on older Pythons. |

## Versions installed on 2026-11-01

```
pandas 3.1.0    numpy 2.5.4    requests 2.34.2
yfinance 1.7.0  matplotlib 3.11.2  pytest 9.2.0
```

Note: pandas 3.x has some behaviour changes vs 2.x. If something misbehaves, check
whether the code was written against pandas 2.

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `SEC_USER_AGENT` | Yes (for SEC downloads) | The SEC asks every API caller to identify themselves with a name and email, e.g. `"Jane Doe jane@example.com"`. Requests without it are rejected. Only needed when the SEC data isn't already cached in `data/raw/`. |

## Setting it up today (manual)

```bash
cd ~/dev/python/intc_valuation
uv venv --python 3.12
uv pip install pandas numpy requests yfinance matplotlib pytest
SEC_USER_AGENT="Your Name you@example.com" uv run python src/data_loader.py
```

## What a proper uv setup would look like (to do)

A `pyproject.toml` replaces the manual install list, and `uv.lock` pins exact versions
so everyone gets the same environment:

```toml
[project]
name = "intc-valuation"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "pandas>=3.1",
    "numpy>=2.5",
    "requests>=2.34",
    "yfinance>=1.7",
    "matplotlib>=3.11",
]

[dependency-groups]
dev = ["pytest>=9.2"]
```

Then anyone can run `uv sync` once and `uv run ...` afterwards. See
[../RESTRUCTURING_PLAN.md](../RESTRUCTURING_PLAN.md) for the full proposal.
