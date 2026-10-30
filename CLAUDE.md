# CLAUDE.md — conventions for this repo

Read this before writing any code here. If a request conflicts with these rules, say so instead of breaking them.

## Project

AI Study Coach: an app for Egyptian university students. Three ML models:
- **A — knowledge** (`ml_core/knowledge`): predicts the chance a student answers the next question on a topic correctly.
- **B — speech** (`ml_core/speech`): transcribes Egyptian Arabic lectures that mix Arabic and English.
- **C — topics** (`ml_core/topics`): tags lecture text chunks with a topic from the course syllabus.

## The three integration rules

1. **One pipeline, two uses.** All preprocessing lives in `ml_core/`, which both training scripts and the app's worker import. Never put preprocessing only in a notebook or a training script.
2. **App-shaped data.** Datasets use the same column names and types as the app tables (`quiz_attempts`, `lecture_chunks`, `course_topics`, `topic_mastery`). Row formats are defined in `ml_core/schemas.py`.
3. **Fixed `predict()` contracts.** Each model exposes one function in `ml_core/<model>/predict.py` with typed input and output from `schemas.py`. Week 1 builds a stub; the trained model later replaces it behind the same function.

| Model | Function | Input | Output |
| --- | --- | --- | --- |
| A | `predict_mastery(history, topic_id)` | `list[Attempt]` | `float` in [0, 1] |
| B | `transcribe(audio_path)` | `str` path | `list[Segment]` |
| C | `classify_chunks(chunks, topics)` | `list[Chunk]`, `list[Topic]` | `list[TopicPrediction]` |

## Naming

| What | Style | Example |
| --- | --- | --- |
| Python variables and functions | snake_case | `lecture_id`, `build_features()` |
| Python classes | PascalCase | `Attempt`, `Segment` |
| Constants | UPPER_SNAKE_CASE | `MAX_CLIP_SECONDS = 30` |
| Files | snake_case | `text_normalize.py` |
| Booleans | `is_` / `has_` prefix | `is_correct`, `has_english` |
| Dataset files | `<model>_<stage>_v<n>.<ext>` | `kt_processed_v1.parquet` |
| Table columns | exactly the app's DB column names | `user_id`, `topic_id`, `is_correct` |
| Audio | FLAC, 16 kHz, mono | `ds_lec03_seg0042.flac` |
| Raw recordings | `<course>_lec<nn>_<yyyymmdd>.<ext>` | `ds_lec03_20261102.m4a` |
| Scripts | run as modules with a config | `python -m ml.speech.scripts.build_dataset --config ml/speech/configs/build.yaml` |
| Branches | `data/<model>-<task>` | `data/topics-ocr-extraction` |
| Commits | Conventional Commits | `feat(speech): add VAD segmentation` |

## Code rules

- Python 3.12, type hints on every function, Ruff for lint and format.
- Functions under ~50 lines; split anything longer.
- Code in `ml_core/` takes its inputs as arguments and never reads from `ml/data/`, so the worker can call it on a single upload.
- Thresholds and paths go in YAML configs under `ml/<model>/configs/`, not in code.
- Every cleaning step logs rows in, rows out and a reason with `ml_core.cleaning_log`.
- Random seed 42 everywhere. Splits are by student, speaker or lecture — never by random row.
- Every cleaning or feature function gets a unit test in `ml_core/tests/`.
- Notebooks are for looking only. Anything that changes data runs from the command line.
- No `print` in `ml_core/`; use `logging`.
- No new library without asking Omar; add it to `pyproject.toml` in the same PR.

## Deployment rules (full version: README section 5)

- Week 1: data work merges into `main`; no deployments. From Week 2: `dev` = staging (auto-deploy), `main` = production (weekly release by Omar).
- Trained models are saved as `<model>_model_v<n>/` in DVC with a `model_card.md`.
- The worker picks model versions from env vars `KNOWLEDGE_MODEL_VERSION`, `SPEECH_MODEL_VERSION`, `TOPICS_MODEL_VERSION` (`stub`, `v1`, …). Never hard-code a model version or path.
- A model replaces its stub only if it beats the stub on the test set, passes the contract tests, meets its speed target and runs a full day on staging.
- Database changes are new numbered files in `db/migrations/`; changes to `quiz_attempts`, `lecture_chunks` or `course_topics` update `ml_core/schemas.py` in the same PR.
- Never commit `.env` or any key. A leaked key is revoked the same day.

## Data rules

- `ml/data/` is never committed to Git. Use DVC: `dvc add`, `dvc push`, commit the `.dvc` file.
- `ml/data/raw/` is read-only: never edit a downloaded or recorded file.
- Every dataset has `ml/<model>/data_card.md`: source, license, size, cleaning steps with counts, splits, known issues.
- Privacy: hash user IDs, no names (professors are P1, P2…), record lectures only with permission.
- Never paste raw student data, audio or API keys into a chat. Schemas and a few made-up rows are fine.

## Arabic text normalization

Use `ml_core.text_normalize`; never write your own version.
- `normalize_for_training()`: remove diacritics and tatweel, unify alef forms (أ إ آ -> ا), Arabic-Indic digits -> Western, English words in Latin script lowercased, remove non-speech tags like [music], collapse spaces.
- `normalize_for_eval()`: all of the above plus ى -> ي, ة -> ه, and punctuation removed.
- Transcribe what the speaker says, in the script they say it in. Don't translate, correct grammar, or convert dialect to MSA.
