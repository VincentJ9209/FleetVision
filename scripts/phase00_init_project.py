"""Phase 00 bootstrap and validation script for FleetVision.

This script is intentionally lightweight: it only uses Python standard library
modules so it can run before installing project dependencies.

Typical usage from the repository root:

    python scripts/phase00_init_project.py --fix
    python scripts/phase00_init_project.py --validate
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REQUIRED_FILES = [
    "README.md",
    "AGENTS.md",
    "CODEX_WORKFLOW.md",
    "PROJECT_CONTEXT_BRIEF.md",
    ".gitignore",
    ".env.example",
    "requirements.txt",
    "pyproject.toml",
    "docker-compose.yml",
    "sql/schema.sql",
    "configs/data/metadata_config.yaml",
    "configs/model/yolo_v001.yaml",
    "configs/model/thresholds.yaml",
    "src/fleetvision/__init__.py",
    "src/fleetvision/data/build_metadata.py",
    "src/fleetvision/vision/compare_damage.py",
    "tests/test_iou.py",
]

REQUIRED_DIRS = [
    "docs",
    ".agents/skills",
    "dataset/00_catalog/raw_excels",
    "dataset/01_raw/01_general_fleet/images",
    "dataset/01_raw/02_claimable_damage/images",
    "dataset/01_raw/03_minor_damage/images",
    "dataset/02_interim/01_extracted_exterior",
    "dataset/02_interim/02_quality_checked",
    "dataset/02_interim/03_review_queue",
    "dataset/02_interim/04_duplicate_checked",
    "dataset/03_reviewed/exterior",
    "dataset/03_reviewed/interior",
    "dataset/03_reviewed/low_quality",
    "dataset/03_reviewed/irrelevant",
    "dataset/03_reviewed/unknown",
    "dataset/04_annotations/cvat_exports",
    "dataset/04_annotations/labelstudio_exports",
    "dataset/04_annotations/yolo_labels_raw",
    "dataset/04_annotations/annotation_versions/v001_damage_bbox",
    "dataset/04_annotations/annotation_versions/v002_damage_bbox",
    "dataset/05_yolo/v001_damage_detect/images/train",
    "dataset/05_yolo/v001_damage_detect/images/val",
    "dataset/05_yolo/v001_damage_detect/images/test",
    "dataset/05_yolo/v001_damage_detect/labels/train",
    "dataset/05_yolo/v001_damage_detect/labels/val",
    "dataset/05_yolo/v001_damage_detect/labels/test",
    "dataset/05_yolo/v002_damage_detect",
    "dataset/06_demo_samples/images",
    "dataset/06_demo_samples/predictions",
    "notebooks",
    "src/fleetvision",
    "configs/data",
    "configs/model",
    "configs/database",
    "configs/dashboard",
    "sql/migrations",
    "scripts",
    "tests",
    "outputs/metadata",
    "outputs/predictions",
    "outputs/evaluation",
    "outputs/reports",
    "outputs/error_analysis/false_positive",
    "outputs/error_analysis/false_negative",
    "outputs/error_analysis/review_required",
    "models/yolo_damage_v001",
    "models/yolo_damage_v002",
    "demo/sample_images",
    "demo/sample_predictions",
    "demo/dashboard_screenshots",
    "demo/demo_video",
    "demo/final_package",
]

GITIGNORE_REQUIRED_SNIPPETS = [
    ".env",
    "dataset/01_raw/",
    "dataset/02_interim/",
    "dataset/03_reviewed/",
    "dataset/04_annotations/",
    "dataset/05_yolo/",
    "models/**/*.pt",
    "outputs/predictions/",
]

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
MODEL_SUFFIXES = {".pt", ".pth", ".onnx", ".engine", ".weights", ".tflite"}
CATALOG_SUFFIXES = {".xls", ".xlsx", ".xlsm", ".csv"}


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str = ""


def count_files(root: Path, suffixes: set[str]) -> int:
    if not root.exists():
        return 0
    return sum(1 for path in root.rglob("*") if path.is_file() and path.suffix.lower() in suffixes)


def ensure_gitkeep(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    gitkeep = directory / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()


def run_git(args: list[str], root: Path) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            check=False,
            text=True,
            capture_output=True,
        )
    except FileNotFoundError:
        return 127, "git command not found"
    return completed.returncode, (completed.stdout + completed.stderr).strip()


def validate(root: Path) -> list[CheckResult]:
    results: list[CheckResult] = []

    for relative_path in REQUIRED_FILES:
        path = root / relative_path
        results.append(
            CheckResult(
                relative_path,
                "PASS" if path.is_file() else "FAIL",
                "file exists" if path.is_file() else "missing file",
            )
        )

    for relative_path in REQUIRED_DIRS:
        path = root / relative_path
        results.append(
            CheckResult(
                relative_path,
                "PASS" if path.is_dir() else "FAIL",
                "directory exists" if path.is_dir() else "missing directory",
            )
        )

    gitignore_path = root / ".gitignore"
    gitignore_text = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""
    for snippet in GITIGNORE_REQUIRED_SNIPPETS:
        results.append(
            CheckResult(
                f".gitignore contains {snippet}",
                "PASS" if snippet in gitignore_text else "FAIL",
                "large/sensitive files protected" if snippet in gitignore_text else "missing ignore rule",
            )
        )

    raw_image_count = count_files(root / "dataset/01_raw", IMAGE_SUFFIXES)
    results.append(
        CheckResult(
            "local raw image count",
            "INFO",
            f"{raw_image_count:,} image file(s) found under dataset/01_raw; local data is allowed, but do not commit it",
        )
    )

    raw_catalog_count = count_files(root / "dataset/00_catalog/raw_excels", CATALOG_SUFFIXES)
    results.append(
        CheckResult(
            "local raw catalog count",
            "INFO",
            f"{raw_catalog_count:,} catalog file(s) found under dataset/00_catalog/raw_excels",
        )
    )

    model_count = count_files(root / "models", MODEL_SUFFIXES)
    results.append(
        CheckResult(
            "local model artifact count",
            "INFO",
            f"{model_count:,} model artifact file(s) found under models; keep weights out of GitHub",
        )
    )

    code, git_top = run_git(["rev-parse", "--show-toplevel"], root)
    if code == 0:
        results.append(CheckResult("git repository", "PASS", f"repo root: {git_top}"))
        code, status = run_git(["status", "--short"], root)
        if code == 0 and status:
            risky_lines = [
                line
                for line in status.splitlines()
                if any(
                    segment in line
                    for segment in [
                        "dataset/01_raw/",
                        "dataset/02_interim/",
                        "dataset/03_reviewed/",
                        "dataset/04_annotations/",
                        "dataset/05_yolo/",
                        "models/",
                        ".env",
                    ]
                )
            ]
            if risky_lines:
                results.append(
                    CheckResult(
                        "git risky changes",
                        "WARN",
                        "review before commit: " + " | ".join(risky_lines[:8]),
                    )
                )
            else:
                results.append(CheckResult("git risky changes", "PASS", "no obvious large/sensitive paths in git status"))
    else:
        results.append(CheckResult("git repository", "WARN", "not inside a Git repository yet"))

    return results


def print_results(results: list[CheckResult]) -> None:
    widths = {
        "name": max(len("item"), *(len(result.name) for result in results)),
        "status": max(len("status"), *(len(result.status) for result in results)),
    }
    print(f"{'item':<{widths['name']}}  {'status':<{widths['status']}}  detail")
    print(f"{'-' * widths['name']}  {'-' * widths['status']}  {'-' * 60}")
    for result in results:
        print(f"{result.name:<{widths['name']}}  {result.status:<{widths['status']}}  {result.detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap and validate FleetVision Phase 00 project setup.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="FleetVision repository root. Default: current directory.")
    parser.add_argument("--fix", action="store_true", help="Create missing required directories and .gitkeep files before validating.")
    parser.add_argument("--validate", action="store_true", help="Validate project setup. This is the default action.")
    parser.add_argument("--create-env", action="store_true", help="Create .env from .env.example when .env is missing. The created .env is local only.")
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.exists():
        print(f"ERROR: root path does not exist: {root}", file=sys.stderr)
        return 2

    if args.fix:
        for relative_path in REQUIRED_DIRS:
            ensure_gitkeep(root / relative_path)

    if args.create_env:
        env_example = root / ".env.example"
        env_file = root / ".env"
        if env_file.exists():
            print(".env already exists; leaving it unchanged.")
        elif env_example.exists():
            env_file.write_text(env_example.read_text(encoding="utf-8"), encoding="utf-8")
            print("Created local .env from .env.example. Do not commit .env.")
        else:
            print("WARNING: .env.example not found; cannot create .env.")

    results = validate(root)
    print_results(results)

    failed = [result for result in results if result.status == "FAIL"]
    if failed:
        print(f"\nPhase 00 validation failed: {len(failed)} required item(s) are missing.")
        return 1

    warnings = [result for result in results if result.status == "WARN"]
    if warnings:
        print(f"\nPhase 00 validation passed with {len(warnings)} warning(s). Review warnings before committing.")
    else:
        print("\nPhase 00 validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
