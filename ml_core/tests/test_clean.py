"""Unit tests for lecture text cleaning pipeline (Issues #26 & #27)."""

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


def test_full_pipeline_records_all_7_cleaning_steps() -> None:
    log = CleaningLog("topics")
    settings = {
        "header_repeat_ratio": 0.5,
        "min_letter_ratio": 0.5,
        "min_words": 5,
        "similarity_threshold": 0.90,
        "cleaning_log": log,
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
        "filter_short_chunks",
        "deduplicate_chunks",
        "tag_language",
    ]
    assert all(row["dataset"] == "topics" for row in log.rows)
    assert all("rows_before" in row and "rows_after" in row for row in log.rows)
