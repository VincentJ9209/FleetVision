"""Convenience wrapper for Phase 03 review label validation.

Run from project root:
    python scripts/phase03_validate_review_labels.py --help
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fleetvision.data.validate_review_labels import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
