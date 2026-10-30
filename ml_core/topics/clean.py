"""Cleaning for lecture text. Owner: Mariam (issue #26).

Header/footer removal, page numbers/URLs/emails, OCR garbage, normalization,
short-chunk filter, exact and near-duplicate removal, language tagging.
"""

from ml_core.schemas import Chunk


def clean_chunks(chunks: list[Chunk], settings: dict) -> list[Chunk]:
    raise NotImplementedError("Issue #26")
