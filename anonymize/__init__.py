"""NER + entity masking + entity_map (Phase 2).

Anonymization writes ``masked_text`` only. Source ``text`` and ``char_span``
remain untouched so verify can ground claims against the original tree.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, Optional, Sequence

from config import load_config
from models.clause import ClauseNode, DocumentEnvelope

DEFAULT_LABELS = frozenset({"PERSON", "ORG", "MONEY", "GPE", "DATE"})


@dataclass(frozen=True)
class EntityHit:
    """Character span of an entity within a single node's ``text``."""

    start: int
    end: int
    label: str
    surface: str


@lru_cache(maxsize=2)
def _load_nlp(model_name: str):
    import spacy

    try:
        return spacy.load(model_name)
    except OSError as exc:
        raise RuntimeError(
            f"spaCy model {model_name!r} is not installed. "
            f"Run: python -m spacy download {model_name}"
        ) from exc


def get_nlp(model_name: str = "en_core_web_sm"):
    """Return a cached spaCy pipeline."""
    return _load_nlp(model_name)


def anonymize(
    envelope: DocumentEnvelope,
    *,
    config: Optional[dict] = None,
    nlp=None,
) -> DocumentEnvelope:
    """Mask PII/entities across the clause tree.

    Same surface string maps to the same token document-wide. ``entity_map``
    stores ``token -> original`` for session-local deanonymization.
    """
    cfg = config or load_config()
    anon_cfg = cfg.get("anonymize") or {}
    model_name = str(anon_cfg.get("model", "en_core_web_sm"))
    labels = frozenset(anon_cfg.get("labels") or DEFAULT_LABELS)

    pipeline = nlp if nlp is not None else get_nlp(model_name)

    # First pass: discover entities per node (overlaps resolved locally).
    node_hits: dict[str, list[EntityHit]] = {}
    for node in envelope.tree.iter_nodes():
        if not node.text:
            node_hits[node.clause_id] = []
            continue
        hits = extract_entities(node.text, pipeline, labels=labels)
        node_hits[node.clause_id] = resolve_overlaps(hits)

    # Assign stable tokens: first-seen surface form wins (case-sensitive).
    surface_to_token: dict[str, str] = {}
    entity_map: dict[str, str] = {}
    counters: dict[str, int] = {}

    for node in envelope.tree.iter_nodes():
        for hit in node_hits.get(node.clause_id, []):
            if hit.surface in surface_to_token:
                continue
            counters[hit.label] = counters.get(hit.label, 0) + 1
            token = f"[{hit.label}_{counters[hit.label]}]"
            surface_to_token[hit.surface] = token
            entity_map[token] = hit.surface

    # Second pass: write masked_text; never mutate text / char_span.
    # Replace every occurrence of known surfaces (not only NER hit spans) so
    # the same string never leaks elsewhere in the tree.
    for node in envelope.tree.iter_nodes():
        if not node.text:
            node.masked_text = ""
            continue
        node.masked_text = apply_masks(node.text, surface_to_token)

    envelope.entity_map = entity_map
    return envelope


def extract_entities(
    text: str,
    nlp,
    *,
    labels: frozenset[str] = DEFAULT_LABELS,
) -> list[EntityHit]:
    """Run spaCy NER and keep only configured entity labels."""
    if not text.strip():
        return []
    doc = nlp(text)
    hits: list[EntityHit] = []
    for ent in doc.ents:
        if ent.label_ not in labels:
            continue
        surface = ent.text
        if not surface.strip():
            continue
        hits.append(
            EntityHit(
                start=ent.start_char,
                end=ent.end_char,
                label=ent.label_,
                surface=surface,
            )
        )
    return hits


def resolve_overlaps(hits: Sequence[EntityHit]) -> list[EntityHit]:
    """Drop overlapping spans, preferring earlier then longer matches."""
    ordered = sorted(hits, key=lambda h: (h.start, -(h.end - h.start)))
    accepted: list[EntityHit] = []
    last_end = -1
    for hit in ordered:
        if hit.start < last_end:
            continue
        accepted.append(hit)
        last_end = hit.end
    return accepted


def apply_masks(text: str, surface_to_token: dict[str, str]) -> str:
    """Replace every known entity surface with its token (longest-first).

    Longest-first avoids partial clobbering when one surface is a substring of
    another (e.g. ``Acme`` vs ``Acme Corporation``).
    """
    if not surface_to_token or not text:
        return text
    masked = text
    for surface in sorted(surface_to_token.keys(), key=len, reverse=True):
        token = surface_to_token[surface]
        if surface:
            masked = masked.replace(surface, token)
    return masked


def apply_masks_at_spans(
    text: str,
    hits: Sequence[EntityHit],
    surface_to_token: dict[str, str],
) -> str:
    """Span-precise replace (right-to-left). Prefer ``apply_masks`` for safety."""
    if not hits:
        return text
    chars = text
    for hit in sorted(hits, key=lambda h: h.start, reverse=True):
        token = surface_to_token.get(hit.surface)
        if token is None:
            continue
        if chars[hit.start : hit.end] == hit.surface:
            chars = chars[: hit.start] + token + chars[hit.end :]
        else:
            chars = chars.replace(hit.surface, token, 1)
    return chars


def build_llm_payload(node: ClauseNode) -> str:
    """Return the only string allowed in LLM prompts for this clause."""
    if node.masked_text is None:
        raise ValueError(
            f"Clause {node.clause_id!r} has no masked_text; run anonymize() first."
        )
    return node.masked_text


def assert_no_raw_entities(payload: str, entity_map: dict[str, str]) -> None:
    """Raise if any original entity string from ``entity_map`` appears in payload."""
    leaked = [
        original
        for original in entity_map.values()
        if original and original in payload
    ]
    if leaked:
        raise AssertionError(
            "Raw entity value(s) leaked into LLM payload: "
            + ", ".join(repr(v) for v in leaked)
        )


def collect_llm_payloads(envelope: DocumentEnvelope) -> list[str]:
    """Gather masked payloads for every non-empty node (LLM input surface)."""
    payloads: list[str] = []
    for node in envelope.tree.iter_nodes():
        if not node.text:
            continue
        payloads.append(build_llm_payload(node))
    return payloads


def mask_entities_in_texts(
    texts: Iterable[str],
    *,
    nlp=None,
    labels: frozenset[str] = DEFAULT_LABELS,
    model_name: str = "en_core_web_sm",
) -> tuple[list[str], dict[str, str]]:
    """Utility: mask a list of strings with a shared entity_map."""
    pipeline = nlp if nlp is not None else get_nlp(model_name)
    text_list = list(texts)
    all_hits = [
        resolve_overlaps(extract_entities(t, pipeline, labels=labels))
        for t in text_list
    ]
    surface_to_token: dict[str, str] = {}
    entity_map: dict[str, str] = {}
    counters: dict[str, int] = {}
    for hits in all_hits:
        for hit in hits:
            if hit.surface in surface_to_token:
                continue
            counters[hit.label] = counters.get(hit.label, 0) + 1
            token = f"[{hit.label}_{counters[hit.label]}]"
            surface_to_token[hit.surface] = token
            entity_map[token] = hit.surface
    masked = [apply_masks(t, surface_to_token) for t in text_list]
    return masked, entity_map


__all__ = [
    "DEFAULT_LABELS",
    "EntityHit",
    "anonymize",
    "apply_masks",
    "apply_masks_at_spans",
    "assert_no_raw_entities",
    "build_llm_payload",
    "collect_llm_payloads",
    "extract_entities",
    "get_nlp",
    "mask_entities_in_texts",
    "resolve_overlaps",
]
