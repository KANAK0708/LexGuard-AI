"""Prompt construction, Ollama client, strict JSON parsing (Phase 4)."""

from __future__ import annotations

from models.clause import DocumentEnvelope


def analyze(envelope: DocumentEnvelope) -> DocumentEnvelope:
    """Run local LLM on masked text only. Stub until Phase 4."""
    raise NotImplementedError("llm/ will be implemented in Phase 4")
