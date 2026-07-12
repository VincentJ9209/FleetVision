"""Fail-closed image deduplication audit for FleetVision Phase 04.5F."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import cv2
import numpy as np
import pandas as pd
import yaml
from PIL import Image, UnidentifiedImageError


IMAGE_HASH_INVENTORY_COLUMNS = [
    "record_id",
    "source_scope",
    "dataset_id",
    "source_bucket",
    "image_id",
    "relative_image_path",
    "file_size_bytes",
    "width",
    "height",
    "aspect_ratio",
    "sha256",
    "phash_hex",
    "dhash_hex",
    "hash_status",
    "error_reason",
]
EXACT_GROUP_COLUMNS = [
    "exact_group_id",
    "sha256",
    "member_count",
    "internal_count",
    "external_count",
    "cross_source",
    "review_status",
]
EXACT_MEMBER_COLUMNS = [
    "exact_group_id",
    "record_id",
    "source_scope",
    "dataset_id",
    "source_bucket",
    "image_id",
    "relative_image_path",
]
PERCEPTUAL_COLUMNS = [
    "candidate_id",
    "left_record_id",
    "right_record_id",
    "left_source_scope",
    "right_source_scope",
    "left_dataset_id",
    "right_dataset_id",
    "left_source_bucket",
    "right_source_bucket",
    "left_image_id",
    "right_image_id",
    "left_relative_image_path",
    "right_relative_image_path",
    "phash_distance",
    "dhash_distance",
    "aspect_ratio_relative_difference",
    "candidate_rule",
    "review_status",
]
SUMMARY_COLUMNS = [
    "dataset_id",
    "internal_image_count",
    "external_image_count",
    "total_image_count",
    "hash_success_count",
    "hash_error_count",
    "external_external_exact_group_count",
    "external_external_exact_image_count",
    "internal_external_exact_group_count",
    "internal_external_exact_image_count",
    "external_external_perceptual_candidate_count",
    "internal_external_perceptual_candidate_count",
    "sha256_dedup_recommendation",
    "perceptual_hash_recommendation",
    "internal_cross_dedup_recommendation",
    "training_acceptance",
]
ERROR_COLUMNS = [
    "record_id",
    "source_scope",
    "image_id",
    "relative_image_path",
    "error_code",
    "error_message",
]

INTERNAL_REQUIRED_COLUMNS = {
    "image_id",
    "source_bucket",
    "original_path",
    "file_size_bytes",
    "width",
    "height",
    "aspect_ratio",
    "is_readable",
}
EXTERNAL_REQUIRED_COLUMNS = {
    "split",
    "annotation_json",
    "image_id",
    "file_name",
    "relative_image_path",
    "width",
    "height",
    "file_exists",
    "size_bytes",
    "sha256",
}


class DeduplicationAuditError(RuntimeError):
    """Base exception for a blocked deduplication audit."""


class ConfigInputError(DeduplicationAuditError):
    """Configuration, schema, or preflight input error (CLI exit 2)."""


class HashingIntegrityError(DeduplicationAuditError):
    """Image reading, hashing, or integrity error (CLI exit 3)."""


class CandidateOverflowError(DeduplicationAuditError):
    """Candidate index exceeded the configured fail-closed limit (CLI exit 4)."""


class OutputPromotionError(DeduplicationAuditError):
    """Staging or atomic output promotion error (CLI exit 5)."""


@dataclass(frozen=True)
class DeduplicationConfig:
    """Validated and resolved Phase 04.5F configuration."""

    dataset_id: str
    project_root: Path
    internal_metadata_path: Path
    external_image_inventory_path: Path
    external_raw_root: Path
    output_root: Path
    sha256_chunk_size_bytes: int
    phash_size: int
    dhash_size: int
    verify_external_sha256: bool
    phash_hamming_distance_max: int
    dhash_hamming_distance_max: int
    aspect_ratio_relative_difference_max: float
    exclude_exact_matches_from_perceptual_candidates: bool
    max_candidates_per_record: int
    candidate_overflow_policy: str
    external_external_exact: bool
    internal_external_exact: bool
    external_external_perceptual: bool
    internal_external_perceptual: bool
    internal_internal_exact: bool
    internal_internal_perceptual: bool
    overwrite_existing_output: bool
    fail_on_any_hash_error: bool
    write_error_report_on_failure: bool


@dataclass(frozen=True)
class ImageHashRecord:
    """Canonical in-memory image and hash record."""

    record_id: str
    source_scope: str
    dataset_id: str
    source_bucket: str
    image_id: str
    relative_image_path: str
    absolute_image_path: Path
    file_size_bytes: int
    width: int
    height: int
    aspect_ratio: float
    sha256: str
    phash_hex: str
    dhash_hex: str
    hash_status: str
    error_reason: str


@dataclass(frozen=True)
class DeduplicationAuditResult:
    """Compact result returned by dry-run and execution modes."""

    dataset_id: str
    executed: bool
    output_root: Path
    internal_image_count: int
    external_image_count: int
    total_image_count: int
    hash_success_count: int
    hash_error_count: int
    gate_classification: str


TOP_KEYS = {
    "dataset_id",
    "internal_metadata_path",
    "external_image_inventory_path",
    "external_raw_root",
    "output_root",
    "hashing",
    "candidate_rules",
    "scope",
    "execution",
}
HASHING_KEYS = {
    "sha256_chunk_size_bytes",
    "phash_size",
    "dhash_size",
    "verify_external_sha256",
}
CANDIDATE_KEYS = {
    "phash_hamming_distance_max",
    "dhash_hamming_distance_max",
    "aspect_ratio_relative_difference_max",
    "exclude_exact_matches_from_perceptual_candidates",
    "max_candidates_per_record",
    "candidate_overflow_policy",
}
SCOPE_KEYS = {
    "external_external_exact",
    "internal_external_exact",
    "external_external_perceptual",
    "internal_external_perceptual",
    "internal_internal_exact",
    "internal_internal_perceptual",
}
EXECUTION_KEYS = {
    "overwrite_existing_output",
    "fail_on_any_hash_error",
    "write_error_report_on_failure",
}


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ConfigInputError(f"config {key} must be a mapping")
    return value


def _validate_exact_keys(mapping: dict[str, Any], expected: set[str], label: str) -> None:
    missing = sorted(expected - set(mapping))
    unknown = sorted(set(mapping) - expected)
    if missing or unknown:
        raise ConfigInputError(f"config {label} keys invalid: missing={missing}; unknown keys={unknown}")


def _require_bool(mapping: dict[str, Any], key: str) -> bool:
    value = mapping[key]
    if not isinstance(value, bool):
        raise ConfigInputError(f"config {key} must be boolean")
    return value


def _require_positive_int(mapping: dict[str, Any], key: str) -> int:
    value = mapping[key]
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ConfigInputError(f"config {key} must be a positive integer")
    return value


def _require_nonnegative_int(mapping: dict[str, Any], key: str) -> int:
    value = mapping[key]
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ConfigInputError(f"config {key} must be a non-negative integer")
    return value


def _resolve_config_path(value: Any, project_root: Path, key: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ConfigInputError(f"config {key} must be a non-empty path string")
    path = Path(value)
    return path if path.is_absolute() else project_root / path


def load_deduplication_config(
    config_path: Path,
    *,
    project_root: Path,
) -> DeduplicationConfig:
    """Load a strict YAML configuration and resolve project-relative paths."""

    if not config_path.is_file():
        raise ConfigInputError(f"config not found: {config_path}")
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ConfigInputError(f"invalid config YAML: {config_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigInputError("config root must be a mapping")
    _validate_exact_keys(data, TOP_KEYS, "root")
    hashing = _require_mapping(data, "hashing")
    candidate = _require_mapping(data, "candidate_rules")
    scope = _require_mapping(data, "scope")
    execution = _require_mapping(data, "execution")
    _validate_exact_keys(hashing, HASHING_KEYS, "hashing")
    _validate_exact_keys(candidate, CANDIDATE_KEYS, "candidate_rules")
    _validate_exact_keys(scope, SCOPE_KEYS, "scope")
    _validate_exact_keys(execution, EXECUTION_KEYS, "execution")

    dataset_id = data["dataset_id"]
    if not isinstance(dataset_id, str) or not dataset_id.strip():
        raise ConfigInputError("config dataset_id must be a non-empty string")
    chunk_size = _require_positive_int(hashing, "sha256_chunk_size_bytes")
    phash_size = _require_positive_int(hashing, "phash_size")
    dhash_size = _require_positive_int(hashing, "dhash_size")
    phash_distance = _require_nonnegative_int(candidate, "phash_hamming_distance_max")
    dhash_distance = _require_nonnegative_int(candidate, "dhash_hamming_distance_max")
    if phash_distance > phash_size * phash_size:
        raise ConfigInputError("phash_hamming_distance_max exceeds pHash bit width")
    if dhash_distance > dhash_size * dhash_size:
        raise ConfigInputError("dhash_hamming_distance_max exceeds dHash bit width")
    tolerance = candidate["aspect_ratio_relative_difference_max"]
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)) or not 0 <= float(tolerance) <= 1:
        raise ConfigInputError("aspect_ratio_relative_difference_max must be within [0, 1]")
    if candidate["candidate_overflow_policy"] != "fail":
        raise ConfigInputError("candidate_overflow_policy must be 'fail'")

    root = project_root.resolve()
    internal_metadata_path = _resolve_config_path(
        data["internal_metadata_path"], root, "internal_metadata_path"
    )
    external_image_inventory_path = _resolve_config_path(
        data["external_image_inventory_path"], root, "external_image_inventory_path"
    )
    external_raw_root = _resolve_config_path(data["external_raw_root"], root, "external_raw_root")
    output_root = _resolve_config_path(data["output_root"], root, "output_root")
    approved_output_parent = root / "outputs/metadata/external_dedup"
    try:
        output_root.resolve().relative_to(approved_output_parent.resolve())
    except ValueError as exc:
        raise ConfigInputError(
            f"output_root must be under {approved_output_parent}"
        ) from exc
    return DeduplicationConfig(
        dataset_id=dataset_id.strip(),
        project_root=root,
        internal_metadata_path=internal_metadata_path,
        external_image_inventory_path=external_image_inventory_path,
        external_raw_root=external_raw_root,
        output_root=output_root,
        sha256_chunk_size_bytes=chunk_size,
        phash_size=phash_size,
        dhash_size=dhash_size,
        verify_external_sha256=_require_bool(hashing, "verify_external_sha256"),
        phash_hamming_distance_max=phash_distance,
        dhash_hamming_distance_max=dhash_distance,
        aspect_ratio_relative_difference_max=float(tolerance),
        exclude_exact_matches_from_perceptual_candidates=_require_bool(candidate, "exclude_exact_matches_from_perceptual_candidates"),
        max_candidates_per_record=_require_positive_int(candidate, "max_candidates_per_record"),
        candidate_overflow_policy="fail",
        external_external_exact=_require_bool(scope, "external_external_exact"),
        internal_external_exact=_require_bool(scope, "internal_external_exact"),
        external_external_perceptual=_require_bool(scope, "external_external_perceptual"),
        internal_external_perceptual=_require_bool(scope, "internal_external_perceptual"),
        internal_internal_exact=_require_bool(scope, "internal_internal_exact"),
        internal_internal_perceptual=_require_bool(scope, "internal_internal_perceptual"),
        overwrite_existing_output=_require_bool(execution, "overwrite_existing_output"),
        fail_on_any_hash_error=_require_bool(execution, "fail_on_any_hash_error"),
        write_error_report_on_failure=_require_bool(execution, "write_error_report_on_failure"),
    )


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Return uppercase SHA256."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest().upper()


def compute_dhash_hex(image: Image.Image, *, hash_size: int = 8) -> str:
    """Return fixed-width uppercase hexadecimal dHash."""

    if hash_size <= 0:
        raise ValueError("hash_size must be positive")
    pixels = np.asarray(
        image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS),
        dtype=np.uint8,
    )
    bits = pixels[:, :-1] > pixels[:, 1:]
    value = 0
    for bit in bits.ravel():
        value = (value << 1) | int(bit)
    return f"{value:0{(hash_size * hash_size + 3) // 4}X}"


def compute_phash_hex(image: Image.Image, *, hash_size: int = 8) -> str:
    """Return fixed-width uppercase hexadecimal pHash using cv2.dct."""

    if hash_size <= 0:
        raise ValueError("hash_size must be positive")
    side = hash_size * 4
    pixels = np.asarray(
        image.convert("L").resize((side, side), Image.Resampling.LANCZOS),
        dtype=np.float32,
    )
    low_frequency = cv2.dct(pixels)[:hash_size, :hash_size]
    flattened = low_frequency.ravel()
    median = float(np.median(flattened[1:])) if flattened.size > 1 else 0.0
    bits = flattened >= median
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return f"{value:0{(hash_size * hash_size + 3) // 4}X}"


def hamming_distance_hex(left: str, right: str) -> int:
    """Return bit Hamming distance for equal-width hexadecimal strings."""

    if len(left) != len(right) or not left:
        raise DeduplicationAuditError("hex hashes must have equal non-zero width")
    try:
        return (int(left, 16) ^ int(right, 16)).bit_count()
    except ValueError as exc:
        raise DeduplicationAuditError("invalid hexadecimal hash") from exc


def _read_csv(path: Path, required: set[str], label: str) -> pd.DataFrame:
    if not path.is_file():
        raise ConfigInputError(f"{label} not found: {path}")
    try:
        frame = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except (OSError, UnicodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise ConfigInputError(f"invalid {label}: {path}: {exc}") from exc
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ConfigInputError(f"{label} missing columns: {missing}")
    return frame


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def _validate_identity(frame: pd.DataFrame, column: str, label: str) -> None:
    values = frame[column].astype(str).str.strip()
    if (values == "").any():
        raise ConfigInputError(f"{label} contains empty {column}")
    duplicates = sorted(values[values.duplicated(keep=False)].unique())
    if duplicates:
        raise ConfigInputError(f"{label} duplicate {column}: {duplicates[:5]}")


def _load_input_frames(config: DeduplicationConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    internal = _read_csv(config.internal_metadata_path, INTERNAL_REQUIRED_COLUMNS, "internal metadata")
    external = _read_csv(config.external_image_inventory_path, EXTERNAL_REQUIRED_COLUMNS, "external inventory")
    _validate_identity(internal, "image_id", "internal metadata")
    splits = external["split"].astype(str).str.strip()
    external_ids = splits + ":" + external["image_id"].astype(str).str.strip()
    if (splits == "").any() or (external_ids.str.endswith(":")).any() or external_ids.duplicated().any():
        raise ConfigInputError("external inventory contains duplicate or empty canonical image IDs")
    invalid_sha = [
        value
        for value in external["sha256"].astype(str).str.strip()
        if len(value) != 64 or any(character not in "0123456789abcdefABCDEF" for character in value)
    ]
    if invalid_sha:
        raise ConfigInputError("invalid external SHA256 value in external inventory")
    return internal, external


def _repo_relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ConfigInputError(f"image path is outside project root: {path}") from exc


def _number(value: Any, *, integer: bool, label: str) -> int | float:
    try:
        numeric = int(value) if integer else float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigInputError(f"invalid numeric {label}: {value!r}") from exc
    if numeric <= 0:
        raise ConfigInputError(f"non-positive {label}: {value!r}")
    return numeric


def _hash_one(
    *,
    record_id: str,
    source_scope: str,
    dataset_id: str,
    source_bucket: str,
    image_id: str,
    path: Path,
    relative_path: str,
    expected_width: Any,
    expected_height: Any,
    expected_size: Any,
    expected_sha256: str | None,
    config: DeduplicationConfig,
) -> ImageHashRecord:
    if not path.is_file():
        raise HashingIntegrityError(f"missing image: record_id={record_id} path={path}")
    expected_w = int(_number(expected_width, integer=True, label="width"))
    expected_h = int(_number(expected_height, integer=True, label="height"))
    expected_bytes = int(_number(expected_size, integer=True, label="file size"))
    actual_size = path.stat().st_size
    digest = sha256_file(path, chunk_size=config.sha256_chunk_size_bytes)
    if expected_sha256 and config.verify_external_sha256 and digest != expected_sha256.strip().upper():
        raise HashingIntegrityError(
            f"external SHA256 mismatch: record_id={record_id} expected={expected_sha256} actual={digest}"
        )
    try:
        with Image.open(path) as opened:
            opened.load()
            width, height = opened.size
            if width != expected_w or height != expected_h:
                raise HashingIntegrityError(
                    f"dimension mismatch: record_id={record_id} expected={expected_w}x{expected_h} actual={width}x{height}"
                )
            phash = compute_phash_hex(opened, hash_size=config.phash_size)
            dhash = compute_dhash_hex(opened, hash_size=config.dhash_size)
    except HashingIntegrityError:
        raise
    except (OSError, ValueError, UnidentifiedImageError) as exc:
        raise HashingIntegrityError(f"unreadable image: record_id={record_id} path={path}: {exc}") from exc
    if actual_size != expected_bytes:
        raise HashingIntegrityError(
            f"file size mismatch: record_id={record_id} expected={expected_bytes} actual={actual_size}"
        )
    return ImageHashRecord(
        record_id=record_id,
        source_scope=source_scope,
        dataset_id=dataset_id,
        source_bucket=source_bucket,
        image_id=image_id,
        relative_image_path=relative_path,
        absolute_image_path=path.resolve(),
        file_size_bytes=actual_size,
        width=width,
        height=height,
        aspect_ratio=width / height,
        sha256=digest,
        phash_hex=phash,
        dhash_hex=dhash,
        hash_status="success",
        error_reason="",
    )


def _build_hash_records(
    config: DeduplicationConfig,
    internal: pd.DataFrame,
    external: pd.DataFrame,
) -> list[ImageHashRecord]:
    records: list[ImageHashRecord] = []
    for row in internal.to_dict("records"):
        image_id = str(row["image_id"]).strip()
        if not _truthy(row["is_readable"]):
            raise HashingIntegrityError(f"internal metadata marks image unreadable: image_id={image_id}")
        source = Path(str(row["original_path"]).strip())
        path = source if source.is_absolute() else config.project_root / source
        relative = _repo_relative(path, config.project_root)
        records.append(
            _hash_one(
                record_id=f"internal:{image_id}",
                source_scope="internal",
                dataset_id="",
                source_bucket=str(row["source_bucket"]).strip(),
                image_id=image_id,
                path=path,
                relative_path=relative,
                expected_width=row["width"],
                expected_height=row["height"],
                expected_size=row["file_size_bytes"],
                expected_sha256=None,
                config=config,
            )
        )
    for row in external.to_dict("records"):
        split = str(row["split"]).strip()
        image_id = str(row["image_id"]).strip()
        if not _truthy(row["file_exists"]):
            raise HashingIntegrityError(f"external inventory marks image missing: split={split} image_id={image_id}")
        inventory_relative = Path(str(row["relative_image_path"]).strip())
        if inventory_relative.is_absolute() or ".." in inventory_relative.parts:
            raise ConfigInputError(f"invalid external relative_image_path: {inventory_relative}")
        path = _external_image_path(config, inventory_relative)
        records.append(
            _hash_one(
                record_id=f"external:{config.dataset_id}:{split}:{image_id}",
                source_scope="external",
                dataset_id=config.dataset_id,
                source_bucket=split,
                image_id=image_id,
                path=path,
                relative_path=_repo_relative(path, config.project_root),
                expected_width=row["width"],
                expected_height=row["height"],
                expected_size=row["size_bytes"],
                expected_sha256=str(row["sha256"]),
                config=config,
            )
        )
    records.sort(key=lambda item: item.record_id)
    ids = [item.record_id for item in records]
    if len(ids) != len(set(ids)):
        raise ConfigInputError("duplicate record IDs")
    return records


def _external_image_path(config: DeduplicationConfig, relative_path: Path) -> Path:
    """Resolve an intake-inventory path below the immutable extracted export."""

    if relative_path.parts and relative_path.parts[0] == "01_extracted_export":
        return config.external_raw_root / relative_path
    return config.external_raw_root / "01_extracted_export" / relative_path


def _preflight_image_paths(
    config: DeduplicationConfig,
    internal: pd.DataFrame,
    external: pd.DataFrame,
) -> None:
    """Check declared image paths without opening images or computing hashes."""

    for row in internal.to_dict("records"):
        image_id = str(row["image_id"]).strip()
        if not _truthy(row["is_readable"]):
            raise ConfigInputError(f"internal metadata marks image unreadable: image_id={image_id}")
        source = Path(str(row["original_path"]).strip())
        path = source if source.is_absolute() else config.project_root / source
        _repo_relative(path, config.project_root)
        if not path.is_file():
            raise ConfigInputError(f"internal image missing: image_id={image_id} path={path}")
    for row in external.to_dict("records"):
        split = str(row["split"]).strip()
        image_id = str(row["image_id"]).strip()
        if not _truthy(row["file_exists"]):
            raise ConfigInputError(
                f"external inventory marks image missing: split={split} image_id={image_id}"
            )
        relative = Path(str(row["relative_image_path"]).strip())
        if relative.is_absolute() or ".." in relative.parts:
            raise ConfigInputError(f"invalid external relative_image_path: {relative}")
        path = _external_image_path(config, relative)
        if not path.is_file():
            raise ConfigInputError(
                f"external image missing: split={split} image_id={image_id} path={path}"
            )


def _pair_scope_allowed(left: str, right: str, *, exact: bool, config: DeduplicationConfig) -> bool:
    scopes = {left, right}
    if scopes == {"external"}:
        return config.external_external_exact if exact else config.external_external_perceptual
    if scopes == {"internal"}:
        return config.internal_internal_exact if exact else config.internal_internal_perceptual
    if scopes == {"internal", "external"}:
        return config.internal_external_exact if exact else config.internal_external_perceptual
    return False


def _build_exact_rows(
    records: list[ImageHashRecord], config: DeduplicationConfig
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_hash: dict[str, list[ImageHashRecord]] = defaultdict(list)
    for item in records:
        by_hash[item.sha256].append(item)
    groups: list[dict[str, Any]] = []
    members: list[dict[str, Any]] = []
    for digest, digest_records in sorted(by_hash.items()):
        if len(digest_records) < 2:
            continue
        allowed = any(
            _pair_scope_allowed(left.source_scope, right.source_scope, exact=True, config=config)
            for index, left in enumerate(digest_records)
            for right in digest_records[index + 1 :]
        )
        if not allowed:
            continue
        ordered = sorted(digest_records, key=lambda item: item.record_id)
        internal_count = sum(item.source_scope == "internal" for item in ordered)
        external_count = sum(item.source_scope == "external" for item in ordered)
        group_id = f"exact-{digest[:16].lower()}"
        groups.append(
            {
                "exact_group_id": group_id,
                "sha256": digest,
                "member_count": len(ordered),
                "internal_count": internal_count,
                "external_count": external_count,
                "cross_source": internal_count > 0 and external_count > 0,
                "review_status": "requires_review",
            }
        )
        for item in ordered:
            members.append(
                {
                    "exact_group_id": group_id,
                    "record_id": item.record_id,
                    "source_scope": item.source_scope,
                    "dataset_id": item.dataset_id,
                    "source_bucket": item.source_bucket,
                    "image_id": item.image_id,
                    "relative_image_path": item.relative_image_path,
                }
            )
    return groups, sorted(members, key=lambda row: (row["exact_group_id"], row["record_id"]))


def _band_values(hash_hex: str, bit_width: int, band_count: int) -> list[int]:
    value = int(hash_hex, 16)
    base, remainder = divmod(bit_width, band_count)
    widths = [base + (1 if index < remainder else 0) for index in range(band_count)]
    values: list[int] = []
    remaining = bit_width
    for width in widths:
        remaining -= width
        values.append((value >> remaining) & ((1 << width) - 1))
    return values


def _aspect_ratio_difference(left: float, right: float) -> float:
    return abs(left - right) / max(left, right)


def _generate_perceptual_candidates(
    records: list[ImageHashRecord], config: DeduplicationConfig
) -> list[dict[str, Any]]:
    bit_width = config.phash_size * config.phash_size
    band_count = config.phash_hamming_distance_max + 1
    indexes: dict[str, list[dict[int, list[ImageHashRecord]]]] = {
        scope: [defaultdict(list) for _ in range(band_count)]
        for scope in ("internal", "external")
    }
    raw_counts: dict[str, int] = defaultdict(int)
    candidates: list[dict[str, Any]] = []
    for current in sorted(records, key=lambda item: item.record_id):
        bands = _band_values(current.phash_hex, bit_width, band_count)
        eligible_scopes = [
            scope
            for scope in ("internal", "external")
            if _pair_scope_allowed(current.source_scope, scope, exact=False, config=config)
        ]
        seen_other_ids: set[str] = set()
        for band_index, band_value in enumerate(bands):
            bucket_records = [
                item
                for scope in eligible_scopes
                for item in indexes[scope][band_index].get(band_value, [])
            ]
            for other in bucket_records:
                if other.record_id in seen_other_ids:
                    continue
                seen_other_ids.add(other.record_id)
                if config.exclude_exact_matches_from_perceptual_candidates and other.sha256 == current.sha256:
                    continue
                left, right = sorted((other, current), key=lambda item: item.record_id)
                raw_counts[left.record_id] += 1
                raw_counts[right.record_id] += 1
                if raw_counts[left.record_id] > config.max_candidates_per_record or raw_counts[right.record_id] > config.max_candidates_per_record:
                    raise CandidateOverflowError(
                        "candidate overflow: "
                        f"left={left.record_id} count={raw_counts[left.record_id]} "
                        f"right={right.record_id} count={raw_counts[right.record_id]} "
                        f"limit={config.max_candidates_per_record}"
                    )
                phash_distance = hamming_distance_hex(left.phash_hex, right.phash_hex)
                if phash_distance > config.phash_hamming_distance_max:
                    continue
                dhash_distance = hamming_distance_hex(left.dhash_hex, right.dhash_hex)
                if dhash_distance > config.dhash_hamming_distance_max:
                    continue
                aspect_difference = _aspect_ratio_difference(left.aspect_ratio, right.aspect_ratio)
                if aspect_difference > config.aspect_ratio_relative_difference_max:
                    continue
                candidate_digest = hashlib.sha256(
                    f"{left.record_id}\n{right.record_id}".encode("utf-8")
                ).hexdigest()[:16]
                candidates.append(
                    {
                        "candidate_id": f"perceptual-{candidate_digest}",
                        "left_record_id": left.record_id,
                        "right_record_id": right.record_id,
                        "left_source_scope": left.source_scope,
                        "right_source_scope": right.source_scope,
                        "left_dataset_id": left.dataset_id,
                        "right_dataset_id": right.dataset_id,
                        "left_source_bucket": left.source_bucket,
                        "right_source_bucket": right.source_bucket,
                        "left_image_id": left.image_id,
                        "right_image_id": right.image_id,
                        "left_relative_image_path": left.relative_image_path,
                        "right_relative_image_path": right.relative_image_path,
                        "phash_distance": phash_distance,
                        "dhash_distance": dhash_distance,
                        "aspect_ratio_relative_difference": aspect_difference,
                        "candidate_rule": "phash_and_dhash_with_aspect_ratio",
                        "review_status": "requires_review",
                    }
                )
        for band_index, band_value in enumerate(bands):
            indexes[current.source_scope][band_index][band_value].append(current)
    return sorted(candidates, key=lambda row: (row["left_record_id"], row["right_record_id"]))


def _write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: list[str]) -> None:
    frame = pd.DataFrame(list(rows), columns=columns)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig")


def _record_output_row(item: ImageHashRecord) -> dict[str, Any]:
    row = asdict(item)
    row.pop("absolute_image_path")
    return row


def _summary_row(
    config: DeduplicationConfig,
    records: list[ImageHashRecord],
    exact_groups: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    external_groups = (
        [row for row in exact_groups if int(row["external_count"]) >= 2]
        if config.external_external_exact
        else []
    )
    cross_groups = (
        [row for row in exact_groups if bool(row["cross_source"])]
        if config.internal_external_exact
        else []
    )
    external_candidates = [
        row for row in candidates if row["left_source_scope"] == row["right_source_scope"] == "external"
    ]
    cross_candidates = [
        row for row in candidates if {row["left_source_scope"], row["right_source_scope"]} == {"internal", "external"}
    ]
    return {
        "dataset_id": config.dataset_id,
        "internal_image_count": sum(item.source_scope == "internal" for item in records),
        "external_image_count": sum(item.source_scope == "external" for item in records),
        "total_image_count": len(records),
        "hash_success_count": len(records),
        "hash_error_count": 0,
        "external_external_exact_group_count": len(external_groups),
        "external_external_exact_image_count": sum(int(row["external_count"]) for row in external_groups),
        "internal_external_exact_group_count": len(cross_groups),
        "internal_external_exact_image_count": sum(int(row["member_count"]) for row in cross_groups),
        "external_external_perceptual_candidate_count": len(external_candidates),
        "internal_external_perceptual_candidate_count": len(cross_candidates),
        "sha256_dedup_recommendation": "complete",
        "perceptual_hash_recommendation": "completed_candidates_pending_review",
        "internal_cross_dedup_recommendation": "completed_candidates_pending_review",
        "training_acceptance": "NOT_YET_APPROVED",
    }


def _config_for_verification(config: DeduplicationConfig) -> dict[str, Any]:
    return {
        "dataset_id": config.dataset_id,
        "internal_metadata_path": _repo_relative(config.internal_metadata_path, config.project_root),
        "external_image_inventory_path": _repo_relative(config.external_image_inventory_path, config.project_root),
        "external_raw_root": _repo_relative(config.external_raw_root, config.project_root),
        "output_root": _repo_relative(config.output_root, config.project_root),
        "hashing": {
            "sha256_chunk_size_bytes": config.sha256_chunk_size_bytes,
            "phash_size": config.phash_size,
            "dhash_size": config.dhash_size,
            "verify_external_sha256": config.verify_external_sha256,
        },
        "candidate_rules": {
            "phash_hamming_distance_max": config.phash_hamming_distance_max,
            "dhash_hamming_distance_max": config.dhash_hamming_distance_max,
            "aspect_ratio_relative_difference_max": config.aspect_ratio_relative_difference_max,
            "exclude_exact_matches_from_perceptual_candidates": config.exclude_exact_matches_from_perceptual_candidates,
            "max_candidates_per_record": config.max_candidates_per_record,
            "candidate_overflow_policy": config.candidate_overflow_policy,
        },
        "scope": {
            "external_external_exact": config.external_external_exact,
            "internal_external_exact": config.internal_external_exact,
            "external_external_perceptual": config.external_external_perceptual,
            "internal_external_perceptual": config.internal_external_perceptual,
            "internal_internal_exact": config.internal_internal_exact,
            "internal_internal_perceptual": config.internal_internal_perceptual,
        },
    }


def _write_success_outputs(
    staging_root: Path,
    *,
    config: DeduplicationConfig,
    records: list[ImageHashRecord],
    exact_groups: list[dict[str, Any]],
    exact_members: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    summary: dict[str, Any],
    input_hashes: dict[str, str],
) -> None:
    _write_csv(staging_root / "image_hash_inventory.csv", (_record_output_row(item) for item in records), IMAGE_HASH_INVENTORY_COLUMNS)
    _write_csv(staging_root / "exact_duplicate_groups.csv", exact_groups, EXACT_GROUP_COLUMNS)
    _write_csv(staging_root / "exact_duplicate_members.csv", exact_members, EXACT_MEMBER_COLUMNS)
    _write_csv(staging_root / "perceptual_duplicate_candidates.csv", candidates, PERCEPTUAL_COLUMNS)
    _write_csv(staging_root / "deduplication_summary.csv", [summary], SUMMARY_COLUMNS)
    _write_csv(staging_root / "deduplication_errors.csv", [], ERROR_COLUMNS)
    output_hashes = {
        path.name: sha256_file(path, chunk_size=config.sha256_chunk_size_bytes)
        for path in sorted(staging_root.glob("*.csv"))
    }
    verification = {
        "dataset_id": config.dataset_id,
        "config": _config_for_verification(config),
        "input_sha256": input_hashes,
        "output_sha256": output_hashes,
        "row_counts": {
            "image_hash_inventory.csv": len(records),
            "exact_duplicate_groups.csv": len(exact_groups),
            "exact_duplicate_members.csv": len(exact_members),
            "perceptual_duplicate_candidates.csv": len(candidates),
            "deduplication_summary.csv": 1,
            "deduplication_errors.csv": 0,
        },
        "algorithms": {
            "sha256": "streaming_sha256_uppercase",
            "phash": "pillow_grayscale_cv2_dct_median_excluding_dc",
            "dhash": "pillow_grayscale_horizontal_adjacent",
            "candidate_index": "phash_multi_index_banding",
        },
        "thresholds": _config_for_verification(config)["candidate_rules"],
        "scope_flags": _config_for_verification(config)["scope"],
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "repository_inputs_modified": False,
        "registry_modified": False,
        "protected_external_assets_modified": False,
        "training_acceptance": "NOT_YET_APPROVED",
    }
    (staging_root / "deduplication_verification.json").write_text(
        json.dumps(verification, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )


def _promote_output(staging_root: Path, output_root: Path, *, overwrite: bool) -> None:
    backup: Path | None = None
    try:
        if output_root.exists():
            if not overwrite:
                raise OutputPromotionError(f"output root already exists: {output_root}")
            backup = Path(
                tempfile.mkdtemp(prefix=f".{output_root.name}.backup-", dir=output_root.parent)
            )
            backup.rmdir()
            os.replace(output_root, backup)
        os.replace(staging_root, output_root)
        if backup is not None:
            try:
                shutil.rmtree(backup)
            except OSError:
                # The verified new output is already atomically promoted. A stale,
                # uniquely named backup is safer than reporting failure after success.
                pass
    except OutputPromotionError:
        raise
    except Exception as exc:
        if backup is not None and backup.exists() and not output_root.exists():
            os.replace(backup, output_root)
        raise OutputPromotionError(f"output promotion failed: {exc}") from exc


def _write_failure_evidence(staging_root: Path, error: Exception) -> None:
    _write_csv(
        staging_root / "deduplication_errors.csv",
        [
            {
                "record_id": "",
                "source_scope": "",
                "image_id": "",
                "relative_image_path": "",
                "error_code": type(error).__name__,
                "error_message": str(error),
            }
        ],
        ERROR_COLUMNS,
    )


def build_deduplication_audit(
    config: DeduplicationConfig,
    *,
    execute: bool,
    overwrite: bool = False,
) -> DeduplicationAuditResult:
    """Validate inputs or execute the staged Phase 04.5F deduplication audit."""

    internal, external = _load_input_frames(config)
    internal_count = len(internal)
    external_count = len(external)
    if not execute:
        _preflight_image_paths(config, internal, external)
        return DeduplicationAuditResult(
            dataset_id=config.dataset_id,
            executed=False,
            output_root=config.output_root,
            internal_image_count=internal_count,
            external_image_count=external_count,
            total_image_count=internal_count + external_count,
            hash_success_count=0,
            hash_error_count=0,
            gate_classification="DEDUPLICATION_PREFLIGHT_VALIDATED",
        )
    if config.output_root.exists() and not overwrite:
        raise OutputPromotionError(f"output root already exists: {config.output_root}")

    config.output_root.parent.mkdir(parents=True, exist_ok=True)
    staging_root = Path(
        tempfile.mkdtemp(prefix=f".{config.output_root.name}.staging-", dir=config.output_root.parent)
    )
    try:
        records = _build_hash_records(config, internal, external)
        exact_groups, exact_members = _build_exact_rows(records, config)
        candidates = _generate_perceptual_candidates(records, config)
        summary = _summary_row(config, records, exact_groups, candidates)
        input_hashes = {
            "internal_metadata_path": sha256_file(config.internal_metadata_path, chunk_size=config.sha256_chunk_size_bytes),
            "external_image_inventory_path": sha256_file(config.external_image_inventory_path, chunk_size=config.sha256_chunk_size_bytes),
        }
        try:
            _write_success_outputs(
                staging_root,
                config=config,
                records=records,
                exact_groups=exact_groups,
                exact_members=exact_members,
                candidates=candidates,
                summary=summary,
                input_hashes=input_hashes,
            )
        except Exception as exc:
            raise OutputPromotionError(f"failed to write staged outputs: {exc}") from exc
        _promote_output(staging_root, config.output_root, overwrite=overwrite)
    except (HashingIntegrityError, CandidateOverflowError) as exc:
        if config.write_error_report_on_failure:
            _write_failure_evidence(staging_root, exc)
        else:
            shutil.rmtree(staging_root, ignore_errors=True)
        raise
    except ConfigInputError:
        shutil.rmtree(staging_root, ignore_errors=True)
        raise
    except OutputPromotionError:
        shutil.rmtree(staging_root, ignore_errors=True)
        raise
    except Exception as exc:
        shutil.rmtree(staging_root, ignore_errors=True)
        raise OutputPromotionError(str(exc)) from exc

    return DeduplicationAuditResult(
        dataset_id=config.dataset_id,
        executed=True,
        output_root=config.output_root,
        internal_image_count=internal_count,
        external_image_count=external_count,
        total_image_count=len(records),
        hash_success_count=len(records),
        hash_error_count=0,
        gate_classification="DEDUPLICATION_AUDIT_COMPLETED_CANDIDATES_PENDING_REVIEW",
    )
