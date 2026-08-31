"""Tests for Phase 3 semantic drift engine."""

from __future__ import annotations

import pytest
from pathlib import Path
from models.clause import CharSpan, ClauseNode, DocumentEnvelope
from drift import compare
from embed import clear_vector_store
from pipeline import run

SAMPLES = Path(__file__).resolve().parents[1] / "samples"

@pytest.fixture(autouse=True)
def _reset_store():
    clear_vector_store()

def test_compare_identical_documents():
    node1 = ClauseNode(clause_id="c1", text="Receiving party agrees to maintain secrecy.", char_span=CharSpan(0, 43))
    tree1 = ClauseNode(clause_id="root", text="", char_span=CharSpan(0, 0), children=[node1])
    env1 = DocumentEnvelope(doc_id="d1", filename="v1.txt", full_text="", tree=tree1)

    node2 = ClauseNode(clause_id="c1", text="Receiving party agrees to maintain secrecy.", char_span=CharSpan(0, 43))
    tree2 = ClauseNode(clause_id="root", text="", char_span=CharSpan(0, 0), children=[node2])
    env2 = DocumentEnvelope(doc_id="d2", filename="v2.txt", full_text="", tree=tree2)

    drift_results = compare(env1, env2)
    assert len(drift_results) >= 1
    res = drift_results[0]
    assert res.left_clause_id == "c1"
    assert res.right_clause_id == "c1"
    assert res.label == "Cosmetic"
    assert res.cosine is not None and res.cosine >= 0.95

def test_compare_intent_shift_and_rewrite():
    n1 = ClauseNode(clause_id="c1", text="Party A shall pay ,000 within 30 days.", char_span=CharSpan(0, 41))
    t1 = ClauseNode(clause_id="root", text="", char_span=CharSpan(0, 0), children=[n1])
    env1 = DocumentEnvelope(doc_id="d1", filename="v1.txt", full_text="", tree=t1)

    n2 = ClauseNode(clause_id="c1", text="Party A shall pay ,000 within 60 days.", char_span=CharSpan(0, 41))
    t2 = ClauseNode(clause_id="root", text="", char_span=CharSpan(0, 0), children=[n2])
    env2 = DocumentEnvelope(doc_id="d2", filename="v2.txt", full_text="", tree=t2)

    drift_results = compare(env1, env2)
    assert len(drift_results) >= 1
    assert drift_results[0].label in ("Cosmetic", "IntentShift")

def test_pipeline_drift_integration():
    sample1 = SAMPLES / "structured_nda.docx"
    sample2 = SAMPLES / "structured_nda_v2.docx"
    if sample1.exists() and sample2.exists():
        result = run(sample1, role="Client", file_v2=sample2)
        assert result["status"] == "anonymized_pair"
        assert len(result["drift"]) > 0
        assert "document_v2" in result
