"""Shared Arabic text normalization for models B and C. Owner: Amr (issue #12).

Rules are listed in CLAUDE.md. Each rule gets one unit test in ml_core/tests/.
"""


def normalize_for_training(text: str) -> str:
    """Diacritics and tatweel removed, alef forms unified, digits to Western,
    English lowercased, non-speech tags removed, spaces collapsed."""
    raise NotImplementedError("Issue #12")


def normalize_for_eval(text: str) -> str:
    """normalize_for_training + (ى -> ي), (ة -> ه), punctuation removed."""
    raise NotImplementedError("Issue #12")
