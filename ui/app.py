"""Commercial Web Application Entrypoint for Privacy-First Legal Risk Quantifier."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

# Ensure project root is in sys.path when running via Streamlit
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from anonymize import anonymize, collect_llm_payloads
from config import load_config
from drift import compare
from embed import embed_document
from ingest import detect_format, ingest_bytes
from llm import analyze as llm_analyze, is_ollama_online
from parser import parse_file
from pipeline import run as run_pipeline
from score import score_document
from ui.components import (
    inject_custom_css,
    render_drift_badge,
    render_executive_summary_box,
    render_guide_banner,
    render_risk_badge,
    render_verified_badge,
)
from verify import verify


def main() -> None:
    st.set_page_config(
        page_title="LexGuard AI — Contract Intelligence Platform",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_custom_css()

    cfg = load_config()
    ollama_base_url = cfg.get("ollama", {}).get("base_url", "http://localhost:11434")
    ollama_model = cfg.get("ollama", {}).get("model", "qwen2.5-coder:7b")

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("<div class='product-title' style='font-size:1.5rem;'>⚖️ LexGuard AI</div>", unsafe_allow_html=True)
        st.caption("AI-Powered Contract Intelligence & Risk Quantification")
        st.markdown("---")

        st.subheader("Perspective Calibration")
        role = st.selectbox(
            "Select Your Legal Role",
            options=["Client", "Vendor", "Licensor", "Licensee", "Employer", "Employee"],
            index=0,
            help="Contract risk weights adjust automatically to highlight risks specific to your legal role.",
        )

        st.markdown("---")
        st.subheader("Engine & Security")
        online = is_ollama_online(ollama_base_url)
        if online:
            st.success(f"Private Local AI (`{ollama_model}`)")
        else:
            st.warning("Local AI Offline (Rule-Based Fallback Mode Active)")

        st.markdown("---")
        st.info(
            "🔒 **Enterprise Privacy Active**: 100% local processing. No contract text or company data ever leaves your device."
        )

    # --- MAIN HERO SECTION ---
    st.markdown("<div class='product-title'>⚖️ LexGuard AI — Contract Risk & Intent Drift Intelligence</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='product-subtitle'>Automated contract risk evaluation, PII anonymization, and cross-version intent drift detection built for corporate legal teams and business executives.</div>",
        unsafe_allow_html=True,
    )

    # Top Visual Guide Banner
    render_guide_banner()

    # Product Tabs (Clean 2-tab Commercial View)
    tab1, tab2 = st.tabs([
        "📊 Contract Risk Audit Dashboard",
        "🔀 Version Drift & Revision Comparison"
    ])

    # =========================================================================
    # TAB 1: CONTRACT RISK AUDIT DASHBOARD
    # =========================================================================
    with tab1:
        st.header("Contract Risk Audit")
        st.caption("Upload a legal agreement to analyze clause-by-clause exposure, fact-checked AI insights, and privacy protection.")

        uploaded_file = st.file_uploader(
            "Upload Contract Agreement (PDF or DOCX)",
            type=["pdf", "docx"],
            key="single_doc_uploader",
        )

        if uploaded_file is not None:
            file_bytes = uploaded_file.getvalue()
            filename = uploaded_file.name

            # Cache key in session_state to prevent re-running on widget clicks
            cache_key = f"doc_{uploaded_file.name}_{len(file_bytes)}_{role}"
            if cache_key not in st.session_state:
                with st.spinner("Analyzing contract structure, privacy masking, and risk exposure..."):
                    ingested = ingest_bytes(file_bytes, filename)
                    envelope = anonymize(parse_file(ingested.path, role=role))
                    envelope = embed_document(envelope)
                    envelope = score_document(envelope, role=role)
                    envelope = llm_analyze(envelope)
                    envelope = verify(envelope)
                    st.session_state[cache_key] = envelope

            envelope = st.session_state[cache_key]
            nodes = [n for n in envelope.tree.iter_nodes() if n.text or n.clause_id != "root"]

            # Compute summary stats
            scores = [n.risk_score for n in nodes if n.risk_score is not None]
            avg_score = sum(scores) / len(scores) if scores else 0.0
            max_score = max(scores) if scores else 0.0
            high_risk_count = sum(1 for s in scores if s >= 0.7)
            entity_count = len(envelope.entity_map)
            verified_claims_count = sum(len(n.verified_claims) for n in nodes)

            st.markdown("---")
            # Executive Takeaway Box
            render_executive_summary_box(avg_score, role, high_risk_count)

            # High level metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Contract Risk Score", f"{avg_score:.2f}", help="Average risk rating across all clauses for your selected role.")
            with col2:
                st.metric("High Exposure Points", f"{high_risk_count}", help="Clauses with risk rating >= 0.70 requiring attention.")
            with col3:
                st.metric("Privacy Tokens Masked", f"{entity_count}", help="Sensitive entity names, dates, and numbers protected locally.")
            with col4:
                st.metric("Attributed AI Citations", f"{verified_claims_count}", help="AI claims fact-checked against exact contract text.")

            st.markdown("---")

            # Privacy details expander with product explanation
            with st.expander("🔒 Privacy & PII Protection Details", expanded=False):
                st.caption(
                    "To uphold enterprise confidentiality, sensitive names (PERSON), company names (ORG), financial figures (MONEY), and dates (DATE) were automatically converted to privacy tokens before AI analysis."
                )
                if envelope.entity_map:
                    st.json(envelope.entity_map)
                else:
                    st.info("No sensitive personal or corporate entities detected in this document.")

            # Filter controls
            col_search, col_cat = st.columns([2, 1])
            with col_search:
                search_query = st.text_input("🔍 Filter clause contents...", key="clause_search").lower()
            with col_cat:
                categories = sorted(list({n.category for n in nodes if n.category}))
                cat_filter = st.selectbox("Category Filter", options=["All Categories"] + categories)

            st.subheader("Clause Exposure & Risk Analysis")
            filtered_nodes = nodes
            if cat_filter != "All Categories":
                filtered_nodes = [n for n in filtered_nodes if n.category == cat_filter]
            if search_query:
                filtered_nodes = [
                    n for n in filtered_nodes if search_query in (n.text or "").lower() or search_query in (n.masked_text or "").lower()
                ]

            for n in filtered_nodes:
                badge_html = render_risk_badge(n.risk_score)
                header_title = f"{n.clause_id.upper()} — {n.category or 'General Terms'}"
                
                with st.expander(header_title, expanded=False):
                    st.markdown(f"**Risk Rating**: {badge_html}", unsafe_allow_html=True)
                    st.markdown(f"**Clause Text**:\n>{n.text}")

                    if n.role_weights_applied:
                        mult = n.role_weights_applied.get("role_multiplier", 1.0)
                        st.caption(f"Role Exposure Factor ({role}): {mult}x multiplier applied")

                    if n.verified_claims:
                        st.markdown("#### Fact-Checked AI Insights")
                        for claim in n.verified_claims:
                            st.markdown(render_verified_badge(), unsafe_allow_html=True)
                            st.markdown(f"**Attributed Quote**: `\"{claim.quoted_text}\"`")
                            st.markdown(f"**Risk Assessment**: {claim.explanation}")

            # Export button
            st.markdown("---")
            report_data = json.dumps(envelope.to_dict(), indent=2)
            st.download_button(
                label="📥 Download Complete Risk Audit Report (JSON)",
                data=report_data,
                file_name=f"risk_audit_{envelope.doc_id}_{role}.json",
                mime="application/json",
            )
        else:
            st.info("💡 Upload a contract document above to view complete risk analysis and clause breakdown.")

    # =========================================================================
    # TAB 2: TWO-VERSION INTENT DRIFT COMPARISON
    # =========================================================================
    with tab2:
        st.header("Version Drift & Revision Comparison")
        st.caption("Compare original contract against counterparty redline revisions to detect hidden obligation shifts or deleted rights.")

        col_v1, col_v2 = st.columns(2)
        with col_v1:
            file_v1 = st.file_uploader("Upload Original Agreement (Version 1)", type=["pdf", "docx"], key="v1_uploader")
        with col_v2:
            file_v2 = st.file_uploader("Upload Revised Redline (Version 2)", type=["pdf", "docx"], key="v2_uploader")

        if file_v1 is not None and file_v2 is not None:
            bytes_v1 = file_v1.getvalue()
            bytes_v2 = file_v2.getvalue()

            pair_key = f"pair_{file_v1.name}_{file_v2.name}_{role}"
            if pair_key not in st.session_state:
                with st.spinner("Analyzing semantic drift across contract revisions..."):
                    ingested_v1 = ingest_bytes(bytes_v1, file_v1.name)
                    ingested_v2 = ingest_bytes(bytes_v2, file_v2.name)

                    pipeline_res = run_pipeline(
                        ingested_v1.path,
                        role=role,
                        file_v2=ingested_v2.path,
                    )
                    st.session_state[pair_key] = pipeline_res

            res = st.session_state[pair_key]
            drifts = res.get("drift", [])

            # Summarize drift tags
            cosmetic_count = sum(1 for d in drifts if d.get("label") == "Cosmetic")
            intent_count = sum(1 for d in drifts if d.get("label") == "IntentShift")
            rewrite_count = sum(1 for d in drifts if d.get("label") == "SubstantialRewrite")

            st.markdown("---")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("🟢 Minor Paraphrases", cosmetic_count, help="Textual rewrites preserving original legal intent.")
            with c2:
                st.metric("🟡 Obligation Shifts", intent_count, help="Clauses where terms or conditions were modified.")
            with c3:
                st.metric("🔴 Critical Redrafts", rewrite_count, help="Major legal changes, added obligations, or deleted rights.")

            st.markdown("---")
            st.subheader("Clause Comparison Matrix")

            for drift in drifts:
                left_id = drift.get("left_clause_id", "")
                right_id = drift.get("right_clause_id", "None")
                cosine = drift.get("cosine", 0.0)
                label = drift.get("label", "Cosmetic")

                badge = render_drift_badge(label)
                title = f"Original Clause {left_id.upper()} ➔ Revised Clause {right_id.upper()}"
                
                with st.expander(title, expanded=False):
                    st.markdown(f"**Revision Impact**: {badge}", unsafe_allow_html=True)
                    st.markdown(f"**Semantic Alignment Index**: `{cosine:.4f}`")

            # Export button
            st.markdown("---")
            drift_export = json.dumps(res, indent=2)
            st.download_button(
                label="📥 Download Version Drift Comparison Report (JSON)",
                data=drift_export,
                file_name=f"version_drift_{role}.json",
                mime="application/json",
            )
        else:
            st.info("💡 Upload both Original Contract V1 and Revised Contract V2 above to run automated drift comparison.")


if __name__ == "__main__":
    main()
