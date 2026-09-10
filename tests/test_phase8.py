"""Unit test suite for Phase 8: Polish, Docs & Portfolio Packaging."""

from __future__ import annotations

import json
from pathlib import Path

from config import load_config
from eval import run_eval

_ROOT = Path(__file__).resolve().parents[1]


def test_readme_exists_and_contains_lexguard() -> None:
    """Verify README.md exists and contains LexGuard AI branding and architecture."""
    readme_path = _ROOT / "README.md"
    assert readme_path.exists(), "README.md must exist in root."
    content = readme_path.read_text(encoding="utf-8")
    assert "LexGuard AI" in content, "README.md must reference LexGuard AI."
    assert "Architecture & Pipeline Flow" in content, "README.md must contain architecture flow."


def test_portfolio_doc_exists() -> None:
    """Verify docs/PORTFOLIO.md exists and contains technical interview highlights."""
    portfolio_path = _ROOT / "docs" / "PORTFOLIO.md"
    assert portfolio_path.exists(), "docs/PORTFOLIO.md must exist."
    content = portfolio_path.read_text(encoding="utf-8")
    assert "Anonymize-Before-Generate" in content, "Portfolio doc must detail privacy invariant."
    assert "Anchor Verification Gate" in content, "Portfolio doc must detail verifier gate."


def test_eval_results_json_artifact_validity() -> None:
    """Verify eval/eval_results.json is generated and contains valid macro_f1 metrics."""
    res = run_eval()
    assert "macro_f1" in res, "Evaluation results must contain macro_f1 key."
    assert res["macro_f1"] >= 0.0, "Macro F1 must be non-negative."
    
    artifact_path = _ROOT / "eval" / "eval_results.json"
    assert artifact_path.exists(), "eval/eval_results.json artifact file must exist."
    data = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert "per_category" in data, "eval_results.json must contain per_category scores."


def test_config_loads_without_errors() -> None:
    """Verify config/config.yaml loads properly and contains model definitions."""
    cfg = load_config()
    assert isinstance(cfg, dict), "Loaded config must be a dictionary."
    assert "ollama" in cfg, "Config must specify ollama section."
    assert "score" in cfg, "Config must specify score section."
