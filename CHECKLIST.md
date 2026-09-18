# Checking research an agent wrote for you

Six checks. Each one names a mistake that produces a *better-looking number*
rather than an error, which is why none of them is caught by "it ran" and none
of them shows up in a review that only reads for style.

Every item was demonstrated on real code in `notebooks/audit.ipynb`: the code in
`src/` was written by a coding agent in a four-minute run, and the numbers below
come from running it and changing one line at a time. None of these checks is
specific to agents. They are what you check in any research result, including
your own. What changes with an agent is that the code arrives faster than you
can read it, and the explanation attached to it is fluent enough to be
convincing whether or not it is true.

---

## 1. Say what the filter removed

Any point-in-time or liquidity filter changes the sample the result is about.
Print the retention fraction and put it in the write-up.

**Demonstrated**: `98.4%` of rows survive the eligibility filter here. All four
captured agent runs applied that filter, unprompted in two cases. Three of them
said what it removed; the fourth did not, so nobody reading its result would
have known what sample the number described.

**What to ask**: what fraction of rows survived, and what does that sample now
represent?

---

## 2. Prove the label's direction on a worked example

A forward return is one `shift` away from being a backward return, and the wrong
direction raises no exception. A comment asserting the direction is not a check.

**Demonstrated**: flipping `close.shift(-21)` to `close.shift(21)` in
`src/label.py` takes the mean information coefficient from 0.028 to **0.9987**.
One character. No error. The code the agent wrote proves its own direction by
printing two real SPY dates with a hand-computed value beside the column value,
which is what a check looks like.

**What to ask**: show me two rows, the dates, the prices, and the arithmetic.

---

## 3. Never a shuffled split on overlapping labels

A label spanning *h* sessions overlaps *h* sessions of its neighbours. A
shuffled split puts overlapping labels on both sides of the train/test boundary,
and the model scores well partly by having memorised the row next door. Walk
forward, and purge the label horizon at every boundary.

**Demonstrated**: replacing `WalkForwardCV` with `KFold(shuffle=True)` takes the
mean IC from 0.028 to **0.287** and the t-statistic to 68. This is the dangerous
one: 0.287 is not so large that it screams "bug", but it is large enough to fund
a project.

**What to ask**: print the date range of each fold's training and test sets. If
they overlap, stop reading the rest of the result.

---

## 4. Report the corrected statistic beside the naive one, always together

Overlapping labels autocorrelate the information coefficient series, and an
ordinary t-statistic on an autocorrelated series is too large, here by a factor
of three. A naive t-statistic published alone is a false positive waiting to be
acted on.

**Demonstrated**: the same experiment, on the same data, is naive t **6.10** and
HAC-corrected t **2.01**. Neither is wrong arithmetic. They answer different
questions, and only one of them answers the question anybody has. 6.10 is a
result a team acts on; 2.01 is a result a team reruns on different data first.

**What to ask**: which standard error is that, and what does it assume about
independence?

---

## 5. Break the headline down until it stops holding

One number over fifteen years of out-of-sample dates is an average. Split it by year, by regime, by
symbol, and say what the breakdown can and cannot establish.

**Demonstrated**: the headline 0.028 is an average over calendar years running
from -0.098 to +0.117, four of fifteen negative. But apply the same correction
from item 4 *within* each year and exactly one year clears a t-statistic of 2.
The correct reading is not "the signal broke in 2013 and 2016"; it is that a
single year of daily data cannot establish what happened in that year, in either
direction.

The same discipline applied to the first half against the second half: the
second half is lower (0.023 against 0.033), and the difference between them has
a t-statistic of 0.36. That is not decay. It is the amount a weak signal moves
when you cut the sample in half.

**None of the four captured agent runs broke its own result down this far.** All
four reported one aggregate and stopped. Nothing in their briefs told them to,
and nothing stopped them either.

**What to ask**: show me this number computed on subsets, and tell me which of
those subsets is large enough to mean anything.

---

## 6. Check the claims in the comments, not just the code

An agent explains itself at length and the explanation is fluent. Fluent is not
the same as true, and the claims that matter are usually claims about *the data*
rather than about the code.

**Demonstrated**: one captured run stopped before running anything to warn that
filtering the panel before computing the label would make `shift(-21)` count
rows rather than trading sessions, mislabelling a long return as a short one for
any symbol with a gap in the middle of its history. The reasoning is correct.
The claim about this dataset is not: the four symbols that lose years lose their
*first* years, so there is no interior gap and the hazard costs nothing here
(0.0282 the safe way, 0.0264 the risky way). Meanwhile a different run asserted in a comment that the
series was gap-free without checking, and happened to be right.

Sound reasoning, a safe choice, and a false statement about the data, in the
same three lines. The only way anyone found out was by running it.

**What to ask**: this comment makes a claim about the data. What would show it
to be true, and did anyone run that?

---

## What stays human

None of the six is about writing code, and an agent can be told to do all of
them. What an agent does not do for you:

- **Choosing the question.** Momentum on 25 ETFs was specified by a person. So
  was the label horizon, and both determine what any of these numbers mean.
- **Deciding what the result does not support.** The best of the captured runs
  wrote its own caveats: no transaction costs, a universe chosen in 2026, one
  configuration, no search. It wrote them because a document in the repository
  told it to. Someone had to decide that belonged there.
- **Deciding whether to risk money on it.** A corrected t-statistic of 2.01 is a
  fact. What to do about it is not.
