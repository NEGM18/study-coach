"""Tests for Model C evaluation & Cohen's kappa calculation (Issues #51 & #52)."""

import json
from pathlib import Path

import pytest

from ml.topics.scripts.build_dataset import evaluate_topic_predictions
from ml.topics.scripts.compute_kappa import (
    compute_cohen_kappa,
    find_disagreements,
    load_kappa_target,
)


def test_evaluation_fails_loudly_on_circular_predictions():
    """Verify evaluation raises ValueError when gold == predictions on every row."""
    gold = [101, 102, 103, 104]
    preds = [101, 102, 103, 104]

    with pytest.raises(ValueError, match="Circular evaluation detected"):
        evaluate_topic_predictions(gold, preds)


def test_evaluation_succeeds_on_honest_predictions():
    """Verify evaluation computes accuracy and macro-F1 when predictions differ."""
    gold = [101, 102, 103, 104]
    preds = [101, 102, 101, 104]  # 3 of 4 match
    course_ids = [1, 1, 1, 1]

    metrics = evaluate_topic_predictions(gold, preds, course_ids=course_ids)
    assert metrics["accuracy"] == 0.75
    assert 0.0 <= metrics["macro_f1"] <= 1.0
    assert 1 in metrics["per_course"]
    assert metrics["per_course"][1]["accuracy"] == 0.75


def test_kappa_script_fails_loudly_on_same_file(tmp_path):
    """Verify Cohen's kappa script rejects passing the same file twice."""
    export_file = tmp_path / "ann1.json"
    export_file.write_text(json.dumps([{"chunk_id": "c1", "topic_id": 101}]), encoding="utf-8")

    with pytest.raises(ValueError, match="identical file paths"):
        compute_cohen_kappa(export_file, export_file)


def test_kappa_script_computes_correct_score_on_two_separate_files(tmp_path):
    """Verify Cohen's kappa calculation on a small hand-verified example.

    Annotator 1 labels: [1, 2, 1, 2] -> P(1)=0.5, P(2)=0.5
    Annotator 2 labels: [1, 2, 2, 2] -> P(1)=0.25, P(2)=0.75
    Po = 3/4 = 0.75
    Pe = (0.5 * 0.25) + (0.5 * 0.75) = 0.50
    Kappa = (0.75 - 0.50) / (1 - 0.50) = 0.5000
    """
    ann1_data = [
        {"chunk_id": "c1", "topic_id": 1},
        {"chunk_id": "c2", "topic_id": 2},
        {"chunk_id": "c3", "topic_id": 1},
        {"chunk_id": "c4", "topic_id": 2},
    ]
    ann2_data = [
        {"chunk_id": "c1", "topic_id": 1},
        {"chunk_id": "c2", "topic_id": 2},
        {"chunk_id": "c3", "topic_id": 2},
        {"chunk_id": "c4", "topic_id": 2},
    ]

    file1 = tmp_path / "mariam_export.json"
    file2 = tmp_path / "omar_export.json"

    file1.write_text(json.dumps(ann1_data), encoding="utf-8")
    file2.write_text(json.dumps(ann2_data), encoding="utf-8")

    kappa = compute_cohen_kappa(file1, file2)
    assert round(kappa, 4) == 0.5000


def test_kappa_script_supports_label_studio_export_format(tmp_path):
    """Verify Cohen's kappa works with standard Label Studio nested annotation JSON."""
    ann1_ls = [
        {
            "id": "c1",
            "annotations": [{"result": [{"value": {"choices": ["101"]}}]}],
        },
        {
            "id": "c2",
            "annotations": [{"result": [{"value": {"choices": ["102"]}}]}],
        },
    ]
    ann2_ls = [
        {
            "id": "c1",
            "annotations": [{"result": [{"value": {"choices": ["101"]}}]}],
        },
        {
            "id": "c2",
            "annotations": [{"result": [{"value": {"choices": ["102"]}}]}],
        },
    ]

    file1 = tmp_path / "ls_mariam.json"
    file2 = tmp_path / "ls_omar.json"

    file1.write_text(json.dumps(ann1_ls), encoding="utf-8")
    file2.write_text(json.dumps(ann2_ls), encoding="utf-8")

    kappa = compute_cohen_kappa(file1, file2)
    assert kappa == 1.0


def test_find_disagreements_identifies_discordant_pairs(tmp_path):
    """Verify find_disagreements returns exact discordant chunk IDs and labels."""
    ann1 = [
        {"chunk_id": "c1", "topic_id": 101},
        {"chunk_id": "c2", "topic_id": 102},
        {"chunk_id": "c3", "topic_id": 103},
    ]
    ann2 = [
        {"chunk_id": "c1", "topic_id": 101},
        {"chunk_id": "c2", "topic_id": 105},  # Disagreement
        {"chunk_id": "c3", "topic_id": 103},
    ]

    f1 = tmp_path / "f1.json"
    f2 = tmp_path / "f2.json"
    f1.write_text(json.dumps(ann1), encoding="utf-8")
    f2.write_text(json.dumps(ann2), encoding="utf-8")

    disagreements = find_disagreements(f1, f2)
    assert len(disagreements) == 1
    assert disagreements[0]["chunk_id"] == "c2"
    assert disagreements[0]["annotator_1_topic_id"] == 102
    assert disagreements[0]["annotator_2_topic_id"] == 105


def test_kappa_fails_on_zero_overlapping_ids(tmp_path):
    """Verify ValueError is raised when two files have no shared chunk IDs."""
    f1 = tmp_path / "f1.json"
    f2 = tmp_path / "f2.json"
    f1.write_text(json.dumps([{"chunk_id": "c1", "topic_id": 101}]), encoding="utf-8")
    f2.write_text(json.dumps([{"chunk_id": "c2", "topic_id": 102}]), encoding="utf-8")

    with pytest.raises(ValueError, match="Zero overlapping chunk IDs"):
        compute_cohen_kappa(f1, f2)


def test_real_blind_exports_meet_kappa_target():
    """Verify real blind independent double-annotation exports meet target threshold."""
    mariam_path = Path("ml/topics/blind_labels_mariam.json")
    omar_path = Path("ml/topics/blind_labels_omar.json")
    config_path = Path("ml/topics/configs/topics_config.yaml")

    assert mariam_path.exists(), f"Mariam export not found at {mariam_path}"
    assert omar_path.exists(), f"Omar export not found at {omar_path}"

    target = load_kappa_target(config_path)
    kappa = compute_cohen_kappa(mariam_path, omar_path)
    disagreements = find_disagreements(mariam_path, omar_path)

    # Real agreement must be high (>= 0.80) but honest (not 1.0000)
    assert target == 0.80
    assert kappa >= target
    assert kappa < 1.0, "Agreement cannot be perfectly identical (1.0000) in real independent annotation"
    assert len(disagreements) > 0, "Real independent annotation must contain edge-case disagreements"
