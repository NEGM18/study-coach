"""Cleaning pipeline for lecture text chunks (Issues #26 & #27, #53).

Executes an 8-step cleaning sequence recording before/after metrics via CleaningLog.
"""

import json
import logging
import re
from collections import Counter
from dataclasses import replace
from pathlib import Path
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


ACADEMIC_TITLE_PATTERN = re.compile(
    r"(?<!\w)(?P<title>(?:أ\.\s*د\.|ا\.\s*د\.|أستاذ\s+دكتور|د\.|م\.|مهندس)|(?:dr\.|prof\.|eng\.|dr\b|prof\b|eng\b))[^\S\n]*",
    re.IGNORECASE,
)
NAME_WORD_PATTERN = re.compile(r"^[a-zA-Z\u0621-\u064A]+(?:-[a-zA-Z\u0621-\u064A]+)?$")
NON_NAME_STOPWORDS = {
    "is",
    "was",
    "are",
    "were",
    "the",
    "a",
    "an",
    "that",
    "this",
    "it",
    "in",
    "on",
    "at",
    "to",
    "for",
    "from",
    "by",
    "with",
    "without",
    "and",
    "or",
    "but",
    "not",
    "so",
    "as",
    "if",
    "of",
    "who",
    "whom",
    "which",
    "what",
    "when",
    "where",
    "why",
    "how",
    "has",
    "have",
    "had",
    "do",
    "does",
    "did",
    "can",
    "could",
    "should",
    "would",
    "may",
    "might",
    "must",
    "will",
    "shall",
    "grading",
    "contact",
    "email",
    "office",
    "hours",
    "exam",
    "midterm",
    "final",
    "labs",
    "project",
    "lecture",
    "course",
    "syllabus",
    "memory",
    "system",
    "scheme",
    "immediately",
    "said",
    "means",
    "stands",
    "refers",
    "indicates",
    "abbreviation",
    "word",
    "title",
    "name",
    "itself",
    "called",
    "about",
    "before",
    "after",
    "today",
    "tomorrow",
    "yesterday",
    "now",
    "later",
    "here",
    "there",
    "في",
    "من",
    "إلى",
    "على",
    "عن",
    "مع",
    "هذا",
    "هذه",
    "ذلك",
    "تلك",
    "هو",
    "هي",
    "أن",
    "إن",
    "كان",
    "كانت",
    "ليس",
    "ليست",
    "ما",
    "لا",
    "لم",
    "لن",
    "أو",
    "ثم",
    "بل",
    "لكن",
    "حيث",
    "كل",
    "جميع",
    "معيد",
    "معيدة",
    "أستاذ",
    "دكتور",
    "محاضر",
    "المادة",
}
PRE_DETERMINERS = {"the", "a", "an", "your", "my", "our", "their", "his", "her", "this", "that"}


def anonymize_text(text: str, name_map: dict[str, str]) -> str:
    """Detect professor/instructor names following English/Arabic titles and replace with P1, P2..."""
    result: list[str] = []
    last_end = 0

    for match in ACADEMIC_TITLE_PATTERN.finditer(text):
        if match.start() < last_end:
            continue

        prefix = text[: match.start()].rstrip()
        prev_word = prefix.split()[-1].lower() if prefix.split() else ""
        if prev_word in PRE_DETERMINERS:
            result.append(text[last_end : match.end()])
            last_end = match.end()
            continue

        start = match.end()
        remainder = text[start:]
        words: list[str] = []
        pos = 0

        while pos < len(remainder) and len(words) < 3:
            m = re.match(r"^[^\S\n]*([^\s\n,;:|/\-—\(\)\[\]\<\>]+)", remainder[pos:])
            if not m:
                break
            token = m.group(1).rstrip(".,;:!?")
            if not token or not NAME_WORD_PATTERN.match(token):
                break
            norm_token = normalize_for_training(token).lower()
            if norm_token in NON_NAME_STOPWORDS:
                break
            words.append(token)
            pos += m.end()

        if not words:
            result.append(text[last_end : match.end()])
            last_end = match.end()
        else:
            name_str = " ".join(words)
            norm_key = normalize_for_training(name_str).lower()
            if norm_key not in name_map:
                name_map[norm_key] = f"P{len(name_map) + 1}"
            p_id = name_map[norm_key]
            result.append(text[last_end : match.start()])
            result.append(p_id)
            last_end = start + pos

    result.append(text[last_end:])
    return "".join(result)


def anonymize_names(
    chunks: list[Chunk],
    mapping_path: str | Path | None = None,
    name_map: dict[str, str] | None = None,
) -> list[Chunk]:
    """Step 5: Detect professor names following English/Arabic titles and replace with P1, P2..."""
    active_map: dict[str, str] = {}
    path_obj: Path | None = None

    if mapping_path:
        path_obj = Path(mapping_path)
        if path_obj.exists():
            try:
                with path_obj.open("r", encoding="utf-8") as f:
                    active_map = json.load(f)
            except Exception as exc:
                LOGGER.warning("Failed to load professor mapping from %s: %s", path_obj, exc)

    if name_map is not None:
        active_map.update(name_map)

    cleaned: list[Chunk] = []
    for c in chunks:
        new_text = anonymize_text(c.text, active_map)
        cleaned.append(replace(c, text=new_text))

    if path_obj is not None:
        try:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with path_obj.open("w", encoding="utf-8") as f:
                json.dump(active_map, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            LOGGER.warning("Failed to write professor mapping to %s: %s", path_obj, exc)

    if name_map is not None:
        name_map.update(active_map)

    return cleaned


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
    """Step 8: Tag language on every remaining chunk."""
    return [replace(c, lang=_detect_language(c.text)) for c in chunks]


def clean_chunks(chunks: list[Chunk], settings: dict[str, Any] | None = None) -> list[Chunk]:
    """Clean lecture text chunks executing the 8-step pipeline with audit logging."""
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

    # Step 5: Anonymize professor names
    mapping_path = cfg.get("professor_mapping_path", "ml/topics/.professor_mapping.json")
    name_map = cfg.get("professor_name_map")
    s5 = anonymize_names(s4, mapping_path=mapping_path, name_map=name_map)
    log.step("anonymize_names", s4, s5, "anonymize instructor names with P1, P2...")

    # Step 6: Filter short chunks
    s6 = _filter_short_chunks(s5, min_words)
    log.step("filter_short_chunks", s5, s6, f"drop chunks with <{min_words} words")

    # Step 7: Deduplicate exact and near-duplicates
    s7 = _deduplicate_chunks(s6, sim_threshold)
    log.step("deduplicate_chunks", s6, s7, f"drop duplicates with >={sim_threshold:.0%} similarity")

    # Step 8: Language tagging
    s8 = _tag_language(s7)
    log.step("tag_language", s7, s8, "tag language as ar, en, or mixed")

    return s8
