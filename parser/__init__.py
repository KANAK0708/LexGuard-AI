"""Layout analysis → nested clause tree."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from config import load_config
from ingest import (
    ExtractedDocument,
    IngestedDocument,
    TextLine,
    extract,
    ingest_file,
)
from models.clause import CharSpan, ClauseNode, DocumentEnvelope

PathLike = Union[str, Path]

# Numbering / article patterns that signal a structural heading or clause start.
_NUMBERING_RE = re.compile(
    r"""
    ^(?:
        (?:ARTICLE|Article|SECTION|Section)\s+[\dIVXLC]+(?:\s*[:.\-–—]\s*|\s+)|
        \d+(?:\.\d+)*[.)]\s+|
        \(\s*[a-zA-Z0-9]+\s*\)\s+|
        [A-Z]\.\s+|
        [ivxlcdm]+\.\s+
    )
    """,
    re.VERBOSE,
)


@dataclass
class _ClassifiedLine:
    line: TextLine
    level: int  # 0 = body, 1..n = heading depth
    is_heading: bool


def parse_file(
    path: PathLike,
    *,
    role: Optional[str] = None,
    config: Optional[dict] = None,
) -> DocumentEnvelope:
    """Ingest and parse a PDF/DOCX file into a DocumentEnvelope."""
    ingested = ingest_file(path)
    return parse_ingested(ingested, role=role, config=config)


def parse_ingested(
    ingested: IngestedDocument,
    *,
    role: Optional[str] = None,
    config: Optional[dict] = None,
) -> DocumentEnvelope:
    """Parse an already-ingested document."""
    extracted = extract(ingested)
    return build_tree(
        extracted,
        doc_id=ingested.content_hash,
        filename=ingested.filename,
        role=role,
        config=config,
    )


def build_tree(
    extracted: ExtractedDocument,
    *,
    doc_id: str,
    filename: str,
    role: Optional[str] = None,
    config: Optional[dict] = None,
) -> DocumentEnvelope:
    """Build a nested clause tree from extracted lines."""
    cfg = config or load_config()
    parser_cfg = cfg.get("parser") or {}
    heading_ratio = float(parser_cfg.get("heading_font_ratio", 1.15))
    min_heading_ratio = float(parser_cfg.get("min_heading_confidence_ratio", 0.08))

    classified = _classify_lines(extracted.lines, heading_ratio)
    heading_count = sum(1 for c in classified if c.is_heading)
    total = max(len(classified), 1)
    heading_frac = heading_count / total

    if heading_count == 0 or heading_frac < min_heading_ratio:
        tree, mode = _paragraph_fallback(extracted)
        confidence: str = "low"
    else:
        tree = _nest_from_headings(classified, extracted.full_text)
        mode = "layout"
        confidence = "high"
        _set_confidence(tree, confidence)  # type: ignore[arg-type]

    return DocumentEnvelope(
        doc_id=doc_id,
        filename=filename,
        full_text=extracted.full_text,
        tree=tree,
        entity_map={},
        parser_mode=mode,  # type: ignore[arg-type]
        role=role,
    )


def _set_confidence(node: ClauseNode, confidence: str) -> None:
    node.confidence = confidence  # type: ignore[assignment]
    for child in node.children:
        _set_confidence(child, confidence)


def _classify_lines(
    lines: list[TextLine], heading_font_ratio: float
) -> list[_ClassifiedLine]:
    if not lines:
        return []

    body_sizes = [ln.font_size for ln in lines if not ln.is_heading_hint]
    median = _median(body_sizes) if body_sizes else _median([ln.font_size for ln in lines])

    classified: list[_ClassifiedLine] = []
    for ln in lines:
        numbered = bool(_NUMBERING_RE.match(ln.text))
        large = ln.font_size >= median * heading_font_ratio
        style_hint = ln.is_heading_hint
        is_heading = style_hint or (large and (ln.bold or numbered)) or (
            numbered and (ln.bold or large or _looks_like_short_heading(ln.text))
        )

        if not is_heading:
            classified.append(_ClassifiedLine(line=ln, level=0, is_heading=False))
            continue

        level = _heading_level(ln, median, numbered=numbered)
        classified.append(_ClassifiedLine(line=ln, level=level, is_heading=True))
    return classified


def _looks_like_short_heading(text: str) -> bool:
    # Short numbered lines without trailing sentence punctuation tend to be headings.
    stripped = text.strip()
    if len(stripped) > 120:
        return False
    if stripped.endswith("."):
        # Allow "1. Definitions" but not long sentences ending with period after many words
        words = stripped.split()
        return len(words) <= 12
    return True


def _heading_level(ln: TextLine, median: float, *, numbered: bool) -> int:
    style = ""
    # DOCX style hints encoded only via is_heading_hint + font size bands
    if ln.is_heading_hint:
        if ln.font_size >= median * 1.4:
            return 1
        if ln.font_size >= median * 1.2:
            return 2
        return 3

    m = re.match(
        r"^(?:(?:ARTICLE|Article|SECTION|Section)\s+[\dIVXLC]+)",
        ln.text,
    )
    if m:
        return 1

    m = re.match(r"^(\d+(?:\.\d+)*)[.)]\s+", ln.text)
    if m:
        depth = m.group(1).count(".") + 1
        return min(depth, 6)

    m = re.match(r"^\(\s*[a-zA-Z0-9]+\s*\)\s+", ln.text)
    if m:
        return 3

    if ln.font_size >= median * 1.35:
        return 1
    if ln.font_size >= median * 1.2 or (numbered and ln.bold):
        return 2
    return 3


def _nest_from_headings(
    classified: list[_ClassifiedLine], full_text: str
) -> ClauseNode:
    """Assemble a tree: body lines attach to the nearest preceding heading."""
    root = ClauseNode(
        clause_id="root",
        text="",
        char_span=CharSpan(0, 0),
        page=None,
        confidence="high",
        children=[],
    )

    # Stack of (level, node). Root is level 0.
    stack: list[tuple[int, ClauseNode]] = [(0, root)]
    body_buf: list[TextLine] = []
    counters: dict[int, int] = {}

    def flush_body(parent: ClauseNode) -> None:
        nonlocal body_buf
        if not body_buf:
            return
        text = "\n".join(b.text for b in body_buf)
        span = _find_span(full_text, text)
        child_id = f"{parent.clause_id}.{len(parent.children) + 1}"
        if parent.clause_id == "root":
            child_id = f"p{len(parent.children) + 1}"
        page = body_buf[0].page
        parent.children.append(
            ClauseNode(
                clause_id=child_id,
                text=text,
                char_span=span,
                page=page,
                confidence="high",
            )
        )
        body_buf = []

    for item in classified:
        if not item.is_heading:
            body_buf.append(item.line)
            continue

        # Close body under current parent before opening a new heading.
        flush_body(stack[-1][1])

        level = item.level
        while len(stack) > 1 and stack[-1][0] >= level:
            stack.pop()

        parent_level, parent = stack[-1]
        counters[level] = counters.get(level, 0) + 1
        # Reset deeper counters
        for deeper in [k for k in counters if k > level]:
            del counters[deeper]

        clause_id = _make_clause_id(counters, level)
        span = _find_span(full_text, item.line.text)
        node = ClauseNode(
            clause_id=clause_id,
            text=item.line.text,
            char_span=span,
            page=item.line.page,
            confidence="high",
            children=[],
        )
        parent.children.append(node)
        stack.append((level, node))

    flush_body(stack[-1][1])

    # If root only has body paragraphs and no headings somehow, still OK.
    if not root.children:
        return _empty_root_from_text(full_text)

    # Root text remains empty; spans of children cover the document.
    return root


def _make_clause_id(counters: dict[int, int], level: int) -> str:
    parts = [str(counters[i]) for i in range(1, level + 1) if i in counters]
    return ".".join(parts) if parts else "1"


def _paragraph_fallback(
    extracted: ExtractedDocument,
) -> tuple[ClauseNode, str]:
    """Chunk by paragraph/line boundaries when heading structure is unclear."""
    root = ClauseNode(
        clause_id="root",
        text="",
        char_span=CharSpan(0, 0),
        confidence="low",
        children=[],
    )
    full_text = extracted.full_text
    for idx, line in enumerate(extracted.lines, start=1):
        if not line.text.strip():
            continue
        span = _find_span(full_text, line.text)
        root.children.append(
            ClauseNode(
                clause_id=f"p{idx}",
                text=line.text,
                char_span=span,
                page=line.page,
                confidence="low",
            )
        )
    if not root.children and full_text.strip():
        root.children.append(
            ClauseNode(
                clause_id="p1",
                text=full_text,
                char_span=CharSpan(0, len(full_text)),
                confidence="low",
            )
        )
    return root, "paragraph_fallback"


def _empty_root_from_text(full_text: str) -> ClauseNode:
    return ClauseNode(
        clause_id="root",
        text="",
        char_span=CharSpan(0, 0),
        confidence="low",
        children=[
            ClauseNode(
                clause_id="p1",
                text=full_text,
                char_span=CharSpan(0, len(full_text)),
                confidence="low",
            )
        ]
        if full_text
        else [],
    )


def _find_span(full_text: str, snippet: str) -> CharSpan:
    """Locate snippet in full_text; prefer exact match, else best-effort."""
    if not snippet:
        return CharSpan(0, 0)
    start = full_text.find(snippet)
    if start >= 0:
        return CharSpan(start, start + len(snippet))
    # Fallback: search first line only
    first = snippet.split("\n", 1)[0]
    start = full_text.find(first)
    if start >= 0:
        return CharSpan(start, start + len(first))
    return CharSpan(0, 0)


def _median(values: list[float]) -> float:
    if not values:
        return 11.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


__all__ = [
    "build_tree",
    "parse_file",
    "parse_ingested",
]
