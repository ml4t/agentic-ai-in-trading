# Environment: instructed-precise

Written by `capture/lib/environment_statement.sh` at
2026-09-18T15:33:10Z, from the image and the working tree the run used.

## The cell

| | |
|---|---|
| Repository environment | `instructed` |
| Brief | `briefs/02-precise.md` |
| Operator replies allowed | 3. A brief that asks the agent to stop and show its work needs someone to answer; each reply sent is recorded verbatim in `replies.txt` |

These two lines are the experimental variable. Everything below is held fixed
across the matrix.

## Agent

| | |
|---|---|
| Model | `claude-sonnet-5` |
| CLI | 2.1.276 (Claude Code) |
| Permission mode | `bypassPermissions`, no tool allowlist |
| Settings sources | `project` only. No user settings, no local settings |
| MCP servers | none (`--strict-mcp-config`, no config supplied) |
| Authentication | `CLAUDE_CODE_OAUTH_TOKEN` from the host environment |
| Skills installed | none beyond the CLI built-ins |

## Clean room

| | |
|---|---|
| Image | `atc26-cleanroom:2.1.276` |
| Image id | `sha256:4d3444b9b2c06b050e6f01b4f6492de50b1f8035e1eaa498b5940a55187f9596` |
| Base | `node:22.22.0-bookworm-slim` |
| HOME inside the container | `/home/agent`, created by the image, empty of agent configuration |
| Host configuration reaching the run | none. `~/.claude` is not mounted; the only host value passed is the OAuth token, as an environment variable |

## Working tree

| | |
|---|---|
| Starting state | `555a8913c058f633a7930f438633ae9d9471b18e` (`attendee-repo` HEAD) |
| Baseline the diff is taken against | `6294c59e192c5a172635e6cebed1c98feb3df3b7` |
| Instruction files present | `./AGENTS.md` `./CLAUDE.md` |
| `uv` | uv 0.10.9 |
| Python | 3.12.13 |

### Price data

Identical bytes in every run, copied from `capture/cache/` into a gitignored
`data/`, so no run differs by what Yahoo returned on the day.

| File | SHA-256 |
|---|---|
| `data/prices.parquet` | `89b387bf31efec16e11f3b5f601272e81c53e05bc681c8e1243ae7dff4b5c829` |
| `data/eligibility.csv` | `1deb6ed5633e7e89840760cc33f459196f6c9da3b5d4c37093980f07b5eccee4` |

### Resolved dependencies

```
Package                 Version
----------------------- ------------
annotated-types         0.8.0
arch                    8.0.0
beautifulsoup4          4.15.0
certifi                 2026.7.22
cffi                    2.1.1
charset-normalizer      3.5.1
cloudpickle             3.1.2
curl-cffi               0.16.3
exchange-calendars      4.13.2
idna                    3.20
jinja2                  3.1.6
joblib                  1.6.0
korean-lunar-calendar   0.4.0
lightgbm                4.6.0
llvmlite                0.49.0
lxml                    6.1.3
markupsafe              3.0.3
ml4t-diagnostic         0.1.5
ml4t-engineer           0.1.4
ml4t-specs              0.1.4
multitasking            0.0.13
numba                   0.67.0
numpy                   2.3.4
packaging               26.3
pandas                  2.3.3
pandas-market-calendars 5.4.0
patsy                   1.0.3
peewee                  4.5.1
platformdirs            4.11.10
polars                  1.35.2
polars-runtime-32       1.35.2
protobuf                7.36.2
pyarrow                 22.0.0
pycparser               3.0
pydantic                2.13.5
pydantic-core           2.46.5
pyluach                 2.3.0
python-dateutil         2.9.0.post0
pytz                    2026.3.post1
pyyaml                  6.0.3
requests                2.34.2
scikit-learn            1.7.2
scipy                   1.18.1
six                     1.17.0
soupsieve               2.9.2
statsmodels             0.14.6
structlog               26.1.0
threadpoolctl           3.7.0
toolz                   1.1.0
tqdm                    4.70.1
typing-extensions       4.16.0
typing-inspection       0.4.4
tzdata                  2026.4
urllib3                 2.8.0
websockets              17.1
yfinance                1.7.0
```
