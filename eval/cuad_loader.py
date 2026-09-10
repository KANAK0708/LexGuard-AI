"""CUAD dataset loader and sample benchmark annotation generator."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class CuadAnnotation:
    contract_title: str
    category: str
    text: str
    start_char: int
    end_char: int


@dataclass
class CuadContract:
    title: str
    paragraphs: List[str]
    annotations: List[CuadAnnotation]


def generate_sample_cuad_data() -> Dict[str, Any]:
    """Generate representative CUAD format sample dataset for benchmark evaluation."""
    return {
        "version": "v1.0",
        "data": [
            {
                "title": "sample_agreement_1",
                "paragraphs": [
                    {
                        "context": "The Client shall indemnify and hold harmless Vendor against all third party claims.",
                        "qas": [
                            {
                                "question": "Indemnification",
                                "id": "q1",
                                "answers": [
                                    {
                                        "text": "indemnify and hold harmless Vendor against all third party claims",
                                        "answer_start": 17,
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "context": "In no event shall aggregate liability exceed total fees paid under this agreement.",
                        "qas": [
                            {
                                "question": "Limitation of Liability",
                                "id": "q2",
                                "answers": [
                                    {
                                        "text": "In no event shall aggregate liability exceed total fees paid",
                                        "answer_start": 0,
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "context": "Either party may terminate this agreement upon thirty (30) days written notice.",
                        "qas": [
                            {
                                "question": "Termination for Convenience",
                                "id": "q3",
                                "answers": [
                                    {
                                        "text": "terminate this agreement upon thirty (30) days written notice",
                                        "answer_start": 17,
                                    }
                                ],
                            }
                        ],
                    },
                ],
            }
        ],
    }


def load_cuad_dataset(path: Optional[Path] = None) -> List[CuadContract]:
    """Load CUAD format JSON dataset into structured CuadContract objects."""
    if path is None or not path.exists():
        raw_data = generate_sample_cuad_data()
    else:
        raw_data = json.loads(path.read_text(encoding="utf-8"))

    contracts: List[CuadContract] = []
    for item in raw_data.get("data", []):
        title = item.get("title", "untitled")
        paragraphs_text: List[str] = []
        annotations: List[CuadAnnotation] = []

        for p in item.get("paragraphs", []):
            context = p.get("context", "")
            paragraphs_text.append(context)
            for qa in p.get("qas", []):
                cat = qa.get("question", "")
                for ans in qa.get("answers", []):
                    ans_text = ans.get("text", "")
                    start = ans.get("answer_start", 0)
                    annotations.append(
                        CuadAnnotation(
                            contract_title=title,
                            category=cat,
                            text=ans_text,
                            start_char=start,
                            end_char=start + len(ans_text),
                        )
                    )

        contracts.append(
            CuadContract(
                title=title,
                paragraphs=paragraphs_text,
                annotations=annotations,
            )
        )

    return contracts
