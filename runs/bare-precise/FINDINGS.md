# Findings: bare-precise

**Cell**: bare checkout, no instruction files, precise specification, three
operator replies available.
**Verdict: sound, and it is the most careful run in the matrix.** Every number
reproduces. It found a leak mechanism that no other run considered and that the
instructed environment's own `AGENTS.md` would have walked into.

## What it produced

Four scripts and three parquet artifacts under `analysis/`, in 10m 16s over 44
tool calls - two and a half times the wall clock of any other cell:
`step1_eligibility.py`, `step2_features.py`, `step4_train.py`,
`step5_evaluate.py`, plus `panel_with_features.parquet`,
`model_panel.parquet` and `oof_predictions.parquet`. Sizes and checksums for
the uncommitted binaries are in `produced/ARTIFACTS.md`.

## Did the checkpoints fire

Yes, both, and they are the reason this run took three turns instead of one.

**Checkpoint 1, the label step.** The agent stopped with the label code written
and not executed, named the line, and gave two ways a lookahead could go wrong
silently rather than one:

> **The line that puts the future into the label** is
> `prices["fwd_ret_21"] = g["close"].apply(lambda s: s.shift(-21) / s - 1)`. It
> looks forward by design [...] The thing to verify isn't "does it look
> forward" (it must), but two ways that lookahead could go wrong silently:
> 1. **Leaking into the features.** [...]
> 2. **Leaking across eligibility gaps.** This is the subtler one.

**Checkpoint 2, the evaluation step.** It stopped again with the step-5 code
shown and unrun, and flagged an argument whose absence would have quietly
changed the answer:

> `entity_col="symbol"` is mandatory. I'm passing the same `oof` frame as both
> `predictions` and `returns`. Without `entity_col`, the join inside
> `cross_sectional_ic_series` has only `date_col` [...]

**The third reply landed after the work was finished** and the agent said so
rather than inventing something to do:

> All five steps are already complete and reported - there's nothing queued that
> needs a go-ahead right now. Did you want me to: push further on hyperparameters
> or the feature set, dig into anything specific in the results [...]

## What it reported

| | |
|---|---|
| Panel survival | 117,460 / 119,408 = 98.4% |
| Modelling rows after warm-up and tail drop | 111,642 |
| Mean cross-sectional IC | 0.0285 over 3,755 daily periods |
| Naive t | 6.10 |
| HAC t, `label_horizon=21` | 2.01, p 0.045, `effective_lags=20` |

> The corrected t-stat of 2.01 is still on the right side of significance
> (p=0.045) but far closer to the edge than the naive number suggests, which is
> exactly the failure mode this workflow is designed to catch: a naive
> evaluation would have overstated confidence in the signal by a factor of ~3.

## Are the numbers right

Yes. Re-running `analysis/step5_evaluate.py` in the same image gives 3,755
periods, mean IC 0.0285, naive SE 0.00467, HAC SE 0.01418, naive t 6.10, HAC t
2.01, p 0.04451, `effective_lags=20`.

They also agree with the independent reference in
`analysis/reference_results.json` (mean IC 0.0319, naive t 6.76, HAC t 2.25) to
within what different LightGBM settings explain, and with `instructed-precise`
(0.0282, 6.104, 2.013) to three digits.

## Which line of code decides it

**The order of the eligibility filter and the label**, which this run reversed
against the obvious reading of the brief, on purpose:

```python
prices["fwd_ret_21"] = g["close"].apply(lambda s: s.shift(-21) / s - 1)
# eligibility filter applied AFTER label construction, not before
prices = prices[eligible_mask].copy()
```

Its reasoning, from checkpoint 1:

> If I computed `shift(-21)` *after* filtering to eligible rows, `.shift(-21)`
> would count 21 *rows* in the filtered frame - but for a symbol with a missing
> year, row *t+21* in the filtered frame might actually be more than a year of
> calendar time ahead of row *t*. That wouldn't error; it would just quietly
> mislabel a ~1-year return as a "21-session" return, and it would desync from
> the `label_horizon=21` purge window.

That is correct in general. It does not bite on this data: I checked every
symbol and no eligibility record has an interior gap - HYG, LQD, VTV and VUG
lose leading years only - so filtering first and filtering last give identical
labels here. `instructed-loose` reached the same conclusion by checking for
gaps; `instructed-precise` asserted a "gap-free close series" in a comment
without checking; this run reasoned about what would happen if the assumption
failed and then arranged not to depend on it.

**This is the sharpest result in the matrix, and it cuts against the
instructed environment.** The `AGENTS.md` in `capture/environments/instructed/`
says "Filter the panel to point-in-time eligible (symbol, date) rows before
computing a single feature." On a panel with an interior eligibility gap, that
instruction, followed literally, produces the silently mislabelled return this
run avoided. A rule written by a competent team turns out to have a case in it
that nobody thought of, and the agent with no rules is the one that found it.

## What it got wrong

Nothing I can fault in the pipeline. Two things worth noting, neither an error:

1. **It left 34 MB of intermediate parquet in the tree** with no cleanup step
   and no `.gitignore` entry, so a `git add -A` in that repository would commit
   them. Nothing in the brief says not to.
2. **It is the slowest cell by a wide margin**, 10m 16s against 4m 2s for both
   loose runs. Roughly half of that is the two checkpoint turns and the model
   fits; the rest is the verification work it chose to do, such as confirming
   that every feature's NaN count is exactly `n_symbols x warm-up length`.
