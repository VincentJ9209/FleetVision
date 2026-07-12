"""Safe Registry v2 schema migration adapter for FleetVision Phase 04.5D-1."""

from __future__ import annotations

import csv
import hashlib
import io
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Mapping, Sequence

import yaml

NEW_COLUMNS = (
    "registry_schema_version",
    "lineage_status",
    "bbox_count_valid_raw",
    "bbox_count_invalid_raw",
    "bbox_quality_status_raw",
    "bbox_repair_count",
    "bbox_count_valid_interim",
    "bbox_count_invalid_interim",
    "bbox_quality_status_interim",
    "bbox_repair_status",
    "local_interim_path",
    "training_acceptance",
)

DRY_RUN_CLASSIFICATION = "EXTERNAL_DATASET_REGISTRY_V2_MIGRATION_DRY_RUN_VERIFIED"
EXECUTE_CLASSIFICATION = "EXTERNAL_DATASET_REGISTRY_V2_MIGRATION_VERIFIED"
ALREADY_APPLIED_CLASSIFICATION = "EXTERNAL_DATASET_REGISTRY_V2_MIGRATION_ALREADY_APPLIED"
BLOCKED_CLASSIFICATION = "EXTERNAL_DATASET_REGISTRY_V2_MIGRATION_BLOCKED"


class RegistryMigrationError(RuntimeError):
    """Raised when the Registry v2 migration gate fails closed."""


@dataclass(frozen=True)
class RegistryMigrationConfig:
    """Validated configuration for one Registry v2 migration."""

    project_root: Path
    registry_csv: Path
    target_dataset_id: str
    expected_input_sha256: str
    expected_current_columns: tuple[str, ...]
    new_columns: tuple[str, ...]
    target_values: Mapping[str, str]


@dataclass(frozen=True)
class RegistryDocument:
    """Decoded Registry bytes plus format metadata and logical rows."""

    path: Path
    raw_bytes: bytes
    sha256: str
    columns: tuple[str, ...]
    rows: tuple[dict[str, str], ...]
    has_utf8_bom: bool
    newline: str
    ends_with_newline: bool


@dataclass(frozen=True)
class MigrationSummary:
    """Stable execution summary used by the CLI and tests."""

    mode: str
    dataset_id: str
    input_rows: int
    input_columns: int
    output_columns: int
    new_columns_added: int
    existing_columns_modified: int
    target_rows_matched: int
    registry_schema_version: str
    input_sha256: str
    output_sha256: str
    registry_updated: bool
    training_acceptance: str


@dataclass(frozen=True)
class MigrationResult:
    """In-memory migration result; dry-run never writes its proposed bytes."""

    classification: str
    summary: MigrationSummary
    output_columns: tuple[str, ...]
    output_rows: tuple[dict[str, str], ...]
    output_bytes: bytes


def _resolve_within_project(value: str | Path, project_root: Path, label: str) -> Path:
    root = project_root.resolve()
    candidate = Path(value)
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise RegistryMigrationError(f"{label} is outside project root: {resolved}") from exc
    return resolved


def load_migration_config(config_path: Path, project_root: Path) -> RegistryMigrationConfig:
    """Load, validate, and resolve one migration config inside the project root."""

    root = project_root.resolve()
    resolved_config = _resolve_within_project(config_path, root, "config path")
    if not resolved_config.is_file():
        raise RegistryMigrationError(f"config not found: {resolved_config}")
    data = yaml.safe_load(resolved_config.read_text(encoding="utf-8")) or {}
    required = {
        "registry_csv",
        "target_dataset_id",
        "expected_input_sha256",
        "expected_current_columns",
        "new_columns",
        "target_values",
    }
    missing = sorted(required - set(data))
    if missing:
        raise RegistryMigrationError(f"config missing required keys: {missing}")

    current_columns = tuple(str(value) for value in data["expected_current_columns"])
    new_columns = tuple(str(value) for value in data["new_columns"])
    target_values = {str(key): str(value) for key, value in dict(data["target_values"]).items()}
    digest = str(data["expected_input_sha256"]).strip()

    if len(current_columns) != 30 or len(set(current_columns)) != len(current_columns):
        raise RegistryMigrationError("expected_current_columns must contain 30 unique columns")
    if new_columns != NEW_COLUMNS:
        raise RegistryMigrationError("new_columns do not match the fixed Registry v2 contract")
    if set(target_values) != set(NEW_COLUMNS):
        raise RegistryMigrationError("target_values must define every Registry v2 column exactly once")
    if target_values["registry_schema_version"] != "2":
        raise RegistryMigrationError("registry_schema_version must be 2")
    if len(digest) != 64 or digest.lower() != digest or any(ch not in "0123456789abcdef" for ch in digest):
        raise RegistryMigrationError("expected_input_sha256 must be a lowercase SHA256")
    _validate_interim_path(target_values["local_interim_path"])

    return RegistryMigrationConfig(
        project_root=root,
        registry_csv=_resolve_within_project(data["registry_csv"], root, "registry path"),
        target_dataset_id=str(data["target_dataset_id"]),
        expected_input_sha256=digest,
        expected_current_columns=current_columns,
        new_columns=new_columns,
        target_values=target_values,
    )


def _validate_interim_path(value: str) -> None:
    candidate = PurePosixPath(value)
    if not value or "\\" in value or candidate.is_absolute() or ".." in candidate.parts or ":" in candidate.parts[0]:
        raise RegistryMigrationError("local_interim_path must be a project-relative POSIX path")


def _detect_newline(payload: bytes) -> tuple[str, bool]:
    body = payload[3:] if payload.startswith(b"\xef\xbb\xbf") else payload
    without_crlf = body.replace(b"\r\n", b"")
    if b"\r" in without_crlf:
        raise RegistryMigrationError("Registry contains unsupported bare CR line endings")
    has_crlf = b"\r\n" in body
    has_lf = b"\n" in without_crlf
    if has_crlf and has_lf:
        raise RegistryMigrationError("Registry contains mixed line endings")
    return ("\r\n" if has_crlf else "\n"), body.endswith((b"\n", b"\r"))


def read_registry(path: Path) -> RegistryDocument:
    """Read one UTF-8 Registry without normalizing its logical values."""

    if not path.is_file():
        raise RegistryMigrationError(f"Registry not found: {path}")
    raw = path.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    try:
        text = raw.decode("utf-8-sig" if has_bom else "utf-8")
    except UnicodeDecodeError as exc:
        raise RegistryMigrationError("Registry must use UTF-8 with optional BOM") from exc
    newline, ends_with_newline = _detect_newline(raw)
    try:
        parsed = list(csv.reader(io.StringIO(text, newline="")))
    except csv.Error as exc:
        raise RegistryMigrationError(f"invalid Registry CSV: {exc}") from exc
    if not parsed or not parsed[0]:
        raise RegistryMigrationError("Registry CSV is empty")
    columns = tuple(parsed[0])
    if len(set(columns)) != len(columns):
        raise RegistryMigrationError("Registry contains duplicate header names")
    rows: list[dict[str, str]] = []
    for index, values in enumerate(parsed[1:], start=2):
        if len(values) != len(columns):
            raise RegistryMigrationError(
                f"Registry row {index} has {len(values)} values; expected {len(columns)}"
            )
        rows.append(dict(zip(columns, values, strict=True)))
    return RegistryDocument(
        path=path,
        raw_bytes=raw,
        sha256=hashlib.sha256(raw).hexdigest(),
        columns=columns,
        rows=tuple(rows),
        has_utf8_bom=has_bom,
        newline=newline,
        ends_with_newline=ends_with_newline,
    )


def _target_count(rows: Sequence[Mapping[str, str]], dataset_id: str) -> int:
    return sum(row.get("dataset_id", "") == dataset_id for row in rows)


def validate_registry_v1(document: RegistryDocument, config: RegistryMigrationConfig) -> None:
    """Validate the exact v1 schema, target identity, and immutable input SHA256."""

    if document.columns != config.expected_current_columns:
        raise RegistryMigrationError(
            f"unexpected Registry v1 schema: expected={len(config.expected_current_columns)} "
            f"actual={len(document.columns)}"
        )
    matched = _target_count(document.rows, config.target_dataset_id)
    if matched != 1:
        raise RegistryMigrationError(
            f"target dataset must appear exactly once: {config.target_dataset_id}; matched={matched}"
        )
    if document.sha256 != config.expected_input_sha256:
        raise RegistryMigrationError(
            f"Registry input SHA256 mismatch: expected={config.expected_input_sha256} "
            f"actual={document.sha256}"
        )


def build_registry_v2_rows(
    document: RegistryDocument,
    config: RegistryMigrationConfig,
) -> tuple[dict[str, str], ...]:
    """Append v2 fields while preserving every v1 value and row order."""

    target_columns = (*config.expected_current_columns, *config.new_columns)
    output: list[dict[str, str]] = []
    for source in document.rows:
        row = {column: source[column] for column in config.expected_current_columns}
        for column in config.new_columns:
            row[column] = ""
        row["registry_schema_version"] = "2"
        if source["dataset_id"] == config.target_dataset_id:
            for column, value in config.target_values.items():
                row[column] = value
        output.append({column: row[column] for column in target_columns})
    return tuple(output)


def validate_registry_v2(
    columns: Sequence[str],
    rows: Sequence[Mapping[str, str]],
    config: RegistryMigrationConfig,
    *,
    source_v1: RegistryDocument | None = None,
) -> None:
    """Validate exact v2 schema, configured values, and append-only immutability."""

    expected_columns = (*config.expected_current_columns, *config.new_columns)
    if tuple(columns) != expected_columns:
        raise RegistryMigrationError("unexpected Registry v2 schema or column order")
    matched = _target_count(rows, config.target_dataset_id)
    if matched != 1:
        raise RegistryMigrationError(
            f"target dataset must appear exactly once: {config.target_dataset_id}; matched={matched}"
        )
    if source_v1 is not None and len(rows) != len(source_v1.rows):
        raise RegistryMigrationError("Registry row count changed during migration build")

    for index, row in enumerate(rows):
        if tuple(row.keys()) != expected_columns:
            raise RegistryMigrationError(f"Registry v2 row {index + 2} has unexpected columns")
        if row["registry_schema_version"] != "2":
            raise RegistryMigrationError("configured v2 value mismatch: registry_schema_version")
        is_target = row["dataset_id"] == config.target_dataset_id
        if is_target:
            for column, expected in config.target_values.items():
                if row[column] != expected:
                    raise RegistryMigrationError(
                        f"configured v2 value mismatch: {column}; expected={expected!r} "
                        f"actual={row[column]!r}"
                    )
        else:
            nonblank = [column for column in config.new_columns[1:] if row[column] != ""]
            if nonblank:
                raise RegistryMigrationError(
                    f"non-target Registry v2 fields must be blank: row={index + 2} columns={nonblank}"
                )
        if source_v1 is not None:
            for column in config.expected_current_columns:
                if row[column] != source_v1.rows[index][column]:
                    raise RegistryMigrationError(
                        f"existing Registry value changed during migration: row={index + 2} "
                        f"column={column}"
                    )


def _serialize_registry(
    source: RegistryDocument,
    columns: Sequence[str],
    rows: Sequence[Mapping[str, str]],
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=list(columns),
        extrasaction="raise",
        lineterminator=source.newline,
        quoting=csv.QUOTE_MINIMAL,
    )
    writer.writeheader()
    writer.writerows(rows)
    text = stream.getvalue()
    if not source.ends_with_newline and text.endswith(source.newline):
        text = text[: -len(source.newline)]
    payload = text.encode("utf-8")
    return (b"\xef\xbb\xbf" + payload) if source.has_utf8_bom else payload


def write_csv_atomically(path: Path, payload: bytes) -> str:
    """Write bytes through a same-directory fsynced temp file and os.replace()."""

    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=".registry_v2_migration_",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        if temporary.read_bytes() != payload:
            raise RegistryMigrationError("staged Registry bytes do not match proposed output")
        try:
            os.replace(temporary, path)
        except OSError as exc:
            raise RegistryMigrationError(f"atomic replacement failed: {exc}") from exc
        temporary = None
        return hashlib.sha256(payload).hexdigest()
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _summary(
    *,
    mode: str,
    classification: str,
    config: RegistryMigrationConfig,
    source: RegistryDocument,
    output_sha256: str,
    output_columns: int,
    updated: bool,
) -> MigrationSummary:
    return MigrationSummary(
        mode=mode,
        dataset_id=config.target_dataset_id,
        input_rows=len(source.rows),
        input_columns=len(source.columns),
        output_columns=output_columns,
        new_columns_added=max(output_columns - len(source.columns), 0),
        existing_columns_modified=0,
        target_rows_matched=_target_count(source.rows, config.target_dataset_id),
        registry_schema_version="2",
        input_sha256=source.sha256,
        output_sha256=output_sha256,
        registry_updated=updated,
        training_acceptance=config.target_values["training_acceptance"],
    )


def migrate_external_dataset_registry_v2(
    config_path: Path,
    project_root: Path,
    *,
    execute: bool = False,
) -> MigrationResult:
    """Validate and propose or atomically execute one Registry v2 migration."""

    config = load_migration_config(config_path, project_root)
    source = read_registry(config.registry_csv)
    target_columns = (*config.expected_current_columns, *config.new_columns)
    mode = "EXECUTE" if execute else "DRY_RUN"

    if source.columns == target_columns:
        validate_registry_v2(source.columns, source.rows, config)
        summary = _summary(
            mode=mode,
            classification=ALREADY_APPLIED_CLASSIFICATION,
            config=config,
            source=source,
            output_sha256=source.sha256,
            output_columns=len(source.columns),
            updated=False,
        )
        return MigrationResult(
            ALREADY_APPLIED_CLASSIFICATION,
            summary,
            source.columns,
            source.rows,
            source.raw_bytes,
        )

    validate_registry_v1(source, config)
    output_rows = build_registry_v2_rows(source, config)
    validate_registry_v2(target_columns, output_rows, config, source_v1=source)
    output_bytes = _serialize_registry(source, target_columns, output_rows)
    output_sha256 = hashlib.sha256(output_bytes).hexdigest()

    classification = EXECUTE_CLASSIFICATION if execute else DRY_RUN_CLASSIFICATION
    if execute:
        current = read_registry(config.registry_csv)
        validate_registry_v1(current, config)
        if current.raw_bytes != source.raw_bytes:
            raise RegistryMigrationError("Registry changed between validation and execution")
        write_csv_atomically(config.registry_csv, output_bytes)
        try:
            written = read_registry(config.registry_csv)
            validate_registry_v2(written.columns, written.rows, config, source_v1=source)
            if written.sha256 != output_sha256:
                raise RegistryMigrationError("post-write Registry SHA256 mismatch")
        except Exception as exc:
            try:
                write_csv_atomically(config.registry_csv, source.raw_bytes)
            except Exception as rollback_exc:
                raise RegistryMigrationError(
                    f"post-write verification failed and rollback failed: {rollback_exc}"
                ) from exc
            raise RegistryMigrationError(f"post-write verification failed: {exc}") from exc

    summary = _summary(
        mode=mode,
        classification=classification,
        config=config,
        source=source,
        output_sha256=output_sha256,
        output_columns=len(target_columns),
        updated=execute,
    )
    return MigrationResult(classification, summary, tuple(target_columns), output_rows, output_bytes)
