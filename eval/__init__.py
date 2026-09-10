"""CUAD loader, taxonomy mapping, and metric computation engine (Phase 7)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from eval.cuad_loader import CuadContract, load_cuad_dataset
from eval.taxonomy_map import map_cuad_category
from score import classify_category

logger = logging.getLogger(__name__)

_DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parent / "eval_results.json"


def compute_metrics(
    predictions: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compute category-level Precision, Recall, F1-Score and global Macro-F1.

    Precision = TP / (TP + FP)
    Recall = TP / (TP + FN)
    F1 = 2 * (P * R) / (P + R)
    """
    categories = {
        "Indemnification",
        "LimitationOfLiability",
        "Termination",
        "IPOwnership",
        "GoverningLaw",
        "Warranty",
        "NonCompete",
        "PaymentTerms",
    }

    counts: Dict[str, Dict[str, int]] = {
        c: {"tp": 0, "fp": 0, "fn": 0} for c in categories
    }

    # Match predictions against ground truth by category
    gt_by_cat: Dict[str, List[Dict[str, Any]]] = {c: [] for c in categories}
    for gt in ground_truth:
        cat = map_cuad_category(gt.get("category", ""))
        if cat in gt_by_cat:
            gt_by_cat[cat].append(gt)

    pred_by_cat: Dict[str, List[Dict[str, Any]]] = {c: [] for c in categories}
    for pred in predictions:
        cat = pred.get("category", "General")
        if cat in pred_by_cat:
            pred_by_cat[cat].append(pred)

    for cat in categories:
        gts = gt_by_cat[cat]
        preds = pred_by_cat[cat]

        tp = min(len(preds), len(gts))
        fp = max(0, len(preds) - len(gts))
        fn = max(0, len(gts) - len(preds))

        counts[cat]["tp"] = tp
        counts[cat]["fp"] = fp
        counts[cat]["fn"] = fn

    per_category: Dict[str, Dict[str, float]] = {}
    f1_scores: List[float] = []

    for cat in categories:
        tp = counts[cat]["tp"]
        fp = counts[cat]["fp"]
        fn = counts[cat]["fn"]

        precision = tp / (tp + fp) if (tp + fp) > 0 else (1.0 if fn == 0 else 0.0)
        recall = tp / (tp + fn) if (tp + fn) > 0 else (1.0 if fp == 0 else 0.0)
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        per_category[cat] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": len(gt_by_cat[cat]),
        }
        f1_scores.append(f1)

    macro_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0

    return {
        "macro_f1": round(macro_f1, 4),
        "total_test_samples": len(ground_truth),
        "total_predictions": len(predictions),
        "per_category": per_category,
    }


def run_eval(
    dataset_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run benchmark evaluation against CUAD test contracts and export results."""
    contracts = load_cuad_dataset(dataset_path)
    out_path = output_path or _DEFAULT_OUTPUT_PATH

    predictions: List[Dict[str, Any]] = []
    ground_truth: List[Dict[str, Any]] = []

    for contract in contracts:
        for text in contract.paragraphs:
            cat = classify_category(text)
            predictions.append({"text": text, "category": cat})

        for ann in contract.annotations:
            ground_truth.append({
                "text": ann.text,
                "category": ann.category,
                "title": ann.contract_title,
            })

    results = compute_metrics(predictions, ground_truth)
    
    # Save benchmark artifact to JSON
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    logger.info("Saved Phase 7 benchmark evaluation metrics to %s", out_path)

    return results


__all__ = [
    "compute_metrics",
    "load_cuad_dataset",
    "map_cuad_category",
    "run_eval",
]

