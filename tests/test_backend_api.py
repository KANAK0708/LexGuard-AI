"""Tests for FastAPI backend REST API endpoints (Render deployment)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


from pathlib import Path

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


@pytest.fixture(scope="module", autouse=True)
def _ensure_samples():
    if not (SAMPLES / "structured_nda.docx").exists():
        from scripts.generate_samples import main

        main()


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "supabase_connected" in data
    assert "ollama_online" in data


def test_analyze_contract_endpoint():
    sample_bytes = (SAMPLES / "structured_nda.docx").read_bytes()
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("structured_nda.docx", sample_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        data={"role": "Client"},
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert res_data["role"] == "Client"
    assert "document" in res_data
    assert res_data["document"]["filename"].endswith(".docx")


def test_compare_contracts_endpoint():
    sample_bytes1 = (SAMPLES / "structured_nda.docx").read_bytes()
    sample_bytes2 = (SAMPLES / "structured_nda_v2.docx").read_bytes() if (SAMPLES / "structured_nda_v2.docx").exists() else sample_bytes1
    
    response = client.post(
        "/api/v1/compare",
        files={
            "file_v1": ("v1.docx", sample_bytes1, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            "file_v2": ("v2.docx", sample_bytes2, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        },
        data={"role": "Vendor"},
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert res_data["role"] == "Vendor"
    assert "document" in res_data
    assert "document_v2" in res_data
    assert "drift" in res_data
