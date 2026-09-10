"""Tests for Phase 2 anonymization (NER masking + LLM payload enforcement)."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from anonymize import (
    EntityHit,
    anonymize,
    apply_masks,
    assert_no_raw_entities,
    build_llm_payload,
    collect_llm_payloads,
    resolve_overlaps,
)
from models.clause import CharSpan, ClauseNode, DocumentEnvelope
from parser import parse_file
from pipeline import run

SAMPLES = __import__("pathlib").Path(__file__).resolve().parents[1] / "samples"


@dataclass
class _FakeEnt:
    text: str
    label_: str
    start_char: int
    end_char: int


class _FakeDoc:
    def __init__(self, ents: list[_FakeEnt]):
        self.ents = ents


class FakeNlp:
    """Deterministic NER stand-in for unit tests (no spaCy model required)."""

    def __init__(self, entities_by_surface: dict[str, str]):
        self.entities_by_surface = entities_by_surface

    def __call__(self, text: str) -> _FakeDoc:
        ents: list[_FakeEnt] = []
        for surface, label in self.entities_by_surface.items():
            start = 0
            while True:
                idx = text.find(surface, start)
                if idx < 0:
                    break
                ents.append(
                    _FakeEnt(
                        text=surface,
                        label_=label,
                        start_char=idx,
                        end_char=idx + len(surface),
                    )
                )
                start = idx + len(surface)
        return _FakeDoc(ents)


def _make_envelope(texts: list[str]) -> DocumentEnvelope:
    full = "\n".join(texts)
    children: list[ClauseNode] = []
    offset = 0
    for i, text in enumerate(texts, start=1):
        start = full.find(text, offset)
        end = start + len(text)
        children.append(
            ClauseNode(
                clause_id=f"p{i}",
                text=text,
                char_span=CharSpan(start, end),
            )
        )
        offset = end
    tree = ClauseNode(
        clause_id="root",
        text="",
        char_span=CharSpan(0, 0),
        children=children,
    )
    return DocumentEnvelope(
        doc_id="test",
        filename="test.txt",
        full_text=full,
        tree=tree,
        parser_mode="paragraph_fallback",
    )


def test_resolve_overlaps_prefers_longer_earlier():
    hits = [
        EntityHit(0, 4, "ORG", "Acme"),
        EntityHit(0, 16, "ORG", "Acme Corporation"),
        EntityHit(20, 28, "PERSON", "Jane Doe"),
    ]
    resolved = resolve_overlaps(hits)
    assert [h.surface for h in resolved] == ["Acme Corporation", "Jane Doe"]


def test_apply_masks_all_occurrences_longest_first():
    text = "Jane Doe works at Acme Corporation with Jane Doe near Acme."
    mapping = {
        "Jane Doe": "[PERSON_1]",
        "Acme Corporation": "[ORG_1]",
        "Acme": "[ORG_2]",
    }
    masked = apply_masks(text, mapping)
    assert masked == "[PERSON_1] works at [ORG_1] with [PERSON_1] near [ORG_2]."
    assert "Jane Doe" not in masked
    assert "Acme Corporation" not in masked


def test_anonymize_masks_and_preserves_source():
    env = _make_envelope(
        [
            "Acme Corporation and Jane Doe signed in Delaware.",
            "Jane Doe shall pay Acme Corporation by January 15, 2024.",
        ]
    )
    original_texts = {n.clause_id: n.text for n in env.tree.iter_nodes()}
    original_spans = {
        n.clause_id: (n.char_span.start, n.char_span.end)
        for n in env.tree.iter_nodes()
    }

    fake = FakeNlp(
        {
            "Acme Corporation": "ORG",
            "Jane Doe": "PERSON",
            "Delaware": "GPE",
            "January 15, 2024": "DATE",
        }
    )
    out = anonymize(env, nlp=fake)

    # Source tree untouched
    for node in out.tree.iter_nodes():
        assert node.text == original_texts[node.clause_id]
        assert (node.char_span.start, node.char_span.end) == original_spans[
            node.clause_id
        ]
        if node.text:
            sliced = out.full_text[node.char_span.start : node.char_span.end]
            assert sliced == node.text

    # Consistent tokens for repeated surfaces
    assert out.entity_map["[ORG_1]"] == "Acme Corporation"
    assert out.entity_map["[PERSON_1]"] == "Jane Doe"
    assert "[ORG_2]" not in out.entity_map  # same ORG string → one token

    for node in out.tree.iter_nodes():
        if not node.text:
            continue
        assert node.masked_text is not None
        for original in out.entity_map.values():
            assert original not in node.masked_text


def test_build_llm_payload_only_masked():
    node = ClauseNode(
        clause_id="1",
        text="Jane Doe of Acme Corporation",
        char_span=CharSpan(0, 28),
        masked_text="[PERSON_1] of [ORG_1]",
    )
    payload = build_llm_payload(node)
    assert payload == "[PERSON_1] of [ORG_1]"
    assert "Jane Doe" not in payload

    bare = ClauseNode(
        clause_id="2",
        text="secret",
        char_span=CharSpan(0, 6),
    )
    with pytest.raises(ValueError, match="masked_text"):
        build_llm_payload(bare)


def test_llm_enforcement_rejects_raw_entities():
    entity_map = {"[ORG_1]": "Acme Corporation", "[PERSON_1]": "Jane Doe"}
    assert_no_raw_entities("[PERSON_1] joined [ORG_1]", entity_map)
    with pytest.raises(AssertionError, match="leaked"):
        assert_no_raw_entities("Contact Jane Doe at Acme Corporation", entity_map)


def test_enforcement_over_full_envelope_payloads():
    env = _make_envelope(
        ["Acme Corporation hired Jane Doe in Delaware on January 15, 2024."]
    )
    fake = FakeNlp(
        {
            "Acme Corporation": "ORG",
            "Jane Doe": "PERSON",
            "Delaware": "GPE",
            "January 15, 2024": "DATE",
        }
    )
    out = anonymize(env, nlp=fake)
    for payload in collect_llm_payloads(out):
        assert_no_raw_entities(payload, out.entity_map)
        # Guard: never include original node.text when entities exist
        assert payload != out.tree.children[0].text or not out.entity_map


@pytest.fixture(scope="module", autouse=True)
def _ensure_samples():
    if not (SAMPLES / "structured_nda.docx").exists():
        from scripts.generate_samples import main

        main()


def test_pipeline_anonymizes_sample_docx():
    """Integration: real spaCy on sample with known fixture entities."""
    spacy = pytest.importorskip("spacy")
    try:
        spacy.load("en_core_web_sm")
    except OSError:
        pytest.skip("en_core_web_sm not installed")

    # Regenerate so entity-bearing paragraphs are present
    from scripts.generate_samples import main

    main()

    from unittest.mock import patch

    with patch("llm.query_ollama") as mock_q:
        mock_q.return_value = '{"category":"Unclassified","plain_language_summary":"summary","risk_explanation":"risk","base_risk_score":0.3,"quoted_text":"text"}'
        result = run(SAMPLES / "structured_nda.docx", role="Client")
    assert result["status"] == "anonymized"
    doc = result["document"]
    assert "entity_map" in doc

    env = anonymize(parse_file(SAMPLES / "structured_nda.docx"))
    # Source spans still resolve
    for node in env.tree.iter_nodes():
        if node.clause_id == "root" and not node.text:
            continue
        if not node.text:
            continue
        assert env.full_text[node.char_span.start : node.char_span.end] == node.text
        assert node.masked_text is not None

    # Known fixture surfaces should appear in entity_map values when detected
    originals = set(env.entity_map.values())
    # At least one of the planted entities should be masked
    planted = {"Acme Corporation", "Jane Doe", "Delaware", "January 15, 2024"}
    assert originals & planted, f"Expected some planted entities; got {originals}"

    for payload in collect_llm_payloads(env):
        assert_no_raw_entities(payload, env.entity_map)
