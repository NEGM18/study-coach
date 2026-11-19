# AI Study Coach

A study coach for Egyptian university students, delivered as a Flutter app for Android and iOS. Students upload lectures and get summaries and quizzes. The app builds a study plan that re-plans after every quiz and shows a readiness score for each exam.

This README is the team's rulebook: folder structure, code rules, Git workflow and deployment rules. `CLAUDE.md` holds the same code rules in the form Claude reads, so keep the two in sync.

---

## 1. Team and models

| Model | What it does in the app | Lead | Partner | Code |
| --- | --- | --- | --- | --- |
| A — Student knowledge model | Predicts mastery per topic from quiz answers | Amr | Hager | `ml_core/knowledge/`, `ml/knowledge/` |
| B — Lecture speech-to-text | Transcribes Egyptian lectures mixing Arabic and English | Omar Negm | Fares | `ml_core/speech/`, `ml/speech/` |
| C — Lecture topic classifier | Tags each lecture chunk with its course topic | Omar Mustafa | Mariam | `ml_core/topics/`, `ml/topics/` |

Omar Negm is the team lead and reviews every PR; Amr reviews Omar's. Tasks live on the [project board](https://github.com/users/NEGM18/projects/4). Week 1 issues #1–#28 match the Week 1 Data Plan tracker; Week 2 issues #35–#57 are tasks W2-01 to W2-23 in `docs/week2_plan.pdf` (W2-NN = issue #(34+NN)). Current status and the plan: [section 7](#7-status-and-roadmap).

---

## 2. Folder structure

```
study-coach/
├── ml_core/                     # shared package: training AND the app's worker import it
│   ├── schemas.py               # app-shaped rows: Attempt, Segment, Chunk, Topic, TopicPrediction
│   ├── text_normalize.py        # shared Arabic rules (Amr)
│   ├── cleaning_log.py          # logs rows in/out per cleaning step (Amr)
│   ├── registry.py              # get_predictor(model): picks stub/v1/... from *_MODEL_VERSION env vars
│   ├── knowledge/               # features.py, predict.py            (model A — Amr)
│   ├── speech/                  # audio.py, predict.py               (model B — Omar Negm)
│   ├── topics/                  # extract.py, clean.py, predict.py   (model C — Mariam, Omar Mustafa)
│   └── tests/                   # unit tests + contract tests for every predict()
├── ml/                          # training only; the app never imports it
│   ├── knowledge/ speech/ topics/
│   │   ├── notebooks/           # exploration only: 01_eda.ipynb, 02_checks.ipynb
│   │   ├── scripts/             # build_dataset.py, split.py, train.py
│   │   ├── configs/             # thresholds and paths in YAML, never in code
│   │   └── data_card.md         # source, license, cleaning counts, splits, known issues
│   └── data/                    # NOT in Git — tracked with DVC
│       ├── raw/                 # untouched downloads and recordings, read-only
│       ├── interim/             # extracted and partly cleaned
│       ├── processed/           # final, app-shaped, split, ready to train
│       └── models/              # <model>_model_v<n>/ + model_card.md (from Week 2)
├── apps/mobile/                 # Flutter app for Android and iOS (from Week 2) — see apps/mobile/README.md
│   ├── lib/core/                # config, API client, router, theme, shared widgets
│   ├── lib/features/<feature>/  # data/ domain/ presentation/ per feature
│   ├── lib/l10n/                # app_ar.arb (default), app_en.arb
│   ├── test/ integration_test/
│   └── config/                  # <flavor>.json for --dart-define-from-file (only .example in Git)
├── services/
│   ├── api/                     # FastAPI (from Week 2)
│   └── worker/                  # processing jobs; imports ml_core
├── db/
│   ├── migrations/              # numbered SQL files: 0001_init.sql, 0002_...
│   └── seed/                    # course_topics_seed.json, catalog.json
├── evals/                       # LLM and model quality checks
├── tests/fixtures/              # small, anonymized sample files only
├── docs/                        # labeling guide, QA checklists, week plans (week2_plan.pdf)
├── .github/                     # CI, PR template, issue template
├── CLAUDE.md                    # code rules for Claude
├── CONTRIBUTING.md              # short version of sections 4–5
├── pyproject.toml               # Python package + Ruff + pytest config
└── .env.example                 # every env var, no values
```

**Where does my code go?**

| If your code… | Put it in |
| --- | --- |
| prepares data the app will also see (normalize, extract, cut audio, build features) | `ml_core/<model>/` |
| predicts something for the app | `ml_core/<model>/predict.py` |
| is a one-off dataset build, split or training run | `ml/<model>/scripts/` |
| only explores or plots | `ml/<model>/notebooks/` |
| tests anything in `ml_core/` | `ml_core/tests/` |
| is a screen, widget or provider for one feature | `apps/mobile/lib/features/<feature>/presentation/` |
| calls our API from the app | `apps/mobile/lib/features/<feature>/data/` through `core/network/api_client.dart` |
| is used by two or more features in the app | `apps/mobile/lib/core/` |

---

## 3. Code rules

### 3.1 The three integration rules

1. **One pipeline, two uses.** All preprocessing lives in `ml_core/`, which both training scripts and the app's worker import. Preprocessing never lives only in a notebook or training script.
2. **App-shaped data.** Datasets use the same column names and types as the app tables (`quiz_attempts`, `lecture_chunks`, `course_topics`, `topic_mastery`). Row formats are defined once in `ml_core/schemas.py`.
3. **Fixed `predict()` contracts.** Each model exposes one function with typed input and output. Week 1 builds a stub; the trained model later replaces it behind the same function, and the stub stays as the fallback.

| Model | Function | Input | Output | Saved to app table | Week 1 stub |
| --- | --- | --- | --- | --- | --- |
| A | `predict_mastery(history, topic_id)` | `list[Attempt]` | `float` in [0, 1] | `topic_mastery` | Smoothed correct rate on the topic |
| B | `transcribe(audio_path)` | `str` path | `list[Segment]` | `lectures`, `lecture_chunks` | Gemini audio transcription |
| C | `classify_chunks(chunks, topics)` | `list[Chunk]`, `list[Topic]` | `list[TopicPrediction]` | `lecture_chunks` | Embedding similarity to syllabus topics |

### 3.2 Naming

Code and names are in English; only user-facing text is in Arabic.

| What | Style | Example |
| --- | --- | --- |
| Python variables and functions | snake_case | `lecture_id`, `build_features()` |
| Python classes | PascalCase | `Attempt`, `CleaningLog` |
| Constants | UPPER_SNAKE_CASE | `MAX_CLIP_SECONDS = 30` |
| Python files | snake_case | `text_normalize.py` |
| Booleans | `is_` / `has_` prefix | `is_correct`, `has_english` |
| Prediction functions | verb + object, typed with `schemas.py` | `transcribe(audio_path: str) -> list[Segment]` |
| Table columns | exactly the app's database column names | `user_id`, `topic_id`, `is_correct` |
| Dataset files | `<model>_<stage>_v<n>.<ext>` | `kt_processed_v1.parquet`, `speech_test_v1.jsonl` |
| Model files | `<model>_model_v<n>/` + `model_card.md` | `speech_model_v1/` |
| Audio | FLAC, 16 kHz, mono | `ds_lec03_seg0042.flac` |
| Raw recordings | `<course>_lec<nn>_<yyyymmdd>.<ext>` | `ds_lec03_20261102.m4a` |
| Scripts | run as modules with a config | `python -m ml.speech.scripts.build_dataset --config ml/speech/configs/build.yaml` |
| Configs | `<step>.yaml` | `build.yaml`, `train.yaml` |
| Migrations | `NNNN_description.sql` | `0002_course_topics.sql` |
| Env vars and dart-defines | UPPER_SNAKE_CASE | `GEMINI_API_KEY`, `API_BASE_URL` |

### 3.3 Writing code

- Python 3.12. Type hints on every function. Ruff for lint and format (`uv run ruff check . && uv run ruff format .`).
- Functions under about 50 lines; split anything longer.
- Code in `ml_core/` takes its inputs as arguments and never reads from `ml/data/`, so the worker can call it on a single upload.
- Thresholds, paths and model versions go in YAML configs, not in code.
- No new library without asking Omar first; add it to `pyproject.toml` in the same PR.
- No `print` in `ml_core/`; use `logging`. Scripts in `ml/` may print summaries.
- No secrets, API keys or real student data in code, commits, issues or chats.

### 3.4 Data rules

- `ml/data/` is never committed to Git. Use DVC: `dvc add <path>`, `dvc push`, commit the `.dvc` file.
- `ml/data/raw/` is read-only: never edit a downloaded or recorded file. Every change is a script you can re-run.
- Every cleaning step logs rows in, rows out and a reason with `ml_core.cleaning_log.CleaningLog`.
- Random seed 42 everywhere. Splits are by student, speaker or lecture — never by random row — so nothing leaks between train and test.
- Every dataset has `ml/<model>/data_card.md`: source, license, size, cleaning steps with counts, splits, known issues.
- Privacy: hash user IDs, no names (professors are P1, P2…), record lectures only with permission. Never paste raw student data, audio or keys into Claude; schemas and a few made-up rows are fine.

### 3.5 Arabic text normalization

Always use `ml_core.text_normalize`; never write your own version.

| Function | Rules |
| --- | --- |
| `normalize_for_training()` | Remove diacritics and tatweel; unify alef forms (أ إ آ -> ا); Arabic-Indic digits -> Western; English words stay in Latin script, lowercased; remove non-speech tags like [music]; collapse spaces |
| `normalize_for_eval()` | Everything above, plus ى -> ي, ة -> ه, and punctuation removed |

Transcribe what the speaker says, in the script they say it in. Don't translate, correct grammar, or convert dialect to MSA.

### 3.6 Flutter app rules (`apps/mobile/`)

**Stack:** Flutter stable, Riverpod (state), go_router (navigation), dio (HTTP), supabase_flutter (auth only), freezed + json_serializable (models), very_good_analysis (lints), flutter_localizations + ARB files (Arabic and English).

| What | Style | Example |
| --- | --- | --- |
| Dart files and folders | snake_case | `quiz_screen.dart`, `study_plan/` |
| Classes, widgets, enums | UpperCamelCase | `QuizScreen`, `ReadinessCard` |
| Variables, functions, params | lowerCamelCase | `lectureId`, `fetchSummary()` |
| Constants | lowerCamelCase (Dart style) | `const maxUploadMb = 50;` |
| Private members | leading underscore | `_selectedTopic` |
| Booleans | `is` / `has` prefix | `isCorrect`, `hasAccess` |
| Screens / widgets / providers | suffix by kind | `QuizScreen`, `QuizCard`, `quizProvider` |
| Routes | kebab-case paths | `/courses/:courseId/quiz` |
| Translation keys (ARB) | lowerCamelCase, grouped by feature | `quizSubmitButton` |

- **Feature-first folders.** Each feature has `data/` (API + JSON models), `domain/` (entities, logic) and `presentation/` (screens, widgets, providers). Features never import each other's `data/`; share through `core/`.
- **The app never calls Gemini or any model directly.** It talks only to our API through `core/network/api_client.dart`. All AI calls, keys and cost limits stay on the server.
- **JSON stays snake_case** on the wire. Dart models use `@JsonSerializable(fieldRename: FieldRename.snake)`, so `lecture_id` maps to `lectureId`.
- **Arabic first and right-to-left.** Every user-facing string goes in `lib/l10n/*.arb`, never hard-coded. Use `EdgeInsetsDirectional` and `AlignmentDirectional`, not left/right, so layouts flip correctly.
- **No business logic in widgets.** Widgets read providers and render; logic lives in `domain/` or providers.
- **Generated files** (`*.g.dart`, `*.freezed.dart`) are not edited by hand; run `dart run build_runner build`.
- `dart format` and `flutter analyze --fatal-infos` must pass. No `print`; use `debugPrint` or a logger.
- Config comes only from `--dart-define-from-file=config/<flavor>.json`: `API_BASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `FLAVOR`. Nothing secret goes in the app — anything in an app can be extracted.

### 3.7 Testing

| Type | What it covers | Runs when |
| --- | --- | --- |
| Unit tests (`pytest`) | Every cleaning, feature and extraction function | Every PR in CI |
| Contract tests | Every `predict()` returns valid app-shaped output | Every PR in CI |
| Flutter unit and widget tests (`flutter test`) | Providers, models, key widgets in Arabic (RTL) and English | Every PR in CI |
| Flutter integration tests | Sign up -> upload a lecture -> take a quiz -> see the plan | Before each release |
| Data checks | Spot-checks of processed samples against raw (20–30 per dataset) | Before a dataset version is pushed |
| Model evaluation | Test-set score vs. the stub and the baseline | Before a model is released |

- Test files mirror the code: `ml_core/topics/clean.py` -> `ml_core/tests/test_topics_clean.py`; `lib/features/quizzes/presentation/quiz_screen.dart` -> `test/features/quizzes/presentation/quiz_screen_test.dart`.
- Contract tests are marked `xfail` until the stub exists. Remove the marker in the PR that builds it.
- A bug becomes an issue with steps to reproduce, then a test that fails before the fix.

---

## 4. Git workflow

### 4.1 Branches

| Branch | Purpose | Who merges |
| --- | --- | --- |
| `main` | Production. Week 1: all data work merges here. | Omar, through reviewed PRs only |
| `dev` | Staging. Created in Week 2 when app code starts; app work merges here. | Omar or Amr, through reviewed PRs |
| `data/<model>-<task>` | Data and ML work | — |
| `feature/<issue>-<short-name>`, `fix/<issue>-<short-name>` | App work (from Week 2) | — |

### 4.2 Commits

Conventional Commits, one change per commit:
`feat(speech): add VAD segmentation` · `fix(topics): keep slide titles during header removal` · `test(knowledge): no-future-leak check` · `data(topics): add topics_processed_v1` · `docs: update data card`

### 4.3 Delivering a task

1. Move your issue to **In Progress** on the board.
2. `git checkout main && git pull && git checkout -b data/<model>-<task>`
3. Build it, run it on real data, add or update tests.
4. `uv run pytest && uv run ruff check . && uv run ruff format --check .`
5. Open a PR with the template and link the issue (`Closes #12`).
6. The reviewer approves or requests changes within 24 hours.
7. Squash-merge, check the result, and close the issue with proof: counts from `cleaning_log.csv`, a screenshot or 5 sample rows.

### 4.4 Review rules

- Omar reviews every PR; Amr reviews Omar's. Fares and Hager ask their pair lead for a first look before requesting Omar.
- Keep PRs under about 400 changed lines; split bigger work.
- The reviewer checks that it works, follows these rules, has tests, and has no secrets or raw data.

### 4.5 Definition of Done

- [ ] Merged with CI green
- [ ] Tests added or updated
- [ ] Data (if any) pushed to DVC and the `.dvc` file committed
- [ ] Data card or model card updated if anything changed
- [ ] Issue closed with proof

---

## 5. Deployment rules

### 5.1 Environments

Each environment has its own database and keys, so testing never touches real students.

| Environment | Branch | Mobile app (flavor) | API and worker | Database | Deploys |
| --- | --- | --- | --- | --- | --- |
| Local | your branch | Emulator or your phone, `config/dev.json` | localhost:8000 | Supabase dev project | You run it |
| Staging | `dev` | Test build via Firebase App Distribution, `config/staging.json` | Railway staging | Supabase staging project | API and worker automatically on every merge; app build by Omar Mustafa when the app changed |
| Production | `main` | Google Play (internal testing during the pilot), `config/prod.json` | Railway production | Supabase production project | Weekly release by Omar |

Week 1 has no deployments: data work merges into `main` and only CI runs.

### 5.2 Mobile app builds

- **One codebase, three flavors.** The flavor only changes `config/<flavor>.json`: `flutter build apk --release --dart-define-from-file=config/staging.json`.
- **Pilot on Android first.** The 20 pilot students get the app through Google Play internal testing (or Firebase App Distribution for quick staging builds). iPhone users need the Apple Developer Program ($99/year) and TestFlight; decide in Week 3 based on how many pilot students use iPhones.
- **Versioning.** `pubspec.yaml` `version: <major>.<minor>.<patch>+<build>`. The minor number is the week (`0.2.0` = Week 2), and the build number goes up by 1 on every build uploaded anywhere.
- **Signing.** The Android upload keystore and `key.properties` are never committed. Omar keeps the keystore and a backup; losing it means the app can't be updated on Google Play.
- **The app and the API must stay compatible.** The API only adds fields under `/api/v1`; it never renames or removes one while an older app version is installed. Breaking changes go to `/api/v2`.
- **Before a build goes out:** `flutter analyze` and `flutter test` pass, the integration test passes on staging, and it's checked on one real Android phone in Arabic and English.

### 5.3 Weekly release (end of each week, after the Day 7 review)

1. Everything planned for the week is merged into `dev` and checked on staging.
2. The manual QA checklist in `docs/qa/` is run on staging; bugs become issues.
3. Omar opens a release PR from `dev` to `main`, titled `release: week-<n>`, and merges after the demo.
4. Amr applies new migrations to production and checks the health endpoint.
5. If the app changed, Omar Mustafa bumps the version in `pubspec.yaml`, builds with `config/prod.json` and uploads it to Google Play internal testing. The API goes out first, then the app.
6. Omar tags the release: `git tag v0.<week>.0 && git push --tags`.
7. If production breaks: revert the release PR on `main` (a new revert commit, never a force-push) and redeploy. An app build can't be pulled back from phones, so fix forward with a new build, and keep the API compatible with the version already installed.

### 5.4 Deploying a model into the app

A trained model replaces its stub only when every box is ticked:

- [ ] It beats its stub on the held-out test set (and model A beats the PFA baseline: AUC 0.717 on the original file; re-measured on `kt_processed_v1` in W2-09, and that number is the bar)
- [ ] Its weights are versioned in DVC as `<model>_model_v<n>/` with a `model_card.md`: data version, metrics, known failures
- [ ] Its `predict()` passes the same contract tests as the stub
- [ ] It meets its speed target on our server: A under 100 ms per call, C under 5 s per lecture, B at most half the audio's length
- [ ] It runs inside the worker on staging for at least one full day of real uploads without errors

**How the switch works.** The worker picks each model's version from an env var: `KNOWLEDGE_MODEL_VERSION`, `SPEECH_MODEL_VERSION`, `TOPICS_MODEL_VERSION`. The value is `stub`, `v1`, `v2` and so on. Releasing a model means changing that value on staging, then on production during the weekly release.

**Rollback** means setting the variable back to the previous version or `stub` and restarting the worker. No code change is needed.

### 5.5 Database changes

- Every change is a new numbered file in `db/migrations/`. Never edit an old one.
- Amr applies it on staging first, then on production during the weekly release.
- Changes to `quiz_attempts`, `lecture_chunks` or `course_topics` must update `ml_core/schemas.py` in the same PR.

### 5.6 Secrets

- `.env.example` lists every variable with no values and is committed. `.env` is in `.gitignore`.
- The mobile app holds only `API_BASE_URL`, `SUPABASE_URL` and the Supabase **anon** key, protected by Row Level Security. Never put the Gemini key, the service-role key or any other secret in the app: anything inside an app can be extracted.
- Dev keys are shared privately by Amr. Staging and production keys live only in Railway and GitHub secrets; the app's `config/*.json` files and the Android keystore live with Omar and are shared privately.
- Only Omar and Amr can see production keys. Each environment has its own Gemini key with a spending alert.
- A key that was ever committed or pasted in a chat is revoked and replaced the same day.

---

## 6. Getting started

```bash
git clone https://github.com/NEGM18/study-coach.git
cd study-coach
pip install uv                          # once
uv sync --extra dev                     # ml_core + test tools; add --extra speech or --extra topics as needed
                                        # model B: .m4a recordings also need ffmpeg on PATH (winget install ffmpeg)
uv run pytest                           # passes, with contract tests marked xfail until stubs exist
uv run ruff check . && uv run ruff format --check .
uv run dvc pull                         # setup and Google authentication: docs/dvc_setup.md (issue #11)

# Mobile app (from Week 2, after the Flutter project is created — see apps/mobile/README.md)
cd apps/mobile
cp config/dev.json.example config/dev.json   # fill in dev values from Amr
flutter pub get
flutter run --dart-define-from-file=config/dev.json
```

Daily async standup in the team chat by 10 pm: done, next, blocked. Stuck for more than an hour after two or three different prompts? Post in the chat instead of looping.

---

## 7. Status and roadmap

*Updated 2026-11-19 (end of Week 1). Full Week 2 plan with every task's steps and tests: [`docs/week2_plan.pdf`](docs/week2_plan.pdf).*

### 7.1 Week 1 — what we finished

**Repo health:** `uv run pytest` 83 passed · `ruff check` and `ruff format --check` clean · CI green on `main`.

| Area | Done | Key numbers | Issues |
| --- | --- | --- | --- |
| Shared | `schemas.py`, `cleaning_log.py`, `text_normalize.py` (one test per rule), DVC remote, CI | 83 tests | #1, #12 (#11 still open) |
| A — knowledge | ASSISTments + EdNet in DVC, EDA, cleaning, app columns, student splits, `features.py`, `predict_mastery()` stub, spot check | ASSISTments 346,860 -> **253,278** rows; EdNet sample 652,345 -> **638,684**; 20/20 spot check | #13–#19 |
| B — speech | `audio.py` (16 kHz FLAC, loudness, VAD), `transcribe()` Gemini stub, `build_dataset.py`, Whisper draft script | Pipeline ready; **dataset not built yet** (no audio in DVC) | #2 (#3–#5, #7–#10 open) |
| C — topics | Topic lists + labeling guide + seed, `extract.py` (PDF/PPTX/OCR), 7-step `clean.py`, Label Studio + Gemini pre-labels, `classify_chunks()` stub, lecture splits | 654 -> **557** chunks; 390 / 87 / 80 split by lecture | #20–#28 |

**Week 1 gate:** A ✅ and C ✅ (dataset + data card + stub passing contract tests). B: stub ✅, dataset ⏳ — waiting on recordings, corrections and MGB-3/ArzEn access.

### 7.2 Still open from Week 1 (carried into Week 2)

| Issue | Owner | Note |
| --- | --- | --- |
| #3, #4, #5, #6 | Omar Negm | Draft transcripts, public dataset conversion, error-rate filter + splits, Day 7 review |
| #7, #8, #9, #10 | Fares | Permissions/MGB-3 + ArzEn access, recordings, 2 h of corrections, 30-clip check |
| #11 | Amr | Code is merged; close it once everyone can `dvc pull` |

### 7.3 Week 1 checkup — problems found (fixed in Week 2)

1. **Model C stub accuracy 1.0000 is circular.** `ml/topics/scripts/build_dataset.py` uses `predicted_topic_id` (the stub's own output) as the true label. There is no real baseline yet -> **W2-17 (#51)**.
2. **Model C kappa 1.0000 is not credible.** 200/200 labels agree, and both annotator columns were committed by the same person -> **W2-18 (#52)**.
3. **Professor names are committed** in `ml/topics/verified_labels.json`, `label_studio_tasks.json` and `spot_check_30.md`, which breaks the "P1, P2…" rule -> **W2-19 (#53)**.
4. `TOPIC_KEYWORDS` and the 0.05 threshold are hard-coded in `ml_core/topics/predict.py`; they belong in YAML -> **W2-17 (#51)**.
5. The PFA baseline (AUC 0.717) was measured on the original 525,534-row file, but we now use the corrected file. Re-measure it before comparing -> **W2-09 (#43)**.
6. `schemas.py` still says "Draft v0" and has no `TopicMastery` row; `db/migrations/` is empty -> **W2-02 (#36)**.

### 7.4 Week 2 — Train v1 models and stand up the app on staging

**Goal:** each model has a trained v1 compared honestly against its stub on the test set, and the app runs end to end on staging (sign up -> upload a lecture -> topic-tagged chunks -> quiz attempt -> mastery) with the stubs behind the same `predict()` functions. From Week 2 app work branches from and merges into **`dev`**.

| Task | Issue | Team | Owner | Due | AI help | What |
| --- | --- | --- | --- | --- | --- | --- |
| W2-01 | #35 | All | Omar Negm | Day 1 | Low | Kickoff, `dev` branch + protection, carry-over |
| W2-02 | #36 | All | Omar Negm | Day 2 | Medium | Supabase dev project, `0001_init.sql` + RLS, `TopicMastery` |
| W2-03 | #37 | All | Amr | Day 4 | High | FastAPI `/api/v1` with auth and tests |
| W2-04 | #38 | All | Omar Negm | Day 5 | High | Worker + `ml_core/registry.py` (model versions from env vars) |
| W2-05 | #39 | All | Omar Negm | Day 6 | Medium | Staging: Supabase + Railway auto-deploy + smoke test |
| W2-06 | #40 | All | Hager | Day 7 | Medium | QA checklist, run on staging, file bugs |
| W2-07 | #41 | All | Omar Negm | Day 7 | Low | Reviews, demo, gate, release `v0.2.0` |
| W2-08 | #42 | A | Amr | Day 3 | High | `train.py` -> `knowledge_model_v1` |
| W2-09 | #43 | A | Hager | Day 4 | High | `evaluate.py`: stub vs PFA vs v1, EdNet transfer |
| W2-10 | #44 | A | Amr | Day 5 | Medium | `predict_mastery()` versioned, < 100 ms |
| W2-11 | #45 | A | Hager | Day 6 | Medium | Model card, edge-case tests, `dvc push` |
| W2-12 | #46 | B | Fares | Day 3 | Low | 10+ recordings, 3+ professors |
| W2-13 | #47 | B | Fares | Day 5 | Low | 4+ hours corrected |
| W2-14 | #48 | B | Omar Negm | Day 5 | Medium | Fine-tune Whisper-small -> `speech_model_v1` |
| W2-15 | #49 | B | Omar Negm | Day 6 | Medium | CER/WER, code-switch breakdown, RTF, model card |
| W2-16 | #50 | B | Fares | Day 7 | Low | Listen to 30 v1 outputs; error report |
| W2-17 | #51 | C | Omar Mustafa | Day 2 | Medium | Fix circular evaluation; config for keywords |
| W2-18 | #52 | C | Mariam | Day 2 | Low | Redo blind 200 labels; real kappa |
| W2-19 | #53 | C | Mariam | Day 3 | High | Anonymize names; `topics_processed_v2` |
| W2-20 | #54 | C | Mariam | Day 5 | High | `train.py` -> `topics_model_v1` |
| W2-21 | #55 | C | Omar Mustafa | Day 6 | Medium | `evaluate.py`, versioned `classify_chunks()`, < 5 s/lecture |
| W2-22 | #56 | App | Omar Mustafa | Day 2 | High | Flutter project, core, Arabic RTL, CI mobile green |
| W2-23 | #57 | App | Omar Mustafa | Day 6 | High | Auth, courses, upload screens; staging test build |

**Dependencies:** W2-03 (API) needs W2-02's Supabase dev project · W2-14 needs #4 and #5 (speech dataset) · W2-20 needs W2-17 and W2-19 · W2-10, W2-15 and W2-21 need W2-04's registry · W2-05 needs W2-02, W2-03 and W2-04 · W2-06 needs W2-05 and W2-23.

### 7.5 Week 2 testing

| Layer | Test | Where |
| --- | --- | --- |
| Unit | Every new cleaning / feature / metric / registry function | `ml_core/tests/`, CI |
| Contract | Each `predict()` parametrized over `stub` and `v1` | `ml_core/tests/test_contracts.py`, CI |
| Speed | A < 100 ms/call · C < 5 s/lecture · B real-time factor <= 0.5 | Tests + model cards |
| Model eval | Test split only: A AUC/log-loss/calibration · B CER/WER (`normalize_for_eval`) · C accuracy/macro-F1 | `ml/<model>/scripts/evaluate.py` |
| API | Each route: happy path, 401, 422 | `services/api/tests/`, CI |
| Worker | Fake slide/audio/quiz jobs end `done`; failures end `failed` | `services/worker/tests/`, CI |
| App | Widget tests in Arabic (RTL) and English; provider tests; integration test on staging | `apps/mobile/test/`, `integration_test/`, CI |
| Manual | QA checklist on a real Android phone | `docs/qa/week2_checklist.md` |

### 7.6 Week 2 gate (Day 7)

- [ ] `dev` exists; API + worker auto-deploy to staging; smoke test green
- [ ] App test build: sign up -> upload -> chunks -> quiz -> mastery works on staging in Arabic and English
- [ ] Each model: v1 in DVC with a model card and an honest test-set comparison against its stub (and A against the re-measured PFA)
- [ ] No professor names or student data in Git; real kappa >= 0.80 for model C
- [ ] A model goes live on staging only if it passes every box in 5.4; otherwise it stays `stub`
- [ ] Release `week-2` merged to `main`, tagged `v0.2.0`

### 7.7 After Week 2 (tentative — check against the 4-week build plan)

Week 3: quizzes, study plan and readiness screens; the summaries and quiz generator (Gemini, server-side) with evals in `evals/`; a model goes to production after its full day on staging; decide on iOS/TestFlight. Week 4: the 20-student pilot on Google Play internal testing.
