# AI Study Coach

A study coach for Egyptian university students: upload lectures, get summaries and quizzes, a study plan that re-plans after every quiz, and a readiness score per exam.

**Week 1 is data only.** Three pairs build the datasets for three models in the app's own formats, using the same preprocessing code the app will run. Tasks live in the GitHub project board and the issues of this repo.

| Model | What it does in the app | Lead | Partner | Code |
| --- | --- | --- | --- | --- |
| A — Student knowledge model | Predicts mastery per topic from quiz answers | Amr | Hager | `ml_core/knowledge/`, `ml/knowledge/` |
| B — Lecture speech-to-text | Transcribes Egyptian lectures mixing Arabic and English | Omar Negm | Fares | `ml_core/speech/`, `ml/speech/` |
| C — Lecture topic classifier | Tags each lecture chunk with its course topic | Omar Mustafa | Mariam | `ml_core/topics/`, `ml/topics/` |

## Repository layout

```
study-coach/
├── ml_core/                 # shared package: training AND the app's worker import it
│   ├── schemas.py           # app-shaped rows: Attempt, Segment, Chunk
│   ├── text_normalize.py    # shared Arabic rules (Amr)
│   ├── cleaning_log.py      # logs rows in/out per cleaning step
│   ├── knowledge/           # features.py, predict.py (Amr)
│   ├── speech/              # audio.py, predict.py (Omar)
│   ├── topics/              # extract.py, clean.py, predict.py (Mariam, Omar Mustafa)
│   └── tests/               # unit tests + contract tests for every predict()
├── ml/                      # training only; the app never imports it
│   ├── knowledge/ speech/ topics/
│   │   ├── notebooks/       # exploration only
│   │   ├── scripts/         # build_dataset.py, split.py
│   │   ├── configs/         # thresholds and paths in YAML
│   │   └── data_card.md
│   └── data/                # NOT in Git — tracked with DVC (raw/ interim/ processed/)
├── apps/web/                # Next.js app (from Week 2)
├── services/api/            # FastAPI (from Week 2)
├── services/worker/         # processing jobs; imports ml_core
├── db/migrations/ db/seed/
├── evals/  tests/fixtures/  docs/
├── CLAUDE.md                # conventions Claude reads every session
└── CONTRIBUTING.md          # branches, commits, PRs, Definition of Done
```

## Getting started

```bash
git clone https://github.com/NEGM18/study-coach.git
cd study-coach
pip install uv                       # once
uv sync --extra dev                  # installs ml_core + test tools
uv run pytest                        # all tests should pass or be marked xfail
uv run ruff check . && uv run ruff format --check .
```

Data is never committed. Once Amr sets up DVC (issue #11), pull it with `dvc pull`.

## How we work

1. Pick your issue on the project board and move it to **In progress**.
2. Branch from `main`: `data/<model>-<task>`, e.g. `data/speech-vad-segmentation`.
3. Build it (with Claude), add tests, run `uv run pytest` and `ruff`.
4. Open a PR with the template. Omar reviews every PR; Amr reviews Omar's.
5. Squash-merge, close the issue with proof (counts, a screenshot or a sample).

Full rules: [CONTRIBUTING.md](CONTRIBUTING.md) and [CLAUDE.md](CLAUDE.md).
