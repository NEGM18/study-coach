"""Contract tests: every predict() must return valid app-shaped output.

They are marked xfail until each stub exists; remove the marker in your PR.
"""

import pytest

from ml_core.knowledge.predict import predict_mastery
from ml_core.schemas import Attempt, Chunk, Segment, Topic, TopicPrediction
from ml_core.speech.predict import transcribe
from ml_core.topics.predict import classify_chunks

pending = pytest.mark.xfail(raises=NotImplementedError, reason="stub not built yet", strict=False)


@pending
def test_predict_mastery_returns_probability():
    history = [
        Attempt(user_id="u1", topic_id=7, question_id=1, attempt_order=1, is_correct=False),
        Attempt(user_id="u1", topic_id=7, question_id=2, attempt_order=2, is_correct=True),
    ]
    p = predict_mastery(history, topic_id=7)
    assert 0.0 <= p <= 1.0


@pending
def test_predict_mastery_handles_empty_history():
    assert 0.0 <= predict_mastery([], topic_id=7) <= 1.0


@pending
def test_transcribe_returns_ordered_segments(tmp_path):
    fixture = "tests/fixtures/speech_sample_01.flac"
    segments = transcribe(fixture)
    assert all(isinstance(s, Segment) for s in segments)
    assert all(s.start_s < s.end_s for s in segments)
    assert [s.start_s for s in segments] == sorted(s.start_s for s in segments)


@pending
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
