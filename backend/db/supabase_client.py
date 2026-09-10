"""Supabase Client integration for storing contracts, clauses, and risk audit logs."""

from __future__ import annotations

import os
import logging
from typing import Any, Dict, Optional

from config import load_config
from models.clause import DocumentEnvelope

logger = logging.getLogger(__name__)

# Lazy initialization of Supabase client
_supabase_client = None


def get_supabase_client():
    """Get or initialize Supabase client instance."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        try:
            cfg = load_config()
            supabase_cfg = cfg.get("supabase", {})
            url = url or supabase_cfg.get("url")
            key = key or supabase_cfg.get("key")
        except Exception:
            pass

    if url and key:
        try:
            from supabase import create_client
            _supabase_client = create_client(url, key)
            logger.info("Successfully connected to Supabase database.")
            return _supabase_client
        except Exception as exc:
            logger.warning("Failed to initialize Supabase client: %s", exc)

    return None


def save_document_envelope(envelope: DocumentEnvelope) -> bool:
    """Save processed DocumentEnvelope to Supabase PostgreSQL database."""
    client = get_supabase_client()
    if client is None:
        logger.info("Supabase client not configured; skipping database persistence.")
        return False

    try:
        data = envelope.to_dict()
        contract_record = {
            "doc_id": envelope.doc_id,
            "filename": envelope.filename,
            "full_text": envelope.full_text,
            "entity_map": envelope.entity_map,
            "parser_mode": envelope.parser_mode,
            "role": envelope.role or "Client",
        }
        client.table("contracts").upsert(contract_record).execute()

        # Insert clause records
        for node in envelope.tree.iter_nodes():
            if not node.text and node.clause_id == "root":
                continue

            clause_record = {
                "doc_id": envelope.doc_id,
                "clause_id": node.clause_id,
                "text": node.text,
                "masked_text": node.masked_text,
                "category": node.category,
                "confidence": node.confidence,
                "risk_score": node.risk_score,
                "role_weights_applied": node.role_weights_applied or {},
                "char_span": node.char_span.to_dict(),
            }
            res = client.table("clauses").insert(clause_record).execute()

            # Insert verified/LLM claims
            clause_db_id = res.data[0]["id"] if res.data and len(res.data) > 0 else None
            if clause_db_id:
                for claim in node.verified_claims:
                    client.table("llm_claims").insert({
                        "clause_db_id": clause_db_id,
                        "doc_id": envelope.doc_id,
                        "quoted_text": claim.quoted_text,
                        "explanation": claim.explanation,
                        "claim_type": claim.claim_type,
                        "is_verified": True,
                    }).execute()

        return True
    except Exception as exc:
        logger.error("Error saving envelope to Supabase: %s", exc)
        return False


def save_drift_comparison(
    left_doc_id: str,
    right_doc_id: str,
    role: str,
    drift_results: list[Dict[str, Any]],
) -> bool:
    """Save cross-version intent drift comparison results to Supabase."""
    client = get_supabase_client()
    if client is None:
        return False

    try:
        record = {
            "left_doc_id": left_doc_id,
            "right_doc_id": right_doc_id,
            "role": role,
            "drift_results": drift_results,
        }
        client.table("drift_comparisons").insert(record).execute()
        return True
    except Exception as exc:
        logger.error("Error saving drift comparison to Supabase: %s", exc)
        return False
