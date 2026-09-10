"""Anchor verification against source tree (Phase 5)."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Optional, Tuple

from config import load_config
from models.clause import ClauseNode, DocumentEnvelope, LlmClaim

logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """Normalize whitespace, case, and punctuation for reliable substring matching."""
    if not text:
        return ""
    # Collapse multiline/extra whitespace to a single space and convert to lowercase
    collapsed = re.sub(r"\s+", " ", text.strip()).lower()
    return collapsed


def verify_claim(
    claim: LlmClaim,
    node: ClauseNode,
    envelope: DocumentEnvelope,
) -> Tuple[bool, str]:
    """Deterministically check if a claim's quoted_text is anchored in the source tree."""
    if not claim.quoted_text or not claim.quoted_text.strip():
        return False, "Empty quoted_text in claim"

    target_node: Optional[ClauseNode] = None
    if claim.clause_id:
        for n in envelope.tree.iter_nodes():
            if n.clause_id == claim.clause_id:
                target_node = n
                break

    if target_node is None:
        target_node = node

    norm_quote = normalize_text(claim.quoted_text)
    norm_source_text = normalize_text(target_node.text)
    norm_masked_text = normalize_text(target_node.masked_text or "")

    # Exact or normalized substring match against source text or masked text
    if norm_quote in norm_source_text or (norm_masked_text and norm_quote in norm_masked_text):
        return True, "Verified"

    # Also check if quote matches anywhere in the document full_text
    norm_full_text = normalize_text(envelope.full_text)
    if norm_quote in norm_full_text:
        # Quote is in document, but associated with wrong clause ID
        return False, f"Quote exists in document but does not match clause '{target_node.clause_id}' text"

    return False, f"Fabricated quote not present in source text for clause '{target_node.clause_id}'"


def log_rejected_claim(
    claim: LlmClaim,
    reason: str,
    doc_id: str,
    log_path: Path,
) -> None:
    """Log unverified / hallucinated claims to local debug file for developer review."""
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_entry = (
            f"[REJECTED CLAIM] doc_id={doc_id} clause_id={claim.clause_id!r} "
            f"reason={reason!r} quoted_text={claim.quoted_text!r}\n"
        )
        with log_path.open("a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as exc:
        logger.warning("Failed to log rejected claim to %s: %s", log_path, exc)


def verify(
    envelope: DocumentEnvelope,
    config: Optional[dict[str, Any]] = None,
) -> DocumentEnvelope:
    """Deterministic quote check gate; filter unverified claims and log rejections."""
    if config is None:
        try:
            config = load_config()
        except Exception:
            config = {}

    paths_cfg = config.get("paths", {})
    debug_log = Path(paths_cfg.get("debug_log", ".cache/verify_rejects.log"))

    for node in envelope.tree.iter_nodes():
        verified_list: list[LlmClaim] = []
        for claim in node.llm_claims:
            is_valid, reason = verify_claim(claim, node, envelope)
            if is_valid:
                verified_list.append(claim)
            else:
                log_rejected_claim(claim, reason, envelope.doc_id, debug_log)

        node.verified_claims = verified_list

    return envelope


__all__ = [
    "log_rejected_claim",
    "normalize_text",
    "verify",
    "verify_claim",
]

