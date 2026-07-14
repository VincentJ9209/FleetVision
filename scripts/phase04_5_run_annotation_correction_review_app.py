"""FleetVision Phase 04.5M local annotation-correction review app."""
from __future__ import annotations
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
from fleetvision.review.annotation_correction_review_app import main
if __name__ == "__main__":
    raise SystemExit(main())
