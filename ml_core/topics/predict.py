"""Model C topic classification stub (Issue #23 & Issue #51).

Deterministic offline classifier matching chunks against syllabus topics via
normalized TF-IDF and keyword similarity with fallback to 'other'.
Thresholds and syllabus keywords are dynamically loaded from external YAML config.
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

DEFAULT_CONFIG_PATH = Path("ml/topics/configs/topics_config.yaml")


def load_topics_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load Model C topic classification configuration from YAML.

    Parameters
    ----------
    config_path : str | Path | None
        Optional explicit path to the YAML config file. If None, checks the
        TOPICS_CONFIG_PATH environment variable, then falls back to default paths.

    Returns
    -------
    dict[str, Any]
        Loaded configuration dictionary, or an empty dictionary if not found.
    """
    if config_path is not None:
        path = Path(config_path)
    else:
        env_path = os.getenv("TOPICS_CONFIG_PATH")
        if env_path and Path(env_path).is_file():
            path = Path(env_path)
        elif DEFAULT_CONFIG_PATH.is_file():
            path = DEFAULT_CONFIG_PATH
        else:
            # Fallback relative to repository root based on file location
            repo_root_path = (
                Path(__file__).resolve().parents[2] / "ml" / "topics" / "configs" / "topics_config.yaml"
            )
            if repo_root_path.is_file():
                path = repo_root_path
            else:
                LOGGER.warning("topics_config.yaml not found at default paths.")
                return {}

    if not path.is_file():
        LOGGER.warning("topics_config.yaml not found at %s", path)
        return {}

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def _build_topic_document(topic: Topic, keywords_dict: dict[str, list[str]] | None = None) -> str:
    """Enrich topic description with keywords and normalize for TF-IDF matching."""
    extra: list[str] = []
    if keywords_dict:
        if topic.name in keywords_dict:
            extra = keywords_dict[topic.name]
        else:
            t_lower = topic.name.lower()
            for k, v in keywords_dict.items():
                if k.lower() == t_lower:
                    extra = v
                    break
    extra_keywords = " ".join(extra)
    raw_doc = f"{topic.name} {topic.description} {extra_keywords}"
    return normalize_for_training(raw_doc)


def _classify_single_chunk(
    chunk: Chunk,
    candidate_topics: list[Topic],
    vectorizer: TfidfVectorizer,
    topic_matrix: Any,
    threshold: float = 0.05,
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

    if best_score > threshold:
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
    config: dict[str, Any] | str | Path | None = None,
) -> list[TopicPrediction]:
    """Model C inference contract: classify chunks against syllabus topics.

    Parameters
    ----------
    chunks : list[Chunk]
        Lecture chunks to classify.
    topics : list[Topic]
        Available syllabus topics from course_topics.
    config : dict[str, Any] | str | Path | None
        Optional configuration dict or path to YAML config. If None, loads
        default configuration via load_topics_config().

    Returns
    -------
    list[TopicPrediction]
        List of predictions matching chunk_id, topic_id, and confidence in [0, 1].
    """
    if not chunks:
        return []
    if not topics:
        raise ValueError("Cannot classify chunks without available topics.")

    # Resolve configuration
    if isinstance(config, (str, Path)):
        resolved_config = load_topics_config(config)
    elif isinstance(config, dict):
        resolved_config = config
    else:
        resolved_config = load_topics_config()

    # Extract stub threshold and syllabus keywords
    stub_section = resolved_config.get("stub", {})
    if isinstance(stub_section, dict) and "threshold" in stub_section:
        threshold = float(stub_section["threshold"])
    elif "threshold" in resolved_config:
        threshold = float(resolved_config["threshold"])
    else:
        threshold = 0.05

    keywords_dict: dict[str, list[str]] = resolved_config.get("keywords", {})

    # Group candidate topics by course_id for fast scoped filtering
    topics_by_course: dict[int, list[Topic]] = {}
    for t in topics:
        topics_by_course.setdefault(t.course_id, []).append(t)

    # Build TF-IDF representations per course group
    vectorizers: dict[int, tuple[TfidfVectorizer, Any]] = {}
    for course_id, course_topics in topics_by_course.items():
        docs = [_build_topic_document(t, keywords_dict) for t in course_topics]
        vec = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
        mat = vec.fit_transform(docs)
        vectorizers[course_id] = (vec, mat)

    # Classify each chunk
    predictions: list[TopicPrediction] = []
    for chunk in chunks:
        candidate_topics = topics_by_course.get(chunk.course_id) or topics
        vec, mat = vectorizers.get(chunk.course_id, (None, None))
        if vec is None:
            docs = [_build_topic_document(t, keywords_dict) for t in candidate_topics]
            vec = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
            mat = vec.fit_transform(docs)

        pred = _classify_single_chunk(chunk, candidate_topics, vec, mat, threshold=threshold)
        predictions.append(pred)

    return predictions
