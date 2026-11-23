"""Tests for Model C evaluation logic and circularity guard (Issue #51)."""

import pytest

from ml.topics.scripts.build_dataset import evaluate_stub_accuracy, evaluate_topic_predictions
from ml_core.schemas import Chunk, Topic


def test_evaluate_topic_predictions_raises_on_circular():
    """Ensure evaluation fails loudly when predictions match gold labels identically."""
    y_true = [101, 102, 103, 104]
    y_pred = [101, 102, 103, 104]

    with pytest.raises(ValueError, match="Circular evaluation detected"):
        evaluate_topic_predictions(y_true, y_pred)


def test_evaluate_topic_predictions_computes_honest_metrics():
    """Verify honest metric computation when predictions and gold labels differ."""
    y_true = [101, 102, 103, 104]
    y_pred = [101, 102, 104, 103]

    metrics = evaluate_topic_predictions(y_true, y_pred)
    assert metrics["accuracy"] == 0.5
    assert 0.0 <= metrics["macro_f1"] <= 1.0


def test_evaluate_stub_accuracy_circularity_guard():
    """Test evaluate_stub_accuracy raises when stub predictions match gold labels identically."""
    topics = [
        Topic(1, 10, "Linked lists", "pointer node"),
        Topic(2, 10, "Binary trees", "root child"),
    ]
    chunks = [
        Chunk("c1", 10, 3, "pointer node next head", topic_id=1),
        Chunk("c2", 10, 4, "root child left right bst", topic_id=2),
    ]

    with pytest.raises(ValueError, match="Circular evaluation detected"):
        evaluate_stub_accuracy(chunks, topics)
