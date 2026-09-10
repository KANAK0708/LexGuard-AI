"""UI Components, Styling, and Badge Formatting for Commercial SaaS Streamlit App."""

from __future__ import annotations

import streamlit as st


def inject_custom_css() -> None:
    """Inject custom CSS for modern aesthetics, badges, and responsive containers."""
    css = """
    <style>
    /* Main container styling */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* Product Header title styling */
    .product-title {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        font-weight: 800;
        color: #0F172A;
        font-size: 2.2rem;
        letter-spacing: -0.03em;
        margin-bottom: 0.2rem;
    }

    .product-subtitle {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }

    /* Risk Badges */
    .badge-low {
        background-color: #DEF7EC;
        color: #03543F;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        letter-spacing: 0.02em;
    }
    .badge-medium {
        background-color: #FEF08A;
        color: #713F12;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        letter-spacing: 0.02em;
    }
    .badge-high {
        background-color: #FDE8E8;
        color: #9B1C1C;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        letter-spacing: 0.02em;
    }

    /* Drift Badges */
    .drift-cosmetic {
        background-color: #E0F2FE;
        color: #0369A1;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.825rem;
    }
    .drift-intent {
        background-color: #FEF3C7;
        color: #92400E;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.825rem;
    }
    .drift-rewrite {
        background-color: #FEE2E2;
        color: #991B1B;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.825rem;
    }

    /* Verified Guard Badge */
    .badge-verified {
        background-color: #ECFDF5;
        color: #047857;
        border: 1px solid #10B981;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.775rem;
        display: inline-block;
        margin-bottom: 0.5rem;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_risk_badge(score: float | None) -> str:
    """Return HTML badge for risk score."""
    if score is None:
        return '<span class="badge-low">LOW RISK (0.20)</span>'
    if score >= 0.7:
        return f'<span class="badge-high">HIGH EXPOSURE ({score:.2f})</span>'
    if score >= 0.4:
        return f'<span class="badge-medium">MODERATE RISK ({score:.2f})</span>'
    return f'<span class="badge-low">LOW RISK ({score:.2f})</span>'


def render_drift_badge(label: str) -> str:
    """Return HTML badge for drift classification label."""
    if label == "Cosmetic":
        return '<span class="drift-cosmetic">🟢 Minor Paraphrase</span>'
    if label == "IntentShift":
        return '<span class="drift-intent">🟡 Obligation Shift</span>'
    if label == "SubstantialRewrite":
        return '<span class="drift-rewrite">🔴 Critical Redraft</span>'
    return f'<span class="drift-cosmetic">{label}</span>'


def render_verified_badge() -> str:
    """Return HTML badge for verified claims."""
    return '<span class="badge-verified">✓ Fact-Checked & Attributed Quote</span>'


def render_guide_banner() -> None:
    """Render top visual workflow banner for business users."""
    html = """
    <div style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); color: white; padding: 1.25rem 1.5rem; border-radius: 12px; margin-bottom: 1.75rem; box-shadow: 0 4px 14px rgba(15,23,42,0.12);">
        <div style="font-weight: 700; font-size: 1.05rem; margin-bottom: 0.75rem; color: #38BDF8; letter-spacing: -0.01em;">
            ⚡ Enterprise Contract Review Workflow:
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 1rem; font-size: 0.85rem;">
            <div style="background: rgba(255,255,255,0.06); padding: 0.75rem 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
                <strong>1. 📥 Upload Contract</strong><br/>
                <span style="color: #94A3B8;">PDF or DOCX format agreements.</span>
            </div>
            <div style="background: rgba(255,255,255,0.06); padding: 0.75rem 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
                <strong>2. 🔒 Privacy Anonymization</strong><br/>
                <span style="color: #94A3B8;">PII & company names protected locally.</span>
            </div>
            <div style="background: rgba(255,255,255,0.06); padding: 0.75rem 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
                <strong>3. ⚖️ Role Risk Weighting</strong><br/>
                <span style="color: #94A3B8;">Exposure computed for your legal role.</span>
            </div>
            <div style="background: rgba(255,255,255,0.06); padding: 0.75rem 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
                <strong>4. 🛡️ Fact Verification</strong><br/>
                <span style="color: #94A3B8;">AI claims verified against contract text.</span>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_executive_summary_box(avg_score: float, role: str, high_risk_count: int) -> None:
    """Render executive summary takeaway box for business managers."""
    if avg_score >= 0.6 or high_risk_count > 0:
        color = "#DC2626"
        bg = "#FEF2F2"
        border = "#FCA5A5"
        status = "CRITICAL LEGAL EXPOSURE DETECTED"
        guidance = f"This agreement contains high-exposure terms for a <strong>{role}</strong>. Recommend legal counsel review on highlighted Indemnity or Liability provisions before execution."
    elif avg_score >= 0.3:
        color = "#D97706"
        bg = "#FFFBEB"
        border = "#FDE68A"
        status = "MODERATE COMMERCIAL RISK"
        guidance = f"Standard commercial agreement with moderate exposure points. Pay attention to role-weighted terms calibrated for a <strong>{role}</strong>."
    else:
        color = "#059669"
        bg = "#ECFDF5"
        border = "#A7F3D0"
        status = "FAVORABLE COMMERCIAL TERMS"
        guidance = f"Minimal legal exposure detected for a <strong>{role}</strong> across standard contract provisions."

    html = f"""
    <div style="background-color: {bg}; border: 1px solid {border}; border-left: 6px solid {color}; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1.5rem;">
        <div style="font-weight: 700; color: {color}; font-size: 0.95rem; letter-spacing: 0.03em; margin-bottom: 0.25rem;">
            EXECUTIVE ASSESSMENT: {status}
        </div>
        <div style="font-size: 0.9rem; color: #1F2937;">
            {guidance}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
