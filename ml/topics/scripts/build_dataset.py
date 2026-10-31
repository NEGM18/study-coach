"""Issue #23: Dataset builder for Model C (Topics Classifier).

Loads verified labels, computes Cohen's kappa and stub baseline accuracy,
splits 70% train / 15% val / 15% grouped strictly by lecture_id (seed 42),
and saves app-shaped parquet dataset to ml/data/processed/topics/topics_processed_v1.parquet.
"""

import argparse
import json
import logging
import random
from pathlib import Path

import pandas as pd
import yaml
from sklearn.metrics import accuracy_score, cohen_kappa_score

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
    """Load verified labeled chunks."""
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
            topic_id=int(d["predicted_topic_id"]),
        )
        for d in data
    ]


def compute_inter_annotator_agreement(blind_path: Path) -> float:
    """Compute Cohen's kappa agreement score on the blind double-annotation sample."""
    with blind_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    ann1 = [d["annotator_1_topic_id"] for d in data]
    ann2 = [d["annotator_2_topic_id"] for d in data]
    return float(cohen_kappa_score(ann1, ann2))


def evaluate_stub_accuracy(chunks: list[Chunk], topics: list[Topic]) -> float:
    """Compute baseline accuracy of the deterministic classify_chunks stub."""
    preds = classify_chunks(chunks, topics)
    y_true = [c.topic_id for c in chunks]
    y_pred = [p.topic_id for p in preds]
    return float(accuracy_score(y_true, y_pred))


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
    args = parser.parse_args()

    with Path(args.config).open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    seed = int(config.get("seed", 42))

    verified_path = Path("ml/topics/verified_labels.json")
    blind_path = Path("ml/topics/blind_agreement_sample.json")
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

    kappa = compute_inter_annotator_agreement(blind_path)
    print(f"Cohen's Kappa Agreement: {kappa:.4f}")

    stub_acc = evaluate_stub_accuracy(chunks, topics)
    print(f"Classifier Stub Accuracy: {stub_acc:.4f}")

    split_map = split_grouped_by_lecture(chunks, seed=seed)
    out_parquet = Path("ml/data/processed/topics/topics_processed_v1.parquet")
    df = build_and_save_dataset(chunks, split_map, out_parquet)

    print(f"Saved processed dataset to {out_parquet} ({len(df)} rows).")
    print("Split counts:\n", df["split"].value_counts())
    print("Language distribution:\n", df["lang"].value_counts())


if __name__ == "__main__":
    main()
