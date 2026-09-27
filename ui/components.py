"""Reusable presentation components for the LexGuard Streamlit application."""

from __future__ import annotations

import html

import streamlit as st


def inject_custom_css() -> None:
    """Install the visual system used by the application."""
    css = """
    <style>
    :root {
        --navy-950: #07111f; --navy-900: #0b1728; --ink: #152238;
        --muted: #637083; --line: #e5eaf0; --canvas: #f5f7fa;
        --card: #ffffff; --teal: #0f766e; --teal-soft: #e9f7f4;
    }
    html, body, [class*="css"] { font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    .stApp, [data-testid="stAppViewContainer"] { background: var(--canvas); color: var(--ink); }
    [data-testid="stHeader"] { background: rgba(245,247,250,.86); backdrop-filter: blur(12px); }
    .main .block-container { max-width: 1220px; padding: 2rem 2.25rem 4rem; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg,var(--navy-950),var(--navy-900)); border-right: 1px solid rgba(255,255,255,.08); }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.25rem; }
    [data-testid="stSidebar"] * { color: #f8fafc; }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p, [data-testid="stSidebar"] .stCaption { color: #9cadbf !important; }
    [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.1); }
    [data-testid="stSidebar"] [data-baseweb="select"] > div { background: rgba(255,255,255,.08); border-color: rgba(255,255,255,.16); }
    h1, h2, h3, h4 { color: var(--ink) !important; letter-spacing: -.025em; }
    p, label, [data-testid="stCaptionContainer"] { color: var(--muted); }

    .stTabs [data-baseweb="tab-list"] { gap:.4rem; background:#e9edf2; padding:.35rem; border-radius:12px; width:fit-content; }
    .stTabs [data-baseweb="tab"] { height:2.65rem; border-radius:9px; padding:0 1.05rem; color:#64748b; font-weight:650; }
    .stTabs [aria-selected="true"] { background:#fff; color:var(--ink) !important; box-shadow:0 1px 3px rgba(15,23,42,.08),0 5px 16px rgba(15,23,42,.05); }
    .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display:none; }
    [data-testid="stFileUploaderDropzone"] { min-height:150px; background:#fbfcfd; border:1.5px dashed #b7c3d0; border-radius:14px; transition:border-color .18s ease,background .18s ease,transform .18s ease; }
    [data-testid="stFileUploaderDropzone"]:hover { background:var(--teal-soft); border-color:var(--teal); transform:translateY(-1px); }
    [data-testid="stFileUploaderDropzone"] button, .stDownloadButton button { background:var(--navy-900) !important; color:#fff !important; border:0 !important; border-radius:9px !important; font-weight:650 !important; min-height:2.55rem; box-shadow:0 4px 12px rgba(7,17,31,.14); }
    [data-testid="stFileUploaderDropzone"] button:hover, .stDownloadButton button:hover { background:var(--teal) !important; }
    [data-baseweb="input"] > div, [data-baseweb="select"] > div { background:#fff; border-color:#d6dde6; border-radius:10px; }
    [data-testid="stMetric"] { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:1rem 1.1rem; box-shadow:0 4px 18px rgba(15,23,42,.035); }
    [data-testid="stMetricLabel"] { color:#68778a; }
    [data-testid="stMetricValue"] { color:var(--ink); font-weight:730; letter-spacing:-.03em; }
    [data-testid="stExpander"] { background:var(--card); border:1px solid var(--line); border-radius:12px; box-shadow:0 3px 14px rgba(15,23,42,.025); overflow:hidden; margin-bottom:.6rem; }
    [data-testid="stExpander"] summary:hover { background:#f8fafc; }
    [data-testid="stAlert"] { border-radius:12px; border-width:1px; }
    hr { border-color:var(--line) !important; margin:1.5rem 0 !important; }

    .brand-lockup { padding:.1rem 0 .8rem; }
    .brand-mark { display:inline-grid; place-items:center; width:38px; height:38px; border-radius:11px; background:linear-gradient(145deg,#1ba298,#0f766e); color:white; font-weight:800; font-family:Georgia,serif; margin-bottom:.7rem; box-shadow:0 8px 22px rgba(15,118,110,.25); }
    .brand-name { color:white; font-size:1.25rem; font-weight:750; letter-spacing:-.03em; }
    .brand-tagline { color:#90a2b5; font-size:.77rem; line-height:1.45; margin-top:.2rem; }
    .sidebar-label { color:#8093a8; font-size:.69rem; font-weight:750; letter-spacing:.1em; text-transform:uppercase; margin:.25rem 0 .45rem; }
    .privacy-card { background:rgba(15,118,110,.13); border:1px solid rgba(74,222,128,.16); border-radius:12px; padding:.85rem .9rem; }
    .privacy-card strong { display:block; font-size:.82rem; margin-bottom:.2rem; }
    .privacy-card span { color:#99c8be !important; font-size:.74rem; line-height:1.45; }

    .hero { position:relative; overflow:hidden; color:white; background:radial-gradient(circle at 92% 15%,rgba(31,166,153,.28),transparent 32%),linear-gradient(135deg,#07111f 0%,#122944 100%); border-radius:20px; padding:2.3rem 2.5rem; margin-bottom:1.4rem; box-shadow:0 18px 45px rgba(7,17,31,.12); }
    .hero:after { content:"§"; position:absolute; right:2.2rem; bottom:-2.5rem; font-family:Georgia,serif; font-size:10rem; color:rgba(255,255,255,.035); }
    .hero-kicker { color:#76d5ca; font-size:.72rem; letter-spacing:.14em; text-transform:uppercase; font-weight:750; margin-bottom:.75rem; }
    .hero h1 { color:white !important; font-size:2.25rem !important; line-height:1.08; margin:0 0 .75rem; max-width:760px; }
    .hero p { color:#afbdca; max-width:720px; line-height:1.65; margin:0; font-size:.96rem; }
    .hero-pills { display:flex; gap:.55rem; flex-wrap:wrap; margin-top:1.25rem; }
    .hero-pill { color:#dbe6ed; background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.1); border-radius:999px; padding:.36rem .7rem; font-size:.72rem; }

    .workflow { display:grid; grid-template-columns:repeat(4,1fr); background:white; border:1px solid var(--line); border-radius:14px; margin-bottom:1.65rem; overflow:hidden; }
    .workflow-step { position:relative; padding:1rem 1.1rem 1rem 3.25rem; min-height:72px; border-right:1px solid var(--line); }
    .workflow-step:last-child { border-right:0; }
    .workflow-num { position:absolute; left:1rem; top:1.1rem; display:grid; place-items:center; width:25px; height:25px; background:var(--teal-soft); color:var(--teal); border-radius:7px; font-size:.72rem; font-weight:800; }
    .workflow-title { color:var(--ink); font-size:.79rem; font-weight:720; margin-bottom:.18rem; }
    .workflow-copy { color:#7b8796; font-size:.7rem; line-height:1.35; }
    .section-eyebrow { color:var(--teal); text-transform:uppercase; letter-spacing:.11em; font-size:.67rem; font-weight:800; margin-bottom:.3rem; }
    .section-heading { color:var(--ink); font-size:1.35rem; font-weight:750; letter-spacing:-.025em; margin-bottom:.2rem; }
    .section-copy { color:var(--muted); font-size:.87rem; margin-bottom:1rem; }
    .empty-state { text-align:center; background:white; border:1px solid var(--line); border-radius:14px; padding:1.25rem; color:#6c7888; font-size:.84rem; margin-top:.8rem; }
    .empty-icon { display:inline-grid; place-items:center; width:34px; height:34px; border-radius:10px; background:var(--teal-soft); color:var(--teal); font-weight:800; margin-right:.55rem; }
    .badge-low,.badge-medium,.badge-high,.drift-cosmetic,.drift-intent,.drift-rewrite,.badge-verified { display:inline-block; font-weight:750; padding:4px 10px; border-radius:999px; font-size:.71rem; letter-spacing:.025em; }
    .badge-low { background:#e9f8f1; color:#08734f; } .badge-medium { background:#fff5d9; color:#8b5b0a; } .badge-high { background:#fdeceb; color:#a43833; }
    .drift-cosmetic { background:#eaf3fb; color:#24648b; } .drift-intent { background:#fff5d9; color:#8b5b0a; } .drift-rewrite { background:#fdeceb; color:#a43833; }
    .badge-verified { background:#e9f8f1; color:#08734f; border:1px solid #b9e6d2; margin-bottom:.5rem; }
    @media (max-width:900px) { .main .block-container{padding:1.25rem 1rem 3rem}.hero{padding:1.6rem 1.35rem}.hero h1{font-size:1.75rem !important}.workflow{grid-template-columns:1fr 1fr}.workflow-step:nth-child(2){border-right:0}.workflow-step:nth-child(-n+2){border-bottom:1px solid var(--line)} }
    @media (max-width:620px) { .workflow{grid-template-columns:1fr}.workflow-step{border-right:0;border-bottom:1px solid var(--line)}.workflow-step:last-child{border-bottom:0}.hero-pills{display:none} }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_brand() -> None:
    st.markdown('<div class="brand-lockup"><div class="brand-mark">L</div><div class="brand-name">LexGuard AI</div><div class="brand-tagline">Private contract intelligence<br/>for modern legal teams</div></div>', unsafe_allow_html=True)


def render_hero() -> None:
    st.markdown('<div class="hero"><div class="hero-kicker">Contract intelligence workspace</div><h1>Know the risk before you sign.</h1><p>Review agreements, surface role-specific exposure, and compare revisions with locally processed, source-verified intelligence.</p><div class="hero-pills"><span class="hero-pill">Private by design</span><span class="hero-pill">Role-calibrated</span><span class="hero-pill">Source verified</span></div></div>', unsafe_allow_html=True)


def render_section_heading(eyebrow: str, title: str, copy: str) -> None:
    st.markdown(f'<div class="section-eyebrow">{html.escape(eyebrow)}</div><div class="section-heading">{html.escape(title)}</div><div class="section-copy">{html.escape(copy)}</div>', unsafe_allow_html=True)


def render_empty_state(message: str) -> None:
    st.markdown(f'<div class="empty-state"><span class="empty-icon">↥</span>{html.escape(message)}</div>', unsafe_allow_html=True)


def render_risk_badge(score: float | None) -> str:
    """Return HTML badge for risk score."""
    if score is None:
        return '<span class="badge-low">LOW RISK · 0.20</span>'
    if score >= 0.7:
        return f'<span class="badge-high">HIGH EXPOSURE · {score:.2f}</span>'
    if score >= 0.4:
        return f'<span class="badge-medium">MODERATE RISK · {score:.2f}</span>'
    return f'<span class="badge-low">LOW RISK · {score:.2f}</span>'


def render_drift_badge(label: str) -> str:
    """Return HTML badge for drift classification label."""
    if label == "Cosmetic":
        return '<span class="drift-cosmetic">Minor Paraphrase</span>'
    if label == "IntentShift":
        return '<span class="drift-intent">Obligation Shift</span>'
    if label == "SubstantialRewrite":
        return '<span class="drift-rewrite">Critical Redraft</span>'
    return f'<span class="drift-cosmetic">{html.escape(label)}</span>'


def render_verified_badge() -> str:
    """Return HTML badge for verified claims."""
    return '<span class="badge-verified">✓ Fact-Checked &amp; Attributed Quote</span>'


def render_guide_banner() -> None:
    """Render the compact four-step workflow."""
    steps = (("01","Upload","PDF or DOCX agreement"),("02","Protect","Sensitive data masked locally"),("03","Analyze","Exposure weighted to your role"),("04","Verify","Every insight checked to source"))
    cards = "".join(f'<div class="workflow-step"><span class="workflow-num">{number}</span><div class="workflow-title">{title}</div><div class="workflow-copy">{copy}</div></div>' for number,title,copy in steps)
    st.markdown(f'<div class="workflow">{cards}</div>', unsafe_allow_html=True)


def render_executive_summary_box(avg_score: float, role: str, high_risk_count: int) -> None:
    """Render an executive-level risk takeaway."""
    if avg_score >= 0.6 or high_risk_count > 0:
        color,bg,border,status = "#c2413b","#fff5f4","#f2c7c4","Critical legal exposure detected"
        guidance = f"High-exposure terms affect the {role} position. Review the highlighted liability and obligation language before execution."
    elif avg_score >= 0.3:
        color,bg,border,status = "#a86e16","#fffaf0","#ecd8aa","Moderate commercial risk"
        guidance = f"The agreement contains manageable exposure points weighted for the {role} position. Review the flagged terms before approval."
    else:
        color,bg,border,status = "#0f766e","#f0faf7","#bfe1d8","Favorable commercial terms"
        guidance = f"Minimal legal exposure was detected for the {role} position across the analyzed provisions."
    st.markdown(f'<div style="background:{bg};border:1px solid {border};border-left:4px solid {color};padding:1rem 1.15rem;border-radius:12px;margin:1rem 0 1.25rem"><div style="font-weight:760;color:{color};font-size:.82rem;letter-spacing:.045em;text-transform:uppercase;margin-bottom:.3rem">{html.escape(status)}</div><div style="font-size:.86rem;color:#465568;line-height:1.5">{html.escape(guidance)}</div></div>', unsafe_allow_html=True)
