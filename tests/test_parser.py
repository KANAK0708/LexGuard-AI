"""Tests for structural layout parser and paragraph fallback."""

from pathlib import Path

import pytest

from parser import parse_file
from pipeline import run

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


@pytest.fixture(scope="module", autouse=True)
def _ensure_samples():
    if not (SAMPLES / "structured_nda.docx").exists():
        from scripts.generate_samples import main

        main()


def _assert_span_integrity(envelope) -> None:
    for node in envelope.tree.iter_nodes():
        if node.clause_id == "root" and not node.text:
            continue
        if not node.text:
            continue
        sliced = envelope.full_text[node.char_span.start : node.char_span.end]
        assert sliced == node.text, (
            f"Span mismatch for {node.clause_id}: "
            f"{sliced!r} != {node.text!r}"
        )


def test_structured_docx_nests_headings():
    env = parse_file(SAMPLES / "structured_nda.docx")
    assert env.parser_mode == "layout"
    assert len(env.tree.children) >= 2
    # Expect numbered section headings among top-level children
    top_texts = " ".join(c.text for c in env.tree.children)
    assert "Definitions" in top_texts or "1." in top_texts
    _assert_span_integrity(env)


def test_structured_pdf_nests_and_spans():
    env = parse_file(SAMPLES / "structured_nda.pdf")
    assert env.parser_mode == "layout"
    assert len(env.tree.children) >= 2
    ids = [n.clause_id for n in env.tree.iter_nodes() if n.clause_id != "root"]
    assert any("." in i or i.isdigit() or i.startswith("p") for i in ids)
    _assert_span_integrity(env)


def test_headingless_docx_triggers_fallback():
    env = parse_file(SAMPLES / "headingless_policy.docx")
    assert env.parser_mode == "paragraph_fallback"
    assert all(
        n.confidence == "low"
        for n in env.tree.iter_nodes()
        if n.clause_id != "root" or n.text
    )
    assert len(env.tree.children) >= 3
    _assert_span_integrity(env)


def test_headingless_pdf_triggers_fallback():
    env = parse_file(SAMPLES / "headingless_policy.pdf")
    assert env.parser_mode == "paragraph_fallback"
    assert len(env.tree.children) >= 2
    _assert_span_integrity(env)


def test_pipeline_run_single_and_pair():
    result = run(SAMPLES / "structured_nda.docx", role="Client")
    assert result["status"] == "anonymized"
    assert result["document"]["parser_mode"] in {"layout", "paragraph_fallback"}
    assert result["role"] == "Client"
    # Phase 2: every text node has masked_text; source spans intact
    tree = result["document"]["tree"]

    def walk(node):
        yield node
        for child in node.get("children") or []:
            yield from walk(child)

    for node in walk(tree):
        if node.get("text"):
            assert node.get("masked_text") is not None

    pair = run(
        SAMPLES / "structured_nda.docx",
        role="Vendor",
        file_v2=SAMPLES / "structured_nda_v2.docx",
    )
    assert pair["status"] == "anonymized_pair"
    assert "document_v2" in pair
