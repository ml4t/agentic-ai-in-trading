# Run: instructed-loose

Mechanical record, written by `capture/lib/render_transcript.py`. The assessment
is in `FINDINGS.md`; nothing here is a judgement.

| | |
|---|---|
| Started (UTC) | 2026-09-18T15:37:28Z |
| Wall clock | 6m 28s (388s) |
| Harness exit code | 0 |
| Agent turns | 46 |
| Tool calls | 27 (3 returned an error) |
| Tools used | Bash x15, Write x7, Read x4, Edit x1 |
| Models billed | claude-sonnet-5 |
| Reported turns | 29 |
| API time | 368155 ms |
| Error flag on the result | False |
| Transcript | `transcript.jsonl` (240,042 bytes), rendered to `transcript.txt` |

## Usage limits

No usage limit fired during this run.

3 rate-limit events in the stream, status allowed. At the end of the run: five_hour: 11% used; seven_day: 16% used.

## What the agent said last

```
No symbol has a gap in its eligibility years, so filtering before computing momentum doesn't introduce artificial discontinuities in the trailing-return window — good, nothing to fix there.

## What I built

`src/etf_momentum/` — a small importable package, no notebook:

- **`data.py`** — loads the panel and applies the point-in-time filter: a (symbol, date) row survives only if `(symbol, date.year)` is in `eligibility.csv`. **117,460 / 119,408 rows survive (98.4%)** — most of what's excluded is pre-2007 warm-up and a handful of early-history rows before a symbol cleared the liquidity bar.
- **`signal.py`** — 12-1 month momentum: `close.shift(21) / close.shift(252) - 1`, computed within symbol via `groupby(symbol).shift`, so every value depends only on that symbol's own past prices. Skips the most recent month (the standard Jegadeesh-Titman construction) to keep short-term reversal out of the feature.
- **`labels.py`** — forward return: `close.shift(-horizon) / close - 1`. The decisive line is the negative shift; `worked_example()` proves the direction on two real SPY dates rather than asserting it:

```
symbol       date      close future_date  future_close  manual_fwd_return  label_fwd_return
   SPY 2025-11-28 677.77      2025-12-30    683.38           0.008268          0.008268
   SPY 2025-11-26 674.10      2025-12-29    684.21           0.015011          0.015011
```

- **Label horizon: 21 sessions (~1 trading month)**, declared once and threaded through everything downstream.
- **`evaluate.py`** — `WalkForwardCV(n_splits=5, label_horizon=21, expanding=True, consecutive=True)`. Momentum has no fitted parameters, so there's nothing for a training fold to overfit; the splitter's job here is to make the IC out-of-sample by construction and to drop the training rows next to each boundary whose 21-day-forward label would otherwise reach into the test period. `label_horizon=21` supplies that gap directly, so I didn't set a separate `gap` — a second hand-picked number would just risk drifting out of sync with the one that actually matters.
- **`portfolio.py`** — a top-minus-bottom quintile spread, computed only on the dates the walk-forward split marked out-of-sample, subsampled to one date every 21 sessions so the periods fed to the Sharpe calculation don't share overlapping label windows.

## Results

**Predictive power (IC, pooled over 5 expanding OOS folds, 2010–2025, 3,755 dates):**

```
mean IC: 0.0436
naive t-stat: 6.90
HAC t-stat:   1.99  (p=0.046, 20 lags)
HAC/naive SE ratio: 3.46x
```

The naive t-stat says "obviously significant." The HAC-corrected one — which is the one that matters, since overlapping 21-day labels autocorrelate the IC series exactly as `AGENTS.md` warns — cuts it to *barely* significant at 5%. The 3.46x inflation factor is right in the "two or three times too large" range the naive statistic is expected to be wrong by.

Per-fold IC is not stable: +0.091 (2010–13), −0.011 (2013–16), +0.035 (2016–19), +0.052 (2019–22), +0.050 (2022–25). One of five three-year windows has the sign flipped.

**Economic size (long top quintile, short bottom quintile, equal-weighted, 179 non-overlapping 21-day periods, OOS only):**

```
mean spread return per period: 0.21%
annualized mean return: 2.50%
annualized Sharpe: 0.18   (95% CI [-0.32, 0.69])
```

The confidence interval on Sharpe straddles zero. This is gross of any trading cost.

## Does it work?

Weakly, and not something I'd act on as-is. The HAC-corrected IC clears 5% significance only barely (p=0.046), and the economic spread built from that same signal has a Sharpe confidence interval that includes zero. The naive statistics alone (t=6.90) would have said "clearly yes" — that's exactly the false positive this pipeline exists to catch.

**What would have to be true for this to be real, and what I haven't ruled out:**

- **Costs** — untested. A 2.5%/year gross spread traded monthly across quintiles of ~5 ETFs each, with real bid/ask spreads and rebalancing tur
```
