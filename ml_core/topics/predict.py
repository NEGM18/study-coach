"""Model C topic classification stub (Issue #23, #51).

Deterministic offline classifier matching chunks against syllabus topics via
normalized TF-IDF and keyword similarity loaded from configuration.
"""

import logging
import os
from pathlib import Path
from typing import Any

import yaml
from sklearn.feature_extraction.text import TfidfVectorizer

from ml_core.schemas import Chunk, Topic, TopicPrediction
from ml_core.text_normalize import normalize_for_training

LOGGER = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = os.environ.get(
    "TOPICS_CONFIG_PATH",
    str(Path(__file__).resolve().parents[2] / "ml" / "topics" / "configs" / "topics_config.yaml"),
)


def load_topics_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load Model C topics configuration from YAML without hard-coding."""
    target_path = Path(config_path or DEFAULT_CONFIG_PATH)
    if target_path.exists():
        try:
            with target_path.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as exc:
            LOGGER.warning("Could not load topics config from %s: %s", target_path, exc)
    return {}


# Dynamically loaded from configuration for backwards compatibility
TOPIC_KEYWORDS: dict[str, list[str]] = load_topics_config().get("topic_keywords", {})


def _build_topic_document(topic: Topic, keywords_map: dict[str, list[str]] | None = None) -> str:
    """Enrich topic description with keywords from config and normalize for TF-IDF matching."""
    active_keywords = keywords_map if keywords_map is not None else TOPIC_KEYWORDS
    extra_keywords = " ".join(active_keywords.get(topic.name, []))
    raw_doc = f"{topic.name} {topic.description} {extra_keywords}"
    return normalize_for_training(raw_doc)


def _classify_single_chunk(
    chunk: Chunk,
    candidate_topics: list[Topic],
    vectorizer: TfidfVectorizer,
    topic_matrix: Any,
    similarity_cutoff: float = 0.05,
) -> TopicPrediction:
    """Classify one chunk using TF-IDF cosine similarity against candidate topic vectors."""
    other_topic = next((t for t in candidate_topics if t.name.lower() == "other"), None)
    clean_text = normalize_for_training(chunk.text)

    if not clean_text.strip():
        fallback_id = other_topic.topic_id if other_topic else candidate_topics[0].topic_id
        return TopicPrediction(chunk_id=chunk.chunk_id, topic_id=fallback_id, confidence=0.0)

    chunk_vec = vectorizer.transform([clean_text])
    similarities = (chunk_vec @ topic_matrix.T).toarray()[0]
    best_idx = int(similarities.argmax())
    best_score = float(similarities[best_idx])

    if best_score > similarity_cutoff:
        chosen_topic = candidate_topics[best_idx]
        confidence = float(min(1.0, max(0.1, best_score * 1.5)))
    elif other_topic:
        chosen_topic = other_topic
        confidence = 0.5
    else:
        chosen_topic = candidate_topics[best_idx]
        confidence = 0.1

    return TopicPrediction(
        chunk_id=chunk.chunk_id,
        topic_id=chosen_topic.topic_id,
        confidence=round(confidence, 4),
    )


def classify_chunks(
    chunks: list[Chunk],
    topics: list[Topic],
    config: dict[str, Any] | None = None,
) -> list[TopicPrediction]:
    """Model C inference contract: classify chunks against syllabus topics.

    Parameters
    ----------
    chunks : list[Chunk]
        Lecture chunks to classify.
    topics : list[Topic]
        Available syllabus topics from course_topics.
    config : dict[str, Any] | None
        Optional configuration dictionary providing topic_keywords and similarity_cutoff.

    Returns
    -------
    list[TopicPrediction]
        List of predictions matching chunk_id, topic_id, and confidence in [0, 1].
    """
    if not chunks:
        return []
    if not topics:
        raise ValueError("Cannot classify chunks without available topics.")

    cfg = config if config is not None else load_topics_config()
    keywords_map: dict[str, list[str]] = cfg.get("topic_keywords", TOPIC_KEYWORDS)
    cutoff = float(cfg.get("similarity_cutoff", cfg.get("similarity_threshold", 0.05)))

    # Group candidate topics by course_id for fast scoped filtering
    topics_by_course: dict[int, list[Topic]] = {}
    for t in topics:
        topics_by_course.setdefault(t.course_id, []).append(t)

    # Build TF-IDF representations per course group
    vectorizers: dict[int, tuple[TfidfVectorizer, Any]] = {}
    for course_id, course_topics in topics_by_course.items():
        docs = [_build_topic_document(t, keywords_map=keywords_map) for t in course_topics]
        vec = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
        mat = vec.fit_transform(docs)
        vectorizers[course_id] = (vec, mat)

    # Classify each chunk
    predictions: list[TopicPrediction] = []
    for chunk in chunks:
        candidate_topics = topics_by_course.get(chunk.course_id) or topics
        vec, mat = vectorizers.get(chunk.course_id, (None, None))
        if vec is None:
            docs = [_build_topic_document(t, keywords_map=keywords_map) for t in candidate_topics]
            vec = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
            mat = vec.fit_transform(docs)

        pred = _classify_single_chunk(chunk, candidate_topics, vec, mat, similarity_cutoff=cutoff)
        predictions.append(pred)

    return predictions
