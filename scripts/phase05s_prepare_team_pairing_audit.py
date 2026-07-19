from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from fleetvision.review.team_pairing_operational import (
    prepare_team_pairing_workspace,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a FleetVision Team Pairing audit workspace."
    )
    parser.add_argument(
        "--config",
        default="configs/data/team_pairing_audit_config.yaml",
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--created-at-utc", default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = prepare_team_pairing_workspace(
        Path(args.config),
        Path(args.project_root).resolve(),
        workspace_root=Path(args.workspace_root).resolve(),
        created_at_utc=args.created_at_utc,
    )
    print("OUTCOME=PASS")
    print("OPERATION=PREPARE_TEAM_PAIRING_AUDIT")
    print(f"WORKSPACE_ROOT={result.workspace_root}")
    print(f"IMAGE_COUNT={result.image_count}")
    print(f"BATCH_COUNT={result.batch_count}")
    print(f"CANDIDATE_MANIFEST={result.candidate_manifest}")
    print(f"REVIEW_DATABASE={result.review_database}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
