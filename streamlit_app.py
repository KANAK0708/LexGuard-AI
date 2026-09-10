"""Streamlit Community Cloud Root Entrypoint for LexGuard AI."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure workspace root is in sys.path for module resolution
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ui.app import main

if __name__ == "__main__":
    main()
