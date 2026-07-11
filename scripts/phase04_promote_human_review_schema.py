"""Convenience wrapper for Phase 04E human-review schema promotion.

Run from project root:
    python scripts/phase04_promote_human_review_schema.py --help
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fleetvision.data.promote_human_review_schema import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
