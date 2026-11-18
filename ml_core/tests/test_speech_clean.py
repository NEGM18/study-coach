"""Model B: manifest cleaning with hours, error rate, speaker-safe splits."""

import pandas as pd
import pytest

from ml_core.speech.clean import (
    HoursLog,
    character_error_rate,
    clean_manifest,
    drop_high_cer,
    speaker_safe_split,
)

SETTINGS = {"min_clip_s": 1.0, "max_clip_s": 30.0, "min_chars_per_s": 2.0, "max_chars_per_s": 30.0}


def manifest() -> pd.DataFrame:
    rows = [
        ("a.flac", 0.0, 0.5, "قصير", "s1", "cv", "cv"),  # too short
        ("b.flac", 0.0, 40.0, "طويل جدا", "s1", "cv", "cv"),  # too long
        ("c.flac", 0.0, 3.0, "[music]", "s2", "cv", "cv"),  # empty after normalization
        ("d.flac", 0.0, 10.0, "كلمة", "s2", "cv", "cv"),  # 0.4 chars/s: misaligned
        ("e.flac", 0.0, 4.0, "الـAPI بيرجع ١٢ عنصر", "s3", "cv", "cv"),
    ]
    return pd.DataFrame(
        rows, columns=["audio_path", "start_s", "end_s", "text", "speaker_id", "lecture_id", "source"]
    )


def test_clean_manifest_applies_each_filter_and_logs_hours() -> None:
    log = HoursLog("speech")
    out = clean_manifest(manifest(), SETTINGS, log)
    assert out["audio_path"].tolist() == ["e.flac"]
    assert out["text"].iloc[0] == "الapi بيرجع 12 عنصر"
    table = log.to_frame()
    assert table["rows_after"].tolist() == [3, 2, 1]
    assert table["hours_before"].iloc[0] == pytest.approx(57.5 / 3600, abs=1e-3)
    assert {"hours_before", "hours_after", "rows_before", "rows_after"} <= set(table.columns)


def test_character_error_rate() -> None:
    assert character_error_rate("على الطاولة", "علي الطاوله") == 0.0  # eval normalization
    assert character_error_rate("abcd", "abxd") == pytest.approx(0.25)
    assert character_error_rate("", "") == 0.0


def test_drop_high_cer_keeps_our_lectures() -> None:
    df = pd.DataFrame(
        {
            "audio_path": ["p1", "p2", "o1"],
            "text": ["hello world", "hello world", "hello world"],
            "source": ["cv", "cv", "ours"],
            "start_s": [0.0, 0.0, 0.0],
            "end_s": [2.0, 2.0, 2.0],
        }
    )
    drafts = {"p1": "hello world", "p2": "zzzzz", "o1": "zzzzz"}
    out = drop_high_cer(df, drafts, max_cer=0.5, log=HoursLog("speech"))
    assert out["audio_path"].tolist() == ["p1", "o1"]


def test_speaker_safe_split() -> None:
    df = pd.DataFrame(
        {
            "source": ["cv", "cv", "ours", "ours", "ours", "ours"],
            "speaker_id": ["s1", "P1", "P1", "P1", "P2", "P2"],
            "lecture_id": ["x", "y", "ds_lec01", "ds_lec01", "ds_lec02", "ds_lec03"],
        }
    )
    out = speaker_safe_split(df, {"dev_fraction_of_ours": 0.5}, seed=42)
    assert out.loc[out["source"] == "cv", "split"].eq("train").all()
    assert "P1" not in set(out.loc[out["split"] == "train", "speaker_id"])  # public P1 row dropped
    assert set(out.loc[out["source"] == "ours", "split"]) <= {"dev", "test"}
    assert out.groupby("lecture_id")["split"].nunique().max() == 1
