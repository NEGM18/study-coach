"""Model A contract. Owner: Amr (issue #15).

Week 1 stub: smoothed correct rate of this student on this topic.
The trained model replaces it later behind the same signature.
"""

from ml_core.schemas import Attempt


def predict_mastery(history: list[Attempt], topic_id: int) -> float:
    """Chance (0..1) that the student answers the next question on `topic_id` correctly."""
    raise NotImplementedError("Issue #15")
