"""Unit tests for lecture text cleaning pipeline (Issues #26 & #27)."""

import pytest

pytest.importorskip("ml_core.topics.clean", reason="needs the topics extra: uv sync --extra topics")

from ml_core.cleaning_log import CleaningLog
from ml_core.schemas import Chunk
from ml_core.topics.clean import (
    _deduplicate_chunks,
    _detect_language,
    _filter_short_chunks,
    _normalize_chunks,
    _remove_metadata,
    _remove_ocr_garbage,
    _remove_repeating_headers,
    _tag_language,
    anonymize_names,
    clean_chunks,
)


def test_step1_remove_repeating_headers() -> None:
    # 3 slides in lecture 1; header appears on all 3 (>50%)
    c1 = Chunk("c1", 1, 10, "CS201 Data Structures\nArrays provide O(1) random memory access.")
    c2 = Chunk("c2", 1, 10, "CS201 Data Structures\nDynamic arrays resize by doubling capacity.")
    c3 = Chunk("c3", 1, 10, "CS201 Data Structures\nLinked lists use node pointers.")

    cleaned = _remove_repeating_headers([c1, c2, c3], max_repeat_ratio=0.5)

    assert len(cleaned) == 3
    assert all("CS201 Data Structures" not in c.text for c in cleaned)
    assert "Arrays provide O(1)" in cleaned[0].text
    assert "Dynamic arrays resize" in cleaned[1].text
    assert "Linked lists use" in cleaned[2].text


def test_step2_remove_metadata_lines() -> None:
    text = (
        "Operating System Dual Mode Operation\n"
        "Page 3 of 20\n"
        "Visit course materials at https://univ.edu.eg/courses\n"
        "Instructor email: tarek@univ.edu.eg\n"
        "Copyright © 2026 University. All Rights Reserved."
    )
    chunk = Chunk("c1", 2, 20, text)
    cleaned = _remove_metadata([chunk])

    assert len(cleaned) == 1
    cleaned_text = cleaned[0].text
    assert "Dual Mode Operation" in cleaned_text
    assert "https://" not in cleaned_text
    assert "tarek@univ.edu.eg" not in cleaned_text
    assert "Page 3" not in cleaned_text
    assert "Copyright" not in cleaned_text


def test_step3_remove_ocr_garbage() -> None:
    text = "Valid technical slide content here\n??? §§§ !!! 1234 %%% @@@ ### ~~~"
    chunk = Chunk("c1", 1, 10, text)
    cleaned = _remove_ocr_garbage([chunk], min_letter_ratio=0.5)

    assert len(cleaned) == 1
    assert "Valid technical slide content here" in cleaned[0].text
    assert "???" not in cleaned[0].text


def test_step4_normalize_training() -> None:
    text = "شَرْحُ خوارزميات الترتيب وَالبحث في قاعة رقم ١٠"
    chunk = Chunk("c1", 1, 10, text)
    cleaned = _normalize_chunks([chunk])

    assert len(cleaned) == 1
    # Diacritics removed, digits converted to 10
    assert cleaned[0].text == "شرح خوارزميات الترتيب والبحث في قاعة رقم 10"


def test_step5_filter_short_chunks() -> None:
    c_long = Chunk("c1", 1, 10, "One two three four five six words.")
    c_short = Chunk("c2", 1, 10, "Only three words.")

    kept = _filter_short_chunks([c_long, c_short], min_words=5)

    assert len(kept) == 1
    assert kept[0].chunk_id == "c1"


def test_step6_deduplicate_chunks() -> None:
    c1 = Chunk("c1", 1, 10, "Binary search requires sorted array elements to divide range.")
    c2 = Chunk("c2", 1, 10, "Binary search requires sorted array elements to divide range.")  # exact dup
    c3 = Chunk(
        "c3", 1, 10, "Binary search requires sorted array elements to divide range efficiently."
    )  # near dup
    c4 = Chunk("c4", 1, 10, "Completely different topic on graphs and minimum spanning trees.")

    deduped = _deduplicate_chunks([c1, c2, c3, c4], similarity_threshold=0.85)

    chunk_ids = [c.chunk_id for c in deduped]
    assert "c1" in chunk_ids
    assert "c2" not in chunk_ids
    assert "c4" in chunk_ids


def test_step7_detect_and_tag_language() -> None:
    assert _detect_language("This is purely English text for lectures.") == "en"
    assert _detect_language("هذا نص باللغة العربية بالكامل لشرح هياكل البيانات.") == "ar"
    assert _detect_language("هذا الشرح يحتوي على Binary Search Trees و Big-O.") == "mixed"

    c_en = Chunk("c1", 1, 10, "This is English lecture material.")
    c_ar = Chunk("c2", 1, 10, "هذا شرح باللغة العربية.")
    c_mix = Chunk("c3", 1, 10, "شرح Dynamic Arrays وطريقة Resizing في الميموري.")

    tagged = _tag_language([c_en, c_ar, c_mix])
    assert [c.lang for c in tagged] == ["en", "ar", "mixed"]


def test_step5_anonymize_names_english_titles() -> None:
    chunks = [
        Chunk("c1", 1, 10, "Welcome to Data Structures by Dr. Ahmed Hassan."),
        Chunk("c2", 1, 10, "Advanced course instructed by Prof. Sherif Nabil."),
        Chunk("c3", 1, 10, "Lab session mentored by Eng. Tarek today."),
    ]
    name_map: dict[str, str] = {}
    cleaned = anonymize_names(chunks, mapping_path=None, name_map=name_map)
    assert "Dr. Ahmed Hassan" not in cleaned[0].text
    assert "P1" in cleaned[0].text
    assert "Prof. Sherif Nabil" not in cleaned[1].text
    assert "P2" in cleaned[1].text
    assert "Eng. Tarek" not in cleaned[2].text
    assert "P3" in cleaned[2].text


def test_step5_anonymize_names_arabic_titles() -> None:
    chunks = [
        Chunk("c1", 1, 10, "محاضرة هياكل البيانات يقدمها د. أحمد حسن في القاعة."),
        Chunk("c2", 1, 10, "مقرر الذكاء الاصطناعي بإشراف أ.د. شريف نبيل."),
        Chunk("c3", 1, 10, "تمارين المعمل مع م. سارة محمود."),
    ]
    name_map: dict[str, str] = {}
    cleaned = anonymize_names(chunks, mapping_path=None, name_map=name_map)
    assert "د. أحمد حسن" not in cleaned[0].text
    assert "P1" in cleaned[0].text
    assert "أ.د. شريف نبيل" not in cleaned[1].text
    assert "P2" in cleaned[1].text
    assert "م. سارة محمود" not in cleaned[2].text
    assert "P3" in cleaned[2].text


def test_step5_anonymize_names_end_of_line() -> None:
    chunks = [
        Chunk("c1", 1, 10, "Course Instructor: Dr. Ahmed Hassan\nNext line of content."),
        Chunk("c2", 1, 10, "Primary Lecturer: Prof. Jane Doe"),
        Chunk("c3", 1, 10, "مدرس المادة: د. أحمد حسن"),
    ]
    name_map: dict[str, str] = {}
    cleaned = anonymize_names(chunks, mapping_path=None, name_map=name_map)
    assert cleaned[0].text == "Course Instructor: P1\nNext line of content."
    assert cleaned[1].text == "Primary Lecturer: P2"
    assert cleaned[2].text == "مدرس المادة: P3"


def test_step5_anonymize_names_non_name_occurrences() -> None:
    non_names = [
        Chunk("c1", 1, 10, "The doctor said dr. is an abbreviation."),
        Chunk("c2", 1, 10, "Please call the dr. immediately for assistance."),
        Chunk("c3", 1, 10, "He earned the title of Dr.\nNew topic starts here."),
        Chunk("c4", 1, 10, "Patient record dr. 123 in table."),
        Chunk("c5", 1, 10, "Check with your dr. before procedure."),
    ]
    name_map: dict[str, str] = {}
    cleaned = anonymize_names(non_names, mapping_path=None, name_map=name_map)
    assert cleaned[0].text == "The doctor said dr. is an abbreviation."
    assert cleaned[1].text == "Please call the dr. immediately for assistance."
    assert cleaned[2].text == "He earned the title of Dr.\nNew topic starts here."
    assert cleaned[3].text == "Patient record dr. 123 in table."
    assert cleaned[4].text == "Check with your dr. before procedure."
    assert len(name_map) == 0


def test_step5_anonymize_names_consistent_mapping(tmp_path) -> None:
    mapping_file = tmp_path / "test_prof_map.json"
    c1 = [Chunk("c1", 1, 10, "Lecture by Dr. Ahmed Hassan.")]
    cleaned1 = anonymize_names(c1, mapping_path=mapping_file)
    assert "P1" in cleaned1[0].text

    c2 = [Chunk("c2", 1, 10, "Notes from dr. ahmed hassan today.")]
    cleaned2 = anonymize_names(c2, mapping_path=mapping_file)
    assert "P1" in cleaned2[0].text


def test_full_pipeline_records_all_8_cleaning_steps() -> None:
    log = CleaningLog("topics")
    settings = {
        "header_repeat_ratio": 0.5,
        "min_letter_ratio": 0.5,
        "min_words": 5,
        "similarity_threshold": 0.90,
        "cleaning_log": log,
        "professor_mapping_path": None,
        "professor_name_map": {},
    }

    chunks = [
        Chunk(
            "c1",
            1,
            10,
            "Header Line\nArrays provide constant time random access indexing in memory.",
        ),
        Chunk(
            "c2",
            1,
            10,
            "Header Line\nDynamic arrays resize dynamically when capacity is exceeded.",
        ),
        Chunk("c3", 1, 10, "Header Line\nShort."),
    ]

    result = clean_chunks(chunks, settings)

    assert len(result) >= 1
    step_names = [row["step"] for row in log.rows]
    assert step_names == [
        "remove_repeating_headers",
        "remove_metadata",
        "remove_ocr_garbage",
        "normalize_for_training",
        "anonymize_names",
        "filter_short_chunks",
        "deduplicate_chunks",
        "tag_language",
    ]
    assert all(row["dataset"] == "topics" for row in log.rows)
    assert all("rows_before" in row and "rows_after" in row for row in log.rows)


def test_no_professor_names_in_committed_topics_files() -> None:
    """CI check: ensure zero real professor names or 'dr. first last' patterns in ml/topics/."""
    import re
    import subprocess
    from pathlib import Path

    res = subprocess.run(
        ["git", "ls-files", "ml/topics"],
        capture_output=True,
        text=True,
        check=True,
    )
    tracked_files = [Path(p.strip()) for p in res.stdout.splitlines() if p.strip()]
    assert tracked_files, "Expected tracked files under ml/topics"

    forbidden_names = [
        "ahmed hassan",
        "sherif nabil",
        "أحمد حسن",
        "شريف نبيل",
    ]
    title_pattern = re.compile(
        r"(?:dr\.|prof\.|eng\.|د\.|أ\.د\.|م\.)\s+([a-zA-Z\u0621-\u064A]+(?:\s+[a-zA-Z\u0621-\u064A]+)+)",
        re.IGNORECASE,
    )

    for file_path in tracked_files:
        if not file_path.exists() or file_path.suffix not in {".json", ".md", ".yaml", ".yml", ".csv", ".py"}:
            continue
        content = file_path.read_text(encoding="utf-8")
        content_lower = content.lower()

        for name in forbidden_names:
            assert name not in content_lower, f"Real professor name '{name}' found in {file_path}"

        for match in title_pattern.finditer(content):
            matched_name = match.group(1).strip()
            if re.match(r"^P\d+$", matched_name, re.IGNORECASE):
                continue
            raise AssertionError(f"Forbidden pattern '{match.group(0)}' found in {file_path}")
