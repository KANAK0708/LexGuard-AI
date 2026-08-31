"""Tests for Phase 3 vector embedding module."""

from __future__ import annotations

import pytest
import numpy as np
from models.clause import CharSpan, ClauseNode, DocumentEnvelope
from embed import embed_document, get_embedding, cosine_similarity, clear_vector_store

@pytest.fixture(autouse=True)
def _reset_store():
    clear_vector_store()

def test_embed_document_attaches_embeddings():
    node1 = ClauseNode(clause_id="c1", text="Acme Corporation agrees to pay ,000.", char_span=CharSpan(0, 40))
    node2 = ClauseNode(clause_id="c2", text="Confidential Information includes trade secrets.", char_span=CharSpan(41, 90))
    tree = ClauseNode(clause_id="root", text="", char_span=CharSpan(0, 0), children=[node1, node2])
    
    envelope = DocumentEnvelope(doc_id="d1", filename="test.txt", full_text="", tree=tree)
    
    out = embed_document(envelope)
    assert node1.embedding_id is not None
    assert node2.embedding_id is not None
    assert node1.embedding_id != node2.embedding_id

    vec1 = get_embedding(node1.embedding_id)
    vec2 = get_embedding(node2.embedding_id)
    
    assert vec1 is not None
    assert vec2 is not None
    assert isinstance(vec1, np.ndarray)
    assert vec1.shape == (128,)

def test_cosine_similarity():
    v1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    v2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    v3 = np.array([0.0, 1.0, 0.0], dtype=np.float32)

    assert abs(cosine_similarity(v1, v2) - 1.0) < 1e-5
    assert abs(cosine_similarity(v1, v3) - 0.0) < 1e-5
