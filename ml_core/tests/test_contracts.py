"""Contract tests: every predict() must return valid app-shaped output.

All three Week 1 stubs exist, so every contract test must pass.
"""

from ml_core.knowledge.predict import predict_mastery
from ml_core.schemas import Attempt, Chunk, Segment, Topic, TopicPrediction
from ml_core.speech.predict import transcribe
from ml_core.topics.predict import classify_chunks


def test_predict_mastery_returns_probability():
    history = [
        Attempt(user_id="u1", topic_id=7, question_id=1, attempt_order=1, is_correct=False),
        Attempt(user_id="u1", topic_id=7, question_id=2, attempt_order=2, is_correct=True),
    ]
    p = predict_mastery(history, topic_id=7)
    assert 0.0 <= p <= 1.0


def test_predict_mastery_handles_empty_history():
    assert 0.0 <= predict_mastery([], topic_id=7) <= 1.0


def test_transcribe_returns_ordered_segments(tmp_path):
    fixture = "tests/fixtures/speech_sample_01.flac"
    segments = transcribe(fixture)
    assert all(isinstance(s, Segment) for s in segments)
    assert all(s.start_s < s.end_s for s in segments)
    assert [s.start_s for s in segments] == sorted(s.start_s for s in segments)


def test_classify_chunks_returns_one_known_topic_per_chunk():
    topics = [Topic(1, 10, "Linked lists"), Topic(2, 10, "Binary trees")]
    chunks = [
        Chunk("c1", 10, 3, "a node points to the next node"),
        Chunk("c2", 10, 4, "left and right child"),
    ]
    preds = classify_chunks(chunks, topics)
    assert [p.chunk_id for p in preds] == ["c1", "c2"]
    assert all(isinstance(p, TopicPrediction) and p.topic_id in {1, 2} for p in preds)
    assert all(0.0 <= p.confidence <= 1.0 for p in preds)


def test_classify_chunks_accepts_custom_config_dict():
    topics = [Topic(1, 10, "Linked lists"), Topic(2, 10, "Binary trees")]
    chunks = [
        Chunk("c1", 10, 3, "a pointer points to another node"),
        Chunk("c2", 10, 4, "root node with left child and right child"),
    ]
    custom_config = {
        "stub": {"threshold": 0.01},
        "keywords": {
            "Linked lists": ["pointer", "node"],
            "Binary trees": ["root", "child"],
        },
    }
    preds = classify_chunks(chunks, topics, config=custom_config)
    assert len(preds) == 2
    assert preds[0].chunk_id == "c1"
    assert preds[0].topic_id == 1
    assert preds[1].chunk_id == "c2"
    assert preds[1].topic_id == 2


def test_classify_chunks_accepts_config_path(tmp_path):
    topics = [Topic(1, 10, "Linked lists"), Topic(2, 10, "Binary trees")]
    chunks = [
        Chunk("c1", 10, 3, "linked list node pointer"),
    ]
    cfg_file = tmp_path / "test_cfg.yaml"
    cfg_file.write_text(
        "stub:\n  threshold: 0.02\nkeywords:\n  Linked lists:\n    - pointer\n",
        encoding="utf-8",
    )
    preds = classify_chunks(chunks, topics, config=cfg_file)
    assert len(preds) == 1
    assert preds[0].topic_id == 1
