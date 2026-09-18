# Findings: bare-loose

**Cell**: bare checkout, no instruction files, loose request.
**Verdict: sound.** Every reported number reproduces from the agent's own code
(`results.txt`), the conclusion follows from the numbers, and I found no leak.
Two minor defects, neither of which moves an answer.

## What it was asked

> Build me a momentum strategy on the ETF panel in this repo and tell me whether
> it actually works.

## What it produced

One file, `scripts/momentum_backtest.py`, in 4m 2s over 22 tool calls.

Cross-sectional 12-1 momentum: rank the eligible symbols each month end by
trailing 12-month return skipping the most recent month, long the top quintile
and short the bottom, equal-weighted, dollar-neutral, monthly rebalance, 10bps
one-way. Plus a market-model regression against SPY, sub-period stability, a
long-only variant against an unranked equal-weight benchmark, and a time-series
momentum comparison.

It fixed the primary specification before looking at any output and said so:

> The spec was fixed before I looked at any output, and I ran one pre-registered
> version plus honest robustness checks rather than trying variants until one
> worked.

## What it reported

> **Does it work? No.**

Long-short Sharpe 0.06 gross and -0.02 net, HAC t 0.25 and -0.07. Alpha to SPY
0.84% a year, t 0.23. The long-only variant at Sharpe 0.69, t 3.92 is dismissed
because an unranked equal-weight basket of the same universe also reaches
Sharpe 0.69, and the spread between them is Sharpe 0.06, t 0.21.

## Are the numbers right

Yes. Re-running the script in the same image reproduces all of it: gross Sharpe
0.06 with HAC t 0.25 (p 0.801), net Sharpe -0.02 with HAC t -0.07 (p 0.945),
annualised alpha 0.84% at t 0.23 with beta -0.09, turnover 0.44 a month, the
long-only leg at Sharpe 0.69 and HAC t 2.96, long-only-minus-benchmark at Sharpe
0.06 and HAC t 0.21, SPY buy-and-hold at Sharpe 0.74, and time-series momentum
at Sharpe 0.39, HAC t 1.59.

## Which line of code decides it

The eligibility application, which nobody asked for:

```python
year = m.year
eligible = eligibility.get(year, set())
```

The year used is the formation month's, and `data/README.md` defines that year's
membership from the *prior* year's volume, so no future information enters the
universe. The bare checkout contains no instruction to do this. It read the data
README, worked out what the file was for, and applied it.

And the line that decides whether the long-only result is a finding or beta: the
benchmark leg. Reporting Sharpe 0.69 with t 3.92 alone would have been a clean,
publishable-looking, wrong answer. The agent built the unranked comparison itself
and reported the difference instead.

## What it got wrong

1. **Zero risk-free rate in every Sharpe.** Over 2008-2025 this overstates the
   long-only and SPY figures. It does not touch the long-short leg, which is
   dollar-neutral, and the long-only conclusion is "no better than the
   benchmark", which a uniform adjustment does not reverse.
2. **Nothing is written to disk.** The script prints. Every number in the answer
   exists only in the terminal and the transcript; answering the same question
   tomorrow means re-running it.

## What it did not do

- It never reported a naive statistic beside the corrected one. It used
  Newey-West throughout, which is right, but a reader cannot see what the
  correction bought.
- It never stated the retention fraction of the eligibility filter it applied,
  so a reader cannot tell whether that filter removed 2% or 40%.
- It did not write down what the result does not support, though it did explain
  the mechanism of the failure and noted that the 2026-chosen universe biases
  toward finding something, "so a clean negative here is a meaningfully honest
  negative".
