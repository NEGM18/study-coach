"""Topic-agnostic features for model A. Owner: Amr (issue #15).

Built from earlier answers only. Never uses topic or question IDs as inputs.
"""

from ml_core.schemas import Attempt

FEATURES = [
    "prior_correct",
    "prior_wrong",
    "answers_since_last_on_topic",
    "topic_correct_rate",
    "question_correct_rate",
]


def build_features(history: list[Attempt], topic_id: int) -> dict[str, float]:
    """Features for the student's NEXT answer on `topic_id`, from `history` only."""
    raise NotImplementedError("Issue #15")
