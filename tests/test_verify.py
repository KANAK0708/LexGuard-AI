"""Tests for Phase 5 Anchor Verification (Hallucination Guard & Adversarial Tests)."""

from __future__ import annotations

from pathlib import Path
import pytest

from models.clause import CharSpan, ClauseNode, DocumentEnvelope, LlmClaim
from verify import log_rejected_claim, normalize_text, verify, verify_claim


def _make_sample_envelope() -> DocumentEnvelope:
    c1 = ClauseNode(
        clause_id="c1",
        text="The Client shall pay all invoices within thirty (30) days.",
        char_span=CharSpan(0, 58),
        masked_text="The [ORG_1] shall pay all invoices within thirty (30) days.",
    )
    c2 = ClauseNode(
        clause_id="c2",
        text="In no event shall Vendor aggregate liability exceed total fees paid.",
        char_span=CharSpan(59, 127),
        masked_text="In no event shall [ORG_2] aggregate liability exceed total fees paid.",
    )
    root = ClauseNode(
        clause_id="root",
        text="",
        char_span=CharSpan(0, 0),
        children=[c1, c2],
    )
    full = f"{c1.text}\n{c2.text}"
    return DocumentEnvelope(
        doc_id="test_doc",
        filename="test_doc.txt",
        full_text=full,
        tree=root,
    )


def test_normalize_text():
    raw = "  The   Client   shall   pay  \n  all   invoices.  "
    norm = normalize_text(raw)
    assert norm == "the client shall pay all invoices."


def test_verify_valid_claim_passes():
    env = _make_sample_envelope()
    node = env.tree.children[0]
    claim = LlmClaim(
        quoted_text="shall pay all invoices within thirty (30) days",
        clause_id="c1",
        explanation="Payment terms requirement",
    )
    node.llm_claims.append(claim)

    out = verify(env)

    assert len(out.tree.children[0].verified_claims) == 1
    assert out.tree.children[0].verified_claims[0].quoted_text == claim.quoted_text


def test_verify_whitespace_case_normalization():
    env = _make_sample_envelope()
    node = env.tree.children[0]
    # Quote with different casing & newlines
    claim = LlmClaim(
        quoted_text="SHALL PAY   ALL INVOICES\nWITHIN THIRTY (30) DAYS",
        clause_id="c1",
        explanation="Payment terms",
    )
    node.llm_claims.append(claim)

    out = verify(env)

    assert len(out.tree.children[0].verified_claims) == 1


def test_verify_fabricated_quote_rejected(tmp_path: Path):
    env = _make_sample_envelope()
    node = env.tree.children[0]
    # Completely fabricated quote not in document
    claim = LlmClaim(
        quoted_text="Vendor guarantees 99.99% uptime SLA under all circumstances.",
        clause_id="c1",
        explanation="Fabricated SLA claim",
    )
    node.llm_claims.append(claim)

    log_file = tmp_path / "verify_rejects.log"
    config = {"paths": {"debug_log": str(log_file)}}

    out = verify(env, config=config)

    # Must be dropped from verified claims
    assert len(out.tree.children[0].verified_claims) == 0

    # Must be logged to debug file
    assert log_file.exists()
    log_text = log_file.read_text(encoding="utf-8")
    assert "Fabricated quote" in log_text
    assert "Vendor guarantees 99.99% uptime" in log_text


def test_verify_wrong_clause_id_rejected(tmp_path: Path):
    env = _make_sample_envelope()
    node = env.tree.children[0]
    # Quote exists in c2, but claimed to belong to c1
    claim = LlmClaim(
        quoted_text="aggregate liability exceed total fees paid",
        clause_id="c1",
        explanation="Misattributed clause ID",
    )
    node.llm_claims.append(claim)

    log_file = tmp_path / "verify_rejects.log"
    config = {"paths": {"debug_log": str(log_file)}}

    out = verify(env, config=config)

    assert len(out.tree.children[0].verified_claims) == 0
    log_text = log_file.read_text(encoding="utf-8")
    assert "does not match clause 'c1'" in log_text


def test_verify_empty_quote_rejected():
    env = _make_sample_envelope()
    node = env.tree.children[0]
    claim = LlmClaim(quoted_text="", clause_id="c1", explanation="Empty quote")
    node.llm_claims.append(claim)

    out = verify(env)

    assert len(out.tree.children[0].verified_claims) == 0
