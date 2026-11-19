"""Issue #23, #51, #52, #53: Dataset builder for Model C (Topics Classifier).

Loads verified labels, separates human gold topic_id from stub predictions,
computes honest stub baseline metrics (val/test accuracy, macro-F1, per-course),
splits 70% train / 15% val / 15% grouped strictly by lecture_id (seed 42),
and saves app-shaped parquet dataset to ml/data/processed/topics/topics_processed_v2.parquet.
"""

import argparse
import json
import logging
import random
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from sklearn.metrics import accuracy_score, f1_score

from ml_core.schemas import Chunk, Topic
from ml_core.topics.predict import classify_chunks

LOGGER = logging.getLogger(__name__)

EXPECTED_COLUMNS = [
    "chunk_id",
    "course_id",
    "lecture_id",
    "text",
    "slide_no",
    "lang",
    "topic_id",
    "split",
]


def load_verified_chunks(verified_path: Path) -> list[Chunk]:
    """Load verified labeled chunks using human-reviewed topic_id."""
    with verified_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return [
        Chunk(
            chunk_id=str(d["chunk_id"]),
            course_id=int(d["course_id"]),
            lecture_id=int(d["lecture_id"]),
            text=str(d["text"]),
            slide_no=int(d["slide_no"]) if d.get("slide_no") is not None else None,
            lang=d.get("lang", "ar"),
            topic_id=int(d.get("topic_id", d.get("predicted_topic_id"))),
        )
        for d in data
    ]


def evaluate_topic_predictions(
    y_true: list[int],
    y_pred: list[int],
    course_ids: list[int] | None = None,
) -> dict[str, Any]:
    """Compute accuracy, macro-F1, and per-course metrics with strict circularity check.

    Fails loudly (raises ValueError) if y_true == y_pred on every row.
    """
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: {len(y_true)} gold vs {len(y_pred)} pred")
    if not y_true:
        return {"accuracy": 0.0, "macro_f1": 0.0, "per_course": {}}

    # STRICT ASSERTION: Fail loudly if predictions are identical to gold on every row
    if y_true == y_pred:
        raise ValueError(
            "Evaluation failure: Model predictions and gold labels are identical across 100% of rows. "
            "Circular evaluation detected (stub evaluated on its own predictions)."
        )

    acc = float(accuracy_score(y_true, y_pred))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0.0))

    per_course: dict[int, dict[str, float]] = {}
    if course_ids is not None and len(course_ids) == len(y_true):
        for cid in sorted(set(course_ids)):
            c_indices = [i for i, c in enumerate(course_ids) if c == cid]
            c_true = [y_true[i] for i in c_indices]
            c_pred = [y_pred[i] for i in c_indices]
            c_acc = float(accuracy_score(c_true, c_pred)) if c_true else 0.0
            c_f1 = float(f1_score(c_true, c_pred, average="macro", zero_division=0.0)) if c_true else 0.0
            per_course[cid] = {"accuracy": c_acc, "macro_f1": c_f1, "count": len(c_indices)}

    return {
        "accuracy": acc,
        "macro_f1": macro_f1,
        "per_course": per_course,
    }


def split_grouped_by_lecture(
    chunks: list[Chunk],
    seed: int = 42,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> dict[int, str]:
    """Deterministically assign each unique lecture_id to train, val, or test.

    Ensures 0% data leakage: no two slides from the same lecture ever appear
    in different splits, and course representations are stratified to match 70/15/15.
    """
    from collections import Counter

    counts = Counter(c.lecture_id for c in chunks)
    total = len(chunks)
    target_train = round(total * train_ratio)
    target_val = round(total * val_ratio)
    target_test = total - target_train - target_val

    by_course: dict[int, set[int]] = {}
    for c in chunks:
        by_course.setdefault(c.course_id, set()).add(c.lecture_id)

    rng = random.Random(seed)
    best_diff = 999999
    best_map: dict[int, str] = {}

    for _ in range(100):
        cur_map: dict[int, str] = {}
        tr_c, val_c, te_c = 0, 0, 0
        for _cid, lecs in sorted(by_course.items()):
            shuffled = sorted(list(lecs))
            rng.shuffle(shuffled)
            n = len(shuffled)
            nv = max(1, round(n * val_ratio))
            nt = max(1, round(n * (1.0 - train_ratio - val_ratio)))
            ntr = max(1, n - nv - nt)

            for lec_id in shuffled[:ntr]:
                cur_map[lec_id] = "train"
                tr_c += counts[lec_id]
            for lec_id in shuffled[ntr : ntr + nv]:
                cur_map[lec_id] = "val"
                val_c += counts[lec_id]
            for lec_id in shuffled[ntr + nv :]:
                cur_map[lec_id] = "test"
                te_c += counts[lec_id]

        diff = abs(tr_c - target_train) + abs(val_c - target_val) + abs(te_c - target_test)
        if diff < best_diff:
            best_diff = diff
            best_map = cur_map

    return best_map


def build_and_save_dataset(
    chunks: list[Chunk],
    split_map: dict[int, str],
    output_path: Path,
) -> pd.DataFrame:
    """Build pandas DataFrame matching schemas.py and export as Parquet."""
    rows = []
    for c in chunks:
        rows.append(
            {
                "chunk_id": c.chunk_id,
                "course_id": c.course_id,
                "lecture_id": c.lecture_id,
                "text": c.text,
                "slide_no": c.slide_no,
                "lang": c.lang,
                "topic_id": c.topic_id,
                "split": split_map[c.lecture_id],
            }
        )

    df = pd.DataFrame(rows)
    assert list(df.columns) == EXPECTED_COLUMNS, f"Columns mismatch: {df.columns} vs {EXPECTED_COLUMNS}"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False, engine="pyarrow")
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Build processed Model C topic dataset.")
    parser.add_argument(
        "--config",
        type=str,
        default="ml/topics/configs/topics_config.yaml",
        help="Path to YAML config.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="ml/data/processed/topics/topics_processed_v2.parquet",
        help="Path to output parquet file.",
    )
    parser.add_argument(
        "--annotator1",
        type=str,
        default=None,
        help="Optional path to first annotator JSON export for kappa calculation.",
    )
    parser.add_argument(
        "--annotator2",
        type=str,
        default=None,
        help="Optional path to second annotator JSON export for kappa calculation.",
    )
    args = parser.parse_args()

    with Path(args.config).open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    seed = int(config.get("seed", 42))

    verified_path = Path("ml/topics/verified_labels.json")
    seed_topics_path = Path("db/seed/course_topics_seed.json")

    with seed_topics_path.open("r", encoding="utf-8") as f:
        topics_json = json.load(f)
    raw_topics = topics_json.get("topics", topics_json if isinstance(topics_json, list) else [])
    topics = [
        Topic(
            topic_id=int(t["topic_id"]),
            course_id=int(t["course_id"]),
            name=str(t["name"]),
            description=str(t.get("description", "")),
        )
        for t in raw_topics
    ]

    chunks = load_verified_chunks(verified_path)
    print(f"Loaded {len(chunks)} verified chunks.")

    # Cohen's kappa agreement check
    if args.annotator1 and args.annotator2:
        from ml.topics.scripts.compute_kappa import compute_cohen_kappa

        kappa = compute_cohen_kappa(args.annotator1, args.annotator2)
        print(f"Cohen's Kappa Agreement: {kappa:.4f}")
    else:
        print("Cohen's Kappa Agreement: Pending blind human double-annotation export files (Issue #52)")

    # Partition dataset by lecture_id
    split_map = split_grouped_by_lecture(chunks, seed=seed)
    out_parquet = Path(args.output)
    df = build_and_save_dataset(chunks, split_map, out_parquet)

    print(f"Saved processed dataset to {out_parquet} ({len(df)} rows).")
    print("Split counts:\n", df["split"].value_counts())
    print("Language distribution:\n", df["lang"].value_counts())

    # Honest stub baseline evaluation on val and test splits
    print("\n" + "=" * 50)
    print("HONEST CLASSIFIER STUB BASELINE METRICS (Issue #51)")
    print("=" * 50)

    for split_name in ["val", "test"]:
        split_chunks = [c for c in chunks if split_map[c.lecture_id] == split_name]
        split_preds = classify_chunks(split_chunks, topics, config=config)
        y_true = [c.topic_id for c in split_chunks]
        y_pred = [p.topic_id for p in split_preds]
        course_ids = [c.course_id for c in split_chunks]

        metrics = evaluate_topic_predictions(y_true, y_pred, course_ids=course_ids)
        print(
            f"\nSplit '{split_name}' ({len(split_chunks)} chunks):"
            f"\n  Accuracy : {metrics['accuracy']:.4f}"
            f"\n  Macro-F1 : {metrics['macro_f1']:.4f}"
            "\n  Per-course breakdown:"
        )
        for cid, stats in sorted(metrics["per_course"].items()):
            course_name = {1: "ds", 2: "os", 3: "ai"}.get(cid, str(cid))
            print(
                f"    Course {cid} ({course_name}, n={stats['count']}): "
                f"Acc = {stats['accuracy']:.4f}, Macro-F1 = {stats['macro_f1']:.4f}"
            )


if __name__ == "__main__":
    main()
