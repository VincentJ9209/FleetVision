from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

import pandas as pd
import yaml

from fleetvision.data.validation_error_human_review import (
    HUMAN_COLUMNS,
    SOURCE_COLUMNS,
    load_config as load_canonical_config,
    read_workbook_dataframe,
    sha256_file,
    source_case_fingerprint,
)


class PackageVerificationError(RuntimeError):
    """Raised when the frozen Phase 04.5L review package cannot be trusted."""


@dataclass(frozen=True)
class ReviewAppConfig:
    schema_version: str
    project_root: Path
    batch_root: Path
    workbook_relative_path: str
    workbook_sha256: str
    frozen_zip_path: Path
    frozen_zip_sha256: str
    expected_case_count: int
    canonical_config_path: Path
    workspace_root: Path
    reviewer: str
    timezone: str
    backup_every_successful_saves: int
    backup_retention: int
    completed_workbook_name: str

    @property
    def workbook_path(self) -> Path:
        return self.batch_root / PurePosixPath(self.workbook_relative_path)


@dataclass(frozen=True)
class SourceCase:
    case_index: int
    review_case_id: str
    source_case_fingerprint: str
    image_id: str
    image_filename: str
    auto_error_category: str
    auto_error_detail_ids: str
    error_case_count: int
    ground_truth_error_count: int
    prediction_error_count: int
    gt_count: int
    prediction_count: int
    max_prediction_confidence: float
    best_iou: float
    threshold_candidate: float
    threshold_designation: str
    original_relpath: str
    overlay_relpath: str
    original_path: Path
    overlay_path: Path


@dataclass(frozen=True)
class VerifiedSourcePackage:
    config: ReviewAppConfig
    batch_root: Path
    workbook_path: Path
    source_manifest: Mapping[str, Any]
    asset_manifest_count: int
    checksum_entry_count: int
    cases: tuple[SourceCase, ...]


def _resolve_path(project_root: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = project_root / path
    return path.resolve()


def _validate_sha256(value: str, label: str) -> str:
    digest = str(value).strip().upper()
    if len(digest) != 64 or any(character not in "0123456789ABCDEF" for character in digest):
        raise PackageVerificationError(f"{label} must be 64 uppercase hex characters")
    return digest


def _assert_not_test_path(path: Path, label: str) -> None:
    if any(part.lower() == "test" for part in path.parts):
        raise PackageVerificationError(f"{label} may not reference test split: {path}")


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _safe_relative_path(value: str, label: str) -> PurePosixPath:
    normalized = str(value).replace("\\", "/")
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or not pure.parts or ".." in pure.parts:
        raise PackageVerificationError(f"{label} must be a safe relative path: {value}")
    if any(part.lower() == "test" for part in pure.parts):
        raise PackageVerificationError(f"{label} may not reference test split: {value}")
    return pure


def _safe_batch_file(batch_root: Path, value: str, label: str) -> Path:
    pure = _safe_relative_path(value, label)
    path = (batch_root / pure).resolve()
    if not _is_relative_to(path, batch_root):
        raise PackageVerificationError(f"{label} escapes batch root: {value}")
    return path


def load_review_app_config(config_path: Path, project_root: Path) -> ReviewAppConfig:
    """Load and validate the local review-app configuration without creating files."""

    project_root = project_root.resolve()
    resolved_config = _resolve_path(project_root, str(config_path))
    if not resolved_config.is_file():
        raise PackageVerificationError(f"review-app config not found: {resolved_config}")

    raw = yaml.safe_load(resolved_config.read_text(encoding="utf-8")) or {}
    try:
        source = raw["source"]
        workspace = raw["workspace"]
        config = ReviewAppConfig(
            schema_version=str(raw["schema_version"]).strip(),
            project_root=project_root,
            batch_root=_resolve_path(project_root, str(source["batch_root"])),
            workbook_relative_path=str(source["workbook_relative_path"]).replace("\\", "/"),
            workbook_sha256=_validate_sha256(source["workbook_sha256"], "workbook_sha256"),
            frozen_zip_path=_resolve_path(project_root, str(source["frozen_zip_path"])),
            frozen_zip_sha256=_validate_sha256(
                source["frozen_zip_sha256"],
                "frozen_zip_sha256",
            ),
            expected_case_count=int(source["expected_case_count"]),
            canonical_config_path=_resolve_path(
                project_root,
                str(source["canonical_config_path"]),
            ),
            workspace_root=_resolve_path(project_root, str(workspace["root"])),
            reviewer=str(workspace["reviewer"]).strip(),
            timezone=str(workspace["timezone"]).strip(),
            backup_every_successful_saves=int(
                workspace["backup_every_successful_saves"]
            ),
            backup_retention=int(workspace["backup_retention"]),
            completed_workbook_name=str(
                workspace["completed_workbook_name"]
            ).strip(),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise PackageVerificationError(
            f"invalid review-app config structure: {exc}"
        ) from exc

    _safe_relative_path(config.workbook_relative_path, "workbook_relative_path")
    _assert_not_test_path(config.batch_root, "batch_root")
    _assert_not_test_path(config.workbook_path, "workbook_path")
    _assert_not_test_path(config.frozen_zip_path, "frozen_zip_path")
    _assert_not_test_path(config.workspace_root, "workspace_root")

    if config.schema_version != "1":
        raise PackageVerificationError(
            f"unsupported review-app schema_version: {config.schema_version}"
        )
    if config.expected_case_count <= 0:
        raise PackageVerificationError("expected_case_count must be positive")
    if not config.reviewer:
        raise PackageVerificationError("reviewer is required")
    if not config.timezone:
        raise PackageVerificationError("timezone is required")
    if config.backup_every_successful_saves <= 0:
        raise PackageVerificationError(
            "backup_every_successful_saves must be positive"
        )
    if config.backup_retention <= 0:
        raise PackageVerificationError("backup_retention must be positive")
    if not config.completed_workbook_name.lower().endswith(".xlsx"):
        raise PackageVerificationError(
            "completed_workbook_name must end with .xlsx"
        )
    if not config.canonical_config_path.is_file():
        raise PackageVerificationError(
            f"canonical config not found: {config.canonical_config_path}"
        )
    if _is_relative_to(config.workspace_root, config.project_root):
        raise PackageVerificationError(
            "workspace_root must remain outside the repository"
        )
    if _is_relative_to(config.workspace_root, config.batch_root):
        raise PackageVerificationError(
            "workspace_root must remain outside the frozen source batch"
        )
    return config


def _read_asset_manifest(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise PackageVerificationError(f"asset manifest not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"relative_path", "size_bytes", "sha256"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise PackageVerificationError(
                f"asset manifest missing required columns: {sorted(required)}"
            )
        return [
            {key: str(value or "").strip() for key, value in row.items()}
            for row in reader
        ]


def _read_checksum_ledger(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise PackageVerificationError(f"checksum ledger not found: {path}")

    entries: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            raise PackageVerificationError(
                f"checksum ledger malformed at line {line_number}"
            )
        digest = _validate_sha256(parts[0], f"checksum line {line_number}")
        relative = _safe_relative_path(
            parts[1].strip(),
            f"checksum line {line_number}",
        ).as_posix()
        if relative in entries:
            raise PackageVerificationError(
                f"checksum ledger duplicate path: {relative}"
            )
        entries[relative] = digest
    return entries


def _all_batch_files(batch_root: Path) -> set[str]:
    return {
        path.relative_to(batch_root).as_posix()
        for path in batch_root.rglob("*")
        if path.is_file()
    }


def _verify_package_ledgers(batch_root: Path) -> tuple[int, int]:
    asset_manifest_path = batch_root / "manifest/asset_manifest.csv"
    checksum_path = batch_root / "manifest/checksums.sha256"

    all_files = _all_batch_files(batch_root)
    expected_asset_paths = all_files - {
        "manifest/asset_manifest.csv",
        "manifest/checksums.sha256",
    }
    expected_checksum_paths = all_files - {"manifest/checksums.sha256"}

    rows = _read_asset_manifest(asset_manifest_path)
    manifest_by_path: dict[str, dict[str, str]] = {}
    for row in rows:
        relative = _safe_relative_path(
            row["relative_path"],
            "asset manifest relative_path",
        ).as_posix()
        if relative in manifest_by_path:
            raise PackageVerificationError(
                f"asset manifest duplicate path: {relative}"
            )
        manifest_by_path[relative] = row

    if set(manifest_by_path) != expected_asset_paths:
        missing = sorted(expected_asset_paths - set(manifest_by_path))
        extra = sorted(set(manifest_by_path) - expected_asset_paths)
        raise PackageVerificationError(
            f"asset manifest file-set mismatch: missing={missing[:5]} extra={extra[:5]}"
        )

    for relative, row in manifest_by_path.items():
        path = _safe_batch_file(batch_root, relative, "asset manifest path")
        if not path.is_file():
            raise PackageVerificationError(
                f"asset manifest file missing: {relative}"
            )
        try:
            expected_size = int(row["size_bytes"])
        except ValueError as exc:
            raise PackageVerificationError(
                f"asset manifest size is invalid: {relative}"
            ) from exc
        expected_hash = _validate_sha256(
            row["sha256"],
            f"asset manifest SHA256 for {relative}",
        )
        if path.stat().st_size != expected_size:
            raise PackageVerificationError(
                f"asset manifest size mismatch: {relative}"
            )
        if sha256_file(path) != expected_hash:
            raise PackageVerificationError(
                f"asset manifest SHA256 mismatch: {relative}"
            )

    checksums = _read_checksum_ledger(checksum_path)
    if set(checksums) != expected_checksum_paths:
        missing = sorted(expected_checksum_paths - set(checksums))
        extra = sorted(set(checksums) - expected_checksum_paths)
        raise PackageVerificationError(
            f"checksum ledger file-set mismatch: missing={missing[:5]} extra={extra[:5]}"
        )

    for relative, expected_hash in checksums.items():
        path = _safe_batch_file(batch_root, relative, "checksum path")
        if not path.is_file() or sha256_file(path) != expected_hash:
            raise PackageVerificationError(
                f"checksum ledger mismatch: {relative}"
            )

    return len(rows), len(checksums)


def _verify_source_manifest(
    config: ReviewAppConfig,
    canonical_config: Any,
    source_manifest: Mapping[str, Any],
) -> None:
    expected = {
        "gate_id": "04.5L-PREP",
        "classification": "VALIDATION_ERROR_HUMAN_REVIEW_PACKAGE_PREPARED",
        "review_batch_id": config.batch_root.name,
        "schema_version": canonical_config.schema_version,
        "source_zip_filename": canonical_config.expected_source_zip_name,
        "source_zip_sha256": canonical_config.expected_source_zip_sha256,
        "source_gate_classification": canonical_config.expected_gate_classification,
        "case_count": config.expected_case_count,
        "threshold_designation": canonical_config.threshold_designation,
        "test_split_read": False,
        "model_inference_executed": False,
        "training_started": False,
        "annotation_modified": False,
        "retraining_status": "NOT_YET_APPROVED",
        "deployment_acceptance": "NOT_YET_APPROVED",
    }
    for key, expected_value in expected.items():
        if source_manifest.get(key) != expected_value:
            raise PackageVerificationError(
                f"source manifest mismatch: {key}="
                f"{source_manifest.get(key)!r}, expected={expected_value!r}"
            )

    try:
        threshold = float(source_manifest.get("threshold_candidate"))
    except (TypeError, ValueError) as exc:
        raise PackageVerificationError(
            "source manifest threshold_candidate is invalid"
        ) from exc
    if not math.isclose(
        threshold,
        canonical_config.threshold_candidate,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise PackageVerificationError(
            "source manifest threshold_candidate mismatch"
        )


def _to_int(value: Any, label: str) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise PackageVerificationError(f"{label} must be an integer") from exc


def _to_float(value: Any, label: str) -> float:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise PackageVerificationError(f"{label} must be numeric") from exc
    if not math.isfinite(number):
        raise PackageVerificationError(f"{label} must be finite")
    return number


def _verify_pristine_workbook(
    frame: pd.DataFrame,
    *,
    config: ReviewAppConfig,
    canonical_config: Any,
    source_manifest: Mapping[str, Any],
) -> tuple[SourceCase, ...]:
    if len(frame) != config.expected_case_count:
        raise PackageVerificationError(
            f"case count mismatch: expected={config.expected_case_count} "
            f"actual={len(frame)}"
        )

    for column in ("review_case_id", "source_case_fingerprint", "image_id"):
        if frame[column].eq("").any() or frame[column].duplicated().any():
            raise PackageVerificationError(
                f"{column} values must be unique and non-blank"
            )

    if set(frame["review_status"]) != {"pending"}:
        raise PackageVerificationError(
            "frozen source Workbook must contain only pending reviews"
        )
    for column in HUMAN_COLUMNS:
        if column == "review_status":
            continue
        if frame[column].ne("").any():
            raise PackageVerificationError(
                f"frozen source Workbook human field must be blank: {column}"
            )

    expected_batch_id = str(source_manifest["review_batch_id"])
    expected_source_zip_hash = str(source_manifest["source_zip_sha256"])
    if set(frame["review_batch_id"]) != {expected_batch_id}:
        raise PackageVerificationError("Workbook review_batch_id mismatch")
    if set(frame["source_04_5k_zip_sha256"]) != {expected_source_zip_hash}:
        raise PackageVerificationError("Workbook source ZIP SHA256 mismatch")
    if set(frame["threshold_designation"]) != {
        canonical_config.threshold_designation
    }:
        raise PackageVerificationError("Workbook threshold designation mismatch")

    cases: list[SourceCase] = []
    for case_index, row in enumerate(frame.to_dict(orient="records"), start=1):
        review_case_id = str(row["review_case_id"])
        actual_fingerprint = str(row["source_case_fingerprint"]).upper()
        expected_fingerprint = source_case_fingerprint(row)
        if actual_fingerprint != expected_fingerprint:
            raise PackageVerificationError(
                f"source fingerprint mismatch: {review_case_id}"
            )

        threshold = _to_float(
            row["threshold_candidate"],
            f"{review_case_id}.threshold_candidate",
        )
        if not math.isclose(
            threshold,
            canonical_config.threshold_candidate,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise PackageVerificationError(
                f"threshold candidate mismatch: {review_case_id}"
            )

        original_relpath = _safe_relative_path(
            row["original_image_relpath"],
            f"{review_case_id}.original_image_relpath",
        ).as_posix()
        overlay_relpath = _safe_relative_path(
            row["overlay_image_relpath"],
            f"{review_case_id}.overlay_image_relpath",
        ).as_posix()
        original_path = _safe_batch_file(
            config.batch_root,
            original_relpath,
            f"{review_case_id}.original",
        )
        overlay_path = _safe_batch_file(
            config.batch_root,
            overlay_relpath,
            f"{review_case_id}.overlay",
        )
        if not original_path.is_file() or not overlay_path.is_file():
            raise PackageVerificationError(
                f"review assets missing: {review_case_id}"
            )

        image_id = str(row["image_id"])
        if str(row["image_filename"]) != image_id:
            raise PackageVerificationError(
                f"image filename mismatch: {review_case_id}"
            )
        if original_relpath != f"assets/original/{image_id}":
            raise PackageVerificationError(
                f"unexpected original image path: {review_case_id}"
            )
        if overlay_relpath != f"assets/overlay/{review_case_id}.jpg":
            raise PackageVerificationError(
                f"unexpected overlay image path: {review_case_id}"
            )

        cases.append(
            SourceCase(
                case_index=case_index,
                review_case_id=review_case_id,
                source_case_fingerprint=actual_fingerprint,
                image_id=image_id,
                image_filename=str(row["image_filename"]),
                auto_error_category=str(row["auto_error_category"]),
                auto_error_detail_ids=str(row["auto_error_detail_ids"]),
                error_case_count=_to_int(
                    row["error_case_count"],
                    f"{review_case_id}.error_case_count",
                ),
                ground_truth_error_count=_to_int(
                    row["ground_truth_error_count"],
                    f"{review_case_id}.ground_truth_error_count",
                ),
                prediction_error_count=_to_int(
                    row["prediction_error_count"],
                    f"{review_case_id}.prediction_error_count",
                ),
                gt_count=_to_int(
                    row["gt_count"],
                    f"{review_case_id}.gt_count",
                ),
                prediction_count=_to_int(
                    row["prediction_count"],
                    f"{review_case_id}.prediction_count",
                ),
                max_prediction_confidence=_to_float(
                    row["max_prediction_confidence"],
                    f"{review_case_id}.max_prediction_confidence",
                ),
                best_iou=_to_float(
                    row["best_iou"],
                    f"{review_case_id}.best_iou",
                ),
                threshold_candidate=threshold,
                threshold_designation=str(row["threshold_designation"]),
                original_relpath=original_relpath,
                overlay_relpath=overlay_relpath,
                original_path=original_path,
                overlay_path=overlay_path,
            )
        )
    return tuple(cases)


def load_verified_source_package(
    config: ReviewAppConfig,
) -> VerifiedSourcePackage:
    """Verify the immutable formal package and return its trusted source cases."""

    if not config.batch_root.is_dir():
        raise PackageVerificationError(
            f"batch root not found: {config.batch_root}"
        )
    if not config.workbook_path.is_file():
        raise PackageVerificationError(
            f"Workbook not found: {config.workbook_path}"
        )
    if sha256_file(config.workbook_path) != config.workbook_sha256:
        raise PackageVerificationError("Workbook SHA256 mismatch")
    if not config.frozen_zip_path.is_file():
        raise PackageVerificationError(
            f"frozen package ZIP not found: {config.frozen_zip_path}"
        )
    if sha256_file(config.frozen_zip_path) != config.frozen_zip_sha256:
        raise PackageVerificationError("frozen package ZIP SHA256 mismatch")

    canonical_config = load_canonical_config(
        config.canonical_config_path,
        config.project_root,
    )
    source_manifest_path = config.batch_root / "manifest/source_manifest.json"
    if not source_manifest_path.is_file():
        raise PackageVerificationError(
            f"source manifest not found: {source_manifest_path}"
        )
    source_manifest = json.loads(
        source_manifest_path.read_text(encoding="utf-8")
    )
    _verify_source_manifest(config, canonical_config, source_manifest)

    asset_manifest_count, checksum_entry_count = _verify_package_ledgers(
        config.batch_root
    )
    expected_asset_count = config.expected_case_count * 2 + 2
    expected_checksum_count = expected_asset_count + 1
    if asset_manifest_count != expected_asset_count:
        raise PackageVerificationError(
            f"asset manifest count mismatch: expected={expected_asset_count} "
            f"actual={asset_manifest_count}"
        )
    if checksum_entry_count != expected_checksum_count:
        raise PackageVerificationError(
            f"checksum entry count mismatch: expected={expected_checksum_count} "
            f"actual={checksum_entry_count}"
        )

    frame = read_workbook_dataframe(config.workbook_path)
    cases = _verify_pristine_workbook(
        frame,
        config=config,
        canonical_config=canonical_config,
        source_manifest=source_manifest,
    )
    return VerifiedSourcePackage(
        config=config,
        batch_root=config.batch_root,
        workbook_path=config.workbook_path,
        source_manifest=source_manifest,
        asset_manifest_count=asset_manifest_count,
        checksum_entry_count=checksum_entry_count,
        cases=cases,
    )
