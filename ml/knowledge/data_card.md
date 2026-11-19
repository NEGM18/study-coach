# Data card — knowledge (Model A)

| Field | Value |
| --- | --- |
| Owner(s) | Amr (pipeline), Hager (sources, EDA, checks) |
| Sources (link, license, download date) | **ASSISTments 2009-2010 skill builder, corrected collapsed version** — https://sites.google.com/site/assistmentsdata/home/2009-2010-assistment-data/skill-builder-data-2009-2010 (file `skill_builder_data_corrected_collapsed.csv`, Google Drive id `1NNXHFRxcArrU0ZJSb9BIL56vmUt5FhlE`); free for research, cite the page URL as its authors ask; downloaded 2026-11-19. **EdNet KT1** — https://github.com/riiid/ednet (`EdNet-KT1.zip` via bit.ly/ednet_kt1, plus `EdNet-Contents.zip` via bit.ly/ednet-content for answer keys and tags); CC BY-NC 4.0; downloaded 2026-11-19. |
| Raw files | `ml/data/raw/knowledge/` (read-only, DVC) |
| Final dataset file(s) | `ml/data/processed/knowledge/kt_processed_v1.parquet` (ASSISTments), `kt_ednet_processed_v1.parquet` (EdNet sample), `kt_topic_map_v1.csv` (source skill_id -> topic_id) |
| Rows | ASSISTments 346,860 raw -> **253,278** clean; EdNet sample (5,000 students, seed 42) 652,345 -> **638,684** |
| Splits (train / val / test) | ASSISTments 210,059 / 22,920 / 20,299 rows (2,375 / 297 / 296 students); EdNet 547,421 / 48,717 / 42,546 rows (2,293 / 287 / 286 students) |
| Split rule | By student, 80/10/10, seed 42 (`ml_core.knowledge.clean.split_by_student`); no student in two splits |
| Columns | `quiz_attempts`: user_id (sha256-hashed, 16 hex), topic_id, question_id, attempt_order (1..n per student), is_correct, response_time_ms, attempt_count, hint_count, plus `split` |

Build: `python -m ml.knowledge.scripts.build_dataset --config ml/knowledge/configs/build.yaml`.
Features for training: `ml_core.knowledge.features.build_feature_frame` (earlier answers only; tested).

## Cleaning steps — ASSISTments (`ml/knowledge/cleaning_log.csv`)

| Step | Rows in | Rows out | Removed | Reason |
| --- | ---: | ---: | ---: | --- |
| keep original problems | 346,860 | 275,458 | 71,402 | scaffolding rows are hints, not real questions |
| drop missing skill_id | 275,458 | 259,399 | 16,059 | topic_id is required |
| drop duplicate order_id | 259,399 | 259,399 | 0 | the corrected file already collapses multi-skill rows |
| drop response time <= 0 (then cap at 99th pct = 366,531 ms) | 259,399 | 259,084 | 315 | non-positive times are logging errors |
| drop students with < 10 answers | 259,084 | 253,373 | 5,711 | too little history |
| drop skills with < 20 answers | 253,373 | 253,278 | 95 | too few answers to estimate the skill |

## Cleaning steps — EdNet KT1 sample (`ml/knowledge/cleaning_log_ednet.csv`)

EdNet is mapped to the same columns first: `is_correct = user_answer == correct_answer`, `topic_id` = first tag of the question, `response_time_ms = elapsed_time`. It has no scaffolding flag, so step 1 is skipped.

| Step | Rows in | Rows out | Removed |
| --- | ---: | ---: | ---: |
| drop missing skill_id | 652,345 | 652,225 | 120 |
| drop duplicate order_id | 652,225 | 652,225 | 0 |
| drop response time <= 0 (cap 97,800 ms) | 652,225 | 650,666 | 1,559 |
| drop students with < 10 answers | 650,666 | 638,684 | 11,982 |
| drop skills with < 20 answers | 638,684 | 638,684 | 0 |

## Correct rate per split

| Dataset | train | val | test |
| --- | ---: | ---: | ---: |
| ASSISTments | 0.6603 | 0.6578 | 0.6437 |
| EdNet sample | 0.6635 | 0.6521 | 0.6574 |

## Data issue list (issue #18, from `notebooks/01_eda.ipynb`)

1. **Original vs corrected file.** The plan's numbers (525,534 -> 253,312) come from the original `skill_builder_data.csv`, which now needs a Google sign-in. We use the authors' corrected file (346,860 rows): it removes the duplicated rows the original had. The final size (253,278) lands within 0.01% of the plan.
2. **71,402 scaffolding rows** (`original == 0`) are follow-up hints, not independent questions.
3. **63,755 rows (18.4%) have no skill_id**; 16,059 of them remain after dropping scaffolding.
4. **47,037 multi-skill rows** have a skill_id like `"1_13"`. We treat each combination as its own topic (149 combined ids -> topic_id 1..149, map in `kt_topic_map_v1.csv`).
5. **Response times:** 317 rows are <= 0 ms (7 negative), and the max is 84,076,920 ms (about 23 h). We cap at the 99th percentile.
6. **1,049 of 4,217 students have < 10 answers**; the median is 23 answers and the max 1,383 (long tail).
7. **14 skills have < 20 answers.**
8. `answer_id` (88% missing) and `bottom_hint` (83% missing) are mostly empty and unused.
9. EdNet: 120 answers are on questions with tag `-1` (no topic), and many sampled students answer fewer than 10 questions.

## Spot check (issue #19)

`ml/knowledge/spot_check_20.md`: 20 random processed rows (seed 42) were looked up in the raw CSV. **20/20 found unchanged** (same student hash, question, skill, correctness, response time after the cap).

## Known issues

- Topic ids are dataset-specific; the app's `course_topics` will use its own ids. The model must stay topic-agnostic (features never use the id as an input).
- Response-time caps differ between the two datasets (366 s vs 98 s), because the cap is computed per dataset.
