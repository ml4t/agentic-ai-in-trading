# Findings: instructed-loose

**Cell**: checkout whose `AGENTS.md` states the research standards, same loose
request as `bare-loose`, same model, image, data and flags.
**Verdict: sound, with one defect that contradicts its own instructions.** Every
number reproduces. The code does not run as delivered.

## What it produced

A package, `src/etf_momentum/`, seven files, in 6m 28s over 27 tool calls:
`data.py`, `signal.py`, `labels.py`, `evaluate.py`, `portfolio.py`, `run.py`,
`__init__.py`.

Every clause of the environment's `AGENTS.md` landed as code:

| Standard | Where |
|---|---|
| Point-in-time first, state the surviving fraction | `data.py`, prints `117,460 / 119,408 rows survive (98.4%)` |
| Features see the past only | `signal.py`, `close.shift(21) / close.shift(252) - 1` within symbol |
| Prove the label direction on a worked example | `labels.py`, prints two real SPY dates with the hand-computed and the column value side by side |
| Declare the horizon in sessions | 21, declared once and threaded through |
| No random split; pass the horizon | `evaluate.py`, `WalkForwardCV(n_splits=5, label_horizon=21, expanding=True, consecutive=True)` |
| Say why if you set a gap without the horizon | it explains why it set no separate `gap` |
| HAC beside naive, every time | `naive t 6.90` and `HAC t 1.99` on consecutive lines with the 3.46x SE ratio |
| What the result does not support | written out at the end of the run |

It also did something `AGENTS.md` does not ask for and which matters: it checked
that the eligibility filter creates no interior gaps before filtering, rather
than assuming it.

> No symbol has a gap in its eligibility years, so filtering before computing
> momentum doesn't introduce artificial discontinuities in the trailing-return
> window.

I verified that independently: HYG, LQD, VTV and VUG lose *leading* years only
(HYG 2007-2009, LQD 2007-2008, VTV 2007-2008, VUG 2007) and no symbol has an
interior gap. The claim is correct.

## What it reported

Pooled out-of-sample over five expanding folds, 3,755 dates: mean IC 0.0436,
naive t 6.90, HAC t 1.99 at p 0.046, SE inflation 3.46x. Per-fold IC +0.091,
-0.011, +0.035, +0.052, +0.050. Economic size over 179 non-overlapping
21-session periods: 2.50% a year, Sharpe 0.18 with a 95% interval of
[-0.32, 0.69].

> The naive t-stat says "obviously significant." The HAC-corrected one [...]
> cuts it to *barely* significant at 5%.

## Are the numbers right

Yes, all of them, reproduced in `results.txt`.

## Which line of code decides it

`evaluate.py`'s splitter call and the tz-aware index feeding it. The per-fold
table proves the split is real: fold 0 trains to 2010-11 and tests 2010-12-27 to
2013-12-18, and every subsequent fold starts where the last one ended with the
label-horizon purge between train and test. Without a timezone-aware timestamp
the library splits by row position and `label_horizon=21` silently means 21
*rows*, which across 25 symbols is under one session of gap instead of 21.

And `labels.py`'s negative shift, settled on two printed SPY dates rather than
asserted: 2025-11-28 close 677.77 against 2025-12-30 close 683.38, hand-computed
0.008268 against the label column's 0.008268.

## What it got wrong

**The package does not run as delivered.** `src/etf_momentum/` has no packaging
configuration and `src` is not on the path, so `uv run python -m etf_momentum.run`
fails with `ModuleNotFoundError`. The agent ran it as
`PYTHONPATH=src uv run python -m etf_momentum.run` and recorded that nowhere -
not in a README, not in `pyproject.toml`, not in a comment. I had to find the
incantation in the transcript to reproduce the numbers.

This is the run contradicting the instruction it was following. Its `AGENTS.md`
says "Analysis code goes in `src/`, is importable, and is not a notebook." It
put the code in `src/` and did not make it importable.

**One overstatement.** Nothing is fitted; the prediction is the raw momentum
signal. The walk-forward folds therefore select test dates without holding any
estimate out, and the per-fold table's `n_train_rows` column describes rows that
were never used for anything. The write-up calls the result "out-of-sample"
without noting that there is no in-sample estimation for it to be out of. It
does not change the conclusion - a raw signal scored on held-out dates is a
legitimate test of a hypothesis - but it is not what "out-of-sample" usually
claims.

## Did the environment change the agent's behaviour

Yes, and specifically. Given the identical request, `bare-loose` did none of the
following:

1. **Stated the retention fraction.** `bare-loose` applied the same filter and
   never said what it removed.
2. **Put both statistics side by side.** `bare-loose` reported Newey-West alone.
3. **Checked that the filter creates no interior gaps** before relying on it.
4. **Wrote down what the result does not support.**
5. **Left something rerunnable.** `bare-loose` prints and exits.

It also switched the deliverable from a portfolio backtest to a predictive-IC
study, which is what `AGENTS.md`'s vocabulary of labels, horizons, splits and
information coefficients steers toward, and it cost 60% more wall clock
(6m 28s against 4m 2s).

Quoted from the transcript, the agent explaining a choice nothing in the request
mentions:

> `label_horizon=21` supplies that gap directly, so I didn't set a separate
> `gap` - a second hand-picked number would just risk drifting out of sync with
> the one that actually matters.
