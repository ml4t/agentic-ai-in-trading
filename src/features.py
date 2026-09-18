"""Eight features, each computed within a symbol from data up to and including
the feature date, plus one cross-sectional transform ranked within a date only.
"""

from __future__ import annotations

import pandas as pd

from ml4t.engineer.features.momentum.rsi import rsi

MOMENTUM_WINDOWS = (21, 63, 126, 252)
VOL_WINDOWS = (21, 63)
RSI_PERIOD = 14


def _symbol_features(g: pd.DataFrame) -> pd.DataFrame:
    """Compute the seven within-symbol features for one symbol's rows, in date order."""
    g = g.sort_values("timestamp")
    close = g["close"]
    daily_return = close.pct_change()

    out = pd.DataFrame(index=g.index)
    for w in MOMENTUM_WINDOWS:
        # momentum_w(t) = close(t) / close(t - w) - 1: uses only close prices at
        # or before t, since t - w < t.
        out[f"mom_{w}"] = close / close.shift(w) - 1

    for w in VOL_WINDOWS:
        # trailing (right-aligned) rolling std of daily returns ending at t.
        out[f"vol_{w}"] = daily_return.rolling(window=w, min_periods=w).std()

    # Wilder's smoothing is recursive from the start of the (gap-free) close
    # series, so rsi(t) depends only on close[..t].
    out["rsi_14"] = rsi(close.to_numpy(), period=RSI_PERIOD)

    return out


def build_features(panel: pd.DataFrame) -> pd.DataFrame:
    """Add eight feature columns to the eligible panel.

    Seven are computed independently within each symbol (no cross-symbol or
    cross-date information). The eighth, dollar-volume rank, is a cross-
    sectional transform: for each date, rank symbols by that date's own
    dollar volume only, never mixing dates.
    """
    df = panel.copy()

    within_symbol = df.groupby("symbol", group_keys=False).apply(
        _symbol_features, include_groups=False
    )
    df = df.join(within_symbol)

    dollar_volume = df["close"] * df["volume"]
    # rank(pct=True) within each date's cross-section only - no other date's
    # rows enter the computation for a given date.
    df["dollar_volume_rank"] = dollar_volume.groupby(df["timestamp"]).rank(pct=True)

    return df


FEATURE_COLUMNS = [
    "mom_21",
    "mom_63",
    "mom_126",
    "mom_252",
    "vol_21",
    "vol_63",
    "rsi_14",
    "dollar_volume_rank",
]


if __name__ == "__main__":
    from src.data import load_eligible_panel

    panel = load_eligible_panel()
    featured = build_features(panel)
    print(featured[["symbol", "timestamp", *FEATURE_COLUMNS]].tail())
    print(featured[FEATURE_COLUMNS].isna().mean())
