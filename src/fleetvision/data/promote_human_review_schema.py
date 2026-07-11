"""Promote verified Pilot 500 human-review fields into canonical review schema.

This Phase 04E adapter reads the verified formal merge CSV, validates the
human-review fields, maps them to the canonical review-label column names, and
writes a separately versioned canonical CSV plus provenance reports. It never
modifies the formal merge input or the existing reviewed-dataset builder.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from fleetvision.data.validate_pilot_human_review import (
    PilotHumanReviewValidationConfig,
    validate_pilot_human_review,
)
from fleetvision.data.validate_review_labels import (
    ERROR_COLUMNS as CANONICAL_ERROR_COLUMNS,
    validate_review_labels,
)


DEFAULT_CONFIG_PATH = Path("configs/data/human_review_schema_promotion_config.yaml")
DEFAULT_INPUT_CSV = Path(
    "outputs/manual_review/collaboration/pilot500_human_review_results_collaboration.csv"
)
DEFAULT_OUTPUT_CSV = Path(
    "outputs/manual_review/collaboration/pilot500_review_labels_canonical.csv"
)
DEFAULT_SUMMARY_CSV = Path(
    "outputs/metadata/pilot500_review_schema_promotion_summary.csv"
)
DEFAULT_ERRORS_CSV = Path(
    "outputs/metadata/pilot500_review_schema_promotion_errors.csv"
)
DEFAULT_MANIFEST_CSV = Path(
    "outputs/metadata/pilot500_review_schema_promotion_manifest.csv"
)
DEFAULT_REVIEW_LABEL_SCHEMA = Path("configs/data/review_label_schema.yaml")

IDENTITY_COLUMNS = [
    "review_id",
    "image_id",
    "source_bucket",
    "original_path",
    "filename",
]

HUMAN_TO_CANONICAL = {
    "human_photo_type_review": "photo_type_review",
    "human_angle_review": "angle_review",
    "human_is_exterior_review": "is_exterior_review",
    "human_has_visible_damage_review": "has_visible_damage_review",
    "human_severity_review": "severity_review",
    "human_review_status": "review_status",
    "human_reviewer": "reviewer",
    "human_reviewed_at": "reviewed_at",
    "human_review_notes": "review_notes",
}

CANONICAL_OUTPUT_COLUMNS = IDENTITY_COLUMNS + list(HUMAN_TO_CANONICAL.values())
REQUIRED_INPUT_COLUMNS = IDENTITY_COLUMNS + list(HUMAN_TO_CANONICAL.keys())
SUMMARY_COLUMNS = [
    "source_rows",
    "promoted_rows",
    "unique_review_id_count",
    "reviewed_count",
    "pending_count",
    "input_validation_error_count",
    "output_validation_error_count",
    "mapping_mismatch_count",
    "logical_fingerprint",
    "is_valid",
]
MANIFEST_COLUMNS = [
    "promotion_timestamp_utc",
    "phase",
    "promotion_status",
    "input_path",
    "output_path",
    "summary_path",
    "errors_path",
    "input_sha256",
    "output_sha256",
    "input_size_bytes",
    "output_size_bytes",
    "row_count",
    "unique_review_id_count",
    "reviewed_count",
    "pending_count",
    "input_validation_error_count",
    "output_validation_error_count",
    "mapping_mismatch_count",
    "logical_fingerprint",
    "column_mapping_json",
    "output_columns_json",
]


@dataclass(frozen=True)
class PromotionConfig:
    """Resolved paths and validation requirements for schema promotion."""

    input_csv: Path
    output_csv: Path
    summary_csv: Path
    errors_csv: Path
    manifest_csv: Path
    review_label_schema: Path
    expected_rows: int = 500
    required_status: str = "reviewed"
    allow_overwrite: bool = False


@dataclass(frozen=True)
class PromotionResult:
    """Verified result returned after canonical schema promotion."""

    is_valid: bool
    row_count: int
    unique_review_id_count: int
    reviewed_count: int
    pending_count: int
    input_validation_error_count: int
    output_validation_error_count: int
    mapping_mismatch_count: int
    logical_fingerprint: str
    input_sha256: str
    output_sha256: str


def find_project_root(start: Path | None = None) -> Path:
    """Find the FleetVision project root from a starting path."""
    current = (start or Path.cwd()).resolve()
    markers = ["PROJECT_CONTEXT_BRIEF.md", "src/fleetvision", "configs/data"]
    for path in [current, *current.parents]:
        if all((path / marker).exists() for marker in markers):
            return path
    return current


def resolve_path(path: str | Path, project_root: Path) -> Path:
    """Resolve a project-relative path."""
    candidate = Path(path)
    return candidate if candidate.is_absolute() else project_root / candidate


def load_config(config_path: Path, project_root: Path) -> PromotionConfig:
    """Load schema-promotion YAML and resolve all paths."""
    if not config_path.exists():
        raise FileNotFoundError(f"schema promotion config not found: {config_path}")
    with config_path.open(encoding="utf-8") as file:
        raw: dict[str, Any] = yaml.safe_load(file) or {}

    return PromotionConfig(
        input_csv=resolve_path(raw.get("input_csv", DEFAULT_INPUT_CSV), project_root),
        output_csv=resolve_path(raw.get("output_csv", DEFAULT_OUTPUT_CSV), project_root),
        summary_csv=resolve_path(raw.get("summary_csv", DEFAULT_SUMMARY_CSV), project_root),
        errors_csv=resolve_path(raw.get("errors_csv", DEFAULT_ERRORS_CSV), project_root),
        manifest_csv=resolve_path(raw.get("manifest_csv", DEFAULT_MANIFEST_CSV), project_root),
        review_label_schema=resolve_path(
            raw.get("review_label_schema", DEFAULT_REVIEW_LABEL_SCHEMA), project_root
        ),
        expected_rows=int(raw.get("expected_rows", 500)),
        required_status=str(raw.get("required_status", "reviewed")).strip().lower(),
        allow_overwrite=bool(raw.get("allow_overwrite", False)),
    )


def read_formal_merge(input_csv: Path) -> pd.DataFrame:
    """Read the formal merge CSV as strings with UTF-8 BOM support."""
    if not input_csv.exists():
        raise FileNotFoundError(f"formal merge CSV not found: {input_csv}")
    return pd.read_csv(
        input_csv,
        dtype="string",
        keep_default_na=False,
        encoding="utf-8-sig",
    ).astype(str)


def promote_dataframe(source: pd.DataFrame) -> pd.DataFrame:
    """Map verified human-review fields to canonical names without mutation."""
    missing = [column for column in REQUIRED_INPUT_COLUMNS if column not in source.columns]
    if missing:
        raise ValueError("formal merge CSV missing required columns: " + ", ".join(missing))

    promoted = source.loc[:, IDENTITY_COLUMNS + list(HUMAN_TO_CANONICAL)].copy()
    promoted = promoted.rename(columns=HUMAN_TO_CANONICAL)
    return promoted.loc[:, CANONICAL_OUTPUT_COLUMNS].astype(str).reset_index(drop=True)


def logical_fingerprint(dataframe: pd.DataFrame) -> str:
    """Return deterministic SHA256 for ordered canonical logical values."""
    payload = dataframe.loc[:, CANONICAL_OUTPUT_COLUMNS].to_csv(
        index=False,
        lineterminator="\n",
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def execute_schema_promotion(config: PromotionConfig) -> PromotionResult:
    """Validate, map, transactionally write, and post-verify promotion outputs."""
    final_paths = [
        config.output_csv,
        config.summary_csv,
        config.errors_csv,
        config.manifest_csv,
    ]
    _validate_final_path_policy(final_paths, config.allow_overwrite)

    source = read_formal_merge(config.input_csv)
    input_validation = validate_pilot_human_review(
        source,
        PilotHumanReviewValidationConfig(
            input_csv=config.input_csv,
            summary_csv=config.summary_csv,
            errors_csv=config.errors_csv,
            expected_rows=config.expected_rows,
            reviewed_status_value=config.required_status,
        ),
    )
    if not input_validation.is_valid:
        raise ValueError(
            f"input human review validation failed with {input_validation.error_count} error(s)"
        )

    statuses = source["human_review_status"].astype(str).str.strip().str.lower()
    nonrequired = int((statuses != config.required_status).sum())
    if nonrequired:
        raise ValueError(
            f"input contains {nonrequired} row(s) whose human_review_status is not "
            f"{config.required_status}"
        )

    promoted = promote_dataframe(source)
    mismatch_count = _count_mapping_mismatches(source, promoted)
    if mismatch_count:
        raise ValueError(f"schema mapping produced {mismatch_count} mismatch(es)")

    fingerprint = logical_fingerprint(promoted)
    input_hash = sha256_file(config.input_csv)

    config.output_csv.parent.mkdir(parents=True, exist_ok=True)
    stage_parent = config.output_csv.parent
    with tempfile.TemporaryDirectory(
        prefix=".schema_promotion_staging_",
        dir=stage_parent,
    ) as temporary_directory:
        staging_root = Path(temporary_directory)
        staged_output = staging_root / config.output_csv.name
        staged_summary = staging_root / config.summary_csv.name
        staged_errors = staging_root / config.errors_csv.name
        staged_manifest = staging_root / config.manifest_csv.name

        promoted.to_csv(staged_output, index=False, encoding="utf-8-sig")
        output_hash = sha256_file(staged_output)

        output_validation = validate_review_labels(
            input_csv=staged_output,
            schema_path=config.review_label_schema,
        )
        if not output_validation.is_valid:
            raise ValueError(
                f"canonical output validation failed with {output_validation.error_count} error(s)"
            )

        staged_roundtrip = pd.read_csv(
            staged_output,
            dtype="string",
            keep_default_na=False,
            encoding="utf-8-sig",
        ).astype(str)
        roundtrip_mismatches = _count_dataframe_mismatches(promoted, staged_roundtrip)
        if roundtrip_mismatches:
            raise ValueError(
                f"canonical output round-trip produced {roundtrip_mismatches} mismatch(es)"
            )
        if logical_fingerprint(staged_roundtrip) != fingerprint:
            raise ValueError("canonical output logical fingerprint changed after CSV round-trip")

        result = PromotionResult(
            is_valid=True,
            row_count=int(len(promoted)),
            unique_review_id_count=int(promoted["review_id"].nunique(dropna=False)),
            reviewed_count=int((promoted["review_status"].str.lower() == config.required_status).sum()),
            pending_count=int((promoted["review_status"].str.lower() == "pending").sum()),
            input_validation_error_count=int(input_validation.error_count),
            output_validation_error_count=int(output_validation.error_count),
            mapping_mismatch_count=int(mismatch_count),
            logical_fingerprint=fingerprint,
            input_sha256=input_hash,
            output_sha256=output_hash,
        )

        _write_staged_reports(
            result=result,
            config=config,
            staged_summary=staged_summary,
            staged_errors=staged_errors,
            staged_manifest=staged_manifest,
            output_size_bytes=staged_output.stat().st_size,
        )

        staged_to_final = {
            staged_output: config.output_csv,
            staged_summary: config.summary_csv,
            staged_errors: config.errors_csv,
            staged_manifest: config.manifest_csv,
        }
        backups = _promote_transactionally(
            staged_to_final,
            allow_overwrite=config.allow_overwrite,
            staging_root=staging_root,
        )
        try:
            _post_verify(result, config)
        except Exception:
            _rollback_promoted_files(staged_to_final.values(), backups)
            raise

    return result


def sha256_file(path: Path) -> str:
    """Return uppercase SHA256 for one file."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Build CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Promote verified FleetVision human-review fields to canonical schema."
    )
    parser.add_argument("--project-root", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--summary-output", type=Path, default=None)
    parser.add_argument("--errors-output", type=Path, default=None)
    parser.add_argument("--manifest-output", type=Path, default=None)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    args = parse_args(argv)
    project_root = find_project_root(args.project_root)
    config_path = resolve_path(args.config, project_root)
    try:
        config = load_config(config_path, project_root)
        config = _apply_overrides(config, args, project_root)
        result = execute_schema_promotion(config)
    except Exception as exc:  # noqa: BLE001 - concise operator-facing failure.
        print(f"ERROR: {exc}")
        print("Gate classification: SCHEMA_PROMOTION_BLOCKED")
        print("FORMAL_MERGE_INPUT_MODIFIED: NO")
        print("REVIEWED_DATASET_BUILD_EXECUTED: NO")
        return 2

    print("=== FleetVision Phase 04E Human Review Schema Promotion ===")
    print("Gate classification: SCHEMA_PROMOTION_VERIFIED")
    print(f"Promoted output: {config.output_csv}")
    print(f"Summary: {config.summary_csv}")
    print(f"Errors: {config.errors_csv}")
    print(f"Manifest: {config.manifest_csv}")
    print(
        "Promotion: "
        f"rows={result.row_count}, "
        f"unique_review_ids={result.unique_review_id_count}, "
        f"reviewed={result.reviewed_count}, "
        f"pending={result.pending_count}, "
        f"validation_errors={result.input_validation_error_count + result.output_validation_error_count}, "
        f"mapping_mismatches={result.mapping_mismatch_count}"
    )
    print(f"Canonical logical fingerprint: {result.logical_fingerprint}")
    print("FORMAL_MERGE_INPUT_MODIFIED: NO")
    print("EXISTING_BUILDER_MODIFIED: NO")
    print("REVIEWED_DATASET_BUILD_EXECUTED: NO")
    print("STOPPED_BEFORE_REVIEWED_DATASET_BUILD_GATE")
    return 0


def _apply_overrides(
    config: PromotionConfig,
    args: argparse.Namespace,
    project_root: Path,
) -> PromotionConfig:
    return replace(
        config,
        input_csv=resolve_path(args.input, project_root) if args.input else config.input_csv,
        output_csv=resolve_path(args.output, project_root) if args.output else config.output_csv,
        summary_csv=(
            resolve_path(args.summary_output, project_root)
            if args.summary_output
            else config.summary_csv
        ),
        errors_csv=(
            resolve_path(args.errors_output, project_root)
            if args.errors_output
            else config.errors_csv
        ),
        manifest_csv=(
            resolve_path(args.manifest_output, project_root)
            if args.manifest_output
            else config.manifest_csv
        ),
        allow_overwrite=config.allow_overwrite or bool(args.overwrite),
    )


def _validate_final_path_policy(paths: list[Path], allow_overwrite: bool) -> None:
    existing = [path for path in paths if path.exists()]
    if existing and not allow_overwrite:
        raise FileExistsError(
            "schema promotion output already exists; explicit overwrite is required: "
            + ", ".join(str(path) for path in existing)
        )


def _count_mapping_mismatches(source: pd.DataFrame, promoted: pd.DataFrame) -> int:
    mismatches = 0
    for column in IDENTITY_COLUMNS:
        mismatches += int((source[column].astype(str) != promoted[column].astype(str)).sum())
    for source_column, target_column in HUMAN_TO_CANONICAL.items():
        mismatches += int(
            (source[source_column].astype(str) != promoted[target_column].astype(str)).sum()
        )
    return mismatches


def _count_dataframe_mismatches(expected: pd.DataFrame, actual: pd.DataFrame) -> int:
    if expected.columns.tolist() != actual.columns.tolist():
        return 1
    if len(expected) != len(actual):
        return abs(len(expected) - len(actual)) or 1
    return int((expected.astype(str) != actual.astype(str)).sum().sum())


def _write_staged_reports(
    *,
    result: PromotionResult,
    config: PromotionConfig,
    staged_summary: Path,
    staged_errors: Path,
    staged_manifest: Path,
    output_size_bytes: int,
) -> None:
    summary_row = {
        "source_rows": result.row_count,
        "promoted_rows": result.row_count,
        "unique_review_id_count": result.unique_review_id_count,
        "reviewed_count": result.reviewed_count,
        "pending_count": result.pending_count,
        "input_validation_error_count": result.input_validation_error_count,
        "output_validation_error_count": result.output_validation_error_count,
        "mapping_mismatch_count": result.mapping_mismatch_count,
        "logical_fingerprint": result.logical_fingerprint,
        "is_valid": str(result.is_valid).lower(),
    }
    pd.DataFrame([summary_row], columns=SUMMARY_COLUMNS).to_csv(
        staged_summary,
        index=False,
        encoding="utf-8-sig",
    )
    pd.DataFrame([], columns=CANONICAL_ERROR_COLUMNS).to_csv(
        staged_errors,
        index=False,
        encoding="utf-8-sig",
    )

    manifest_row = {
        "promotion_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "04E",
        "promotion_status": "PROMOTED_AND_VERIFIED",
        "input_path": str(config.input_csv),
        "output_path": str(config.output_csv),
        "summary_path": str(config.summary_csv),
        "errors_path": str(config.errors_csv),
        "input_sha256": result.input_sha256,
        "output_sha256": result.output_sha256,
        "input_size_bytes": config.input_csv.stat().st_size,
        "output_size_bytes": output_size_bytes,
        "row_count": result.row_count,
        "unique_review_id_count": result.unique_review_id_count,
        "reviewed_count": result.reviewed_count,
        "pending_count": result.pending_count,
        "input_validation_error_count": result.input_validation_error_count,
        "output_validation_error_count": result.output_validation_error_count,
        "mapping_mismatch_count": result.mapping_mismatch_count,
        "logical_fingerprint": result.logical_fingerprint,
        "column_mapping_json": json.dumps(
            HUMAN_TO_CANONICAL,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
        "output_columns_json": json.dumps(
            CANONICAL_OUTPUT_COLUMNS,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    }
    with staged_manifest.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerow(manifest_row)


def _promote_transactionally(
    staged_to_final: dict[Path, Path],
    *,
    allow_overwrite: bool,
    staging_root: Path,
) -> dict[Path, Path | None]:
    _validate_final_path_policy(list(staged_to_final.values()), allow_overwrite)
    backup_root = staging_root / "rollback"
    backup_root.mkdir(parents=True, exist_ok=True)
    backups: dict[Path, Path | None] = {}
    promoted: list[Path] = []
    try:
        for index, final_path in enumerate(staged_to_final.values()):
            final_path.parent.mkdir(parents=True, exist_ok=True)
            if final_path.exists():
                backup_path = backup_root / f"{index}_{final_path.name}"
                shutil.copy2(final_path, backup_path)
                backups[final_path] = backup_path
            else:
                backups[final_path] = None
        for staged_path, final_path in staged_to_final.items():
            os.replace(staged_path, final_path)
            promoted.append(final_path)
    except Exception:
        _rollback_promoted_files(promoted, backups)
        raise
    return backups


def _rollback_promoted_files(
    final_paths: Any,
    backups: dict[Path, Path | None],
) -> None:
    for final_path in final_paths:
        path = Path(final_path)
        backup = backups.get(path)
        if path.exists():
            path.unlink()
        if backup is not None and backup.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            os.replace(backup, path)


def _post_verify(result: PromotionResult, config: PromotionConfig) -> None:
    if sha256_file(config.input_csv) != result.input_sha256:
        raise ValueError("formal merge input SHA256 changed during schema promotion")
    if sha256_file(config.output_csv) != result.output_sha256:
        raise ValueError("promoted output SHA256 does not match staged output")

    promoted = pd.read_csv(
        config.output_csv,
        dtype="string",
        keep_default_na=False,
        encoding="utf-8-sig",
    ).astype(str)
    if len(promoted) != result.row_count:
        raise ValueError("promoted output row count changed after promotion")
    if promoted["review_id"].nunique(dropna=False) != result.unique_review_id_count:
        raise ValueError("promoted output unique review_id count changed after promotion")
    if logical_fingerprint(promoted) != result.logical_fingerprint:
        raise ValueError("promoted output logical fingerprint mismatch")

    validation = validate_review_labels(
        input_csv=config.output_csv,
        schema_path=config.review_label_schema,
    )
    if not validation.is_valid:
        raise ValueError(
            f"post-promotion canonical validation failed with {validation.error_count} error(s)"
        )

    with config.manifest_csv.open(newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))
    if len(rows) != 1:
        raise ValueError("promotion manifest must contain exactly one data row")
    manifest = rows[0]
    if manifest.get("promotion_status") != "PROMOTED_AND_VERIFIED":
        raise ValueError("promotion manifest status is not PROMOTED_AND_VERIFIED")
    if manifest.get("input_sha256") != result.input_sha256:
        raise ValueError("promotion manifest input SHA256 mismatch")
    if manifest.get("output_sha256") != result.output_sha256:
        raise ValueError("promotion manifest output SHA256 mismatch")
    if manifest.get("logical_fingerprint") != result.logical_fingerprint:
        raise ValueError("promotion manifest logical fingerprint mismatch")


if __name__ == "__main__":
    raise SystemExit(main())
