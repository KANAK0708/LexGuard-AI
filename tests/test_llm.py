"""Tests for Phase 4 LLM integration (Ollama client, strict JSON parsing, retry & fallback)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from llm import (
    analyze,
    analyze_clause_node,
    build_prompt,
    parse_llm_json,
    query_ollama,
)
from models.clause import CharSpan, ClauseNode, DocumentEnvelope, LlmClaim


def test_build_prompt_privacy():
    node = ClauseNode(
        clause_id="p1",
        text="Jane Doe of Acme Corporation shall indemnify Client.",
        char_span=CharSpan(0, 52),
        masked_text="[PERSON_1] of [ORG_1] shall indemnify Client.",
    )
    prompt = build_prompt(node)

    assert "[PERSON_1] of [ORG_1] shall indemnify Client." in prompt
    assert "Jane Doe" not in prompt
    assert "Acme Corporation" not in prompt


def test_parse_llm_json_valid():
    raw_json = json.dumps({
        "category": "Indemnity",
        "plain_language_summary": "Indemnification requirement",
        "risk_explanation": "High risk obligation for indemnifying third party claims",
        "base_risk_score": 0.8,
        "quoted_text": "[PERSON_1] of [ORG_1] shall indemnify Client."
    })
    parsed = parse_llm_json(raw_json)

    assert parsed["category"] == "Indemnity"
    assert parsed["plain_language_summary"] == "Indemnification requirement"
    assert parsed["base_risk_score"] == 0.8


def test_parse_llm_json_markdown_wrapped():
    raw_markdown = """```json
{
  "category": "Termination",
  "plain_language_summary": "Either party may terminate",
  "risk_explanation": "Standard 30 day notice period",
  "base_risk_score": 0.4,
  "quoted_text": "Either party may terminate on notice."
}
```"""
    parsed = parse_llm_json(raw_markdown)

    assert parsed["category"] == "Termination"
    assert parsed["base_risk_score"] == 0.4


def test_parse_llm_json_invalid_structure():
    with pytest.raises(ValueError, match="Missing required key"):
        parse_llm_json('{"category": "Indemnity"}')


@patch("llm.query_ollama")
def test_analyze_clause_node_retry_logic(mock_query):
    node = ClauseNode(
        clause_id="c1",
        text="The vendor shall warrant all products.",
        char_span=CharSpan(0, 38),
        masked_text="The vendor shall warrant all products.",
    )

    # First attempt fails with malformed JSON, second attempt succeeds
    valid_resp = json.dumps({
        "category": "Warranty",
        "plain_language_summary": "Product warranty",
        "risk_explanation": "Vendor warrants quality",
        "base_risk_score": 0.5,
        "quoted_text": "The vendor shall warrant all products."
    })
    mock_query.side_effect = ["Invalid JSON non-dict text", valid_resp]

    claim = analyze_clause_node(node, max_retries=1)

    assert claim is not None
    assert mock_query.call_count == 2
    assert node.category == "Warranty"
    assert "Product warranty" in claim.explanation


@patch("llm.query_ollama")
def test_analyze_offline_graceful_fallback(mock_query):
    node = ClauseNode(
        clause_id="c2",
        text="In no event shall aggregate liability exceed fee.",
        char_span=CharSpan(0, 48),
        masked_text="In no event shall aggregate liability exceed fee.",
    )
    mock_query.side_effect = requests.RequestException("Connection refused")

    claim = analyze_clause_node(node, max_retries=1)

    assert claim is not None
    assert "Fallback" in claim.explanation
    assert claim.clause_id == "c2"


@patch("llm.query_ollama")
def test_analyze_document_envelope(mock_query):
    mock_query.return_value = json.dumps({
        "category": "LimitationOfLiability",
        "plain_language_summary": "Liability capped",
        "risk_explanation": "Liability cap protects vendor",
        "base_risk_score": 0.6,
        "quoted_text": "Liability capped at fee."
    })

    child = ClauseNode(
        clause_id="c1",
        text="Liability capped at fee.",
        char_span=CharSpan(0, 24),
        masked_text="Liability capped at fee.",
    )
    tree = ClauseNode(clause_id="root", text="", char_span=CharSpan(0, 0), children=[child])
    env = DocumentEnvelope(
        doc_id="d1",
        filename="test.txt",
        full_text="Liability capped at fee.",
        tree=tree,
    )

    out = analyze(env)

    assert len(out.tree.children[0].llm_claims) == 1
    assert out.tree.children[0].category == "LimitationOfLiability"
