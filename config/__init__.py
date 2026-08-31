"""Configuration loading for the Legal Risk Quantifier."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load YAML config from the default or provided path."""
    cfg_path = path or _CONFIG_PATH
    # utf-8-sig tolerates BOM; replace handles odd Windows encodings on comments
    raw = cfg_path.read_bytes()
    text = raw.decode("utf-8-sig")
    return yaml.safe_load(text)
