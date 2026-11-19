"""Cohen's kappa agreement calculation for blind double-annotation (Issue #28, #52 / W2-18).

Requires two separate annotator export files (e.g. from Mariam and Omar Mustafa).
Fails loudly if the same file or identical annotator export is passed twice.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import yaml
from sklearn.metrics import cohen_kappa_score

LOGGER = logging.getLogger(__name__)


def load_kappa_target(config_path: Path | str = "ml/topics/configs/topics_config.yaml") -> float:
    """Load target Cohen's kappa agreement threshold from YAML configuration."""
    path = Path(config_path)
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
            return float(cfg.get("agreement_kappa_target", 0.80))
    return 0.80


def extract_annotations_from_file(file_path: Path | str) -> dict[str, int]:
    """Parse annotator export file into mapping of chunk_id -> topic_id.

    Supports:
    1. Standard Label Studio task export JSON (with annotations[].result[].value.choices).
    2. Flat annotation JSON list ([{"chunk_id": ..., "topic_id": ...}]).
    3. Task format with data and label/choice.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Annotator file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list in {path}, got {type(data).__name__}")

    annotations: dict[str, int] = {}
    for item in data:
        chunk_id: str | None = None
        topic_id: int | None = None

        if "chunk_id" in item and "topic_id" in item:
            chunk_id = str(item["chunk_id"])
            topic_id = int(item["topic_id"])
        elif "id" in item and "annotations" in item:
            chunk_id = str(item["id"])
            ann_list = item.get("annotations", [])
            if ann_list:
                results = ann_list[0].get("result", [])
                for r in results:
                    choices = r.get("value", {}).get("choices", [])
                    if choices:
                        topic_id = int(choices[0])
                        break
        elif "data" in item and "topic_id" in item:
            chunk_id = str(item["data"].get("chunk_id", item.get("id")))
            topic_id = int(item["topic_id"])

        if chunk_id is not None and topic_id is not None:
            annotations[chunk_id] = topic_id

    if not annotations:
        raise ValueError(f"No valid annotations found in {path}")

    return annotations


def find_disagreements(file1: Path | str, file2: Path | str) -> list[dict[str, Any]]:
    """Identify chunk IDs where two separate annotator exports assigned different topic IDs."""
    ann1 = extract_annotations_from_file(file1)
    ann2 = extract_annotations_from_file(file2)

    common_ids = sorted(set(ann1.keys()) & set(ann2.keys()))
    disagreements = []
    for cid in common_ids:
        if ann1[cid] != ann2[cid]:
            disagreements.append(
                {
                    "chunk_id": cid,
                    "annotator_1_topic_id": ann1[cid],
                    "annotator_2_topic_id": ann2[cid],
                }
            )
    return disagreements


def compute_cohen_kappa(file1: Path | str, file2: Path | str) -> float:
    """Compute Cohen's kappa agreement between two separate annotator export files.

    Fails loudly if the same file or identical annotator export is passed twice.
    """
    p1 = Path(file1).resolve()
    p2 = Path(file2).resolve()

    if p1 == p2:
        raise ValueError(
            f"Cannot compute Cohen's kappa on identical file paths: {p1}. "
            "Two separate annotator export files are required (W2-18 / Issue #52)."
        )

    try:
        if p1.samefile(p2):
            raise ValueError(
                f"Files {p1} and {p2} point to the same filesystem location. "
                "Two separate annotator export files are required."
            )
    except OSError:
        pass

    ann1 = extract_annotations_from_file(p1)
    ann2 = extract_annotations_from_file(p2)

    # Check common chunk IDs
    common_ids = sorted(set(ann1.keys()) & set(ann2.keys()))
    if not common_ids:
        raise ValueError(f"Zero overlapping chunk IDs found between {p1.name} and {p2.name}")

    if len(common_ids) < len(ann1) or len(common_ids) < len(ann2):
        LOGGER.warning(
            "Partial overlap: %d shared chunks (file1 had %d, file2 had %d)",
            len(common_ids),
            len(ann1),
            len(ann2),
        )

    labels1 = [ann1[cid] for cid in common_ids]
    labels2 = [ann2[cid] for cid in common_ids]

    return float(cohen_kappa_score(labels1, labels2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute Cohen's kappa agreement from two annotator export files."
    )
    parser.add_argument(
        "--annotator1",
        type=str,
        required=True,
        help="Path to first annotator JSON export (e.g. Mariam).",
    )
    parser.add_argument(
        "--annotator2",
        type=str,
        required=True,
        help="Path to second annotator JSON export (e.g. Omar Mustafa).",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="ml/topics/configs/topics_config.yaml",
        help="Path to YAML configuration containing agreement_kappa_target.",
    )
    parser.add_argument(
        "--show-disagreements",
        action="store_true",
        help="Print list of chunks with discordant annotations.",
    )
    args = parser.parse_args()

    target = load_kappa_target(args.config)
    kappa = compute_cohen_kappa(args.annotator1, args.annotator2)
    disagreements = find_disagreements(args.annotator1, args.annotator2)

    print("=" * 60)
    print("INTER-ANNOTATOR AGREEMENT REPORT (Issue #52 / W2-18)")
    print("=" * 60)
    print(f"Annotator 1 export : {args.annotator1}")
    print(f"Annotator 2 export : {args.annotator2}")
    print(f"Target threshold   : >= {target:.2f}")
    print(f"Cohen's Kappa      : {kappa:.4f}")
    print(f"Total Disagreements: {len(disagreements)}")
    print(f"Status             : {'PASS (Target met)' if kappa >= target else 'FAIL (Below target)'}")
    print("=" * 60)

    if args.show_disagreements and disagreements:
        print("\nDiscordant Items:")
        for d in disagreements:
            print(
                f"  - [{d['chunk_id']}] Annotator 1: {d['annotator_1_topic_id']} vs "
                f"Annotator 2: {d['annotator_2_topic_id']}"
            )


if __name__ == "__main__":
    main()
