"""Prompt construction, Ollama client, strict JSON parsing (Phase 4)."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional
import requests

from config import load_config
from models.clause import ClauseNode, DocumentEnvelope, LlmClaim

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {
    "Termination",
    "Indemnity",
    "LimitationOfLiability",
    "Confidentiality",
    "IntellectualProperty",
    "Payment",
    "GoverningLaw",
    "Warranty",
    "NonCompete",
    "Assignment",
    "Unclassified",
    "General",
}


def build_prompt(node: ClauseNode) -> str:
    """Build strict JSON prompt for an anonymized clause text.

    HARD INVARIANT: Must strictly consume ``node.masked_text`` to avoid
    exposing raw entity strings to the LLM.
    """
    text_to_use = node.masked_text if node.masked_text is not None else node.text
    if not text_to_use:
        text_to_use = ""

    return f"""Analyze the following anonymized legal contract clause text and provide your analysis in strict JSON format.

Clause Text:
\"\"\"{text_to_use}\"\"\"

Respond ONLY with a JSON object matching this exact structure:
{{
  "category": "Indemnity | LimitationOfLiability | NonCompete | IntellectualProperty | Termination | Payment | Warranty | Confidentiality | GoverningLaw | Assignment | Unclassified",
  "plain_language_summary": "<brief 1-2 sentence plain english summary>",
  "risk_explanation": "<explanation of legal risk or obligations>",
  "base_risk_score": <float between 0.0 and 1.0>,
  "quoted_text": "<exact quote from the clause text supporting this analysis>"
}}"""


def parse_llm_json(response_text: str) -> dict[str, Any]:
    """Parse and validate JSON output from LLM response."""
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ValueError("LLM response is not a JSON object")

    # Required fields validation
    required = ["plain_language_summary", "risk_explanation", "quoted_text"]
    for req in required:
        if req not in data:
            raise ValueError(f"Missing required key in LLM JSON: {req!r}")

    cat = str(data.get("category", "Unclassified")).strip()
    if cat not in VALID_CATEGORIES:
        cat = "Unclassified"
    data["category"] = cat

    try:
        data["base_risk_score"] = float(data.get("base_risk_score", 0.3))
    except (ValueError, TypeError):
        data["base_risk_score"] = 0.3

    return data


def get_available_ollama_models(base_url: str = "http://localhost:11434") -> list[str]:
    """Fetch installed model names from local Ollama tags API."""
    try:
        url = f"{base_url.rstrip('/')}/api/tags"
        resp = requests.get(url, timeout=2.0)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            return [m.get("name", "") for m in models if m.get("name")]
    except Exception:
        pass
    return []


def resolve_model_name(requested_model: str, available_models: list[str]) -> str:
    """Resolve requested model name against locally available Ollama models."""
    if not available_models:
        return requested_model

    req_clean = requested_model.lower().strip()
    # 1. Exact match
    for m in available_models:
        if m.lower() == req_clean:
            return m

    # 2. Base name match (e.g. qwen2.5-coder in qwen2.5-coder:7b)
    base_req = req_clean.split(":")[0]
    for m in available_models:
        if base_req in m.lower():
            return m

    # 3. Fallback to first installed model
    return available_models[0]


def query_ollama(
    prompt: str,
    *,
    base_url: str = "http://localhost:11434",
    model: str = "llama3:8b-instruct-q4_0",
    timeout: int = 120,
) -> str:
    """Send request to local Ollama server generation endpoint."""
    url = f"{base_url.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "format": "json",
        "stream": False,
    }
    resp = requests.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    res_data = resp.json()
    return str(res_data.get("response", ""))


def analyze_clause_node(
    node: ClauseNode,
    *,
    base_url: str = "http://localhost:11434",
    model: str = "llama3:8b-instruct-q4_0",
    timeout: int = 120,
    max_retries: int = 1,
) -> Optional[LlmClaim]:
    """Analyze a single clause node using Ollama with single-retry fallback."""
    text_to_use = node.masked_text if node.masked_text is not None else node.text
    if not text_to_use or not text_to_use.strip():
        return None

    prompt = build_prompt(node)
    
    for attempt in range(max_retries + 1):
        try:
            curr_prompt = prompt if attempt == 0 else f"{prompt}\n\nREMINDER: Output ONLY valid JSON matching the exact schema specified."
            raw_resp = query_ollama(
                curr_prompt,
                base_url=base_url,
                model=model,
                timeout=timeout,
            )
            parsed = parse_llm_json(raw_resp)
            
            if parsed.get("category") and parsed["category"] != "Unclassified":
                node.category = parsed["category"]

            return LlmClaim(
                quoted_text=parsed.get("quoted_text", text_to_use),
                clause_id=node.clause_id,
                explanation=f"{parsed.get('plain_language_summary', '')} - {parsed.get('risk_explanation', '')}".strip(" -"),
                claim_type="risk",
            )
        except requests.exceptions.HTTPError as http_err:
            if http_err.response is not None and http_err.response.status_code == 404:
                logger.warning(
                    "Ollama model '%s' not found on server at %s. Using graceful fallback.",
                    model,
                    base_url,
                )
                break
            logger.warning(
                "Ollama query attempt %d failed for clause %s: %s",
                attempt + 1,
                node.clause_id,
                http_err,
            )
        except Exception as exc:
            logger.warning(
                "Ollama query attempt %d failed for clause %s: %s",
                attempt + 1,
                node.clause_id,
                exc,
            )

    # Graceful fallback claim on failure / offline server
    return LlmClaim(
        quoted_text=text_to_use,
        clause_id=node.clause_id,
        explanation="Fallback analysis (LLM model unavailable or response malformed)",
        claim_type="risk",
    )


def is_ollama_online(base_url: str = "http://localhost:11434") -> bool:
    """Check if the local Ollama server is online and responding."""
    try:
        url = f"{base_url.rstrip('/')}/api/tags"
        resp = requests.get(url, timeout=1.0)
        return resp.status_code == 200
    except Exception:
        return False


def analyze(
    envelope: DocumentEnvelope,
    config: Optional[dict[str, Any]] = None,
) -> DocumentEnvelope:
    """Run local LLM analysis on all masked clauses in the document envelope."""
    if config is None:
        try:
            config = load_config()
        except Exception:
            config = {}

    ollama_cfg = config.get("ollama", {})
    llm_cfg = config.get("llm", {})

    base_url = str(ollama_cfg.get("base_url", "http://localhost:11434"))
    configured_model = str(ollama_cfg.get("model", "llama3:8b-instruct-q4_0"))
    timeout = int(ollama_cfg.get("timeout_seconds", 5))
    max_retries = int(llm_cfg.get("max_retries", 1))

    available = get_available_ollama_models(base_url)
    model = resolve_model_name(configured_model, available) if available else configured_model

    online = is_ollama_online(base_url)
    if not online:
        logger.warning(
            "Ollama server at %s is offline or unreachable. Using fallback analysis.",
            base_url,
        )

    for node in envelope.tree.iter_nodes():
        if not node.text and node.clause_id == "root":
            continue

        if not online:
            text_to_use = node.masked_text if node.masked_text is not None else node.text
            if text_to_use and text_to_use.strip():
                node.llm_claims.append(
                    LlmClaim(
                        quoted_text=text_to_use,
                        clause_id=node.clause_id,
                        explanation="Fallback analysis (LLM server offline)",
                        claim_type="risk",
                    )
                )
            continue

        claim = analyze_clause_node(
            node,
            base_url=base_url,
            model=model,
            timeout=timeout,
            max_retries=max_retries,
        )
        if claim is not None:
            node.llm_claims.append(claim)

    return envelope


__all__ = [
    "analyze",
    "analyze_clause_node",
    "build_prompt",
    "is_ollama_online",
    "parse_llm_json",
    "query_ollama",
    "VALID_CATEGORIES",
]

