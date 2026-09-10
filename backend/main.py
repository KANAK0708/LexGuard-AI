"""FastAPI Backend REST API Application for Render Deployment."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.db.supabase_client import (
    get_supabase_client,
    save_document_envelope,
    save_drift_comparison,
)
from ingest import ingest_bytes
from llm import is_ollama_online
from pipeline import run as run_pipeline

app = FastAPI(
    title="LexGuard AI API",
    description="Production REST API backend for LexGuard AI contract risk quantification and intent drift analysis.",
    version="1.0.0",
)

# Enable CORS for Vercel frontend / cross-origin web apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalysisResponse(BaseModel):
    status: str
    role: str
    document: Dict[str, Any]
    saved_to_supabase: bool


class ComparisonResponse(BaseModel):
    status: str
    role: str
    document: Dict[str, Any]
    document_v2: Dict[str, Any]
    drift: list[Dict[str, Any]]
    saved_to_supabase: bool


@app.get("/")
@app.get("/health")
@app.get("/api/v1/health")
def health_check() -> Dict[str, Any]:
    """Health check endpoint for Render deployment monitoring."""
    supabase_active = get_supabase_client() is not None
    ollama_active = is_ollama_online()
    return {
        "status": "online",
        "version": "1.0.0",
        "supabase_connected": supabase_active,
        "ollama_online": ollama_active,
    }


@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze_contract(
    file: UploadFile = File(...),
    role: str = Form("Client"),
) -> Dict[str, Any]:
    """Analyze a single contract agreement (PDF or DOCX) for risk exposure."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        ingested = ingest_bytes(content, file.filename)
        result = run_pipeline(ingested.path, role=role)
        
        # Save to Supabase database
        from models.clause import DocumentEnvelope
        env = DocumentEnvelope.from_dict(result["document"])
        saved = save_document_envelope(env)

        return {
            "status": "success",
            "role": role,
            "document": result["document"],
            "saved_to_supabase": saved,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Contract analysis failed: {exc}")


@app.post("/api/v1/compare", response_model=ComparisonResponse)
async def compare_contracts(
    file_v1: UploadFile = File(...),
    file_v2: UploadFile = File(...),
    role: str = Form("Client"),
) -> Dict[str, Any]:
    """Compare Contract V1 vs Contract V2 to analyze semantic intent drift."""
    if not file_v1.filename or not file_v2.filename:
        raise HTTPException(status_code=400, detail="Both files must have valid filenames.")

    bytes1 = await file_v1.read()
    bytes2 = await file_v2.read()

    try:
        ingested1 = ingest_bytes(bytes1, file_v1.filename)
        ingested2 = ingest_bytes(bytes2, file_v2.filename)

        result = run_pipeline(ingested1.path, role=role, file_v2=ingested2.path)

        # Save drift comparison to Supabase
        doc1_id = result["document"]["doc_id"]
        doc2_id = result["document_v2"]["doc_id"]
        saved = save_drift_comparison(doc1_id, doc2_id, role, result.get("drift", []))

        return {
            "status": "success",
            "role": role,
            "document": result["document"],
            "document_v2": result["document_v2"],
            "drift": result.get("drift", []),
            "saved_to_supabase": saved,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Contract comparison failed: {exc}")
