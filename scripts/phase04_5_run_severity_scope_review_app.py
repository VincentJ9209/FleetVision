"""Launch the FleetVision Traditional Chinese severity-scope review app."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
APP_PATH = SRC_ROOT / "fleetvision/review/severity_scope_review_app.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch the FleetVision local Traditional Chinese scope-review app."
    )
    parser.add_argument(
        "--config",
        default="configs/data/severity_scope_review_app_config.yaml",
    )
    parser.add_argument("--project-root", default=str(PROJECT_ROOT))
    parser.add_argument("--f1-workspace-root", default="")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--port", type=int, default=8502)
    parser.add_argument("--address", default="127.0.0.1")
    return parser.parse_args()


def build_command(args: argparse.Namespace) -> list[str]:
    if not 1 <= int(args.port) <= 65535:
        raise ValueError("port must be between 1 and 65535")
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(APP_PATH),
        "--browser.gatherUsageStats=false",
        f"--server.headless={'true' if args.headless else 'false'}",
        f"--server.port={int(args.port)}",
        f"--server.address={args.address}",
        "--",
        "--config",
        str(args.config),
        "--project-root",
        str(Path(args.project_root).resolve()),
    ]
    if args.f1_workspace_root:
        command.extend(
            [
                "--f1-workspace-root",
                str(Path(args.f1_workspace_root).resolve()),
            ]
        )
    return command


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    if not project_root.is_dir():
        raise FileNotFoundError(f"project root not found: {project_root}")
    if not APP_PATH.is_file():
        raise FileNotFoundError(f"scope review app not found: {APP_PATH}")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        part
        for part in (str(SRC_ROOT), environment.get("PYTHONPATH", ""))
        if part
    )
    environment["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    return subprocess.call(
        build_command(args),
        cwd=project_root,
        env=environment,
    )


if __name__ == "__main__":
    raise SystemExit(main())
