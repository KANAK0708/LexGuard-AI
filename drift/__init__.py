"""Cross-version clause matching + similarity classification (Phase 3)."""

from __future__ import annotations

from typing import List, Optional
from models.clause import DocumentEnvelope, DriftResult, DriftLabel
from embed import embed_document, get_embedding, cosine_similarity

def compare(left: DocumentEnvelope, right: DocumentEnvelope) -> List[DriftResult]:
    """
    Matches clauses across document versions and classifies semantic drift.
    """
    if not any(node.embedding_id for node in left.tree.iter_nodes()):
        embed_document(left)
    if not any(node.embedding_id for node in right.tree.iter_nodes()):
        embed_document(right)

    left_nodes = [n for n in left.tree.iter_nodes() if n.text or n.clause_id != 'root']
    right_nodes = [n for n in right.tree.iter_nodes() if n.text or n.clause_id != 'root']

    matched_right_ids = set()
    results: List[DriftResult] = []

    for l_node in left_nodes:
        l_vec = get_embedding(l_node.embedding_id) if l_node.embedding_id else None
        
        best_match = None
        best_score = -1.0
        
        # 1. Exact clause_id match
        for r_node in right_nodes:
            if r_node.clause_id == l_node.clause_id:
                r_vec = get_embedding(r_node.embedding_id) if r_node.embedding_id else None
                sim = cosine_similarity(l_vec, r_vec)
                best_match = r_node
                best_score = sim
                break

        # 2. Maximum vector similarity match
        if best_match is None:
            for r_node in right_nodes:
                r_vec = get_embedding(r_node.embedding_id) if r_node.embedding_id else None
                sim = cosine_similarity(l_vec, r_vec)
                if sim > best_score:
                    best_score = sim
                    best_match = r_node

        if best_match is not None and best_score >= 0.3:
            matched_right_ids.add(best_match.clause_id)
            right_cid = best_match.clause_id
            cos_val = float(best_score)

            if cos_val >= 0.95:
                label: DriftLabel = 'Cosmetic'
            elif cos_val >= 0.70:
                label = 'IntentShift'
            else:
                label = 'SubstantialRewrite'

            results.append(
                DriftResult(
                    left_clause_id=l_node.clause_id,
                    right_clause_id=right_cid,
                    cosine=cos_val,
                    label=label
                )
            )
        else:
            results.append(
                DriftResult(
                    left_clause_id=l_node.clause_id,
                    right_clause_id=None,
                    cosine=None,
                    label='Unmatched'
                )
            )

    # Added clauses in right document
    for r_node in right_nodes:
        if r_node.clause_id not in matched_right_ids:
            results.append(
                DriftResult(
                    left_clause_id=r_node.clause_id,
                    right_clause_id=None,
                    cosine=None,
                    label='Unmatched'
                )
            )

    return results

__all__ = ['compare']
