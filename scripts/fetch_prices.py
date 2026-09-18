"""Fetch the ETF price panel this repository works on.

Prices are downloaded from Yahoo Finance at run time and written to `data/`,
which is gitignored: no price data ships with this repository.

    python scripts/fetch_prices.py

Writes `data/prices.parquet` (long OHLCV panel) and `data/eligibility.csv`
(point-in-time membership). Both are described in `data/README.md`.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd
import yfinance as yf

# 25 liquid US-listed ETFs, all trading before the start date below.
UNIVERSE: tuple[str, ...] = (
    "SPY",
    "QQQ",
    "IWM",
    "DIA",
    "MDY",  # US equity, broad
    "VTV",
    "VUG",  # US equity, style
    "XLB",
    "XLE",
    "XLF",
    "XLI",
    "XLK",  # US sectors
    "XLP",
    "XLU",
    "XLV",
    "XLY",
    "EFA",
    "EWJ",  # international developed
    "EEM",
    "FXI",  # emerging markets
    "TLT",
    "IEF",
    "LQD",
    "HYG",  # fixed income
    "GLD",  # commodities
)

# One warm-up year is downloaded ahead of the panel so that the first panel year
# has a prior year to establish eligibility from. Warm-up rows are not written.
FETCH_START = "2006-01-01"
PANEL_START = "2007-01-01"
END = "2025-12-31"

# Point-in-time eligibility: a symbol is eligible for calendar year Y when its
# average daily dollar volume over year Y-1 cleared this threshold on at least
# this many sessions. Not inflation-adjusted.
ADV_THRESHOLD_USD = 10_000_000
MIN_SESSIONS_PRIOR_YEAR = 200

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def download(symbols: tuple[str, ...], start: str, end: str) -> pd.DataFrame:
    """Download daily OHLCV and return a long panel."""
    raw = yf.download(
        list(symbols),
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        group_by="ticker",
        threads=True,
    )
    if raw.empty:
        raise RuntimeError("Yahoo Finance returned no rows")

    frames = []
    for symbol in symbols:
        if symbol not in raw.columns.get_level_values(0):
            print(f"  warning: {symbol} returned no data", file=sys.stderr)
            continue
        frame = raw[symbol].dropna(how="all").copy()
        frame.columns = [c.lower() for c in frame.columns]
        frame["symbol"] = symbol
        frames.append(frame.reset_index().rename(columns={"Date": "timestamp"}))

    panel = pd.concat(frames, ignore_index=True)
    panel = panel[["timestamp", "open", "high", "low", "close", "volume", "symbol"]]
    panel["timestamp"] = pd.to_datetime(panel["timestamp"]).dt.tz_localize(None)
    return panel.sort_values(["symbol", "timestamp"]).reset_index(drop=True)


def build_eligibility(panel: pd.DataFrame) -> pd.DataFrame:
    """Derive (symbol, eligible_year) rows from the prior year's dollar volume."""
    frame = panel.assign(
        year=panel["timestamp"].dt.year,
        dollar_volume=panel["close"] * panel["volume"],
    )
    by_year = frame.groupby(["symbol", "year"])["dollar_volume"].agg(["mean", "size"])
    qualifies = (by_year["mean"] >= ADV_THRESHOLD_USD) & (
        by_year["size"] >= MIN_SESSIONS_PRIOR_YEAR
    )
    eligible = by_year[qualifies].reset_index()[["symbol", "year"]]
    eligible["eligible_year"] = eligible["year"] + 1
    return (
        eligible[["symbol", "eligible_year"]]
        .sort_values(["symbol", "eligible_year"])
        .reset_index(drop=True)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default=PANEL_START)
    parser.add_argument("--end", default=END)
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()

    print(f"Fetching {len(UNIVERSE)} symbols, {args.start} to {args.end} ...")
    fetched = download(UNIVERSE, FETCH_START, args.end)
    eligibility = build_eligibility(fetched)
    panel = fetched[fetched["timestamp"] >= pd.Timestamp(args.start)].reset_index(drop=True)
    eligibility = eligibility[
        eligibility["eligible_year"] >= pd.Timestamp(args.start).year
    ].reset_index(drop=True)

    prices_path = DATA_DIR / "prices.parquet"
    eligibility_path = DATA_DIR / "eligibility.csv"
    panel.to_parquet(prices_path, index=False)
    eligibility.to_csv(eligibility_path, index=False)

    elapsed = time.monotonic() - started
    print(
        f"{len(panel):,} rows, {panel['symbol'].nunique()} symbols, "
        f"{panel['timestamp'].min().date()} to {panel['timestamp'].max().date()}"
    )
    print(f"{len(eligibility):,} (symbol, year) eligibility rows")
    print(
        f"wrote {prices_path.relative_to(prices_path.parents[1])} "
        f"({prices_path.stat().st_size / 1e6:.1f} MB) and "
        f"{eligibility_path.relative_to(eligibility_path.parents[1])}"
    )
    print(f"elapsed {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
