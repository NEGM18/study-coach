"""Topic-agnostic features for model A. Owner: Amr (issue #15).

Built from earlier answers only. Never uses topic or question IDs as inputs:
IDs only select which earlier answers are counted.
"""

import pandas as pd

from ml_core.schemas import Attempt

FEATURES = [
    "prior_correct",
    "prior_wrong",
    "answers_since_last_on_topic",
    "topic_correct_rate",
    "question_correct_rate",
]
PRIOR_MEAN = 0.5  # rate assumed before any evidence
PRIOR_STRENGTH = 2.0  # pseudo-answers behind PRIOR_MEAN


def smoothed_rate[T: (float, pd.Series)](n_correct: T, n_total: T) -> T:
    """Correct rate pulled toward PRIOR_MEAN when there are few answers."""
    return (n_correct + PRIOR_STRENGTH * PRIOR_MEAN) / (n_total + PRIOR_STRENGTH)


def build_features(history: list[Attempt], topic_id: int, question_id: int | None = None) -> dict[str, float]:
    """Features for the student's NEXT answer on `topic_id`, from `history` only."""
    ordered = sorted(history, key=lambda a: a.attempt_order)
    on_topic = [a for a in ordered if a.topic_id == topic_id]
    on_question = [a for a in ordered if question_id is not None and a.question_id == question_id]
    prior_correct = float(sum(a.is_correct for a in on_topic))

    last_index = max((i for i, a in enumerate(ordered) if a.topic_id == topic_id), default=None)
    since_last = float(len(ordered)) if last_index is None else float(len(ordered) - 1 - last_index)

    return {
        "prior_correct": prior_correct,
        "prior_wrong": float(len(on_topic)) - prior_correct,
        "answers_since_last_on_topic": since_last,
        "topic_correct_rate": smoothed_rate(prior_correct, float(len(on_topic))),
        "question_correct_rate": smoothed_rate(
            float(sum(a.is_correct for a in on_question)), float(len(on_question))
        ),
    }


def build_feature_frame(attempts: pd.DataFrame) -> pd.DataFrame:
    """Add FEATURES to app-shaped `quiz_attempts` rows; each row sees only earlier rows.

    Needs columns user_id, topic_id, question_id, attempt_order, is_correct.
    Gives the same numbers as `build_features(earlier_rows, topic_id, question_id)` per row.
    """
    df = attempts.sort_values(["user_id", "attempt_order"]).reset_index(drop=True)
    correct = df["is_correct"].astype(int)
    topic_keys = [df["user_id"], df["topic_id"]]
    question_keys = [df["user_id"], df["question_id"]]

    topic_seen = correct.groupby(topic_keys).cumcount().astype(float)
    df["prior_correct"] = (correct.groupby(topic_keys).cumsum() - correct).astype(float)
    df["prior_wrong"] = topic_seen - df["prior_correct"]
    df["topic_correct_rate"] = smoothed_rate(df["prior_correct"], topic_seen)

    question_seen = correct.groupby(question_keys).cumcount().astype(float)
    question_correct = (correct.groupby(question_keys).cumsum() - correct).astype(float)
    df["question_correct_rate"] = smoothed_rate(question_correct, question_seen)

    position = correct.groupby(df["user_id"]).cumcount().astype(float)
    last_position = position.groupby(topic_keys).shift(1)
    df["answers_since_last_on_topic"] = (position - 1 - last_position).fillna(position)
    return df
