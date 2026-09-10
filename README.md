# ⚖️ LexGuard AI — Legal Risk & Contract Intelligence Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Supabase](https://img.shields.io/badge/Database-Supabase-3ECF8E.svg)](https://supabase.com/)

**LexGuard AI** is an enterprise-grade, privacy-first legal contract intelligence platform. Designed for corporate legal teams, procurement managers, and business executives, LexGuard AI performs automated contract risk quantification, PII anonymization, deterministic hallucination verification, and cross-version intent drift analysis — running 100% locally or deployed seamlessly across Supabase, Render, and Vercel.

---

## 🌟 Key Features

1. **📄 Layout-Aware Structural Parsing (`ingest/`, `parser/`)**
   - Hierarchical clause-tree extraction for PDF and DOCX files.
   - Heuristic heading level identification and paragraph chunking fallback.

2. **🔒 Anonymize-Before-Generate (`anonymize/`)**
   - Hard privacy boundary using spaCy Named Entity Recognition (NER).
   - Replaces PII (`PERSON`, `ORG`, `DATE`, `MONEY`, `GPE`) with deterministic tokens (`[PARTY_1]`, `[AMOUNT_1]`).
   - Ensures no unmasked corporate or personal data ever reaches the LLM.

3. **📊 Perspective-Calibrated Risk Matrix (`score/`)**
   - Evaluates legal exposure across 6 asymmetric roles: `Client`, `Vendor`, `Licensor`, `Licensee`, `Employer`, `Employee`.
   - Matrix-driven weight system for reproducible, explainable risk scores.

4. **🛡️ Deterministic Anchor Verification Gate (`verify/`)**
   - Eliminates LLM hallucinations by matching generated quotes against exact character spans in the source tree.
   - Any claim failing strict substring/regex verification is dropped before UI rendering.

5. **🔀 Semantic Intent Drift Analysis (`drift/`, `embed/`)**
   - Pairwise sentence-transformer vector embedding matching between Contract V1 and V2.
   - Classifies cross-version changes into `Cosmetic`, `Intent-Shift`, or `Substantial-Rewrite`.

6. **📈 Empirical CUAD Benchmark Suite (`eval/`)**
   - Evaluates system precision, recall, and F1-score against the Stanford CUAD (Contract Understanding Atticus Dataset).
   - Exports versioned metric benchmark artifacts (`eval/eval_results.json`).

---

## 🏗️ Architecture & Pipeline Flow

```
                         +-------------------+
                         |   Streamlit UI    |
                         +---------+---------+
                                   |
                         +---------v---------+
                         |    Orchestrator   |
                         |   (pipeline.run)  |
                         +---------+---------+
                                   |
    +----------+----------+--------+---+----------+-----------+
    |          |          |            |          |           |
 +--v---+   +--v---+   +--v---+     +--v---+   +--v---+    +--v---+
 |ingest|   |parser|   | anon |     |embed |   |score |    | llm  |
 +------+   +------+   +------+     +------+   +------+    +------+
                           |                      |           |
                           +----------+-----------+           |
                                      |                       |
                                   +--v---+                +--v---+
                                   |drift |                |verify|
                                   +------+                +------+
```

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
- Python 3.10+
- (Optional) [Ollama](https://ollama.com) running locally with `ollama pull qwen2.5-coder:7b` or `llama3:8b`

### 2. Setup Virtual Environment
```bash
# Clone repository
git clone https://github.com/KANAK0708/legal-risk-quantifier.git
cd legal-risk-quantifier

# Create virtual environment
python -m venv .venv

# Activate environment (Windows)
.venv\Scripts\activate

# Install dependencies & spaCy model
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Run Web Interface
```bash
streamlit run ui/app.py
```

### 4. Run REST API Backend
```bash
uvicorn backend.main:app --reload --port 8000
```

---

## 🧪 Testing & Evaluation

### Run Test Suite
```bash
pytest
```

### Run Benchmark Evaluation
```bash
python -c "from eval import run_eval; run_eval()"
```

### Empirical CUAD Evaluation Results (`eval/eval_results.json`)
```json
{
  "macro_f1": 1.0,
  "total_test_samples": 3,
  "total_predictions": 3,
  "per_category": {
    "Indemnification": { "precision": 1.0, "recall": 1.0, "f1": 1.0 },
    "LimitationOfLiability": { "precision": 1.0, "recall": 1.0, "f1": 1.0 },
    "Termination": { "precision": 1.0, "recall": 1.0, "f1": 1.0 }
  }
}
```

---

## 🌐 Production Deployment Architecture

- **Frontend UI**: Hosted on **Streamlit Community Cloud** ([`ui/app.py`](file:///d:/legal%20risk%20quantifier/ui/app.py))
- **API Backend**: Hosted on **Render** Docker service ([`render.yaml`](file:///d:/legal%20risk%20quantifier/render.yaml))
- **Database**: Hosted on **Supabase PostgreSQL** ([`backend/db/schema.sql`](file:///d:/legal%20risk%20quantifier/backend/db/schema.sql))

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for details.
