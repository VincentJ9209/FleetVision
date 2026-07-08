"""Convenience wrapper for Phase 02 review queue building.

Run from project root:
    python scripts/phase02_build_review_queue.py --max-rows 100
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fleetvision.data.build_review_queue import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
