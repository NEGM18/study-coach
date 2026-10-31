"""Unit tests for single-file slide and OCR extraction (Issue #25)."""

from pathlib import Path

import pptx
import pymupdf
import pytest
from PIL import Image, ImageDraw, ImageFont
from pptx.util import Inches

from ml_core.topics.extract import Page, extract_file


def _render_text_to_image(text: str, path: Path) -> Path:
    """Helper to render synthetic text to an image file for OCR tests."""
    img = Image.new("RGB", (600, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.text((20, 20), text, fill=(0, 0, 0), font=font)
    img.save(str(path))
    return path


def test_extract_file_digital_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "digital_test.pdf"
    doc = pymupdf.open()

    p1 = doc.new_page(width=600, height=400)
    p1.insert_text(pymupdf.Point(40, 50), "CS201 Data Structures and Algorithms", fontsize=16)
    p1.insert_text(
        pymupdf.Point(40, 90),
        "Dynamic arrays provide amortized constant time insertion O(1).",
        fontsize=12,
    )

    p2 = doc.new_page(width=600, height=400)
    p2.insert_text(pymupdf.Point(40, 50), "Linked Lists and Pointer Manipulation", fontsize=16)
    p2.insert_text(
        pymupdf.Point(40, 90),
        "Each node maintains a payload and a pointer to the next element.",
        fontsize=12,
    )

    doc.save(str(pdf_path))
    doc.close()

    pages = extract_file(pdf_path)

    assert len(pages) == 2
    assert all(isinstance(p, Page) for p in pages)
    assert pages[0].slide_no == 1
    assert "CS201 Data Structures" in pages[0].text
    assert not pages[0].is_ocr
    assert not pages[0].is_low_text

    assert pages[1].slide_no == 2
    assert "Linked Lists" in pages[1].text
    assert not pages[1].is_ocr
    assert not pages[1].is_low_text


def test_extract_file_scanned_pdf_ocr(tmp_path: Path) -> None:
    img_path = tmp_path / "scanned_slide.png"
    _render_text_to_image("Operating Systems Kernel Mode Interrupts", img_path)

    pdf_path = tmp_path / "scanned_test.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=600, height=400)
    page.insert_image(pymupdf.Rect(20, 20, 580, 220), filename=str(img_path))
    doc.save(str(pdf_path))
    doc.close()

    pages = extract_file(pdf_path, settings={"min_char_threshold": 30})

    assert len(pages) == 1
    page_res = pages[0]
    assert page_res.slide_no == 1
    assert page_res.is_ocr
    assert "Operating" in page_res.text or "Systems" in page_res.text or len(page_res.text) > 0


def test_extract_file_pptx_with_text_and_tables(tmp_path: Path) -> None:
    pptx_path = tmp_path / "sample_deck.pptx"
    prs = pptx.Presentation()

    # Slide 1: Text boxes
    slide1 = prs.slides.add_slide(prs.slide_layouts[6])
    tb = slide1.shapes.add_textbox(Inches(1), Inches(1), Inches(6), Inches(3))
    p = tb.text_frame.paragraphs[0]
    p.text = "Artificial Intelligence Heuristic Search"
    p2 = tb.text_frame.add_paragraph()
    p2.text = "A* search evaluates nodes by combining cost g(n) and heuristic h(n)."

    # Slide 2: Table
    slide2 = prs.slides.add_slide(prs.slide_layouts[6])
    table_shape = slide2.shapes.add_table(2, 2, Inches(1), Inches(1), Inches(6), Inches(2))
    table = table_shape.table
    table.cell(0, 0).text = "Algorithm"
    table.cell(0, 1).text = "Completeness"
    table.cell(1, 0).text = "BFS"
    table.cell(1, 1).text = "Yes"

    prs.save(str(pptx_path))

    pages = extract_file(pptx_path)

    assert len(pages) == 2
    assert pages[0].slide_no == 1
    assert "Artificial Intelligence" in pages[0].text
    assert not pages[0].is_ocr

    assert pages[1].slide_no == 2
    assert "BFS" in pages[1].text
    assert "Completeness" in pages[1].text


def test_extract_file_pptx_image_ocr(tmp_path: Path) -> None:
    img_path = tmp_path / "slide_img.png"
    _render_text_to_image("CPU Scheduling Algorithms Round Robin", img_path)

    pptx_path = tmp_path / "image_deck.pptx"
    prs = pptx.Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.shapes.add_picture(str(img_path), Inches(1), Inches(1), width=Inches(6))
    prs.save(str(pptx_path))

    pages = extract_file(pptx_path, settings={"min_char_threshold": 40})

    assert len(pages) == 1
    assert pages[0].slide_no == 1
    assert pages[0].is_ocr
    assert len(pages[0].text) > 0


def test_extract_file_nonexistent_raises_file_not_found(tmp_path: Path) -> None:
    missing_path = tmp_path / "does_not_exist.pdf"
    with pytest.raises(FileNotFoundError, match="File not found"):
        extract_file(missing_path)


def test_extract_file_directory_raises_value_error(tmp_path: Path) -> None:
    dir_path = tmp_path / "subfolder"
    dir_path.mkdir()
    with pytest.raises(ValueError, match="not a regular file"):
        extract_file(dir_path)


def test_extract_file_unsupported_extension_raises_value_error(tmp_path: Path) -> None:
    dummy_file = tmp_path / "notes.docx"
    dummy_file.write_text("dummy content", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported file format"):
        extract_file(dummy_file)


def test_extract_file_legacy_ppt_raises_descriptive_error(tmp_path: Path) -> None:
    ppt_file = tmp_path / "legacy.ppt"
    ppt_file.write_text("legacy binary", encoding="utf-8")
    with pytest.raises(ValueError, match="Legacy .ppt format is unsupported"):
        extract_file(ppt_file)
