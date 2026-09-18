"""21-session forward return label.

The line that decides direction is the `shift(-LABEL_HORIZON)` below: a
*negative* shift pulls a value from `LABEL_HORIZON` rows *ahead* in the
(date-sorted, within-symbol) frame up to the current row - i.e. the future
close - not a value from behind it. `shift(+n)` would instead pull the past
and silently produce a backward-looking label with no error.

label(t) = close(t + h) / close(t) - 1, so it is only defined through
(n - h) of each symbol's rows; the last h rows of each symbol get NaN.
"""

from __future__ import annotations

import pandas as pd

LABEL_HORIZON = 21


def _symbol_label(g: pd.DataFrame) -> pd.Series:
    g = g.sort_values("timestamp")
    close = g["close"]
    return close.shift(-LABEL_HORIZON) / close - 1


def build_label(panel: pd.DataFrame) -> pd.DataFrame:
    df = panel.copy()
    df["fwd_ret_21"] = df.groupby("symbol", group_keys=False).apply(
        _symbol_label, include_groups=False
    )
    return df


def _worked_example(panel: pd.DataFrame, symbol: str = "SPY") -> None:
    """Print two dates' worth of close prices against their labels, by hand."""
    g = panel.loc[panel["symbol"] == symbol].sort_values("timestamp").reset_index(drop=True)
    g["fwd_ret_21"] = _symbol_label(g)

    for i in (100, 500):
        t0 = g.loc[i, "timestamp"]
        c0 = g.loc[i, "close"]
        t1 = g.loc[i + LABEL_HORIZON, "timestamp"]
        c1 = g.loc[i + LABEL_HORIZON, "close"]
        label = g.loc[i, "fwd_ret_21"]
        hand_computed = c1 / c0 - 1
        print(
            f"{symbol} row {i}: date {t0.date()} close {c0:.4f}  ->  "
            f"row {i + LABEL_HORIZON}: date {t1.date()} close {c1:.4f}  "
            f"label={label:.6f}  hand-computed={hand_computed:.6f}  "
            f"match={abs(label - hand_computed) < 1e-12}"
        )
        assert t1 > t0, "label date must be strictly after the feature date"
        assert abs(label - hand_computed) < 1e-12


if __name__ == "__main__":
    from src.data import load_eligible_panel

    panel = load_eligible_panel()
    _worked_example(panel)
