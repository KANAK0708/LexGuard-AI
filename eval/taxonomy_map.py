"""Taxonomy mapping between Stanford CUAD categories and LexGuard AI categories."""

from __future__ import annotations

from typing import Dict

# Map Stanford CUAD 41-category labels to LexGuard AI internal categories
CUAD_TO_LEXGUARD_MAP: Dict[str, str] = {
    # Indemnity & Liability
    "Indemnification": "Indemnification",
    "Limitation of Liability": "LimitationOfLiability",
    "Cap on Liability": "LimitationOfLiability",
    "Liquidated Damages": "LimitationOfLiability",
    
    # Termination & Duration
    "Termination for Convenience": "Termination",
    "Right of First Refusal": "Termination",
    "Expiration Date": "Termination",
    "Notice Period To Terminate Renewal": "Termination",

    # Intellectual Property
    "IP Ownership": "IPOwnership",
    "License Grant": "IPOwnership",
    "Non-Transferable License": "IPOwnership",
    "Affiliate License-Licensor": "IPOwnership",
    
    # Restrictive Covenants
    "Non-Compete": "NonCompete",
    "Non-Solicitation": "NonCompete",
    "Exclusivity": "NonCompete",

    # Warranties & Disclaimers
    "Warranty": "Warranty",
    "Warranty Disclaimer": "Warranty",
    
    # Financial & Payment
    "Payment Terms": "PaymentTerms",
    "Price Restriction": "PaymentTerms",

    # Governing Law
    "Governing Law": "GoverningLaw",
}



def map_cuad_category(cuad_label: str) -> str:
    """Map a CUAD category label to LexGuard AI internal taxonomy."""
    clean = cuad_label.strip()
    return CUAD_TO_LEXGUARD_MAP.get(clean, "General")
