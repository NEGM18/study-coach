"""Shared Arabic text normalization for models B and C. Owner: Amr (issue #12).

Rules are listed in CLAUDE.md. Each rule gets one unit test in ml_core/tests/.
"""

import re

# Arabic diacritics / tashkeel range: \u064B - \u0652 plus dagger alif \u0670
DIACRITICS_PATTERN = re.compile(r"[\u064B-\u0652\u0670]")
TATWEEL_CHAR = "\u0640"
ALEF_VARIANTS_PATTERN = re.compile(r"[إأآٱ]")
NON_SPEECH_TAGS_PATTERN = re.compile(r"\[[\w\s]+\]|<[\w\s]+>")
MULTI_SPACE_PATTERN = re.compile(r"\s+")

ARABIC_INDIC_DIGITS_TABLE = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
EVAL_MAP_TABLE = str.maketrans({"ى": "ي", "ة": "ه"})
PUNCTUATION_PATTERN = re.compile(r"""[!"#$%&'()*+,-./:;<=>?@\[\\\]^_`{|}~،؛؟«»…—\–]""")


def normalize_for_training(text: str) -> str:
    """Diacritics and tatweel removed, alef forms unified, digits to Western,
    English lowercased, non-speech tags removed, spaces collapsed.
    """
    if not text:
        return ""

    # Remove non-speech tags (e.g. [music], [noise])
    s = NON_SPEECH_TAGS_PATTERN.sub(" ", text)

    # Remove diacritics and tatweel
    s = DIACRITICS_PATTERN.sub("", s)
    s = s.replace(TATWEEL_CHAR, "")

    # Unify alef forms
    s = ALEF_VARIANTS_PATTERN.sub("ا", s)

    # Convert Arabic-Indic digits to Western digits
    s = s.translate(ARABIC_INDIC_DIGITS_TABLE)

    # Lowercase Latin text
    s = s.lower()

    # Collapse multiple whitespace characters
    s = MULTI_SPACE_PATTERN.sub(" ", s).strip()
    return s


def normalize_for_eval(text: str) -> str:
    """normalize_for_training + (ى -> ي), (ة -> ه), punctuation removed."""
    s = normalize_for_training(text)
    if not s:
        return ""

    # ى -> ي and ة -> ه
    s = s.translate(EVAL_MAP_TABLE)

    # Remove punctuation
    s = PUNCTUATION_PATTERN.sub(" ", s)

    # Collapse spaces again after punctuation removal
    return MULTI_SPACE_PATTERN.sub(" ", s).strip()
