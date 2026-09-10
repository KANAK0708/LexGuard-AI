"""Global pytest configuration and fixtures."""

from __future__ import annotations

from unittest.mock import patch
import pytest


@pytest.fixture(autouse=True)
def mock_ollama_offline_by_default(request):
    """Prevent automated unit tests from making real multi-node network requests to local Ollama."""
    if "test_llm" in request.module.__name__:
        yield
    else:
        with patch("llm.is_ollama_online", return_value=False):
            yield
