from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from fleetvision.review.team_pairing_review_app import load_team_pairing_review_runtime
from fleetvision.review.team_pairing_review_export import export_completed_team_pairing_review


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export a completed FleetVision Team Pairing review workspace."
    )
    parser.add_argument(
        "--config",
        default="configs/data/team_pairing_audit_config.yaml",
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--timestamp", default=None)
    parser.add_argument("--repository-commit", default=None)
    return parser.parse_args(argv)


def _git_head(project_root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "UNKNOWN"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config)
    workspace_root = Path(args.workspace_root).resolve()
    runtime = load_team_pairing_review_runtime(
        config_path,
        project_root,
        workspace_root=workspace_root,
    )
    result = export_completed_team_pairing_review(
        runtime,
        timestamp=args.timestamp,
        repository_commit=args.repository_commit or _git_head(project_root),
    )
    print(f"EXPORT_ROOT={result.export_root}")
    print(f"SUMMARY_JSON={result.summary_json}")
    print(f"CHECKSUM_MANIFEST={result.checksum_manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
