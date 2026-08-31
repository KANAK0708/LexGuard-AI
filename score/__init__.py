"""Asymmetric Role-Weighted Risk Scoring Module (Phase 4)."""

from __future__ import annotations

import re
from typing import Dict, Any, Optional
from models.clause import ClauseNode, DocumentEnvelope

CATEGORY_PATTERNS = {
    "Indemnification": [r"\bindemnif\w*", r"\bhold harmless\b", r"\bdefend and hold\b"],
    "LimitationOfLiability": [r"\blimitation of liability\b", r"\bconsequential damages\b", r"\baggregate liability\b", r"\bcap on liability\b", r"\bin no event shall\b"],
    "NonCompete": [r"\bnon-compete\b", r"\bnoncompete\b", r"\brestrictive covenant\b", r"\bnon-solicit\b", r"\bsolicit customers\b"],
    "IPOwnership": [r"\bintellectual property\b", r"\bwork for hire\b", r"\bassigns? all rights\b", r"\bpatent\b", r"\btrademark\b", r"\bcopyright\b"],
    "Termination": [r"\bterminate\b", r"\btermination\b", r"\bcancel(?:lation)?\b", r"\bnotice period\b"],
    "PaymentTerms": [r"\bpayments?\b", r"\binvoices?\b", r"\bfees?\b", r"\binterest rate\b", r"\blate fee\b", r"\bpaid\b", r"\bpayable\b"],
    "Warranty": [r"\bwarrant\w*\b", r"\bdisclaim\w*\b", r"\bas is\b", r"\bfitness for a particular\b"],
}

ROLE_WEIGHT_MATRIX: Dict[str, Dict[str, float]] = {
    "Employee": {
        "NonCompete": 2.0,
        "IPOwnership": 1.8,
        "Termination": 1.7,
        "Indemnification": 1.5,
        "LimitationOfLiability": 1.2,
        "PaymentTerms": 1.1,
        "Warranty": 1.0,
        "General": 1.0,
    },
    "Employer": {
        "IPOwnership": 1.5,
        "Termination": 1.2,
        "NonCompete": 1.1,
        "Indemnification": 1.3,
        "LimitationOfLiability": 1.3,
        "PaymentTerms": 1.0,
        "Warranty": 1.0,
        "General": 1.0,
    },
    "Vendor": {
        "LimitationOfLiability": 1.8,
        "Indemnification": 1.5,
        "PaymentTerms": 1.4,
        "Warranty": 1.2,
        "Termination": 1.3,
        "IPOwnership": 1.2,
        "NonCompete": 1.2,
        "General": 1.0,
    },
    "Client": {
        "Warranty": 1.8,
        "LimitationOfLiability": 1.5,
        "Indemnification": 1.4,
        "PaymentTerms": 1.2,
        "Termination": 1.2,
        "IPOwnership": 1.3,
        "NonCompete": 1.0,
        "General": 1.0,
    },
}

def classify_category(text: str) -> str:
    if not text:
        return "General"
    
    text_lower = text.lower()
    for cat, patterns in CATEGORY_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text_lower):
                return cat
                
    return "General"

def compute_base_risk(text: str, category: str) -> float:
    if not text or category == "General":
        return 0.2

    text_lower = text.lower()
    base_scores = {
        "Indemnification": 0.6,
        "LimitationOfLiability": 0.5,
        "NonCompete": 0.5,
        "IPOwnership": 0.5,
        "Termination": 0.4,
        "PaymentTerms": 0.3,
        "Warranty": 0.4,
    }
    
    score = base_scores.get(category, 0.2)
    
    high_risk_triggers = ["unlimited", "sole discretion", "immediately", "irrevocable", "liquidated damages", "waives", "all claims"]
    for trigger in high_risk_triggers:
        if trigger in text_lower:
            score += 0.15

    return min(1.0, score)

def score_document(envelope: DocumentEnvelope, role: str = "Client") -> DocumentEnvelope:
    envelope.role = role
    role_weights = ROLE_WEIGHT_MATRIX.get(role, ROLE_WEIGHT_MATRIX["Client"])

    for node in envelope.tree.iter_nodes():
        if not node.text and node.clause_id == "root":
            continue
            
        target_text = node.masked_text if node.masked_text is not None else node.text
        cat = classify_category(target_text)
        node.category = cat
        
        base_score = compute_base_risk(target_text, cat)
        multiplier = role_weights.get(cat, 1.0)
        
        final_score = min(1.0, round(base_score * multiplier, 3))
        node.risk_score = final_score
        node.role_weights_applied = {
            "base_score": base_score,
            "role_multiplier": multiplier,
            "role": role,
        }

    return envelope

__all__ = [
    "classify_category",
    "compute_base_risk",
    "score_document",
    "ROLE_WEIGHT_MATRIX",
]
