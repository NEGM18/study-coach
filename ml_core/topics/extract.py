"""Text extraction shared by training and the app. Owner: Mariam (issue #25).

PyMuPDF for PDFs, python-pptx for PPTX, Tesseract OCR (ara+eng) for scanned
pages. Takes ONE file and returns one entry per slide/page.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Page:
    slide_no: int
    text: str
    is_ocr: bool
    is_low_text: bool


def extract_file(path: str) -> list[Page]:
    raise NotImplementedError("Issue #25")
