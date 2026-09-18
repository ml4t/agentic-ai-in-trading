# Agentic AI in Trading

Materials for the opening workshop of QuantInsti's Algorithmic Trading
Conference 2026, Thursday 24 September.

**Status: under construction.** The notebook and the run artifacts land here
once the runs behind them are captured and checked.

## What is here now

A price panel and nothing built on top of it.

```bash
uv sync                              # pinned dependencies, Python 3.12
uv run python scripts/fetch_prices.py
```

The fetch downloads daily OHLCV for 25 liquid US-listed ETFs from Yahoo
Finance, 2007-01-01 to 2025-12-31, and writes `data/prices.parquet` and
`data/eligibility.csv`. Both are gitignored: no price data ships with this
repository. `data/README.md` describes the two files.

## What will be here

- `notebooks/` - one notebook, opens in Colab, runs start to finish in a
  browser. It fetches its own price data, so there is nothing to install and no
  API key of any kind.
- `briefs/` - the two specifications handed to the coding agent in the session,
  exactly as given.
- `runs/` - what the agent did with each one: the transcript, the code it wrote,
  and the results.
- `CHECKLIST.md` - what to check before trusting a research component an agent
  wrote for you.

## Requirements

A browser and a Google account for the notebook. For a local checkout, Python
3.12 and [uv](https://docs.astral.sh/uv/).
