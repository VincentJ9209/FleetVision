"""Prepare a governed Phase 04.5M annotation-correction review package."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
from fleetvision.review.annotation_correction_review_package import load_correction_review_config, prepare_correction_review_package

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--f2-workspace-root", type=Path, required=True)
    parser.add_argument("--timestamp", default=None)
    args = parser.parse_args()
    try:
        config = load_correction_review_config(args.config, args.project_root)
        package = prepare_correction_review_package(config, args.f2_workspace_root, timestamp=args.timestamp)
    except Exception as exc:
        print("Gate classification: PHASE_04_5M_ANNOTATION_CORRECTION_REVIEW_PACKAGE_BLOCKED")
        print(f"Reason: {exc}")
        print("TEST_SPLIT_READ: NO\nMODEL_INFERENCE_EXECUTED: NO\nANNOTATION_MODIFIED: NO\nTRAINING_STARTED: NO")
        return 1
    print("Gate classification: PHASE_04_5M_ANNOTATION_CORRECTION_REVIEW_PACKAGE_PREPARED")
    print(f"Workspace: {package.workspace_root}")
    print(f"Review cases: {len(package.cases)}")
    print(f"Source CSV SHA256: {package.source_csv_sha256}")
    print("TEST_SPLIT_READ: NO\nMODEL_INFERENCE_EXECUTED: NO\nANNOTATION_MODIFIED: NO\nTRAINING_STARTED: NO")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
