# Findings: instructed-precise

**Cell**: checkout carrying the research standards, precise specification, three
operator replies available.
**Verdict: sound.** Every number reproduces. It reaches the same answer as
`bare-precise` to three significant figures, in 40% of the wall clock, and it
skips one check that `bare-precise` made.

## What it produced

A package, `src/`, six files, in 4m 2s over 36 tool calls: `data.py`,
`features.py`, `label.py`, `model.py`, `evaluate.py`, `__init__.py`.

## Did the checkpoints fire

Yes, both.

**Checkpoint 1, the label step**, with the code written and unrun:

> The line that decides direction: `close.shift(-LABEL_HORIZON) / close - 1`.
> `shift(-21)` pulls a value from 21 rows **ahead** in the symbol's date-sorted
> frame - i.e., the future close. `shift(+21)` would instead pull the past and
> silently produce a backward-looking label with no exception raised either way;
> this is exactly the failure mode AGENTS.md warns about. [...] I have not run
> this yet. Want me to proceed and run it, or do you want changes first?

Note that it credits `AGENTS.md` for the failure mode. The precise brief asks
for the same thing, so here the two sources agree and the environment adds
nothing the brief did not already demand.

**Checkpoint 2, the evaluation step**, again with the code shown and unrun,
explaining each of the three calls and ending "Want me to run it?".

**The third reply landed after completion** and the agent declined to invent
work: "I don't have a pending action queued up - the pipeline (steps 1-5)
already ran and I posted the final results."

## What it reported

| | naive | HAC |
|---|---|---|
| t-statistic | 6.104 | 2.013 |
| p-value | <0.0001 | 0.044 |

Mean IC 0.0282 over 3,755 dates, retention 98.4%, ratio 3.03x.

> Naive/HAC ratio = 3.0x, in line with AGENTS.md's warning that naive t-stats on
> overlapping-label IC series are inflated by roughly that factor.

Followed by five written caveats: no costs or capacity, the 2026-chosen universe
("the eligibility filter fixes *membership timing* per year, not the *initial
symbol list*"), one asset class, and - the one no other run raised - that a
p=0.044 result from a single configuration is not multiple-testing corrected.

## Are the numbers right

Yes. Re-running `python -m src.evaluate` reproduces retention 98.4%, the five
fold spans, 3,755 dates, mean IC 0.0282, naive t 6.104, HAC t 2.013 at p 0.0442
with 20 lags, ratio 3.03x.

The fold boundaries are identical to those of
`analysis/reference_pipeline.py`, which was written independently: fold 1 trains
to 2013-11-18 and validates from 2013-12-19 in both. Train end always precedes
validation start, with about a month of purge between them.

## Which line of code decides it

`model.py:42`:

```python
X_indexed = X.set_index(pd.DatetimeIndex(model_df["timestamp"]).tz_localize("UTC"))
```

and the sort on the line before the split, `sort_values(["timestamp", "symbol"])`.
Together these are what make `label_horizon=21` mean 21 sessions. Without the
timezone the library splits by row position and purges 21 rows, which across 25
symbols is under one session; without the date sort a positional split separates
symbols rather than dates.

`label.py:23`, `close.shift(-LABEL_HORIZON) / close - 1`, decides the label
direction, and `_worked_example` settles it on two SPY rows with an assertion
that the label date is strictly after the feature date.

`features.py` keeps `dollar_volume_rank` inside a single date and every other
feature inside a single symbol, so nothing crosses either boundary.

## What it got wrong

**It asserted a precondition instead of checking it.** `features.py` says
Wilder's smoothing "is recursive from the start of the (gap-free) close series".
The series is gap-free, and I verified it - no symbol has an interior
eligibility gap - but this run did not. `instructed-loose` checked, and
`bare-precise` restructured the pipeline so that the answer would be right
either way. This run took the gap-free property on faith.

That matters because the instruction it was following is what creates the
exposure: its `AGENTS.md` says to filter before computing a single feature, and
on a panel with an interior gap that produces a `shift(-21)` spanning more than
21 sessions with no error. See `bare-precise/FINDINGS.md` for the mechanism.

Nothing else. The pipeline is correct and the write-up is accurate.

## Did the environment change the agent's behaviour

**Barely, and that is the finding for this row of the matrix.** Against
`bare-precise`:

| | bare-precise | instructed-precise |
|---|---|---|
| Mean IC | 0.0285 | 0.0282 |
| Naive t | 6.10 | 6.104 |
| HAC t | 2.01 | 2.013 |
| Retention | 98.4% | 98.4% |
| Wall clock | 10m 16s | 4m 2s |
| Deliverable | four numbered scripts plus parquet artifacts | six importable modules |

The two agree on every number that matters. What differs is shape and thoroughness,
and on thoroughness the bare run is ahead: it checked the NaN counts, it reasoned
about the filter-order trap, and it took two and a half times as long doing so.

The environment's contribution here is the packaging convention and the
multiple-testing caveat. Everything else in `AGENTS.md` was already in the
brief, so the instructed column had nothing left to add. **A precise enough
specification makes the repository's standards redundant**, which is the
complement of what the loose row shows.
