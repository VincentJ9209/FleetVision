"""Convenience wrapper for Phase 04 reviewed dataset building.

Run from project root:
    python scripts/phase04_build_reviewed_dataset.py --help
    python scripts/phase04_build_reviewed_dataset.py --input dataset/00_catalog/image_review_labels.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fleetvision.data.build_reviewed_dataset import main  # noqa: E402


if __name__ == "__main__":
    main()
