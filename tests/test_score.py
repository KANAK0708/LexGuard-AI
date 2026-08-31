"""Tests for Phase 4 Asymmetric Role-Weighted Risk Scoring Module."""

from __future__ import annotations

import pytest
from pathlib import Path
from models.clause import CharSpan, ClauseNode, DocumentEnvelope
from score import classify_category, compute_base_risk, score_document, ROLE_WEIGHT_MATRIX
from pipeline import run

SAMPLES = Path(__file__).resolve().parents[1] / "samples"

def test_classify_category():
    assert classify_category("Party A agrees to indemnify Party B.") == "Indemnification"
    assert classify_category("In no event shall aggregate liability exceed ,000.") == "LimitationOfLiability"
    assert classify_category("Employee agrees not to engage in non-compete business.") == "NonCompete"
    assert classify_category("All intellectual property belongs to Employer.") == "IPOwnership"
    assert classify_category("Either party may terminate upon 30 days notice.") == "Termination"
    assert classify_category("Invoices shall be paid within 30 days.") == "PaymentTerms"
    assert classify_category("The services are provided as is without warranty.") == "Warranty"
    assert classify_category("This agreement is governed by law.") == "General"

def test_asymmetric_role_scoring_difference():
    # Non-compete clause scored for Employee vs Employer
    text = "Employee agrees to a strict non-compete for 24 months with liquidated damages."
    node = ClauseNode(clause_id="c1", text=text, char_span=CharSpan(0, len(text)))
    tree = ClauseNode(clause_id="root", text="", char_span=CharSpan(0, 0), children=[node])
    
    env_emp = DocumentEnvelope(doc_id="d1", filename="test.txt", full_text="", tree=tree)
    score_document(env_emp, role="Employee")
    emp_score = node.risk_score
    emp_weights = node.role_weights_applied

    node_employer = ClauseNode(clause_id="c1", text=text, char_span=CharSpan(0, len(text)))
    tree_employer = ClauseNode(clause_id="root", text="", char_span=CharSpan(0, 0), children=[node_employer])
    env_employer = DocumentEnvelope(doc_id="d2", filename="test.txt", full_text="", tree=tree_employer)
    score_document(env_employer, role="Employer")
    employer_score = node_employer.risk_score

    assert emp_score is not None
    assert employer_score is not None
    # Employee risk multiplier for NonCompete (2.0) > Employer (1.1)
    assert emp_score > employer_score
    assert emp_weights["role_multiplier"] == 2.0

def test_pipeline_score_integration():
    sample = SAMPLES / "structured_nda.docx"
    if sample.exists():
        result = run(sample, role="Vendor")
        doc = result["document"]
        assert doc["role"] == "Vendor"
        
        # Verify nodes have category and risk_score assigned
        tree = doc["tree"]
        def check_scores(n):
            if n.get("text"):
                assert n.get("category") is not None
                assert n.get("risk_score") is not None
                assert n.get("role_weights_applied") is not None
            for c in n.get("children") or []:
                check_scores(c)
                
        check_scores(tree)
