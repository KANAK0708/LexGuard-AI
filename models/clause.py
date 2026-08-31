"""Canonical clause-tree and document envelope schemas.

Character spans on source ``text`` must survive anonymization so verify can
match quoted claims against the original tree. LLM modules may only consume
``masked_text``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any, Literal, Optional

Confidence = Literal["high", "low"]
ParserMode = Literal["layout", "paragraph_fallback"]
DriftLabel = Literal["Cosmetic", "IntentShift", "SubstantialRewrite", "Unmatched"]


@dataclass
class CharSpan:
    start: int
    end: int

    def to_dict(self) -> dict[str, int]:
        return {"start": self.start, "end": self.end}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CharSpan:
        return cls(start=int(data["start"]), end=int(data["end"]))


@dataclass
class LlmClaim:
    quoted_text: str
    clause_id: str
    explanation: str = ""
    claim_type: str = "risk"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LlmClaim:
        return cls(
            quoted_text=str(data.get("quoted_text", "")),
            clause_id=str(data.get("clause_id", "")),
            explanation=str(data.get("explanation", "")),
            claim_type=str(data.get("claim_type", "risk")),
        )


@dataclass
class ClauseNode:
    clause_id: str
    text: str
    char_span: CharSpan
    masked_text: Optional[str] = None
    category: Optional[str] = None
    page: Optional[int] = None
    confidence: Confidence = "high"
    children: list[ClauseNode] = field(default_factory=list)
    embedding_id: Optional[str] = None
    risk_score: Optional[float] = None
    role_weights_applied: Optional[dict[str, float]] = None
    llm_claims: list[LlmClaim] = field(default_factory=list)
    verified_claims: list[LlmClaim] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "clause_id": self.clause_id,
            "text": self.text,
            "masked_text": self.masked_text,
            "category": self.category,
            "char_span": self.char_span.to_dict(),
            "page": self.page,
            "confidence": self.confidence,
            "children": [c.to_dict() for c in self.children],
            "embedding_id": self.embedding_id,
            "risk_score": self.risk_score,
            "role_weights_applied": self.role_weights_applied,
            "llm_claims": [c.to_dict() for c in self.llm_claims],
            "verified_claims": [c.to_dict() for c in self.verified_claims],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ClauseNode:
        return cls(
            clause_id=str(data["clause_id"]),
            text=str(data["text"]),
            char_span=CharSpan.from_dict(data["char_span"]),
            masked_text=data.get("masked_text"),
            category=data.get("category"),
            page=data.get("page"),
            confidence=data.get("confidence", "high"),
            children=[cls.from_dict(c) for c in data.get("children", [])],
            embedding_id=data.get("embedding_id"),
            risk_score=data.get("risk_score"),
            role_weights_applied=data.get("role_weights_applied"),
            llm_claims=[LlmClaim.from_dict(c) for c in data.get("llm_claims", [])],
            verified_claims=[
                LlmClaim.from_dict(c) for c in data.get("verified_claims", [])
            ],
        )

    def iter_nodes(self) -> list[ClauseNode]:
        """Depth-first flatten of this node and descendants."""
        nodes = [self]
        for child in self.children:
            nodes.extend(child.iter_nodes())
        return nodes


@dataclass
class DocumentEnvelope:
    doc_id: str
    filename: str
    full_text: str
    tree: ClauseNode
    entity_map: dict[str, str] = field(default_factory=dict)
    parser_mode: ParserMode = "layout"
    role: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "filename": self.filename,
            "full_text": self.full_text,
            "tree": self.tree.to_dict(),
            "entity_map": self.entity_map,
            "parser_mode": self.parser_mode,
            "role": self.role,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocumentEnvelope:
        return cls(
            doc_id=str(data["doc_id"]),
            filename=str(data["filename"]),
            full_text=str(data["full_text"]),
            tree=ClauseNode.from_dict(data["tree"]),
            entity_map=dict(data.get("entity_map") or {}),
            parser_mode=data.get("parser_mode", "layout"),
            role=data.get("role"),
        )

    def span_text(self, node: ClauseNode) -> str:
        """Return ``full_text[char_span]`` for integrity checks."""
        return self.full_text[node.char_span.start : node.char_span.end]


@dataclass
class DriftResult:
    left_clause_id: str
    right_clause_id: Optional[str]
    cosine: Optional[float]
    label: DriftLabel

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DriftResult:
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})
