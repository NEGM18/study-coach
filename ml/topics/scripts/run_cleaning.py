"""Issue #27: Run extraction + cleaning pipeline on raw lecture decks across all 3 pilot courses.

Saves audit trail to ml/topics/cleaning_log.csv and generates a side-by-side
verification report of 30 random chunks in ml/topics/spot_check_30.md.
"""

import argparse
import random
import re
from pathlib import Path
from typing import Any

import yaml

from ml_core.cleaning_log import CleaningLog
from ml_core.schemas import Chunk
from ml_core.topics.clean import clean_chunks
from ml_core.topics.extract import extract_file

COURSE_CODE_TO_ID = {
    "ds": 1,
    "os": 2,
    "ai": 3,
}


def parse_lecture_id(file_path: Path, course_id: int) -> int:
    """Derive deterministic integer lecture_id from filename (e.g. ds_lec02.pdf -> 102)."""
    match = re.search(r"lec(\d+)", file_path.stem, re.IGNORECASE)
    lec_num = int(match.group(1)) if match else 1
    return course_id * 100 + lec_num


def extract_raw_chunks(raw_dir: Path, config: dict[str, Any]) -> tuple[list[Chunk], dict[str, str]]:
    """Extract all slides across the 3 pilot courses into Chunk objects."""
    all_chunks: list[Chunk] = []
    original_texts: dict[str, str] = {}

    for course_code, course_id in sorted(COURSE_CODE_TO_ID.items()):
        course_path = raw_dir / course_code
        if not course_path.exists():
            continue

        deck_files = sorted(
            [f for f in course_path.iterdir() if f.suffix.lower() in {".pdf", ".pptx"}],
            key=lambda f: f.name,
        )
        for deck_file in deck_files:
            lecture_id = parse_lecture_id(deck_file, course_id)
            pages = extract_file(deck_file, settings=config)

            for page in pages:
                chunk_id = f"c_{course_code}_l{lecture_id}_s{page.slide_no:02d}"
                chunk = Chunk(
                    chunk_id=chunk_id,
                    course_id=course_id,
                    lecture_id=lecture_id,
                    text=page.text,
                    slide_no=page.slide_no,
                )
                all_chunks.append(chunk)
                original_texts[chunk_id] = page.text

    return all_chunks, original_texts


def generate_spot_check_report(
    sampled_chunks: list[Chunk],
    original_texts: dict[str, str],
    log: CleaningLog,
    output_path: Path,
) -> None:
    """Generate Markdown report comparing original vs cleaned text side-by-side."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = [
        "# Issue #27: Cleaning Pipeline 30-Chunk Spot-Check",
        "",
        "This report verifies that the 7-step cleaning pipeline eliminates headers, metadata,",
        "and OCR noise while preserving genuine lecture content across all pilot courses.",
        "",
        "## Cleaning Audit Trail Summary",
        "",
        "| Step | Rows Before | Rows After | Delta | Reason |",
        "|---|---|---|---|---|",
    ]

    for row in log.rows:
        delta = int(row["rows_before"]) - int(row["rows_after"])
        lines.append(
            f"| `{row['step']}` | {row['rows_before']} | {row['rows_after']} | -{delta} | {row['reason']} |"
        )

    lines.extend(
        [
            "",
            f"## Spot-Check Sample ({len(sampled_chunks)} Chunks, Seed 42)",
            "",
        ]
    )

    for idx, c in enumerate(sampled_chunks, start=1):
        orig = original_texts.get(c.chunk_id, "").strip().replace("\n", " <br> ")
        cleaned = c.text.strip().replace("\n", " <br> ")
        lines.append(f"### Chunk {idx}: `{c.chunk_id}` (Course {c.course_id}, Lang: `{c.lang}`)")
        lines.append(f"* **Original Slide Text**:\n  > {orig}")
        lines.append(f"* **Cleaned & Normalized Chunk**:\n  > {cleaned}")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run topics extraction and cleaning pipeline.")
    parser.add_argument(
        "--config",
        type=str,
        default="ml/topics/configs/topics_config.yaml",
        help="Path to topics YAML configuration file.",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    raw_dir = Path("ml/data/raw/topics")
    print(f"Extracting lecture decks from {raw_dir}...")
    raw_chunks, original_texts = extract_raw_chunks(raw_dir, config)
    print(f"Extracted {len(raw_chunks)} total raw slides across 3 courses.")

    cleaning_log = CleaningLog("topics")
    config["cleaning_log"] = cleaning_log

    print("Executing 7-step cleaning pipeline...")
    cleaned_chunks = clean_chunks(raw_chunks, config)
    print(f"Cleaning complete: {len(raw_chunks)} -> {len(cleaned_chunks)} chunks.")

    log_path = Path(config.get("cleaning_log_path", "ml/topics/cleaning_log.csv"))
    cleaning_log.save(str(log_path))
    print(f"Saved cleaning log to {log_path}.")

    seed = int(config.get("seed", 42))
    num_samples = int(config.get("num_spot_check_chunks", 30))
    rng = random.Random(seed)
    sample_size = min(num_samples, len(cleaned_chunks))
    sampled = rng.sample(cleaned_chunks, sample_size)

    report_path = Path(config.get("spot_check_output", "ml/topics/spot_check_30.md"))
    generate_spot_check_report(sampled, original_texts, cleaning_log, report_path)
    print(f"Generated 30-chunk spot-check report at {report_path}.")


if __name__ == "__main__":
    main()
