"""File upload handling and format detection (PDF / DOCX)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import BinaryIO, Union

from docx import Document
import fitz  # PyMuPDF
import pdfplumber

PathLike = Union[str, Path]


class DocumentFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"


@dataclass
class IngestedDocument:
    path: Path
    filename: str
    fmt: DocumentFormat
    content_hash: str
    raw_bytes: bytes


def detect_format(path: PathLike) -> DocumentFormat:
    """Detect document format from suffix."""
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        return DocumentFormat.PDF
    if suffix in {".docx", ".doc"}:
        if suffix == ".doc":
            raise ValueError(
                "Legacy .doc is not supported; convert to .docx or .pdf."
            )
        return DocumentFormat.DOCX
    raise ValueError(f"Unsupported file type: {suffix!r}. Use PDF or DOCX.")


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ingest_file(path: PathLike) -> IngestedDocument:
    """Load a file from disk and return an ingested document descriptor."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    data = p.read_bytes()
    fmt = detect_format(p)
    return IngestedDocument(
        path=p.resolve(),
        filename=p.name,
        fmt=fmt,
        content_hash=content_hash(data),
        raw_bytes=data,
    )


def ingest_bytes(
    data: bytes,
    filename: str,
    *,
    tmp_dir: PathLike | None = None,
) -> IngestedDocument:
    """Ingest uploaded bytes (e.g. from Streamlit) by writing a temp file."""
    suffix = Path(filename).suffix.lower()
    detect_format(filename)  # validate
    base = Path(tmp_dir) if tmp_dir else Path(".cache") / "uploads"
    base.mkdir(parents=True, exist_ok=True)
    digest = content_hash(data)
    out = base / f"{digest}{suffix}"
    if not out.exists():
        out.write_bytes(data)
    return IngestedDocument(
        path=out.resolve(),
        filename=filename,
        fmt=detect_format(filename),
        content_hash=digest,
        raw_bytes=data,
    )


@dataclass
class TextLine:
    """A single visual line extracted from a document."""

    text: str
    font_size: float
    bold: bool
    page: int
    is_heading_hint: bool = False


@dataclass
class ExtractedDocument:
    """Normalized extraction shared by PDF and DOCX paths."""

    full_text: str
    lines: list[TextLine]
    page_count: int


def extract(ingested: IngestedDocument) -> ExtractedDocument:
    """Extract text lines (+ font metadata when available)."""
    if ingested.fmt == DocumentFormat.PDF:
        return _extract_pdf(ingested.path)
    return _extract_docx(ingested.path)


def _extract_pdf(path: Path) -> ExtractedDocument:
    lines: list[TextLine] = []
    text_parts: list[str] = []

    # Prefer pdfplumber for character-level font sizes; fall back to PyMuPDF.
    try:
        with pdfplumber.open(path) as pdf:
            page_count = len(pdf.pages)
            for page_idx, page in enumerate(pdf.pages, start=1):
                chars = page.chars or []
                if not chars:
                    page_text = page.extract_text() or ""
                    for raw in page_text.splitlines():
                        raw = raw.strip()
                        if not raw:
                            continue
                        lines.append(
                            TextLine(
                                text=raw,
                                font_size=11.0,
                                bold=False,
                                page=page_idx,
                            )
                        )
                        text_parts.append(raw)
                    continue

                # Group characters into lines by similar y-position.
                sorted_chars = sorted(
                    chars, key=lambda c: (-round(float(c.get("top", 0)), 1), float(c.get("x0", 0)))
                )
                current: list[dict] = []
                current_top: float | None = None
                y_tol = 3.0

                def flush(group: list[dict]) -> None:
                    if not group:
                        return
                    group = sorted(group, key=lambda c: float(c.get("x0", 0)))
                    text = "".join(c.get("text", "") for c in group).strip()
                    if not text:
                        return
                    sizes = [float(c.get("size", 11.0)) for c in group]
                    fonts = [str(c.get("fontname", "")) for c in group]
                    font_size = sum(sizes) / len(sizes)
                    bold = any("bold" in f.lower() or "black" in f.lower() for f in fonts)
                    lines.append(
                        TextLine(
                            text=text,
                            font_size=font_size,
                            bold=bold,
                            page=page_idx,
                        )
                    )
                    text_parts.append(text)

                for ch in sorted_chars:
                    top = float(ch.get("top", 0))
                    if current_top is None or abs(top - current_top) <= y_tol:
                        current.append(ch)
                        if current_top is None:
                            current_top = top
                    else:
                        flush(current)
                        current = [ch]
                        current_top = top
                flush(current)
    except Exception:
        # PyMuPDF fallback
        doc = fitz.open(path)
        page_count = doc.page_count
        for page_idx, page in enumerate(doc, start=1):
            blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
            for block in blocks:
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    spans = line.get("spans", [])
                    if not spans:
                        continue
                    text = "".join(s.get("text", "") for s in spans).strip()
                    if not text:
                        continue
                    sizes = [float(s.get("size", 11.0)) for s in spans]
                    fonts = [str(s.get("font", "")) for s in spans]
                    font_size = sum(sizes) / len(sizes)
                    bold = any("bold" in f.lower() for f in fonts)
                    lines.append(
                        TextLine(
                            text=text,
                            font_size=font_size,
                            bold=bold,
                            page=page_idx,
                        )
                    )
                    text_parts.append(text)
        doc.close()

    full_text = "\n".join(text_parts)
    return ExtractedDocument(full_text=full_text, lines=lines, page_count=page_count)


def _extract_docx(path: Path) -> ExtractedDocument:
    doc = Document(path)
    lines: list[TextLine] = []
    text_parts: list[str] = []

    for para in doc.paragraphs:
        text = (para.text or "").strip()
        if not text:
            continue

        style_name = (para.style.name if para.style is not None else "") or ""
        style_lower = style_name.lower()
        is_heading = style_lower.startswith("heading") or style_lower.startswith("title")

        # Approximate font size from runs; default body = 11pt, headings larger.
        run_sizes = []
        bold = False
        for run in para.runs:
            if run.bold:
                bold = True
            if run.font is not None and run.font.size is not None:
                run_sizes.append(run.font.size.pt)

        if run_sizes:
            font_size = sum(run_sizes) / len(run_sizes)
        elif is_heading:
            # Heading 1 ~ 16, Heading 2 ~ 14, etc.
            level = 1
            for part in style_lower.split():
                if part.isdigit():
                    level = int(part)
                    break
            font_size = max(12.0, 18.0 - (level - 1) * 2.0)
        else:
            font_size = 11.0

        lines.append(
            TextLine(
                text=text,
                font_size=font_size,
                bold=bold or is_heading,
                page=1,
                is_heading_hint=is_heading,
            )
        )
        text_parts.append(text)

    full_text = "\n".join(text_parts)
    return ExtractedDocument(
        full_text=full_text, lines=lines, page_count=1
    )


# Re-export BinaryIO for type checkers / callers
__all__ = [
    "BinaryIO",
    "DocumentFormat",
    "ExtractedDocument",
    "IngestedDocument",
    "TextLine",
    "content_hash",
    "detect_format",
    "extract",
    "ingest_bytes",
    "ingest_file",
]
