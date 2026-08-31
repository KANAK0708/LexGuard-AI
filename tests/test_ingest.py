"""Tests for ingest format detection and extraction."""

from pathlib import Path

import pytest

from ingest import detect_format, DocumentFormat, extract, ingest_file

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


@pytest.fixture(scope="module", autouse=True)
def _ensure_samples():
    if not (SAMPLES / "structured_nda.docx").exists():
        from scripts.generate_samples import main

        main()


def test_detect_format_pdf_docx():
    assert detect_format("a.pdf") == DocumentFormat.PDF
    assert detect_format("a.docx") == DocumentFormat.DOCX


def test_detect_format_rejects_unknown():
    with pytest.raises(ValueError, match="Unsupported"):
        detect_format("notes.txt")


def test_extract_docx_structured():
    ingested = ingest_file(SAMPLES / "structured_nda.docx")
    extracted = extract(ingested)
    assert "Confidential Information" in extracted.full_text
    assert len(extracted.lines) >= 5
    assert any(ln.is_heading_hint or ln.bold for ln in extracted.lines)


def test_extract_pdf_structured():
    ingested = ingest_file(SAMPLES / "structured_nda.pdf")
    extracted = extract(ingested)
    assert "Definitions" in extracted.full_text
    assert extracted.page_count >= 1
    assert len(extracted.lines) >= 5
