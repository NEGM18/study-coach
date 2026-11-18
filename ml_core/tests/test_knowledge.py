"""Model A: cleaning, app columns, student splits, leak-free features, stub."""

import pandas as pd
import pytest

from ml_core.cleaning_log import CleaningLog
from ml_core.knowledge.clean import (
    APP_COLUMN_ORDER,
    clean_attempts,
    hash_user_id,
    split_by_student,
    to_app_columns,
)
from ml_core.knowledge.features import FEATURES, build_feature_frame, build_features
from ml_core.knowledge.predict import predict_mastery
from ml_core.schemas import Attempt

SETTINGS = {"response_time_cap_quantile": 0.99, "min_answers_per_student": 2, "min_answers_per_skill": 2}


def raw_rows() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_id": [1, 2, 2, 3, 4, 5, 6, 7, 8],
            "user_id": [10, 10, 10, 10, 20, 20, 20, 30, 20],
            "problem_id": [100, 101, 101, 102, 100, 101, 103, 100, 104],
            "skill_id": [1, 1, 1, 2, 1, 2, None, 1, 2],
            "correct": [1, 0, 0, 1, 1, 1, 0, 1, 0],
            "ms_first_response": [500, 800, 800, 0, 700, 900, 400, 300, 1000],
            "original": [1, 1, 1, 1, 1, 1, 1, 1, 0],
        }
    )


def test_clean_logs_each_step_and_applies_rules() -> None:
    log = CleaningLog("knowledge")
    out = clean_attempts(raw_rows(), SETTINGS, log)
    steps = [(r["step"], r["rows_before"], r["rows_after"]) for r in log.rows]
    assert steps[:4] == [
        ("keep original problems", 9, 8),
        ("drop missing skill_id", 8, 7),
        ("drop duplicate order_id", 7, 6),
        ("drop response time <= 0", 6, 5),
    ]
    assert set(out["user_id"]) == {10, 20}  # user 30 has one answer
    assert out["order_id"].is_unique


def test_response_time_is_capped_at_quantile() -> None:
    out = clean_attempts(raw_rows(), {**SETTINGS, "response_time_cap_quantile": 0.5}, CleaningLog("k"))
    assert out["ms_first_response"].max() <= 800


def test_to_app_columns_renames_hashes_and_orders() -> None:
    df = pd.DataFrame(
        {
            "user_id": [7, 7, 8],
            "order_id": [50, 40, 60],
            "skill_id": [1.0, 2.0, 1.0],
            "problem_id": [9, 8, 9],
            "correct": [1, 0, 1],
            "ms_first_response": [100.4, 200.0, 300.0],
        }
    )
    out = to_app_columns(df, salt="s")
    assert list(out.columns) == APP_COLUMN_ORDER
    assert "7" not in set(out["user_id"])
    first = out[out["user_id"] == hash_user_id(7, "s")]
    assert first["attempt_order"].tolist() == [1, 2]
    assert first["question_id"].tolist() == [8, 9]  # order_id 40 comes first
    assert out["is_correct"].dtype == bool


def test_split_never_puts_a_student_in_two_splits() -> None:
    df = pd.DataFrame({"user_id": [f"u{i // 3}" for i in range(300)]})
    out = split_by_student(df, {"train": 0.8, "val": 0.1, "test": 0.1}, seed=42)
    assert out.groupby("user_id")["split"].nunique().max() == 1
    assert out.drop_duplicates("user_id")["split"].value_counts().to_dict() == {
        "train": 80,
        "val": 10,
        "test": 10,
    }
    assert out.equals(split_by_student(df, {"train": 0.8, "val": 0.1, "test": 0.1}, seed=42))


def history() -> list[Attempt]:
    rows = [(1, 7, 1, True), (2, 8, 2, False), (3, 7, 3, False), (4, 9, 4, True), (5, 7, 1, True)]
    return [Attempt("u1", topic, question, order, ok) for order, topic, question, ok in rows]


def test_build_features_counts_topic_history() -> None:
    feats = build_features(history(), topic_id=7, question_id=1)
    assert feats["prior_correct"] == 2
    assert feats["prior_wrong"] == 1
    assert feats["answers_since_last_on_topic"] == 0
    assert feats["topic_correct_rate"] == pytest.approx(3 / 5)
    assert feats["question_correct_rate"] == pytest.approx(3 / 4)


def test_feature_frame_uses_only_earlier_answers() -> None:
    attempts = history()
    frame = build_feature_frame(pd.DataFrame([a.__dict__ for a in attempts]))
    for i, attempt in enumerate(attempts):
        expected = build_features(attempts[:i], attempt.topic_id, attempt.question_id)
        assert frame.loc[i, FEATURES].to_dict() == pytest.approx(expected)


def test_changing_a_later_answer_never_changes_earlier_features() -> None:
    attempts = history()
    flipped = attempts[:-1] + [Attempt("u1", 7, 1, 5, False)]
    a = build_feature_frame(pd.DataFrame([x.__dict__ for x in attempts]))
    b = build_feature_frame(pd.DataFrame([x.__dict__ for x in flipped]))
    assert a[FEATURES].equals(b[FEATURES])


def test_predict_mastery_is_smoothed_topic_rate() -> None:
    assert predict_mastery([], topic_id=7) == 0.5
    assert predict_mastery(history(), topic_id=7) == pytest.approx(3 / 5)
    assert predict_mastery(history(), topic_id=8) < 0.5
