import re
from dataclasses import fields
from pathlib import Path

import pytest

from ml_core.schemas import Attempt, Chunk, Topic, TopicMastery

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "db" / "migrations"
TABLE_FOR: dict[type, str] = {
    Attempt: "quiz_attempts",
    Chunk: "lecture_chunks",
    Topic: "course_topics",
    TopicMastery: "topic_mastery",
}


def _table_columns() -> dict[str, set[str]]:
    """Column names per `create table public.<name>` in all migrations, in order."""
    sql = "\n".join(p.read_text(encoding="utf-8") for p in sorted(MIGRATIONS_DIR.glob("*.sql")))
    sql = re.sub(r"--[^\n]*", "", sql)
    tables: dict[str, set[str]] = {}
    for name, body in re.findall(r"create table public\.(\w+)\s*\((.*?)\n\);", sql, flags=re.S):
        columns = {line.split()[0] for line in body.splitlines() if line.strip()}
        tables[name] = columns - {"primary", "unique", "check", "foreign", "constraint"}
    return tables


def test_attempt_defaults() -> None:
    a = Attempt(user_id="h1", topic_id=1, question_id=2, attempt_order=1, is_correct=True)
    assert a.attempt_count == 1 and a.hint_count == 0


def test_topic_mastery_row() -> None:
    row = TopicMastery(user_id="u1", topic_id=101, mastery=0.75)
    assert row.updated_at is None and 0.0 <= row.mastery <= 1.0


@pytest.mark.parametrize("dataclass_type", list(TABLE_FOR))
def test_dataclass_fields_are_table_columns(dataclass_type: type) -> None:
    table = TABLE_FOR[dataclass_type]
    columns = _table_columns()[table]
    missing = {f.name for f in fields(dataclass_type)} - columns
    assert not missing, f"{table} is missing columns {sorted(missing)}"
