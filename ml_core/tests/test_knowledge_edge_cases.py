"""Edge-case unit tests for predict_mastery (W2-11, issue #45).

Every test verifies that predict_mastery returns a valid probability in [0, 1]
under unusual but realistic input conditions.  Six cases are required by the spec:

    1. 0 attempts (empty history)
    2. 1 attempt on the topic
    3. unseen topic (history only contains other topics)
    4. 1,000+ history attempts
    5. all-correct history
    6. all-wrong history

We also test that the stub is monotone in evidence (more correct answers → higher
prediction than more wrong answers on the same topic).
"""

import pytest

from ml_core.knowledge.predict import predict_mastery
from ml_core.schemas import Attempt

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def make_attempt(order: int, topic: int, correct: bool, question: int = 1) -> Attempt:
    return Attempt(
        user_id="u_test",
        topic_id=topic,
        question_id=question,
        attempt_order=order,
        is_correct=correct,
    )


def many_attempts(n: int, topic: int, correct: bool) -> list[Attempt]:
    return [make_attempt(i, topic, correct, question=i) for i in range(1, n + 1)]


# ---------------------------------------------------------------------------
# Edge-case 1: 0 attempts (empty history)
# ---------------------------------------------------------------------------


def test_predict_mastery_zero_attempts_returns_valid_probability() -> None:
    """With no history, the stub returns the prior (0.5); always in [0, 1]."""
    p = predict_mastery([], topic_id=7)
    assert 0.0 <= p <= 1.0, f"Expected probability in [0,1], got {p}"
    assert p == pytest.approx(0.5), "Stub prior should be 0.5 with no evidence"


# ---------------------------------------------------------------------------
# Edge-case 2: exactly 1 attempt on the topic
# ---------------------------------------------------------------------------


def test_predict_mastery_one_correct_attempt_returns_valid_probability() -> None:
    history = [make_attempt(1, topic=7, correct=True)]
    p = predict_mastery(history, topic_id=7)
    assert 0.0 <= p <= 1.0, f"Expected probability in [0,1], got {p}"
    # With 1 correct + 2 pseudo-answers (PRIOR_STRENGTH=2, PRIOR_MEAN=0.5):
    # (1 + 2*0.5) / (1 + 2) = 2/3 ≈ 0.667
    assert p == pytest.approx(2 / 3), "Expected smoothed rate (1+1)/(1+2) = 2/3"


def test_predict_mastery_one_wrong_attempt_returns_valid_probability() -> None:
    history = [make_attempt(1, topic=7, correct=False)]
    p = predict_mastery(history, topic_id=7)
    assert 0.0 <= p <= 1.0, f"Expected probability in [0,1], got {p}"
    # (0 + 2*0.5) / (1 + 2) = 1/3 ≈ 0.333
    assert p == pytest.approx(1 / 3), "Expected smoothed rate (0+1)/(1+2) = 1/3"


# ---------------------------------------------------------------------------
# Edge-case 3: unseen topic (all history on a different topic)
# ---------------------------------------------------------------------------


def test_predict_mastery_unseen_topic_returns_prior() -> None:
    """When no history is on the queried topic, return the stub prior."""
    history = [
        make_attempt(1, topic=99, correct=True),
        make_attempt(2, topic=99, correct=True),
        make_attempt(3, topic=99, correct=False),
    ]
    p = predict_mastery(history, topic_id=7)  # topic 7 never seen
    assert 0.0 <= p <= 1.0, f"Expected probability in [0,1], got {p}"
    assert p == pytest.approx(0.5), "Stub prior should be 0.5 for an unseen topic"


# ---------------------------------------------------------------------------
# Edge-case 4: 1,000+ history attempts
# ---------------------------------------------------------------------------


def test_predict_mastery_long_history_stays_in_range() -> None:
    """With 1,200 attempts on the topic, result stays in [0, 1] and is well-defined."""
    history = many_attempts(600, topic=7, correct=True) + many_attempts(600, topic=7, correct=False)
    p = predict_mastery(history, topic_id=7)
    assert 0.0 <= p <= 1.0, f"Expected probability in [0,1], got {p}"
    # 600 correct out of 1200 → smoothed rate ≈ 0.5 (prior washes out quickly)
    assert p == pytest.approx(0.5, abs=0.01)


# ---------------------------------------------------------------------------
# Edge-case 5: all-correct history
# ---------------------------------------------------------------------------


def test_predict_mastery_all_correct_returns_high_probability() -> None:
    """All-correct history should produce a probability > 0.5."""
    history = many_attempts(50, topic=7, correct=True)
    p = predict_mastery(history, topic_id=7)
    assert 0.0 <= p <= 1.0, f"Expected probability in [0,1], got {p}"
    assert p > 0.5, f"All-correct history should give p > 0.5; got {p}"
    # Exact: (50 + 1) / (50 + 2) = 51/52 ≈ 0.981
    assert p == pytest.approx(51 / 52, abs=1e-6)


# ---------------------------------------------------------------------------
# Edge-case 6: all-wrong history
# ---------------------------------------------------------------------------


def test_predict_mastery_all_wrong_returns_low_probability() -> None:
    """All-wrong history should produce a probability < 0.5."""
    history = many_attempts(50, topic=7, correct=False)
    p = predict_mastery(history, topic_id=7)
    assert 0.0 <= p <= 1.0, f"Expected probability in [0,1], got {p}"
    assert p < 0.5, f"All-wrong history should give p < 0.5; got {p}"
    # Exact: (0 + 1) / (50 + 2) = 1/52 ≈ 0.019
    assert p == pytest.approx(1 / 52, abs=1e-6)


# ---------------------------------------------------------------------------
# Monotone evidence (extra sanity)
# ---------------------------------------------------------------------------


def test_predict_mastery_more_correct_gives_higher_estimate() -> None:
    """More correct answers on a topic → higher prediction than more wrong answers."""
    history_good = many_attempts(20, topic=7, correct=True)
    history_bad = many_attempts(20, topic=7, correct=False)
    p_good = predict_mastery(history_good, topic_id=7)
    p_bad = predict_mastery(history_bad, topic_id=7)
    assert 0.0 <= p_good <= 1.0
    assert 0.0 <= p_bad <= 1.0
    assert p_good > p_bad, f"Expected p_good ({p_good:.4f}) > p_bad ({p_bad:.4f})"


# ---------------------------------------------------------------------------
# Metric unit test: hand-verified 6-row example (W2-09 requirement)
# ---------------------------------------------------------------------------


def test_metrics_match_hand_calculations() -> None:
    """6-row toy example with hand-calculated AUC, accuracy, log-loss, ECE.

    Rows (y_true, y_prob):
        (1, 0.9), (1, 0.8), (1, 0.4), (0, 0.3), (0, 0.2), (0, 0.1)

    AUC: 9 concordant pairs out of 9 possible (all positive scores > all negative) = 1.0
    Accuracy (threshold 0.5): preds = [1,1,0,0,0,0], truth = [1,1,1,0,0,0] → 5/6 ≈ 0.8333
    Log-loss: mean of [-log(0.9), -log(0.8), -log(0.4), -log(0.7), -log(0.8), -log(0.9)]
    ECE (1 bin): |mean_true - mean_pred| = |0.5 - 0.45| = 0.05  (all in one bin)
    """
    import math

    from sklearn.calibration import calibration_curve
    from sklearn.metrics import accuracy_score, log_loss, roc_auc_score

    y_true = [1, 1, 1, 0, 0, 0]
    y_prob = [0.9, 0.8, 0.4, 0.3, 0.2, 0.1]

    # AUC
    auc = roc_auc_score(y_true, y_prob)
    assert auc == pytest.approx(1.0), f"Expected AUC=1.0, got {auc}"

    # Accuracy
    y_pred = [int(p >= 0.5) for p in y_prob]
    acc = accuracy_score(y_true, y_pred)
    assert acc == pytest.approx(5 / 6, abs=1e-6), f"Expected acc≈0.8333, got {acc}"

    # Log-loss (hand: mean of individual terms)
    hand_ll = -sum(
        t * math.log(p) + (1 - t) * math.log(1 - p) for t, p in zip(y_true, y_prob, strict=True)
    ) / len(y_true)
    sk_ll = log_loss(y_true, y_prob)
    assert sk_ll == pytest.approx(hand_ll, rel=1e-6), f"Log-loss mismatch: sklearn={sk_ll}, hand={hand_ll}"

    # ECE (1-bin calibration)
    frac, mean_pred = calibration_curve(y_true, y_prob, n_bins=1)
    ece = abs(frac[0] - mean_pred[0])
    # mean_pred ≈ 0.45, mean_true (fraction positive in that bin) = 0.5 → ECE = 0.05
    assert ece == pytest.approx(abs(0.5 - 0.45), abs=1e-2)
