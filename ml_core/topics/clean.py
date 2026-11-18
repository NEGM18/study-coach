"""Cleaning pipeline for lecture text chunks (Issues #26 & #27).

Executes a 7-step cleaning sequence recording before/after metrics via CleaningLog.
"""

import logging
import re
from collections import Counter
from dataclasses import replace
from typing import Any

from datasketch import MinHash

from ml_core.cleaning_log import CleaningLog
from ml_core.schemas import Chunk, Lang
from ml_core.text_normalize import normalize_for_training

LOGGER = logging.getLogger(__name__)

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PAGE_NUM_PATTERN = re.compile(r"^(?:page\s*)?\d+(?:\s*(?:of|/)\s*\d+)?$|^-\s*\d+\s*-$|^\d+$", re.IGNORECASE)
COPYRIGHT_PATTERN = re.compile(r"©|copyright|all rights reserved|confidential", re.IGNORECASE)
DANGLING_CONNECTIVE_PATTERN = re.compile(
    r"^(?:slides\s+available\s+at|visit|website|contact|email|available\s+at|link)[\s:]*$",
    re.IGNORECASE,
)
ARABIC_LETTER_PATTERN = re.compile(r"[\u0621-\u064A]")
LATIN_LETTER_PATTERN = re.compile(r"[a-zA-Z]")


def _remove_repeating_headers(chunks: list[Chunk], max_repeat_ratio: float) -> list[Chunk]:
    """Step 1: Remove lines that repeat on more than max_repeat_ratio of lecture slides."""
    by_lecture: dict[int, list[Chunk]] = {}
    for c in chunks:
        by_lecture.setdefault(c.lecture_id, []).append(c)

    cleaned_chunks: list[Chunk] = []
    for lecture_chunks in by_lecture.values():
        total_slides = len(lecture_chunks)
        line_slide_counts: Counter[str] = Counter()

        for c in lecture_chunks:
            slide_unique_lines = {line.strip() for line in c.text.split("\n") if line.strip()}
            for line in slide_unique_lines:
                line_slide_counts[line] += 1

        frequent_lines = {
            line
            for line, count in line_slide_counts.items()
            if total_slides > 1 and (count / total_slides) > max_repeat_ratio
        }

        for c in lecture_chunks:
            lines = [line.strip() for line in c.text.split("\n")]
            filtered = [line for line in lines if line and line not in frequent_lines]
            new_text = "\n".join(filtered).strip()
            cleaned_chunks.append(replace(c, text=new_text))

    return cleaned_chunks


def _clean_metadata_line(line: str) -> str:
    """Removes URLs, emails, and determines if line is metadata."""
    trimmed = line.strip()
    if not trimmed:
        return ""
    if COPYRIGHT_PATTERN.search(trimmed) or PAGE_NUM_PATTERN.match(trimmed):
        return ""

    without_urls = URL_PATTERN.sub("", trimmed)
    without_emails = EMAIL_PATTERN.sub("", without_urls)
    clean_line = re.sub(r"\s+", " ", without_emails).strip()
    if PAGE_NUM_PATTERN.match(clean_line) or DANGLING_CONNECTIVE_PATTERN.match(clean_line):
        return ""
    return clean_line


def _remove_metadata(chunks: list[Chunk]) -> list[Chunk]:
    """Step 2: Drop standalone page numbers, URLs, emails, and copyright notices."""
    cleaned: list[Chunk] = []
    for c in chunks:
        lines = [_clean_metadata_line(line) for line in c.text.split("\n")]
        valid_lines = [line for line in lines if line]
        cleaned.append(replace(c, text="\n".join(valid_lines).strip()))
    return cleaned


def _is_valid_letter_line(line: str, min_letter_ratio: float) -> bool:
    """Check if non-whitespace characters contain sufficient valid letters."""
    non_ws = [ch for ch in line if not ch.isspace()]
    if not non_ws:
        return False
    arabic_count = len(ARABIC_LETTER_PATTERN.findall(line))
    latin_count = len(LATIN_LETTER_PATTERN.findall(line))
    letter_count = arabic_count + latin_count
    return (letter_count / len(non_ws)) >= min_letter_ratio


def _remove_ocr_garbage(chunks: list[Chunk], min_letter_ratio: float) -> list[Chunk]:
    """Step 3: Drop OCR garbage lines with < min_letter_ratio valid letters."""
    cleaned: list[Chunk] = []
    for c in chunks:
        lines = [line.strip() for line in c.text.split("\n") if line.strip()]
        valid_lines = [line for line in lines if _is_valid_letter_line(line, min_letter_ratio)]
        cleaned.append(replace(c, text="\n".join(valid_lines).strip()))
    return cleaned


def _normalize_chunks(chunks: list[Chunk]) -> list[Chunk]:
    """Step 4: Normalize Arabic and Latin text using shared normalize_for_training."""
    return [replace(c, text=normalize_for_training(c.text)) for c in chunks]


def _filter_short_chunks(chunks: list[Chunk], min_words: int) -> list[Chunk]:
    """Step 5: Drop chunks with fewer than min_words."""
    return [c for c in chunks if len(c.text.split()) >= min_words]


def _build_minhash(text: str, num_perm: int = 64) -> MinHash:
    """Builds a MinHash representation for near-duplicate comparison."""
    m = MinHash(num_perm=num_perm)
    words = text.split()
    for w in words:
        m.update(w.encode("utf-8"))
    return m


def _deduplicate_chunks(chunks: list[Chunk], similarity_threshold: float) -> list[Chunk]:
    """Step 6: Drop exact duplicates and near-duplicates above similarity threshold."""
    unique_chunks: list[Chunk] = []
    seen_exact_texts: set[str] = set()
    seen_hashes: list[MinHash] = []

    for c in chunks:
        if c.text in seen_exact_texts:
            continue

        mh = _build_minhash(c.text)
        is_near_dup = any(mh.jaccard(prev_mh) >= similarity_threshold for prev_mh in seen_hashes)
        if is_near_dup:
            continue

        seen_exact_texts.add(c.text)
        seen_hashes.append(mh)
        unique_chunks.append(c)

    return unique_chunks


def _detect_language(text: str) -> Lang:
    """Step 7 helper: Classifies text language as 'ar', 'en', or 'mixed'."""
    arabic_count = len(ARABIC_LETTER_PATTERN.findall(text))
    latin_count = len(LATIN_LETTER_PATTERN.findall(text))
    total_letters = arabic_count + latin_count

    if total_letters == 0 or arabic_count / total_letters >= 0.85:
        return "ar"
    if latin_count / total_letters >= 0.85:
        return "en"
    return "mixed"


def _tag_language(chunks: list[Chunk]) -> list[Chunk]:
    """Step 7: Tag language on every remaining chunk."""
    return [replace(c, lang=_detect_language(c.text)) for c in chunks]


def clean_chunks(chunks: list[Chunk], settings: dict[str, Any] | None = None) -> list[Chunk]:
    """Clean lecture text chunks executing the 7-step pipeline with audit logging."""
    cfg = settings or {}
    header_ratio = float(cfg.get("header_repeat_ratio", 0.5))
    min_letter_ratio = float(cfg.get("min_letter_ratio", 0.5))
    min_words = int(cfg.get("min_words", 5))
    sim_threshold = float(cfg.get("similarity_threshold", 0.90))

    log = cfg.get("cleaning_log")
    if log is None:
        log = CleaningLog("topics")
        cfg["cleaning_log"] = log

    # Step 1: Remove repeating headers/footers
    s1 = _remove_repeating_headers(chunks, header_ratio)
    log.step("remove_repeating_headers", chunks, s1, f"drop lines repeating >{header_ratio:.0%}")

    # Step 2: Remove metadata (page numbers, URLs, emails, copyright)
    s2 = _remove_metadata(s1)
    log.step("remove_metadata", s1, s2, "drop page numbers, URLs, emails, and copyright")

    # Step 3: Remove OCR garbage lines
    s3 = _remove_ocr_garbage(s2, min_letter_ratio)
    log.step("remove_ocr_garbage", s2, s3, f"drop lines with <{min_letter_ratio:.0%} valid letters")

    # Step 4: Normalize text
    s4 = _normalize_chunks(s3)
    log.step("normalize_for_training", s3, s4, "apply shared Arabic/Latin normalization")

    # Step 5: Filter short chunks
    s5 = _filter_short_chunks(s4, min_words)
    log.step("filter_short_chunks", s4, s5, f"drop chunks with <{min_words} words")

    # Step 6: Deduplicate exact and near-duplicates
    s6 = _deduplicate_chunks(s5, sim_threshold)
    log.step("deduplicate_chunks", s5, s6, f"drop duplicates with >={sim_threshold:.0%} similarity")

    # Step 7: Language tagging
    s7 = _tag_language(s6)
    log.step("tag_language", s6, s7, "tag language as ar, en, or mixed")

    return s7
