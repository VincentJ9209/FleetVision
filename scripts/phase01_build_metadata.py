"""Convenience wrapper for Phase 01 metadata building.

Run from project root:
    python scripts/phase01_build_metadata.py --config configs/data/metadata_config.yaml --project-root .
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fleetvision.data.build_metadata import main  # noqa: E402


if __name__ == "__main__":
    main()