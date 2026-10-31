"""Cleaning counts, logging, and portable CSV output for every dataset."""

import csv
import logging
from pathlib import Path

import pandas as pd
import pytest

from ml_core.cleaning_log import CleaningLog

CSV_FIELDS = ["dataset", "step", "rows_before", "rows_after", "reason"]


def test_step_records_counts_and_returns_after_without_mutating_inputs() -> None:
    log = CleaningLog("knowledge")
    before = [1, 2, 3]
    after = [1, 3]

    result = log.step("drop missing topic_id", before, after, "topic_id is required")

    assert result is after
    assert before == [1, 2, 3]
    assert after == [1, 3]
    assert log.rows == [
        {
            "dataset": "knowledge",
            "step": "drop missing topic_id",
            "rows_before": 3,
            "rows_after": 2,
            "reason": "topic_id is required",
        }
    ]


@pytest.mark.parametrize("before_count,after_count", [(0, 0), (3, 0), (2, 2), (1, 3)])
def test_step_supports_empty_unchanged_and_increased_counts(before_count: int, after_count: int) -> None:
    log = CleaningLog("topics")
    after = tuple(range(after_count))

    assert log.step("clean", list(range(before_count)), after) is after
    assert log.rows[0]["rows_before"] == before_count
    assert log.rows[0]["rows_after"] == after_count
    assert log.rows[0]["reason"] == ""


def test_step_counts_dataframe_rows_including_missing_values() -> None:
    log = CleaningLog("knowledge")
    before = pd.DataFrame({"topic_id": [1, None, 2], "is_correct": [True, False, True]})
    after = before.loc[before["topic_id"].notna()]
    original_before = before.copy(deep=True)
    original_after = after.copy(deep=True)

    assert log.step("drop missing topic_id", before, after, "missing topic") is after
    assert log.rows[0]["rows_before"] == 3
    assert log.rows[0]["rows_after"] == 2
    pd.testing.assert_frame_equal(before, original_before)
    pd.testing.assert_frame_equal(after, original_after)


def test_steps_preserve_order_and_snapshot_counts() -> None:
    log = CleaningLog("speech")
    before = [1, 2, 3]
    after = [1, 2]
    log.step("remove silence", before, after, "silent segment")
    log.step("normalize", after, after, "normalize text")
    before.clear()
    after.append(3)

    assert [row["step"] for row in log.rows] == ["remove silence", "normalize"]
    assert [row["rows_before"] for row in log.rows] == [3, 2]
    assert [row["rows_after"] for row in log.rows] == [2, 2]
    assert [row["reason"] for row in log.rows] == ["silent segment", "normalize text"]


def test_log_instances_keep_independent_datasets_and_rows() -> None:
    knowledge_log = CleaningLog("knowledge")
    topics_log = CleaningLog("topics")

    assert knowledge_log.dataset == "knowledge"
    assert topics_log.dataset == "topics"
    assert knowledge_log.rows == topics_log.rows == []
    knowledge_log.step("filter", [1], [], "invalid row")

    assert topics_log.rows == []
    assert knowledge_log.rows is not topics_log.rows
    topics_log.step("normalize", [1], [1], "text normalization")
    assert knowledge_log.rows[0]["dataset"] == "knowledge"
    assert topics_log.rows[0]["dataset"] == "topics"


def test_step_emits_info_with_dataset_step_counts_and_reason(caplog: pytest.LogCaptureFixture) -> None:
    log = CleaningLog("knowledge")

    with caplog.at_level(logging.INFO, logger="ml_core.cleaning_log"):
        log.step("drop missing topic_id", range(31), range(29), "topic_id is required")

    records = [record for record in caplog.records if record.name == "ml_core.cleaning_log"]
    assert len(records) == 1
    assert records[0].levelno == logging.INFO
    message = records[0].getMessage()
    assert all(value in message for value in ["knowledge", "drop missing topic_id", "31", "29"])
    assert "topic_id is required" in message


def test_save_round_trips_unicode_and_csv_special_characters_in_step_order(tmp_path: Path) -> None:
    log = CleaningLog("معرفة, knowledge")
    log.step('remove "empty", rows', [1, 2], [1], 'سبب, "quoted"\nsecond line')
    log.step("normalize", [1], [1], "توحيد النص")
    path = tmp_path / "cleaning_log.csv"

    assert log.save(str(path)) is None

    with path.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)
        assert reader.fieldnames == CSV_FIELDS
    assert rows == [{key: str(value) for key, value in row.items()} for row in log.rows]


def test_save_creates_missing_parent_directories(tmp_path: Path) -> None:
    log = CleaningLog("topics")
    log.step("clean", [1, 2], [1], "invalid topic")
    path = tmp_path / "nested" / "reports" / "cleaning_log.csv"

    log.save(str(path))

    with path.open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))
    assert len(rows) == 1
    assert rows[0]["dataset"] == "topics"


def test_save_empty_log_writes_header_only(tmp_path: Path) -> None:
    log = CleaningLog("speech")
    path = tmp_path / "empty.csv"

    log.save(str(path))

    with path.open(encoding="utf-8", newline="") as csv_file:
        assert list(csv.reader(csv_file)) == [CSV_FIELDS]
    assert log.rows == []


def test_save_replaces_previous_snapshot_without_duplicate_headers_or_rows(tmp_path: Path) -> None:
    log = CleaningLog("knowledge")
    log.step("first", [1, 2, 3], [1, 2], "invalid row")
    path = tmp_path / "cleaning_log.csv"
    log.save(str(path))
    original_text = path.read_text(encoding="utf-8")

    log.save(str(path))
    assert path.read_text(encoding="utf-8") == original_text
    log.step("second", [1, 2], [1], "duplicate row")
    log.save(str(path))

    with path.open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))
    assert [row["step"] for row in rows] == ["first", "second"]
    assert rows == [{key: str(value) for key, value in row.items()} for row in log.rows]
