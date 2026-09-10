"""Tests for Phase 6 Streamlit UI components and badge rendering."""

from __future__ import annotations

from ui import app, render_drift_badge, render_risk_badge, render_verified_badge


def test_render_risk_badge():
    high = render_risk_badge(0.85)
    assert "badge-high" in high
    assert "HIGH EXPOSURE" in high

    medium = render_risk_badge(0.50)
    assert "badge-medium" in medium
    assert "MODERATE RISK" in medium

    low = render_risk_badge(0.20)
    assert "badge-low" in low
    assert "LOW RISK" in low


def test_render_drift_badge():
    cosmetic = render_drift_badge("Cosmetic")
    assert "Minor Paraphrase" in cosmetic
    assert "drift-cosmetic" in cosmetic

    intent = render_drift_badge("IntentShift")
    assert "Obligation Shift" in intent
    assert "drift-intent" in intent

    rewrite = render_drift_badge("SubstantialRewrite")
    assert "Critical Redraft" in rewrite
    assert "drift-rewrite" in rewrite


def test_render_verified_badge():
    badge = render_verified_badge()
    assert "Fact-Checked & Attributed Quote" in badge


def test_ui_app_import():
    assert callable(app)
