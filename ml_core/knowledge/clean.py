"""Cleaning, app renaming and student splits for model A. Owner: Amr (issues #13, #14).

Input rows use ASSISTments column names (EdNet is mapped to them first).
Thresholds come from ml/knowledge/configs/build.yaml and are passed in as `settings`.
"""

import hashlib
import logging

import numpy as np
import pandas as pd

from ml_core.cleaning_log import CleaningLog

LOGGER = logging.getLogger(__name__)

APP_COLUMNS = {
    "skill_id": "topic_id",
    "problem_id": "question_id",
    "correct": "is_correct",
    "ms_first_response": "response_time_ms",
    "order_id": "attempt_order",
}
APP_COLUMN_ORDER = [
    "user_id",
    "topic_id",
    "question_id",
    "attempt_order",
    "is_correct",
    "response_time_ms",
    "attempt_count",
    "hint_count",
]


def clean_attempts(df: pd.DataFrame, settings: dict, log: CleaningLog) -> pd.DataFrame:
    """Run every data-plan cleaning step in order, logging rows in and out."""
    if "original" in df.columns:
        df = log.step("keep original problems", df, df[df["original"] == 1], "scaffolding rows are hints")
    df = log.step("drop missing skill_id", df, df[df["skill_id"].notna()], "topic_id is required")
    df = log.step(
        "drop duplicate order_id",
        df,
        df.drop_duplicates("order_id", keep="first"),
        "multi-skill rows repeat one answer",
    )
    df = log.step(
        "drop response time <= 0",
        df,
        df[df["ms_first_response"] > 0].copy(),
        "non-positive times are logging errors",
    )
    cap = df["ms_first_response"].quantile(settings["response_time_cap_quantile"])
    df["ms_first_response"] = df["ms_first_response"].clip(upper=cap)
    LOGGER.info("capped ms_first_response at %.0f ms", cap)
    return drop_sparse(df, settings, log)


def drop_sparse(df: pd.DataFrame, settings: dict, log: CleaningLog) -> pd.DataFrame:
    """Drop students and skills with too few answers to learn from."""
    per_user = df["user_id"].value_counts()
    keep_users = per_user[per_user >= settings["min_answers_per_student"]].index
    df = log.step(
        f"drop students with < {settings['min_answers_per_student']} answers",
        df,
        df[df["user_id"].isin(keep_users)],
        "too little history",
    )
    per_skill = df["skill_id"].value_counts()
    keep_skills = per_skill[per_skill >= settings["min_answers_per_skill"]].index
    return log.step(
        f"drop skills with < {settings['min_answers_per_skill']} answers",
        df,
        df[df["skill_id"].isin(keep_skills)],
        "too few answers to estimate the skill",
    )


def hash_user_id(user_id: object, salt: str) -> str:
    """Stable, non-reversible student ID (privacy rule: never store raw IDs)."""
    return hashlib.sha256(f"{salt}:{user_id}".encode()).hexdigest()[:16]


def to_app_columns(df: pd.DataFrame, salt: str) -> pd.DataFrame:
    """Rename to `quiz_attempts` columns, hash users and number each student's answers from 1."""
    out = df.rename(columns=APP_COLUMNS)
    out = out.sort_values(["user_id", "attempt_order"])
    out["attempt_order"] = out.groupby("user_id").cumcount() + 1
    out["user_id"] = out["user_id"].map(lambda u: hash_user_id(u, salt))
    out["topic_id"] = out["topic_id"].astype(int)
    out["question_id"] = out["question_id"].astype(int)
    out["is_correct"] = out["is_correct"].astype(bool)
    out["response_time_ms"] = out["response_time_ms"].round().astype("Int64")
    for column in ("attempt_count", "hint_count"):
        out[column] = out[column].fillna(0).astype(int) if column in out else 0
    return out[APP_COLUMN_ORDER].reset_index(drop=True)


def split_by_student(df: pd.DataFrame, fractions: dict[str, float], seed: int) -> pd.DataFrame:
    """Add a `split` column; every student lands in exactly one split."""
    users = np.array(sorted(df["user_id"].unique()))
    np.random.default_rng(seed).shuffle(users)
    position = np.arange(len(users))
    train_end = fractions["train"] * len(users)
    val_end = (fractions["train"] + fractions["val"]) * len(users)
    names = np.where(position < train_end, "train", np.where(position < val_end, "val", "test"))
    out = df.copy()
    out["split"] = out["user_id"].map(dict(zip(users, names, strict=True)))
    return out
