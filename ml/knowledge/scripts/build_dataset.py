"""Build the model A dataset (issues #13, #14).

ASSISTments 2009-2010 skill builder -> kt_processed_v1.parquet, and the same
pipeline on an EdNet KT1 student sample -> kt_ednet_processed_v1.parquet.

Run: python -m ml.knowledge.scripts.build_dataset --config ml/knowledge/configs/build.yaml
     (add --skip-ednet to build ASSISTments only)
"""

import argparse
import io
import logging
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from ml_core.cleaning_log import CleaningLog
from ml_core.knowledge.clean import clean_attempts, split_by_student, to_app_columns

LOGGER = logging.getLogger(__name__)
ASSISTMENTS_COLUMNS = [
    "order_id",
    "user_id",
    "problem_id",
    "original",
    "correct",
    "attempt_count",
    "ms_first_response",
    "skill_id",
    "hint_count",
]


def encode_skill_ids(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Map skill_id values (e.g. "1_13" for collapsed multi-skill rows) to stable ints 1..N."""
    present = df["skill_id"].dropna().astype(str)
    names = sorted(present.unique())
    codes = {name: index for index, name in enumerate(names, start=1)}
    out = df.copy()
    out["skill_id"] = df["skill_id"].map(lambda s: codes.get(str(s)) if pd.notna(s) else np.nan)
    return out, pd.DataFrame({"source_skill_id": names, "topic_id": list(codes.values())})


def load_assistments(cfg: dict) -> pd.DataFrame:
    path = cfg["assistments"]["raw_path"]
    df = pd.read_csv(
        path, encoding=cfg["assistments"]["encoding"], usecols=ASSISTMENTS_COLUMNS, dtype={"skill_id": str}
    )
    LOGGER.info("ASSISTments raw: %d rows, %d students", len(df), df["user_id"].nunique())
    return df


def load_ednet_sample(cfg: dict) -> pd.DataFrame:
    """Read a seeded sample of EdNet KT1 students and map them to ASSISTments columns."""
    questions = pd.read_csv(cfg["ednet"]["questions_csv"], usecols=["question_id", "correct_answer", "tags"])
    answer_key = questions.set_index("question_id")
    frames = []
    with zipfile.ZipFile(cfg["ednet"]["kt1_zip"]) as archive:
        members = sorted(n for n in archive.namelist() if n.endswith(".csv") and Path(n).stem.startswith("u"))
        rng = np.random.default_rng(cfg["seed"])
        sample = rng.choice(members, size=min(cfg["ednet"]["sample_students"], len(members)), replace=False)
        for name in sorted(sample):
            user = pd.read_csv(io.BytesIO(archive.read(name)))
            user["user_id"] = Path(name).stem
            frames.append(user)
    raw = pd.concat(frames, ignore_index=True).sort_values(["user_id", "timestamp"], kind="stable")
    key = answer_key.reindex(raw["question_id"])
    first_tag = key["tags"].astype(str).str.split(";").str[0]
    return pd.DataFrame(
        {
            "order_id": np.arange(1, len(raw) + 1),
            "user_id": raw["user_id"].to_numpy(),
            "problem_id": raw["question_id"].str.lstrip("q").astype(int).to_numpy(),
            "correct": (raw["user_answer"].to_numpy() == key["correct_answer"].to_numpy()).astype(int),
            "ms_first_response": raw["elapsed_time"].to_numpy(),
            "skill_id": pd.to_numeric(first_tag, errors="coerce").where(first_tag != "-1").to_numpy(),
        }
    )


def build(raw: pd.DataFrame, name: str, cfg: dict, out_path: str, log_path: str) -> pd.DataFrame:
    log = CleaningLog(name)
    clean = clean_attempts(raw, cfg["cleaning"], log)
    app = split_by_student(to_app_columns(clean, cfg["user_id_salt"]), cfg["splits"], cfg["seed"])
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    app.to_parquet(out_path, index=False)
    log.save(log_path)
    summary = app.groupby("split").agg(rows=("is_correct", "size"), students=("user_id", "nunique"))
    summary["correct_rate"] = app.groupby("split")["is_correct"].mean().round(4)
    LOGGER.info("%s: %d -> %d rows, wrote %s\n%s", name, len(raw), len(app), out_path, summary)
    return app


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="ml/knowledge/configs/build.yaml")
    parser.add_argument("--skip-ednet", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    out = cfg["output"]

    raw, topic_map = encode_skill_ids(load_assistments(cfg))
    Path(out["processed"]).parent.mkdir(parents=True, exist_ok=True)
    topic_map.to_csv(Path(out["processed"]).with_name("kt_topic_map_v1.csv"), index=False)
    build(raw, "knowledge_assistments", cfg, out["processed"], out["cleaning_log"])
    if not args.skip_ednet:
        build(
            load_ednet_sample(cfg), "knowledge_ednet", cfg, out["ednet_processed"], out["ednet_cleaning_log"]
        )


if __name__ == "__main__":
    main()
