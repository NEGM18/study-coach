"""Issue #19: pick 20 random processed rows and find each one in the raw ASSISTments file.

Run: python -m ml.knowledge.scripts.spot_check --config ml/knowledge/configs/build.yaml
Writes ml/knowledge/spot_check_20.md.
"""

import argparse
import logging
from pathlib import Path

import pandas as pd
import yaml

from ml_core.knowledge.clean import hash_user_id

LOGGER = logging.getLogger(__name__)
SAMPLE_SIZE = 20


def find_in_raw(row: pd.Series, raw: pd.DataFrame, skill_names: dict[int, str]) -> tuple[str, str]:
    """Return (verdict, raw order_id) for one processed row."""
    match = raw[
        (raw["user_hash"] == row["user_id"])
        & (raw["problem_id"] == row["question_id"])
        & (raw["skill_id"] == skill_names[row["topic_id"]])
        & (raw["correct"] == int(row["is_correct"]))
    ]
    if match.empty:
        return "MISMATCH: not found", "-"
    exact = match[match["ms_first_response"].clip(upper=row["response_time_ms"]) == row["response_time_ms"]]
    if exact.empty:
        return "MISMATCH: response time differs", str(match["order_id"].iloc[0])
    return "ok", str(exact["order_id"].iloc[0])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="ml/knowledge/configs/build.yaml")
    parser.add_argument("--out", default="ml/knowledge/spot_check_20.md")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    processed = pd.read_parquet(cfg["output"]["processed"])
    topic_map = pd.read_csv(Path(cfg["output"]["processed"]).with_name("kt_topic_map_v1.csv"), dtype=str)
    skill_names = {
        int(t): s for s, t in zip(topic_map["source_skill_id"], topic_map["topic_id"], strict=True)
    }
    raw = pd.read_csv(
        cfg["assistments"]["raw_path"], encoding="latin-1", dtype={"skill_id": str}, low_memory=False
    )
    raw["user_hash"] = raw["user_id"].map(lambda u: hash_user_id(u, cfg["user_id_salt"]))

    sample = processed.sample(SAMPLE_SIZE, random_state=cfg["seed"])
    lines = [
        "# Spot check: 20 processed rows vs raw (issue #19)",
        "",
        f"Sampled with seed {cfg['seed']} from `{cfg['output']['processed']}`.",
        "",
        "| user_id (hashed) | topic_id | question_id | is_correct | response_time_ms "
        "| raw order_id | result |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    verdicts = []
    for _, row in sample.iterrows():
        verdict, order_id = find_in_raw(row, raw, skill_names)
        verdicts.append(verdict)
        lines.append(
            f"| {row.user_id} | {row.topic_id} | {row.question_id} | {row.is_correct} | "
            f"{row.response_time_ms} | {order_id} | {verdict} |"
        )
    n_ok = sum(v == "ok" for v in verdicts)
    lines += ["", f"**Result: {n_ok}/{SAMPLE_SIZE} rows found unchanged in the raw file.**", ""]
    Path(args.out).write_text("\n".join(lines), encoding="utf-8")
    LOGGER.info("%d/%d rows ok, wrote %s", n_ok, SAMPLE_SIZE, args.out)


if __name__ == "__main__":
    main()
