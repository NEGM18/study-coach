"""App-shaped row formats shared by training and the app's worker.

Field names match the app's database columns exactly. The tables are created by
db/migrations/0001_init.sql; ml_core/tests/test_schemas.py checks every field below is a
column there. A change to quiz_attempts, lecture_chunks, course_topics or topic_mastery
updates this file and adds a new migration in the same PR.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

Lang = Literal["ar", "en", "mixed"]


@dataclass(frozen=True)
class Attempt:
    """One answer to one quiz question. Mirrors the `quiz_attempts` table."""

    user_id: str  # hashed, never a real name or email
    topic_id: int
    question_id: int
    attempt_order: int  # position in this student's history, starting at 1
    is_correct: bool
    response_time_ms: int | None = None
    attempt_count: int = 1
    hint_count: int = 0


@dataclass(frozen=True)
class Segment:
    """One transcribed piece of a lecture recording."""

    start_s: float
    end_s: float
    text: str  # normalized with text_normalize.normalize_for_training
    has_english: bool = False


@dataclass(frozen=True)
class Chunk:
    """One piece of lecture text. Mirrors the `lecture_chunks` table."""

    chunk_id: str
    course_id: int
    lecture_id: int
    text: str
    slide_no: int | None = None
    lang: Lang = "ar"
    topic_id: int | None = None


@dataclass(frozen=True)
class Topic:
    """One syllabus topic. Mirrors the `course_topics` table."""

    topic_id: int
    course_id: int
    name: str
    description: str = ""


@dataclass(frozen=True)
class TopicPrediction:
    chunk_id: str
    topic_id: int
    confidence: float  # 0..1


@dataclass(frozen=True)
class TopicMastery:
    """A student's current mastery of one topic. Mirrors the `topic_mastery` table."""

    user_id: str
    topic_id: int
    mastery: float  # 0..1, from knowledge.predict.predict_mastery
    updated_at: datetime | None = None
