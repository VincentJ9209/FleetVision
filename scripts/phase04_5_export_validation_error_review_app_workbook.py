"""Export a completed Workbook from FleetVision local review state."""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from fleetvision.review.validation_error_review_export import (  # noqa: E402
    export_completed_workbook,
)
from fleetvision.review.validation_error_review_package import (  # noqa: E402
    load_review_app_config,
    load_verified_source_package,
)
from fleetvision.review.validation_error_review_state import (  # noqa: E402
    ReviewStateStore,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export the completed FleetVision Phase 04.5L review "
            "Workbook. All 130 cases must be reviewed with no pending "
            "or adjudication cases."
        )
    )
    parser.add_argument(
        "--config",
        default=(
            "configs/data/"
            "validation_error_review_app_config.yaml"
        ),
        help="Review-app YAML config path.",
    )
    parser.add_argument(
        "--project-root",
        default=str(PROJECT_ROOT),
        help="FleetVision repository root.",
    )
    parser.add_argument(
        "--workspace-root",
        default="",
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    config = load_review_app_config(
        Path(args.config),
        project_root,
    )
    package = load_verified_source_package(config)

    if args.workspace_root:
        config = replace(
            config,
            workspace_root=Path(args.workspace_root).resolve(),
        )
        package = replace(package, config=config)

    store = ReviewStateStore(
        config.workspace_root,
        backup_retention=config.backup_retention,
    )
    store.initialize(package)
    result = export_completed_workbook(package, store)

    print(
        "Gate classification: "
        "LOCAL_REVIEW_APP_COMPLETED_WORKBOOK_EXPORTED"
    )
    print(f"Completed Workbook: {result.output_path}")
    print(f"Completed Workbook SHA256: {result.sha256}")
    print(f"Review cases: {result.row_count}")
    print(f"Logical fingerprint: {result.logical_fingerprint}")
    print(f"Pre-export backup: {result.backup_path}")
    print("TEST_SPLIT_READ: NO")
    print("MODEL_INFERENCE_EXECUTED: NO")
    print("ANNOTATION_MODIFIED: NO")
    print("TRAINING_STARTED: NO")
    print("RETRAINING_STATUS: NOT_YET_APPROVED")
    print("DEPLOYMENT_ACCEPTANCE: NOT_YET_APPROVED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
