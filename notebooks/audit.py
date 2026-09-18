# ---
# jupyter:
#   jupytext:
#     formats: py:percent,ipynb
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Auditing a strategy a coding agent wrote
#
# A coding agent was given a research brief and a repository of daily ETF
# prices, and it wrote a complete predictive pipeline: data loading, features,
# a label, a model, an evaluation. The code in `src/` of this repository is
# what it produced, copied here unedited. The transcript of the run that wrote
# it is in `runs/instructed-precise/`.
#
# This notebook does three things, in order:
#
# 1. Explains what the strategy is and what "does it work" means here.
# 2. Runs the agent's code as delivered and reproduces its headline result.
# 3. Changes one line at a time and watches the headline move.
#
# Nothing here needs an agent, an API key or an account. It takes about three
# minutes to run start to finish.

# %% [markdown]
# ## 0. Setup
#
# On Colab this clones the repository, installs the pinned dependencies and
# downloads the price panel from Yahoo Finance. Locally it assumes you are
# running from a checkout with `uv sync` already done.

# %%
import os
import subprocess
import sys
from pathlib import Path

IN_COLAB = "google.colab" in sys.modules

if IN_COLAB:
    subprocess.run(
        ["git", "clone", "-q", "https://github.com/ml4t/agentic-ai-in-trading.git"],
        check=True,
    )
    os.chdir("agentic-ai-in-trading")
    subprocess.run(
        [
            sys.executable, "-m", "pip", "install", "-q",
            "ml4t-diagnostic==0.1.5", "ml4t-engineer==0.1.4", "lightgbm==4.6.0",
            "yfinance==1.7.0", "pyarrow==22.0.0", "statsmodels==0.14.6",
        ],
        check=True,
    )
elif Path.cwd().name == "notebooks":
    os.chdir("..")

sys.path.insert(0, str(Path.cwd()))
print("working directory:", Path.cwd())

# %% [markdown]
# The price panel is not shipped with this repository. It is downloaded from
# Yahoo Finance when you first run this cell, which takes about a minute.

# %%
if not Path("data/prices.parquet").exists():
    subprocess.run([sys.executable, "scripts/fetch_prices.py"], check=True)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

pd.set_option("display.width", 120)
pd.set_option("display.max_columns", 20)

prices = pd.read_parquet("data/prices.parquet")
print(f"{len(prices):,} rows, {prices['symbol'].nunique()} symbols, "
      f"{prices['timestamp'].min().date()} to {prices['timestamp'].max().date()}")
prices.head()

# %% [markdown]
# ## 1. What is being tested
#
# The question the agent was asked is whether **momentum predicts the next
# month's return** across this set of 25 US-listed ETFs.
#
# Momentum, here, is just past return: how much a fund has gone up or down over
# the last 21, 63, 126 or 252 trading sessions. The claim being tested is that
# funds which have done well recently keep doing well for about another month,
# relative to the others.
#
# That claim is tested one date at a time. On each date the model ranks all 25
# ETFs by predicted return. Then we wait 21 sessions, look at what actually
# happened, and ask how well the ranking matched the outcome. That agreement is
# a rank correlation between -1 and +1, called the **information coefficient**
# (IC). Average it over every date in the sample and you have one number that
# says whether the ranking was any good.
#
# An IC of 0.03 is not a 3% return. It is a correlation between today's ranking
# and what happened afterwards, on a scale where 1.0 would mean the ranking was
# perfect every single time. 0.03 is a weak relationship, and weak is normal:
# published equity signals routinely live between 0.02 and 0.05. The question is
# never whether the number is big, it is whether the number is real.

# %%
spy = prices[prices["symbol"] == "SPY"].set_index("timestamp")
ax = (spy["close"] / spy["close"].iloc[0]).plot(
    figsize=(10, 3), title="SPY, normalised to 1.0 at the start of the panel"
)
ax.set_xlabel("")
ax.figure.tight_layout()

# %% [markdown]
# ### The eligibility file, and why it exists
#
# The 25 symbols were chosen in 2026, from ETFs that are liquid in 2026. That
# choice looks backwards: an ETF that launched in 2005 and closed in 2012 is
# not in the list, and neither is one that stayed too small to trade. Testing a
# signal on survivors only will flatter it.
#
# `data/eligibility.csv` is the correction. A symbol counts for a calendar year
# only if its average daily dollar volume in the *previous* year cleared a
# threshold, so membership is decided using information that existed at the
# time. Everything in the pipeline runs on eligible rows only.

# %%
eligibility = pd.read_csv("data/eligibility.csv")
print(f"{len(eligibility)} (symbol, year) pairs are eligible")
eligibility.groupby("eligible_year").size().head(8)

# %% [markdown]
# ## 2. The code the agent wrote
#
# Five modules, written in a single agent run lasting four minutes, in a
# container with no instructions from us beyond the research brief in
# `briefs/precise.md`. The files below are exactly as the agent left them,
# including its own comments and docstrings: those are part of what we are
# auditing.
#
# | File | What it does |
# |---|---|
# | `src/data.py` | Loads prices, applies the eligibility filter, prints what survived |
# | `src/features.py` | Eight features: four momentum windows, two volatility windows, RSI, dollar-volume rank |
# | `src/label.py` | The 21-session forward return, with a worked example that checks its direction |
# | `src/model.py` | LightGBM, five walk-forward folds |
# | `src/evaluate.py` | The information coefficient, with two t-statistics |
#
# Read the label module. The agent was asked to name the line of code that
# decides whether the label looks forwards or backwards, and to prove which way
# it points rather than assert it. This is what it wrote.

# %%
print(Path("src/label.py").read_text())

# %% [markdown]
# ## 3. Run it as delivered
#
# `build_dataset()` loads, filters, builds features and builds the label.
# `run_walk_forward()` trains five models, each on data strictly earlier than
# the dates it is scored on. `evaluate()` reports the result.
#
# Nothing below is our code. These are the agent's own functions, called in the
# order its own `__main__` block calls them.

# %%
from src.evaluate import evaluate  # noqa: E402
from src.features import build_features  # noqa: E402
from src.label import LABEL_HORIZON, build_label  # noqa: E402
from src.model import build_dataset, run_walk_forward  # noqa: E402

dataset = build_dataset()
print(f"\n{len(dataset):,} rows with features and a label")

# %%
oof = run_walk_forward(dataset)
print(f"\n{len(oof):,} out-of-fold predictions")

# %%
evaluate(oof)

# %% [markdown]
# Three numbers to carry through the rest of this notebook:
#
# - **Mean IC 0.0282.** The ranking was right slightly more often than wrong.
# - **Naive t-statistic 6.10.** Read literally, odds of a million to one against
#   this being luck.
# - **HAC-corrected t-statistic 2.01.** The same data, with one assumption
#   repaired. Just past the conventional 5% threshold.
#
# The gap between 6.10 and 2.01 is the single most useful thing in this
# notebook, and section 4 comes back to it. The agent reported both numbers
# without being asked which to prefer, and its own summary called the corrected
# one *barely* significant. That is the correct reading.

# %% [markdown]
# ## 4. Four checks, one line each
#
# Three questions carry all of this, and each check below answers one of them:
#
# 1. **What are you predicting?** The label. Check 1.
# 2. **What was knowable when?** The timeline. Checks 2 and 3.
# 3. **Does the evidence say what you think it says?** The statistic and the
#    sample. Check 4, and section 5.
#
# Every check changes exactly one thing and reruns **the agent's own**
# `run_walk_forward`. Same features, same label horizon, same model, same
# number of folds. Whatever moves, moves because of the single change.
#
# Each of the four is a mistake that produces a *better-looking number* rather
# than an error message. None of them raises an exception. None of them shows
# up in a code review that only asks "does it run".

# %%
from ml4t.diagnostic.metrics import compute_ic_hac_stats, cross_sectional_ic_series  # noqa: E402


def score(predictions: pd.DataFrame) -> dict:
    """The agent's own evaluation, returned as numbers instead of printed."""
    series = cross_sectional_ic_series(
        predictions=predictions,
        returns=predictions,
        pred_col="prediction",
        ret_col="fwd_ret_21",
        date_col="timestamp",
        entity_col="symbol",
    ).dropna(subset=["ic"])
    ic = series["ic"].to_numpy(dtype="float64")
    hac = compute_ic_hac_stats(series, ic_col="ic", label_horizon=LABEL_HORIZON)
    return {
        "mean_ic": float(ic.mean()),
        "naive_t": float(ic.mean() / (ic.std(ddof=1) / np.sqrt(len(ic)))),
        "hac_t": float(hac["t_stat"]),
        "n_predictions": int(len(predictions)),
    }


results = {"as the agent wrote it": score(oof)}
results["as the agent wrote it"]

# %% [markdown]
# ### Check 1. Does the label point forwards?
#
# `src/label.py` computes `close.shift(-21) / close - 1`: the price 21 sessions
# **ahead**, divided by today's price. Change the minus sign and it becomes the
# price 21 sessions **behind**, which is a return that has already happened.
#
# One character. Everything still runs.

# %%
backward = dataset.copy()
past_close = backward.groupby("symbol", group_keys=False)["close"].shift(LABEL_HORIZON)
backward["fwd_ret_21"] = backward["close"] / past_close - 1.0
backward = backward.dropna(subset=["fwd_ret_21"]).reset_index(drop=True)

results["label points backwards"] = score(run_walk_forward(backward))
results["label points backwards"]

# %% [markdown]
# **Mean IC 0.9987.** A rank correlation of essentially one between prediction
# and outcome.
#
# This one is easy to catch, because nothing in markets correlates at 0.999 and
# anybody who has seen a real result knows it. It is in the notebook as a
# calibration exercise: this is what an obvious leak looks like. The next one is
# the same class of mistake and does not look obvious at all.

# %% [markdown]
# ### Check 2. Is the split respecting time?
#
# `src/model.py` uses `WalkForwardCV`: each fold trains on data strictly earlier
# than the dates it is scored on, with a 21-session gap on either side of the
# boundary so no training label reaches into the test period.
#
# Replace it with `KFold(shuffle=True)`. That is the default split in most
# tutorials, and it is what a model does when nobody is thinking about time. The
# feature set, the label, the model and the number of folds are untouched.

# %%
from sklearn.model_selection import KFold  # noqa: E402

from src import model as agent_model  # noqa: E402


class ShuffledKFold:
    """Accepts the same arguments as the splitter the agent chose, ignores time."""

    def __init__(self, n_splits: int = 5, seed: int = 0, **_ignored) -> None:
        self._kfold = KFold(n_splits=n_splits, shuffle=True, random_state=seed)

    def split(self, X, y=None, groups=None):
        yield from self._kfold.split(X, y, groups)


original_splitter = agent_model.WalkForwardCV
agent_model.WalkForwardCV = ShuffledKFold
try:
    results["shuffled split"] = score(run_walk_forward(dataset))
finally:
    agent_model.WalkForwardCV = original_splitter

results["shuffled split"]

# %% [markdown]
# **Mean IC 0.287, naive t-statistic 68.** Ten times the real signal.
#
# Look at the fold printout above. Every fold now trains and tests on the same
# date range, 2008 to 2025. Time has stopped existing.
#
# Why: the label spans 21 sessions, so today's label and tomorrow's label share
# 20 of their 21 days. A shuffled split scatters those neighbours across the
# train/test boundary, and the model scores well on a test row partly by having
# memorised the training row next door.
#
# This is the dangerous one. 0.287 is not so large that it screams "bug". It is
# large enough to be exciting, small enough to be believed, and it comes with a
# t-statistic that no reviewer would question. A shuffled split on a time series
# is the most common way a research result turns out to be nothing.
#
# The name matters: this is *temporal leakage*, not overfitting. The model is
# not too complex for the data. It was scored on dates whose outcomes it had
# already been shown. Overfitting is fixed with fewer parameters or more data;
# this is fixed by respecting the clock, and nothing else fixes it.

# %% [markdown]
# ### Check 3. Does the order of filtering and labelling matter?
#
# One of the other captured runs, `runs/bare-precise`, stopped before running
# anything to raise a hazard nobody had asked it about. Its brief says to filter
# the panel to eligible rows *first*. If you do, it argued, then `shift(-21)`
# counts 21 rows in the *filtered* frame rather than 21 trading sessions. For a
# symbol missing a year in the middle of its history, that would silently label
# a year-long return as a one-month return, and the result would look better
# than it is.
#
# It restructured its pipeline so the answer is right either way. The reasoning
# is sound. Is it true of this data?

# %%
raw = pd.read_parquet("data/prices.parquet")
filter_last = build_label(build_features(raw))
keys = set(map(tuple, eligibility[["symbol", "eligible_year"]].to_numpy()))
keep = [
    (s, t.year) in keys
    for s, t in zip(filter_last["symbol"], filter_last["timestamp"], strict=True)
]
filter_last = filter_last.loc[keep].sort_values(["timestamp", "symbol"]).reset_index(drop=True)

results["label after the filter"] = score(run_walk_forward(filter_last))
results["label after the filter"]

# %% [markdown]
# **Mean IC 0.0264 against 0.0282.** Nothing happens.
#
# The reason is in the eligibility file: the four symbols that lose years lose
# their *first* years, not middle ones, so there is no interior gap for `shift`
# to step across.

# %%
years = eligibility.groupby("symbol")["eligible_year"].agg(["min", "max", "count"])
years["has_interior_gap"] = years["max"] - years["min"] + 1 != years["count"]
years[years["min"] > eligibility["eligible_year"].min()]

# %% [markdown]
# This is the check worth remembering, and it is the one that produced no
# drama. The agent identified a real failure mode, reasoned about it correctly,
# made the safe choice, and stated something about this dataset that is not
# true. The reasoning being sound did not make the claim true, and the only way
# anyone found out was by running it.
#
# Both halves matter. Take the safe branch, and also check the claim.

# %% [markdown]
# ### Check 4. Which t-statistic are you reading?
#
# This one changes no code at all. The agent's own `evaluate()` already printed
# both numbers.
#
# The naive t-statistic assumes each date's IC is an independent observation.
# They are not independent: consecutive dates' labels overlap by up to 20 of
# their 21 days, so the series is strongly autocorrelated and the naive formula
# divides by a standard error that is roughly three times too small. The
# HAC-corrected statistic estimates the standard error from a covariance that
# accounts for that overlap.

# %%
summary = pd.DataFrame(results).T[["mean_ic", "naive_t", "hac_t", "n_predictions"]]
summary["naive / hac"] = summary["naive_t"] / summary["hac_t"]
summary.round(4)

# %% [markdown]
# Read the first row across: the same experiment, the same data, reported two
# ways. 6.10 is a result a team acts on. 2.01 is a result a team runs again on
# different data before spending anything.
#
# Neither number is wrong arithmetic. They answer different questions, and only
# one of them answers the question anybody actually has.

# %% [markdown]
# ## 5. What the average hides
#
# One number over fifteen years is an average. Break it apart by calendar year
# and apply the same correction as above within each year.

# %%
ic_series = cross_sectional_ic_series(
    predictions=oof,
    returns=oof,
    pred_col="prediction",
    ret_col="fwd_ret_21",
    date_col="timestamp",
    entity_col="symbol",
).dropna(subset=["ic"])
ic_series = ic_series.rename(columns={"timestamp": "date"})

rows = []
for year, group in ic_series.groupby(ic_series["date"].dt.year):
    ic = group["ic"].to_numpy(dtype="float64")
    if len(ic) < 60:
        continue
    hac = compute_ic_hac_stats(group, ic_col="ic", label_horizon=LABEL_HORIZON)
    rows.append({
        "year": int(year),
        "n_dates": len(ic),
        "mean_ic": ic.mean(),
        "naive_t": ic.mean() / (ic.std(ddof=1) / np.sqrt(len(ic))),
        "hac_t": float(hac["t_stat"]),
    })

by_year = pd.DataFrame(rows).set_index("year")
by_year.round(3)

# %%
ax = by_year["mean_ic"].plot(
    kind="bar", figsize=(10, 3), title="Mean IC by calendar year", color="#4c72b0"
)
ax.axhline(0, color="black", linewidth=0.8)
ax.set_xlabel("")
ax.figure.tight_layout()

# %% [markdown]
# The headline average is made of years running from -0.10 to +0.11. Four of
# fifteen are negative.
#
# Now read the `hac_t` column rather than the bars. Exactly one year of the
# fifteen clears a corrected t-statistic of 2, and it is a positive one. The
# worst year, 2016 at -0.098, reaches -1.66: by the same standard applied to the
# headline result ten cells ago, that is not distinguishable from zero.
#
# So the honest summary is not "the signal broke in 2013 and 2016". It is that
# **a single year of daily data is not enough to say what happened in that
# year**, in either direction, and the year-to-year swing in the bars is mostly
# what a weak signal looks like when you slice it thinly. Apply the correction
# you were taught two sections ago to the numbers you would rather it did not
# apply to.
#
# That is worth knowing before you react to a bad quarter. It is also worth
# knowing that **none of the four captured agent runs broke its own result down
# this far.** All four reported a single aggregate and stopped. Nothing in any
# of their briefs told them to go further, and nothing stopped them either.

# %% [markdown]
# ## 6. After deployment: what you would actually watch
#
# Everything above is about whether a result is real. A separate question is
# whether it stays real once the model is running, which is where the word
# *drift* belongs.
#
# Be clear about what this data can and cannot show. Split the out-of-sample
# period in half and compare.

# %%
midpoint = ic_series["date"].quantile(0.5)
halves = []
for name, part in (
    ("first half", ic_series[ic_series["date"] <= midpoint]),
    ("second half", ic_series[ic_series["date"] > midpoint]),
):
    ic = part["ic"].to_numpy(dtype="float64")
    hac = compute_ic_hac_stats(part, ic_col="ic", label_horizon=LABEL_HORIZON)
    halves.append({
        "period": name,
        "from": part["date"].min().date(),
        "to": part["date"].max().date(),
        "mean_ic": ic.mean(),
        "hac_t": float(hac["t_stat"]),
    })

halves_frame = pd.DataFrame(halves).set_index("period")
halves_frame.round(4)

# %% [markdown]
# The second half is lower: mean IC 0.023 against 0.033. That is the shape
# everyone is looking for, and it is where the word *decay* usually gets
# attached to a result.
#
# Resist it, and apply the same standard as before. Each half's own corrected
# t-statistic is 1.59 and 1.24, so neither half is distinguishable from zero on
# its own. The quantity that would have to be significant for "it decayed" to
# mean anything is the **difference** between them.

# %%
se = (halves_frame["mean_ic"] / halves_frame["hac_t"]).to_numpy()
diff = halves_frame["mean_ic"].iloc[0] - halves_frame["mean_ic"].iloc[1]
se_diff = float(np.sqrt((se**2).sum()))
print(f"first half minus second half: {diff:.4f}")
print(f"standard error of the difference: {se_diff:.4f}")
print(f"t-statistic: {diff / se_diff:.2f}")

# %% [markdown]
# A t-statistic of about 0.36. **This strategy shows no decay that this data can
# establish**, and this notebook is not going to manufacture one by choosing a
# window where the number falls.
#
# That is worth sitting with, because "the signal is weaker lately" is a claim
# people act on constantly, and the sample needed to support it is far larger
# than people expect. Eighteen years of daily data on 25 ETFs is not enough to
# detect a halving of a weak signal.
#
# So how would you know? Not from the outcome, at least not quickly. What you
# can see immediately is the **input** side, and this data does show drift
# there. The features this model reads are not drawn from a stable distribution.

# %%
usable = dataset.dropna(subset=["vol_21", "mom_252", "fwd_ret_21"]).copy()
usable["year"] = usable["timestamp"].dt.year
input_drift = usable.groupby("year")[["vol_21", "mom_252"]].agg(["mean", "std"]).round(4)
input_drift

# %%
ax = usable.groupby("year")["vol_21"].mean().plot(
    figsize=(10, 3), marker="o",
    title="Mean 21-session realized volatility, by year: the model's input distribution",
)
ax.set_xlabel("")
ax.figure.tight_layout()

# %% [markdown]
# Mean 21-session volatility runs from 0.0056 in 2017 to 0.0234 in 2008, a
# factor of four. A model fitted mostly on quiet years is asked to score inputs
# from a loud one, and nothing in the pipeline notices or complains.
#
# This is the drift you can actually detect in a workshop, and in production it
# is the one that warns you first, because it needs no outcomes at all. Three
# things are worth logging from the day a model goes live:
#
# 1. **Input distribution.** Per feature, per period: mean, standard deviation,
#    and the share of live values falling outside the training range. Alerts
#    here fire immediately, long before any label has resolved.
# 2. **Prediction distribution.** The spread of the model's own output. A model
#    whose predictions collapse toward a constant has stopped discriminating,
#    which is visible without waiting for returns.
# 3. **Realized IC, on a rolling window, with the corrected statistic.** This is
#    the one people reach for first and it is the slowest: a 21-session label
#    resolves 21 sessions late, and section 5 just showed that a year of it is
#    not enough to conclude anything. Treat it as confirmation, not as an alarm.
#
# ### The obvious fix, measured
#
# The reflex when a model might be stale is to retrain more often. The agent's
# pipeline uses five expanding folds over eighteen years, so a model can be
# nearly three years old by the end of the period it is scored on. Try fifteen
# folds instead, which keeps it under one year old. Nothing else changes.

# %%
original_n_splits = agent_model.N_SPLITS
agent_model.N_SPLITS = 15
try:
    frequent = score(run_walk_forward(dataset))
finally:
    agent_model.N_SPLITS = original_n_splits

cadence = pd.DataFrame(
    {"retrain 5 times": results["as the agent wrote it"], "retrain 15 times": frequent}
).T[["mean_ic", "naive_t", "hac_t", "n_predictions"]]
cadence.round(4)

# %% [markdown]
# Retraining three times as often made the result worse, not better. The reason
# is not that fresher models are bad: it is that with fifteen folds the early
# models are fitted on about a year of data each, and a model fitted on a year
# of 25 ETFs has nothing to say.
#
# Retraining cadence is a trade between staleness and sample size. It has a
# right answer for a given dataset and the answer is not "more often". Measure
# it before you change it.

# %% [markdown]
# ## 7. The checklist
#
# `CHECKLIST.md` in this repository is the full version, with what each item
# caught. Six checks under three questions, all of them demonstrated above
# rather than asserted:
#
# **What are you predicting?**
#
# 1. **Say what the filter removed.** A retention percentage, printed. `98.4%`
#    here.
# 2. **Prove the label's direction on a worked example.** Two real dates, a
#    hand-computed value, an equality check. Never an assertion in a comment.
#
# **What was knowable when?**
#
# 3. **Never a shuffled split on overlapping labels.** Walk forward, and purge
#    the label horizon at every boundary.
# 4. **Check the claims in the comments, not just the code.** The agent's
#    reasoning about gaps was correct in shape and false about this dataset.
#
# **Does the evidence say what you think it says?**
#
# 5. **Report the corrected statistic beside the naive one, always together.**
#    A naive t-statistic published alone is a false positive waiting to be
#    acted on.
# 6. **Break the headline down until it stops holding.** By year, by regime, by
#    symbol. Then say what the breakdown can and cannot establish.
#
# None of these is specific to agents. They are what you check in any research
# result, including your own. What changes with an agent is that the code
# arrives faster than you can read it, and the explanation attached to it is
# fluent enough to be convincing whether or not it is true.

# %% [markdown]
# ### What a team does with this on Monday
#
# Each check above is a few lines of test that then never has to be remembered
# again. The middle column is the one that pays.
#
# | Delegate to the agent | Automate as a test | The human owns |
# |---|---|---|
# | Writing the pipeline | Label direction, on a worked example | The research question |
# | Implementing features | Fold boundaries and purge width | What the result has to clear |
# | Running the experiment | Retention and sample assertions | The economic reading |
# | Producing diagnostics | Both statistics reported together | The capital decision |
# | Drafting the write-up | Reproducing the headline from a clean checkout | Every exception to the above |
#
# The agent wrote this entire study in four minutes, and it was sound. What it
# did not do was decide what question to ask, what the result had to clear, or
# what any of it was worth. The agent can write the research. You still own the
# proof.
