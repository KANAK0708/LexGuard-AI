"""Clause vectorization + caching (Phase 3)."""

from __future__ import annotations

import hashlib
import re
from typing import Dict, Optional
import numpy as np

from models.clause import ClauseNode, DocumentEnvelope

# In-memory vector store mapping embedding_id -> np.ndarray
_VECTOR_STORE: Dict[str, np.ndarray] = {}

def _compute_text_vector(text: str, dim: int = 128) -> np.ndarray:
    if not text or not text.strip():
        return np.zeros(dim, dtype=np.float32)

    clean_text = text.lower()
    words = re.findall(r'\w+', clean_text)
    vec = np.zeros(dim, dtype=np.float32)
    
    for word in words:
        h = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if ((h >> 8) & 1) == 1 else -1.0
        vec[idx] += sign

    for i in range(max(0, len(clean_text) - 2)):
        ngram = clean_text[i:i+3]
        h = int(hashlib.sha256(ngram.encode('utf-8')).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if ((h >> 8) & 1) == 1 else -1.0
        vec[idx] += sign * 0.5

    norm = np.linalg.norm(vec)
    if norm > 1e-9:
        vec = vec / norm
    
    return vec

def get_embedding(embedding_id: str) -> Optional[np.ndarray]:
    return _VECTOR_STORE.get(embedding_id)

def clear_vector_store() -> None:
    _VECTOR_STORE.clear()

def cosine_similarity(v1: Optional[np.ndarray], v2: Optional[np.ndarray]) -> float:
    if v1 is None or v2 is None:
        return 0.0
    dot = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 < 1e-9 or norm2 < 1e-9:
        return 0.0
    val = float(dot / (norm1 * norm2))
    return max(-1.0, min(1.0, val))

def embed_document(envelope: DocumentEnvelope) -> DocumentEnvelope:
    nodes = envelope.tree.iter_nodes()
    for node in nodes:
        target_text = node.masked_text if node.masked_text is not None else node.text
        content_hash = hashlib.sha256(f"{node.clause_id}:{target_text}".encode('utf-8')).hexdigest()[:16]
        emb_id = f"emb_{node.clause_id}_{content_hash}"
        
        vec = _compute_text_vector(target_text)
        _VECTOR_STORE[emb_id] = vec
        node.embedding_id = emb_id

    return envelope

__all__ = [
    "embed_document",
    "get_embedding",
    "clear_vector_store",
    "cosine_similarity",
]
