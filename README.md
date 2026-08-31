# Privacy-First Asymmetric Legal Risk Quantifier

Local, privacy-first contract risk analysis (Streamlit + Ollama). Phases 0–2 deliver scaffolding, the structural layout parser, and NER anonymization.

## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Optional (later phases): install [Ollama](https://ollama.com) and pull a quantized instruct model, e.g. `ollama pull llama3:8b-instruct-q4_0`.

## Module map

| Module | Owns |
|--------|------|
| `ingest/` | File upload, PDF/DOCX detection & extraction |
| `parser/` | Layout heuristics → nested clause tree |
| `anonymize/` | NER + masking + `entity_map` (Phase 2) |
| `embed/` / `drift/` | Vectors + cross-version drift (Phase 3) |
| `score/` / `llm/` | Role weights + Ollama JSON (Phase 4) |
| `verify/` | Anchor verification gate (Phase 5) |
| `ui/` | Streamlit (Milestone A / Phase 6) |
| `eval/` | CUAD metrics (Phase 7) |
| `pipeline/` | Single orchestrator `run()` |
| `models/` | Shared `ClauseNode` / `DocumentEnvelope` |

## Parse + anonymize

```python
from parser import parse_file
from anonymize import anonymize, build_llm_payload, assert_no_raw_entities
from pipeline import run

env = anonymize(parse_file("samples/structured_nda.docx"))
print(env.parser_mode, env.entity_map)
for node in env.tree.iter_nodes():
    if node.text:
        payload = build_llm_payload(node)
        assert_no_raw_entities(payload, env.entity_map)

result = run("samples/structured_nda.docx", role="Client")
# status: "anonymized"
```

**Invariant:** LLM modules may only consume `masked_text` via `build_llm_payload`. Source `text` / `char_span` stay intact for verify.

## Tests

```bash
python scripts/generate_samples.py
pytest
```

## Hard invariants (upcoming phases)

- Anonymize before any LLM call
- No LLM claim reaches the UI without deterministic anchor verification
- Thresholds and role weights live in `config/config.yaml`
