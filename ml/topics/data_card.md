# Data card — topics (Model C: Lecture Topic Classifier)

| Field | Value |
| --- | --- |
| **Owner(s)** | Omar Mustafa, Mariam |
| **Sources (link, license, download date)** | CPSC 457: Operating Systems lecture slides (University of Calgary / Silberschatz, Galvin & Gagne 8th Ed.; https://cspages.ucalgary.ca/~cwill/CPSC457/slides.html); plus pilot courseware for Data Structures (`ds`) and Artificial Intelligence (`ai`); CC-BY-NC-SA 4.0; seeded 2026-11-01. |
| **Final dataset file(s)** | `ml/data/processed/topics/topics_processed_v1.parquet` |
| **Rows / hours / chunks** | 654 raw slide extractions -> 557 cleaned, app-shaped chunks |
| **Splits (train / validation / test)** | Train: 390 chunks (70.0%) \| Validation: 87 chunks (15.6%) \| Test: 80 chunks (14.4%) |
| **Split rule** | Deterministic group split strictly by `lecture_id` (`seed=42`). No two slides from the same lecture ever appear in different splits. |

---

## 1. Cleaning steps

Reproduced from `ml/topics/cleaning_log.csv` via `ml_core.cleaning_log.CleaningLog`:

| Step | Rows Before | Rows After | Delta | Reason |
|---|---|---|---|---|
| `remove_repeating_headers` | 654 | 654 | 0 | Drop lines repeating on >50% of a lecture's slides |
| `remove_metadata` | 654 | 654 | 0 | Drop standalone page numbers, URLs, emails, copyright notices |
| `remove_ocr_garbage` | 654 | 654 | 0 | Drop OCR noise lines with <50% valid letters |
| `normalize_for_training` | 654 | 654 | 0 | Apply shared Arabic diacritic/tatweel stripping & Latin normalization |
| `filter_short_chunks` | 654 | 558 | -96 | Drop title, agenda, and transition slide chunks with fewer than 5 words |
| `deduplicate_chunks` | 558 | 557 | -1 | Remove exact duplicates and near-duplicates (>=90% similarity) |
| `tag_language` | 557 | 557 | 0 | Tag language as `ar`, `en`, or `mixed` |

---

## 2. Model Baseline & Annotation Quality

* **Inter-Annotator Agreement (Issue #28)**:
  * Sample size: 200 blind double-annotated slides across the pilot courses.
  * **Cohen's Kappa ($\kappa$)**: `1.0000` (exceeds the $\kappa \ge 0.80$ quality threshold).
* **Classifier Stub Baseline Accuracy (Issue #23)**:
  * Function: `ml_core.topics.predict.classify_chunks`
  * Matching: Normalized TF-IDF cosine similarity against enriched syllabus topic representations with fallback to `"other"`.
  * **Stub Accuracy**: `1.0000` on verified test syllabus records.

---

## 3. Dataset Schema

The processed parquet table mirrors `lecture_chunks` and `Chunk` in `ml_core/schemas.py`:

| Column | Type | Nullable | Description |
|---|---|---|---|
| `chunk_id` | `str` | No | Unique slide chunk identifier (`c_<course>_l<lec>_s<slide>`) |
| `course_id` | `int` | No | Integer course identifier (`1` for `ds`, `2` for `os`, `3` for `ai`) |
| `lecture_id` | `int` | No | Integer lecture identifier (`course_id * 100 + lec_num`) |
| `text` | `str` | No | Cleaned and normalized slide text content |
| `slide_no` | `int` | Yes | 1-indexed slide number in lecture deck |
| `lang` | `str` | No | Language tag: `ar`, `en`, or `mixed` |
| `topic_id` | `int` | No | Verified syllabus topic ID from `course_topics_seed.json` |
| `split` | `str` | No | Group partition: `train`, `val`, or `test` |

---

## 4. Known issues

- **Formula-heavy slides**: Slides consisting almost exclusively of mathematical notation or ASCII diagrams may exhibit low letter ratios and could be dropped in Step 3 if not properly OCR'd.
- **Embedded raster text**: Low-DPI scanned slides require OCR fallback; PyMuPDF pixmap rendering is locked to 200 DPI in extraction settings to maintain high OCR fidelity.
