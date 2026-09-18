# Agentic AI in Trading

Materials for the opening workshop of QuantInsti's Algorithmic Trading
Conference 2026, Thursday 24 September.

A coding agent was given a research brief and a panel of daily ETF prices, and
it wrote a complete predictive pipeline: data loading, features, a label, a
model, an evaluation. This repository holds what it wrote, the transcript of the
run that wrote it, and a notebook that runs the code and takes it apart.

## Start here

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ml4t/agentic-ai-in-trading/blob/main/notebooks/audit.ipynb)

[**`notebooks/audit.ipynb`**](notebooks/audit.ipynb) explains what the strategy
is, reproduces the agent's headline result, then changes one line at a time and
watches the result move.

**It is committed with the outputs of a real run**, so you can read every number
on GitHub without executing anything. To run it yourself, open it in Colab: it
takes about three minutes, and needs nothing installed, no account beyond a
Google login, no API key, and no agent on your side. During the workshop the
presenter runs it; you are not asked to execute anything live.

[**`CHECKLIST.md`**](CHECKLIST.md) is the takeaway: six checks under three
questions - what are you predicting, what was knowable when, does the evidence
say what you think it says - each one demonstrated in the notebook rather than
asserted.

## What is here

| Path | What it holds |
|---|---|
| `notebooks/audit.ipynb` | The notebook, with stored outputs. Paired with `audit.py` via jupytext |
| `src/` | The five modules the agent wrote, **copied unedited** from `runs/instructed-precise/` |
| `CHECKLIST.md` | Six checks, with what each one caught |
| `briefs/` | The two research briefs handed to the agent, byte for byte |
| `runs/` | Four captured runs: environment, transcript, diff, findings |
| `scripts/fetch_prices.py` | Downloads the price panel from Yahoo Finance |

### The four runs

The same model, the same container, the same data, the same task. Two research
briefs across two repository setups:

| Run | Brief | Repository | Wall clock | Headline |
|---|---|---|---|---|
| `bare-loose` | one sentence | no instructions | 4m 02s | long-short Sharpe 0.06 gross, -0.02 net |
| `instructed-loose` | one sentence | research standards in `AGENTS.md` | 6m 28s | mean IC 0.0436, naive t 6.90, corrected t 1.99 |
| `bare-precise` | five numbered steps | no instructions | 10m 16s | mean IC 0.0285, naive t 6.10, corrected t 2.01 |
| `instructed-precise` | five numbered steps | research standards in `AGENTS.md` | 4m 02s | mean IC 0.0282, naive t 6.104, corrected t 2.013 |

All four answered the research question in the negative, which is the correct
answer. They differ in how much evidence each one handed back. Each run
directory carries its own `ENVIRONMENT.md` stating the model, the harness
version, the container image, the home directory and the data checksums, so any
two can be compared knowing exactly what differed.

`src/` in this repository is `instructed-precise`'s output, unedited. Its
docstrings and comments are the agent's own and are part of what the notebook
audits.

## Running it locally

The price data is not shipped with this repository: the panel it came from may
not be redistributed, so the fetch script downloads its own from Yahoo Finance.

```bash
uv sync
uv run python scripts/fetch_prices.py     # writes data/, gitignored
```

Then open `notebooks/audit.ipynb` in Jupyter or VS Code. Python 3.12 and
[uv](https://docs.astral.sh/uv/). To run the agent's pipeline on its own,
exactly as the agent ran it:

```bash
uv run python -m src.evaluate
```

## License

MIT, including the code the agent wrote. The price data is not covered: it is
not shipped here and is downloaded from Yahoo Finance at run time, under
whatever terms that source imposes.

## Where this continues

The workshop covers one iteration of one stage of a research workflow. The
[Machine Learning for Trading](https://github.com/stefan-jansen/machine-learning-for-trading)
repository and book cover the whole of it, including the chapters on autonomous
agents and on monitoring a model after it is deployed.
