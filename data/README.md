# Data

Nothing in this directory is committed. `scripts/fetch_prices.py` downloads the
prices from Yahoo Finance and writes both files below.

## `prices.parquet`

Daily OHLCV for 25 liquid US-listed ETFs, 2007-01-01 to 2025-12-31, adjusted for
splits and dividends. Long format, one row per (symbol, session):

| Column | Type | Meaning |
|---|---|---|
| `timestamp` | datetime64, tz-naive | Session date |
| `open`, `high`, `low`, `close` | float64 | Adjusted prices |
| `volume` | float64 | Shares traded |
| `symbol` | str | Ticker |

Coverage is not uniform. SPY, QQQ and the sector SPDRs trade across the whole
window; HYG starts in April 2007.

The 25 symbols were chosen in 2026, from ETFs that are liquid today. Which
tickers are on the list at all therefore reflects hindsight.

## `eligibility.csv`

Point-in-time membership, one row per (symbol, year) the symbol was eligible
for: `symbol, eligible_year`.

A symbol is eligible for calendar year Y when, over year Y-1, its average daily
dollar volume was at least $10M across at least 200 sessions. The threshold is
not inflation-adjusted. A symbol absent from a year has no row for that year.
