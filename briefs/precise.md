Using `data/prices.parquet` (25 US-listed ETFs, daily OHLCV, 2007-2025) and the
point-in-time membership in `data/eligibility.csv` - `data/README.md` says what
both files contain:

1. Filter to eligible (symbol, date) pairs before computing anything else. A
   row is eligible for a year only if it has a row in `eligibility.csv` for
   that year. Report what fraction of the panel survives.
2. Build eight features, computed within each symbol from data up to and
   including the feature date and no later: momentum at 21, 63, 126 and 252
   sessions; realized volatility at 21 and 63 sessions; RSI(14) via
   `ml4t.engineer.features.momentum.rsi.rsi`; and cross-sectional
   dollar-volume rank.
3. Build a 21-session forward return label. Before you run anything: name the
   line of code that could put the future into the label, and say how you know
   it does not.
4. Train a LightGBM regressor predicting the label from the eight features,
   split with `ml4t.diagnostic.splitters.WalkForwardCV` at `label_horizon=21` -
   not a random train/test split. Say why a random split is wrong here.
5. Evaluate with `ml4t.diagnostic.metrics.cross_sectional_ic_series` followed by
   `compute_ic_hac_stats(..., label_horizon=21)`. Report the naive t-statistic
   and the HAC-corrected t-statistic side by side, and explain why they differ.

Stop and show me your code before running it at step 3 and at step 5. Those are
the two steps where a bug produces a good-looking wrong number instead of an
error.
