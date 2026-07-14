"""Export the completed severity-scope Workbook from local SQLite state."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from fleetvision.review.severity_scope_review_export import (  # noqa: E402
    export_completed_scope_workbook,
)
from fleetvision.review.severity_scope_review_package import (  # noqa: E402
    discover_latest_f1_workspace,
    load_scope_review_app_config,
    load_verified_scope_package,
)
from fleetvision.review.severity_scope_review_state import (  # noqa: E402
    ScopeReviewStateStore,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export the completed FleetVision severity-scope Workbook. "
            "All 130 cases must be reviewed with no pending/adjudication cases."
        )
    )
    parser.add_argument(
        "--config",
        default="configs/data/severity_scope_review_app_config.yaml",
    )
    parser.add_argument("--project-root", default=str(PROJECT_ROOT))
    parser.add_argument("--f1-workspace-root", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    config = load_scope_review_app_config(Path(args.config), project_root)
    root = (
        Path(args.f1_workspace_root).resolve()
        if args.f1_workspace_root
        else discover_latest_f1_workspace(config)
    )
    package = load_verified_scope_package(config, root)
    store = ScopeReviewStateStore(
        package.app_workspace_root,
        backup_retention=config.backup_retention,
    )
    store.initialize(package)
    result = export_completed_scope_workbook(package, store)
    print("Gate classification: LOCAL_SCOPE_REVIEW_APP_COMPLETED_WORKBOOK_EXPORTED")
    print(f"Completed Scope Workbook: {result.output_path}")
    print(f"Completed Scope Workbook SHA256: {result.sha256}")
    print(f"Review cases: {result.row_count}")
    print(f"Pre-export backup: {result.backup_path}")
    print(f"Export evidence: {result.result_path}")
    print("TEST_SPLIT_READ: NO")
    print("MODEL_INFERENCE_EXECUTED: NO")
    print("ANNOTATION_MODIFIED: NO")
    print("TRAINING_STARTED: NO")
    print("RETRAINING_STATUS: NOT_YET_APPROVED")
    print("DEPLOYMENT_ACCEPTANCE: NOT_YET_APPROVED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
