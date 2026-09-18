"""Load prices and apply the point-in-time eligibility filter.

See data/README.md: a (symbol, year) is eligible only if eligibility.csv has
a row for it. The universe of 25 symbols was chosen in 2026 from ETFs liquid
today, so this filter is what makes the panel point-in-time rather than
survivorship-biased.
"""

from __future__ import annotations

import pandas as pd


def load_eligible_panel(
    prices_path: str = "data/prices.parquet",
    eligibility_path: str = "data/eligibility.csv",
) -> pd.DataFrame:
    """Return prices restricted to point-in-time eligible (symbol, year) rows."""
    prices = pd.read_parquet(prices_path)
    eligibility = pd.read_csv(eligibility_path)

    prices = prices.sort_values(["symbol", "timestamp"]).reset_index(drop=True)
    prices["year"] = prices["timestamp"].dt.year

    eligible_pairs = set(map(tuple, eligibility[["symbol", "eligible_year"]].to_numpy()))
    is_eligible = [
        (sym, yr) in eligible_pairs
        for sym, yr in zip(prices["symbol"], prices["year"], strict=True)
    ]

    n_total = len(prices)
    filtered = prices.loc[is_eligible].drop(columns="year").reset_index(drop=True)
    n_kept = len(filtered)

    print(
        f"Point-in-time eligibility filter: {n_kept:,} / {n_total:,} rows survive "
        f"({n_kept / n_total:.1%})."
    )
    return filtered


if __name__ == "__main__":
    load_eligible_panel()
