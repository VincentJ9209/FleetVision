"""CLI for FleetVision Phase 04.5F canonical annotation and split QA."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from fleetvision.data.validate_external_annotation_split_balance import (
    AnnotationQaError,
    load_annotation_qa_config,
    run_annotation_split_balance_qa,
)

DEFAULT_CONFIG = Path("configs/data/external_annotation_split_balance_qa_config.yaml")


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "PROJECT_CONTEXT_BRIEF.md").is_file() and (candidate / "src/fleetvision").is_dir():
            return candidate
    return current


def locate_latest_plan_zip(upload_root: Path) -> Path:
    candidates = sorted(
        upload_root.glob("04_5F-7_*_ZIP_LOG.zip"),
        key=lambda path: path.stat().st_mtime_ns,
        reverse=True,
    )
    if not candidates:
        raise AnnotationQaError(
            f"no 04.5F-7 split-plan ZIP found under {upload_root}; pass --split-plan-zip"
        )
    return candidates[0]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate canonical COCO annotations against the immutable group-safe split plan."
    )
    parser.add_argument("--project-root", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--split-plan-zip", type=Path, default=None)
    parser.add_argument("--output-root", type=Path, default=None)
    return parser


def _package_evidence(root: Path, destination: Path) -> str:
    """Create ZIP and sidecar via sibling staging without overwriting evidence."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    sidecar = Path(str(destination) + ".sha256.txt")
    if destination.exists() or sidecar.exists():
        raise AnnotationQaError(
            f"QA evidence package already exists: zip={destination.exists()} sidecar={sidecar.exists()}"
        )
    zip_handle, zip_name = tempfile.mkstemp(
        prefix=f".{destination.name}.staging-", suffix=".zip", dir=destination.parent
    )
    os.close(zip_handle)
    staged_zip = Path(zip_name)
    sidecar_handle, sidecar_name = tempfile.mkstemp(
        prefix=f".{sidecar.name}.staging-", suffix=".txt", dir=destination.parent
    )
    os.close(sidecar_handle)
    staged_sidecar = Path(sidecar_name)
    promoted_zip = False
    try:
        with zipfile.ZipFile(staged_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(root).as_posix())
        with zipfile.ZipFile(staged_zip, "r") as archive:
            bad = archive.testzip()
            if bad:
                raise AnnotationQaError(f"QA evidence ZIP CRC failure: {bad}")
        zip_sha256 = hashlib.sha256(staged_zip.read_bytes()).hexdigest().upper()
        staged_sidecar.write_text(
            f"{zip_sha256}  {destination.name}\n", encoding="utf-8"
        )
        os.replace(staged_zip, destination)
        promoted_zip = True
        os.replace(staged_sidecar, sidecar)
        return zip_sha256
    except AnnotationQaError:
        raise
    except Exception as exc:
        raise AnnotationQaError(f"QA evidence packaging failed: {exc}") from exc
    finally:
        staged_zip.unlink(missing_ok=True)
        staged_sidecar.unlink(missing_ok=True)
        if promoted_zip and not sidecar.exists():
            destination.unlink(missing_ok=True)


def _print(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = find_project_root(args.project_root)
    config_path = args.config if args.config.is_absolute() else project_root / args.config
    local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    upload_root = local_app_data / "Temp/FleetVision_GateLogs/Upload"
    work_root = local_app_data / "Temp/FleetVision_GateLogs/Work"
    token = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + os.urandom(4).hex()
    run_name = f"04_5F-8C_{token}"
    explicit_output = args.output_root is not None
    output_root = (
        args.output_root.resolve()
        if explicit_output
        else work_root / run_name / "annotation_qa_evidence"
    )
    plan_zip = (
        args.split_plan_zip.resolve()
        if args.split_plan_zip is not None
        else locate_latest_plan_zip(upload_root)
    )
    try:
        config = load_annotation_qa_config(config_path, project_root=project_root)
        result = run_annotation_split_balance_qa(
            config,
            plan_zip=plan_zip,
            output_root=output_root,
        )
    except AnnotationQaError as exc:
        _print(
            {
                "exit_code": 2,
                "classification": "ANNOTATION_AND_SPLIT_BALANCE_QA_FAILED",
                "error": str(exc),
                "training_acceptance": "NOT_YET_APPROVED",
            }
        )
        return 2

    zip_path = (
        Path(str(output_root) + ".zip")
        if explicit_output
        else upload_root / f"{run_name}_ZIP_LOG.zip"
    )
    try:
        zip_sha256 = _package_evidence(output_root, zip_path)
    except AnnotationQaError as exc:
        _print(
            {
                "exit_code": 2,
                "classification": "ANNOTATION_AND_SPLIT_BALANCE_QA_FAILED",
                "error": str(exc),
                "training_acceptance": "NOT_YET_APPROVED",
            }
        )
        return 2
    _print(
        {
            "exit_code": 0,
            "classification": result.classification,
            "source_images": result.source_images,
            "source_annotations": result.source_annotations,
            "model_included_images": result.model_included_images,
            "excluded_correlated_eval_variants": result.excluded_correlated_eval_variants,
            "source_families": result.source_families,
            "family_leakage_count": result.family_leakage_count,
            "invalid_bbox_count": result.invalid_bbox_count,
            "unresolved_plan_to_coco_joins": result.unresolved_plan_to_coco_joins,
            "annotation_count_inconsistent_families": result.annotation_count_inconsistent_families,
            "targeted_visual_review_items": result.targeted_visual_review_items,
            "output_root": str(result.output_root),
            "zip_log": str(zip_path),
            "zip_sha256": zip_sha256,
            "training_acceptance": "NOT_YET_APPROVED",
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
