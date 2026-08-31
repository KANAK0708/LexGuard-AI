"""Package import smoke tests for Phase 0 scaffolding."""

import importlib

MODULES = [
    "config",
    "models",
    "models.clause",
    "ingest",
    "parser",
    "anonymize",
    "embed",
    "drift",
    "score",
    "llm",
    "verify",
    "eval",
    "ui",
    "pipeline",
]


def test_all_packages_import():
    for name in MODULES:
        importlib.import_module(name)
