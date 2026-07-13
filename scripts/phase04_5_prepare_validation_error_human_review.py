"""FleetVision Phase 04.5L prepare CLI wrapper."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from fleetvision.data.validation_error_human_review import main_prepare  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main_prepare())
