# Model card — knowledge_model_v1 (Model A)

> **Status:** Template — fill in metrics once W2-08 (Amr's `train.py`) is merged and
> `ml/knowledge/scripts/evaluate.py` has been run on `kt_processed_v1`.

---

## Model details

| Field | Value |
| --- | --- |
| Model name | `knowledge_model_v1` |
| Version | v1 |
| Owner | Amr (lead), Hager (eval, card, tests) |
| Date | 2026-11 (Week 2) |
| Registry key | `KNOWLEDGE_MODEL_VERSION=v1` |
| Weights path | `ml/data/models/knowledge_model_v1/` (DVC, never committed to Git) |
| Data version | `kt_processed_v1.parquet` (ASSISTments, 253,278 rows) + `kt_ednet_processed_v1.parquet` (EdNet sample, 638,684 rows) — see `ml/knowledge/data_card.md` |
| Config | `ml/knowledge/configs/train.yaml` (Amr — W2-08) |
| Evaluation script | `ml/knowledge/scripts/evaluate.py` — see `ml/knowledge/eval_v1.md` |

---

## Task

Predict the probability that a student answers the **next question** on a given topic
correctly, given their earlier quiz attempts.

**Predict contract:**
```python
predict_mastery(history: list[Attempt], topic_id: int) -> float  # in [0, 1]
```

---

## Data version

| Dataset | Raw rows | Clean rows | Split (train / val / test) |
| --- | ---: | ---: | --- |
| ASSISTments 2009-2010 (corrected collapsed) | 346,860 | 253,278 | 210,059 / 22,920 / 20,299 |
| EdNet KT1 sample (5,000 students, seed 42) | 652,345 | 638,684 | 547,421 / 48,717 / 42,546 |

Splits are by student (seed 42, 80/10/10); no student appears in two splits.
Full cleaning steps in `ml/knowledge/data_card.md`.

---

## Features

Built by `ml_core.knowledge.features.build_feature_frame`.
Every feature uses **only earlier answers** (no look-ahead).

| Feature | Description |
| --- | --- |
| `prior_correct` | # correct answers on this topic before this attempt |
| `prior_wrong` | # wrong answers on this topic before this attempt |
| `topic_correct_rate` | Smoothed correct rate on this topic (prior: 0.5, strength: 2) |
| `question_correct_rate` | Smoothed correct rate on this question (same prior) |
| `answers_since_last_on_topic` | Positions elapsed since the student last answered this topic |

Topic and question IDs are **not features** — they are only used to filter the history.
This keeps the model topic-agnostic so it generalises to new topics without retraining.

---

## Training config (W2-08 — fill in after Amr's PR is merged)

| Hyperparameter | Value |
| --- | --- |
| Algorithm | *(set by `ml/knowledge/configs/train.yaml`)* |
| Random seed | 42 |
| Train split | `split == "train"` |
| Val split | `split == "val"` (used for early stopping / tuning only) |

> **Rule:** `split == "test"` rows are **never** seen during training or tuning.

---

## Test-set metrics (fill in after `evaluate.py` is run)

Evaluated strictly on `split == "test"` by `ml/knowledge/scripts/evaluate.py`.
See full report in `ml/knowledge/eval_v1.md`.

### ASSISTments (`kt_processed_v1`, test rows: 20,299)

| Model | AUC | Accuracy | Log-loss | Calibration ECE |
| --- | ---: | ---: | ---: | ---: |
| Stub | *(run evaluate.py)* | | | |
| PFA (re-measured on corrected file) | *(run evaluate.py)* | | | |
| **v1** | *(run evaluate.py)* | | | |

### EdNet KT1 (`kt_ednet_processed_v1`, test rows: 42,546)

| Model | AUC | Accuracy | Log-loss | Calibration ECE |
| --- | ---: | ---: | ---: | ---: |
| Stub | *(run evaluate.py)* | | | |
| PFA (EdNet in-domain) | *(run evaluate.py)* | | | |
| **v1** | *(run evaluate.py)* | | | |

### Cross-dataset transfer (ASSISTments → EdNet)

| Model | AUC | Accuracy | Log-loss | Calibration ECE |
| --- | ---: | ---: | ---: | ---: |
| PFA (ASSISTments train → EdNet test) | *(run evaluate.py)* | | | |

**Gate:** v1 replaces the stub only if its AUC on ASSISTments test > stub AUC **and** > the
re-measured PFA AUC (from `eval_v1.md`). The old 0.717 figure came from the original
525,534-row file and is superseded by the corrected-file number.

---

## Speed

Target: **< 100 ms per `predict_mastery()` call** on the API server.

| Measurement | Value |
| --- | --- |
| Median latency (single call, CPU) | *(measure after W2-10)* |
| p99 latency | *(measure after W2-10)* |

---

## Deployment

1. Weights are saved to `ml/data/models/knowledge_model_v1/` and tracked with DVC.
2. Add a `dvc push` after training; commit the `.dvc` pointer file (never the weights).
3. Register the model:
   ```python
   from ml_core.registry import register

   register("knowledge", "v1", "ml_core.knowledge.predict_v1:predict_mastery")
   ```
4. On staging: set `KNOWLEDGE_MODEL_VERSION=v1` in Railway env vars; restart the worker.
5. Rollback: set `KNOWLEDGE_MODEL_VERSION=stub` and restart.

### DVC commands
```bash
# After training saves weights to ml/data/models/knowledge_model_v1/
dvc add ml/data/models/knowledge_model_v1
git add ml/data/models/knowledge_model_v1.dvc .gitignore
git commit -m "data(knowledge): add knowledge_model_v1 weights to DVC"
dvc push
```

> **Never** commit `.joblib`, `.pkl`, `.pt` or any weight files directly to Git.

---

## Edge cases and unit tests

Tests are in `ml_core/tests/test_knowledge_edge_cases.py` (W2-11).
Run: `uv run pytest ml_core/tests/test_knowledge_edge_cases.py -v`

| Case | Expected behaviour |
| --- | --- |
| 0 attempts (empty history) | Returns prior ≈ 0.5; in [0, 1] |
| 1 attempt on topic (correct) | Returns smoothed rate 2/3; in [0, 1] |
| 1 attempt on topic (wrong) | Returns smoothed rate 1/3; in [0, 1] |
| Unseen topic (all history on other topics) | Returns prior 0.5; in [0, 1] |
| 1,200 mixed attempts | Returns ≈ 0.5; in [0, 1]; no crash |
| 50 all-correct | Returns > 0.5 (≈ 0.981); in [0, 1] |
| 50 all-wrong | Returns < 0.5 (≈ 0.019); in [0, 1] |

The contract test in `ml_core/tests/test_contracts.py` also covers the `predict_mastery`
signature for both `stub` and (once registered) `v1`.

---

## Known limitations

- **Topic-ID mismatch across datasets.** ASSISTments topic IDs (1–149) are unrelated to
  EdNet tag IDs, so cross-dataset transfer via PFA is poor. The model features are
  topic-agnostic, so v1 may generalise better — measure in `eval_v1.md`.
- **Response-time caps differ.** ASSISTments cap ≈ 366 s; EdNet cap ≈ 98 s. Models trained
  on one dataset should not be evaluated on the other using response time as a feature without
  re-normalisation.
- **EdNet user-answer missingness.** 39 rows in the EDA sample had no `user_answer`; the
  pipeline excludes them. The same gap may appear in production EdNet data.
- **Cold-start students.** For students with 0 or 1 attempts the model falls back to the
  prior (0.5). This is by design; more evidence is needed for personalisation.
