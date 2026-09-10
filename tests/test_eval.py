"""Tests for Phase 7 CUAD benchmark evaluation and metric computation."""

from __future__ import annotations

import json
from pathlib import Path

from eval import compute_metrics, load_cuad_dataset, map_cuad_category, run_eval


def test_map_cuad_category():
    assert map_cuad_category("Indemnification") == "Indemnification"
    assert map_cuad_category("Limitation of Liability") == "LimitationOfLiability"
    assert map_cuad_category("Termination for Convenience") == "Termination"
    assert map_cuad_category("IP Ownership") == "IPOwnership"
    assert map_cuad_category("Unknown Label") == "General"


def test_compute_metrics_calculation():
    preds = [
        {"text": "clause 1", "category": "Indemnification"},
        {"text": "clause 2", "category": "LimitationOfLiability"},
        {"text": "clause 3", "category": "Termination"},
    ]
    gt = [
        {"text": "clause 1", "category": "Indemnification"},
        {"text": "clause 2", "category": "Limitation of Liability"},
        {"text": "clause 3", "category": "Termination for Convenience"},
    ]

    metrics = compute_metrics(preds, gt)

    assert "macro_f1" in metrics
    assert metrics["macro_f1"] > 0.0
    assert "per_category" in metrics
    assert "Indemnification" in metrics["per_category"]
    assert metrics["per_category"]["Indemnification"]["f1"] == 1.0


def test_run_eval_generates_artifact(tmp_path: Path):
    out_file = tmp_path / "eval_results.json"
    results = run_eval(output_path=out_file)

    assert out_file.exists()
    assert "macro_f1" in results
    
    file_data = json.loads(out_file.read_text(encoding="utf-8"))
    assert "macro_f1" in file_data
    assert "per_category" in file_data
