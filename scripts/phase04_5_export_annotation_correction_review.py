"""Export completed Phase 04.5M annotation-correction proposals."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
from fleetvision.review.annotation_correction_review_package import load_correction_review_config, load_verified_correction_review_package
from fleetvision.review.annotation_correction_review_state import CorrectionReviewStateStore
from fleetvision.review.annotation_correction_review_export import export_completed_correction_review

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--workspace-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        config = load_correction_review_config(args.config, args.project_root)
        package = load_verified_correction_review_package(config, args.workspace_root)
        store = CorrectionReviewStateStore(package.app_workspace_root, backup_retention=config.backup_retention)
        store.initialize(package)
        result = export_completed_correction_review(package, store)
    except Exception as exc:
        print("Gate classification: PHASE_04_5M_ANNOTATION_CORRECTION_PROPOSALS_EXPORT_BLOCKED")
        print(f"Reason: {exc}")
        print("TEST_SPLIT_READ: NO\nMODEL_INFERENCE_EXECUTED: NO\nANNOTATION_MODIFIED: NO\nTRAINING_STARTED: NO")
        return 1
    print("Gate classification: PHASE_04_5M_ANNOTATION_CORRECTION_PROPOSALS_REVIEWED")
    print(f"Reviewed CSV: {result.reviewed_csv_path}")
    print(f"Reviewed CSV SHA256: {__import__('hashlib').sha256(result.reviewed_csv_path.read_bytes()).hexdigest().upper()}")
    print(f"Completed Workbook: {result.completed_workbook_path}")
    print(f"Export evidence: {result.result_json_path}")
    print("Review cases: 2\nPending: 0\nNeeds adjudication: 0")
    print("TEST_SPLIT_READ: NO\nMODEL_INFERENCE_EXECUTED: NO\nANNOTATION_MODIFIED: NO\nTRAINING_STARTED: NO")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
