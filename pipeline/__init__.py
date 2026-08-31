"""Pipeline orchestrator - single entrypoint for the analysis flow."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Union

from anonymize import anonymize
from embed import embed_document
from drift import compare
from parser import parse_file
from score import score_document

PathLike = Union[str, Path]


def run(
    file_path: PathLike,
    role: str = "Client",
    file_v2: Optional[PathLike] = None,
) -> dict[str, Any]:
    """Run the available pipeline stages and return a JSON-serializable result.

    Phase 0-4: ingest -> parse -> anonymize -> embed -> score -> drift comparison.
    """
    envelope = anonymize(parse_file(file_path, role=role))
    envelope = embed_document(envelope)
    envelope = score_document(envelope, role=role)

    result: dict[str, Any] = {
        "document": envelope.to_dict(),
        "drift": [],
        "status": "anonymized",
        "role": role,
    }

    if file_v2 is not None:
        envelope_v2 = anonymize(parse_file(file_v2, role=role))
        envelope_v2 = embed_document(envelope_v2)
        envelope_v2 = score_document(envelope_v2, role=role)
        drift_results = compare(envelope, envelope_v2)
        result["document_v2"] = envelope_v2.to_dict()
        result["drift"] = [d.to_dict() for d in drift_results]
        result["status"] = "anonymized_pair"

    return result
