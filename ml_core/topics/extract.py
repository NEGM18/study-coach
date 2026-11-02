"""Text extraction shared by training and the app. Owner: Mariam (issue #25).

PyMuPDF for PDFs, python-pptx for PPTX, Tesseract OCR (ara+eng) for scanned
pages. Takes ONE file and returns one entry per slide/page.
"""

import io
import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pptx
import pymupdf
import pytesseract
from PIL import Image
from pptx.enum.shapes import MSO_SHAPE_TYPE

LOGGER = logging.getLogger(__name__)

DEFAULT_MIN_CHARS = 50
DEFAULT_OCR_LANG = "ara+eng"
DEFAULT_DPI = 200


@dataclass(frozen=True)
class Page:
    slide_no: int
    text: str
    is_ocr: bool
    is_low_text: bool


def _resolve_tesseract_binary() -> None:
    """Ensure pytesseract locates the Tesseract OCR binary on Windows or Unix."""
    if shutil.which("tesseract"):
        return

    candidate_env = os.environ.get("TESSERACT_CMD")
    if candidate_env and Path(candidate_env).is_file():
        pytesseract.pytesseract.tesseract_cmd = candidate_env
        return

    local_app_data = os.environ.get("LOCALAPPDATA", "")
    program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
    standard_paths = [
        Path(local_app_data) / "Programs" / "Tesseract-OCR" / "tesseract.exe",
        Path(program_files) / "Tesseract-OCR" / "tesseract.exe",
        Path("C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe"),
        Path("/usr/bin/tesseract"),
        Path("/usr/local/bin/tesseract"),
    ]
    for candidate in standard_paths:
        if candidate.is_file():
            pytesseract.pytesseract.tesseract_cmd = str(candidate)
            return


def _ocr_image(img: Image.Image, lang: str = DEFAULT_OCR_LANG) -> str:
    """Execute Tesseract OCR on a PIL Image object with specified language."""
    _resolve_tesseract_binary()
    try:
        raw_text = pytesseract.image_to_string(img, lang=lang)
        return raw_text.strip()
    except Exception as exc:
        LOGGER.warning("Tesseract OCR failed on image: %s", exc)
        return ""


def _extract_pdf_page(
    page: pymupdf.Page,
    slide_no: int,
    min_chars: int,
    ocr_lang: str,
    dpi: int,
) -> Page:
    """Extract digital text or fallback to OCR for a single PDF page."""
    digital_text = page.get_text("text").strip()
    if len(digital_text) >= min_chars:
        return Page(slide_no=slide_no, text=digital_text, is_ocr=False, is_low_text=False)

    LOGGER.debug("Page %d has %d chars (< %d). Triggering OCR.", slide_no, len(digital_text), min_chars)
    pix = page.get_pixmap(dpi=dpi)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    ocr_text = _ocr_image(img, lang=ocr_lang)

    final_text = ocr_text if len(ocr_text) >= len(digital_text) else digital_text
    is_low = len(final_text) < min_chars
    return Page(slide_no=slide_no, text=final_text, is_ocr=True, is_low_text=is_low)


def _extract_pdf(path: Path, settings: dict[str, Any]) -> list[Page]:
    """Extract all pages from a PDF document."""
    min_chars = int(settings.get("min_char_threshold", DEFAULT_MIN_CHARS))
    ocr_lang = str(settings.get("ocr_lang", DEFAULT_OCR_LANG))
    dpi = int(settings.get("dpi", DEFAULT_DPI))

    pages: list[Page] = []
    with pymupdf.open(str(path)) as doc:
        for idx, page in enumerate(doc):
            pages.append(_extract_pdf_page(page, idx + 1, min_chars, ocr_lang, dpi))
    return pages


def _collect_pptx_shapes(shape_collection: Any) -> list[Any]:
    """Recursively collect leaf shapes from groups."""
    shapes = []
    for shape in shape_collection:
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            shapes.extend(_collect_pptx_shapes(shape.shapes))
        else:
            shapes.append(shape)
    return shapes


def _extract_pptx_slide_text(shapes: list[Any]) -> tuple[str, list[bytes]]:
    """Extract direct text from text frames and tables, collecting embedded images."""
    text_pieces: list[str] = []
    images: list[bytes] = []

    for shape in shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                p_text = p.text.strip()
                if p_text:
                    text_pieces.append(p_text)
        elif shape.has_table:
            for row in shape.table.rows:
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    if cell_text:
                        text_pieces.append(cell_text)
        elif shape.shape_type == MSO_SHAPE_TYPE.PICTURE and hasattr(shape, "image"):
            images.append(shape.image.blob)

    return "\n".join(text_pieces).strip(), images


def _extract_pptx_slide(
    slide: Any,
    slide_no: int,
    min_chars: int,
    ocr_lang: str,
) -> Page:
    """Extract content from a PowerPoint slide, OCR-ing pictures if text is deficient."""
    shapes = _collect_pptx_shapes(slide.shapes)
    text, image_blobs = _extract_pptx_slide_text(shapes)

    if len(text) >= min_chars:
        return Page(slide_no=slide_no, text=text, is_ocr=False, is_low_text=False)

    ocr_pieces: list[str] = []
    if image_blobs:
        for blob in image_blobs:
            img = Image.open(io.BytesIO(blob))
            extracted = _ocr_image(img, lang=ocr_lang)
            if extracted:
                ocr_pieces.append(extracted)

    combined_ocr = "\n".join(ocr_pieces).strip()
    is_ocr = bool(combined_ocr or image_blobs)
    final_text = f"{text}\n{combined_ocr}".strip() if (text and combined_ocr) else (combined_ocr or text)
    is_low = len(final_text) < min_chars

    return Page(slide_no=slide_no, text=final_text, is_ocr=is_ocr, is_low_text=is_low)


def _extract_pptx(path: Path, settings: dict[str, Any]) -> list[Page]:
    """Extract all slides from a PowerPoint presentation."""
    min_chars = int(settings.get("min_char_threshold", DEFAULT_MIN_CHARS))
    ocr_lang = str(settings.get("ocr_lang", DEFAULT_OCR_LANG))

    prs = pptx.Presentation(str(path))
    pages: list[Page] = []
    for idx, slide in enumerate(prs.slides):
        pages.append(_extract_pptx_slide(slide, idx + 1, min_chars, ocr_lang))
    return pages


def extract_file(path: str | Path, settings: dict[str, Any] | None = None) -> list[Page]:
    """Extract slide text from ONE file (.pdf or .pptx) using digital extraction + OCR fallback.

    Parameters
    ----------
    path : str | Path
        Filesystem path to a single .pdf or .pptx file.
    settings : dict | None
        Optional extraction configuration overrides:
        - min_char_threshold: int (default: 50)
        - ocr_lang: str (default: 'ara+eng')
        - dpi: int (default: 200)

    Returns
    -------
    list[Page]
        Extracted slides with page number, text content, and OCR/low-text tags.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"Path is not a regular file: {file_path}")

    config = settings or {}
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf(file_path, config)
    if suffix in {".pptx", ".ppt"}:
        if suffix == ".ppt":
            raise ValueError("Legacy .ppt format is unsupported; please convert to .pptx.")
        return _extract_pptx(file_path, config)

    raise ValueError(f"Unsupported file format '{suffix}'. Only .pdf and .pptx are supported.")
