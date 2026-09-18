"""Evaluate out-of-fold predictions: naive IC t-stat vs HAC-corrected t-stat.

Why they differ: fwd_ret_21 is a 21-session forward return, so consecutive
daily observations share up to 20 of their 21 return days. That overlap
autocorrelates the daily cross-sectional IC series (an MA(20)-like process),
which violates the i.i.d. assumption behind the naive t-statistic
(mean_ic / (std_ic / sqrt(n))). The naive t-statistic effectively treats each
overlapping day as an independent observation, so it understates the true
standard error and overstates significance - often by a factor of two or
three, per AGENTS.md. The HAC (Newey-West) t-statistic instead estimates the
standard error from a covariance matrix that accounts for autocorrelation up
to label_horizon - 1 lags, which is why compute_ic_hac_stats is called with
label_horizon=21.
"""

from __future__ import annotations

import pandas as pd

from ml4t.diagnostic.metrics import compute_ic_hac_stats, cross_sectional_ic_series
from ml4t.diagnostic.metrics.ic_inference import compute_ic_summary_stats
from src.label import LABEL_HORIZON
from src.model import build_dataset, run_walk_forward


def evaluate(oof: pd.DataFrame) -> None:
    ic_series = cross_sectional_ic_series(
        predictions=oof,
        returns=oof,
        pred_col="prediction",
        ret_col="fwd_ret_21",
        date_col="timestamp",
        entity_col="symbol",
    )

    naive = compute_ic_summary_stats(ic_series, ic_col="ic")
    hac = compute_ic_hac_stats(ic_series, ic_col="ic", label_horizon=LABEL_HORIZON)

    print(f"IC series: {naive['n_periods']} dates with a valid cross-sectional IC")
    print(f"Mean IC: {naive['mean_ic']:.4f}")
    print(f"Naive t-stat:          {naive['t_stat']:.3f}  (p={naive['p_value']:.4f})")
    print(
        f"HAC-corrected t-stat:  {hac['t_stat']:.3f}  (p={hac['p_value']:.4f}, "
        f"lags={hac['effective_lags']})"
    )
    print(f"Naive / HAC ratio: {naive['t_stat'] / hac['t_stat']:.2f}x")


if __name__ == "__main__":
    dataset = build_dataset()
    oof = run_walk_forward(dataset)
    evaluate(oof)
