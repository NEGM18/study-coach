"""Model C contract. Owner: Omar Mustafa (issue #23).

Week 1 stub: embedding similarity between each chunk and the syllabus topics.
It stays as the fallback for courses we haven't labeled.
"""

from ml_core.schemas import Chunk, Topic, TopicPrediction


def classify_chunks(chunks: list[Chunk], topics: list[Topic]) -> list[TopicPrediction]:
    raise NotImplementedError("Issue #23")
