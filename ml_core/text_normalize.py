"""Normalize Arabic and Latin text for speech and topic models."""

import re
import unicodedata

TRAINING_TRANSLATION = str.maketrans(
    "أإآٱ٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
    "اااا01234567890123456789",
    "ـ",
)
EVAL_TRANSLATION = str.maketrans("ىة", "يه")
NON_SPEECH_WORDS = (
    r"\s*(?:music|(?:background\s+)?noise|silence|laughter|applause|"
    r"cough(?:ing)?|breath(?:ing)?|inaudible|unintelligible)\s*"
)
NON_SPEECH_TAG = re.compile(rf"\[{NON_SPEECH_WORDS}\]|<{NON_SPEECH_WORDS}>", flags=re.IGNORECASE)


def normalize_for_training(text: str) -> str:
    """Normalize script variants in transcripts while preserving wording and punctuation."""
    # Compose alef with combining hamza or madda before applying the alef mapping.
    text = unicodedata.normalize("NFC", text).translate(TRAINING_TRANSLATION)
    characters: list[str] = []
    for character in text:
        name = unicodedata.name(character, "")
        if name.startswith("ARABIC ") and unicodedata.category(character).startswith("M"):
            continue
        characters.append(character.lower() if name.startswith("LATIN ") else character)
    return " ".join(NON_SPEECH_TAG.sub(" ", "".join(characters)).split())


def normalize_for_eval(text: str) -> str:
    """Apply training normalization and ignore letter variants and punctuation in scoring."""
    text = normalize_for_training(text).translate(EVAL_TRANSLATION)
    without_punctuation = "".join(
        " " if unicodedata.category(character).startswith("P") else character for character in text
    )
    return " ".join(without_punctuation.split())
