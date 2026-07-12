"""Safe Registry v2 intake-promotion adapter for FleetVision Phase 04.5D-2."""

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

PROMOTION_COLUMNS = (
    "download_date",
    "image_count_downloaded",
    "bbox_count_reported",
    "bbox_count_valid",
    "accepted_image_count",
    "rejected_image_count",
    "bbox_quality_status",
    "sha256_dedup_status",
    "usage_status",
    "local_raw_path",
    "notes",
)

IDENTITY_COLUMNS = (
    "dataset_id",
    "platform",
    "dataset_name",
    "source_url",
    "publisher",
    "license",
    "license_evidence_url",
    "license_verified",
    "search_date",
    "dataset_version",
    "task_type",
    "annotation_format",
    "original_classes",
    "image_count_reported",
    "mapping_to_damage",
    "domain_similarity",
    "perceptual_hash_status",
    "internal_cross_dedup_status",
    "rejection_reason",
)

PROTECTED_V2_COLUMNS = (
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

DRY_RUN_CLASSIFICATION = (
    "EXTERNAL_DATASET_REGISTRY_V2_INTAKE_PROMOTION_DRY_RUN_VERIFIED"
)
EXECUTE_CLASSIFICATION = "EXTERNAL_DATASET_REGISTRY_V2_INTAKE_PROMOTION_VERIFIED"
ALREADY_APPLIED_CLASSIFICATION = (
    "EXTERNAL_DATASET_REGISTRY_V2_INTAKE_PROMOTION_ALREADY_APPLIED"
)
BLOCKED_CLASSIFICATION = "EXTERNAL_DATASET_REGISTRY_V2_INTAKE_PROMOTION_BLOCKED"


class RegistryIntakePromotionError(RuntimeError):
    """Raised when the Registry v2 intake-promotion gate fails closed."""


@dataclass(frozen=True)
class RegistryIntakePromotionConfig:
    """Validated configuration for one Registry v2 intake promotion."""

    project_root: Path
    registry_csv: Path
    proposal_csv: Path
    target_dataset_id: str
    expected_registry_dataset_id_order: tuple[str, ...]
    expected_registry_sha256: str
    expected_proposal_sha256: str
    expected_registry_columns: tuple[str, ...]
    expected_proposal_columns: tuple[str, ...]
    promotion_columns: tuple[str, ...]
    identity_columns: tuple[str, ...]
    protected_v2_columns: tuple[str, ...]
    expected_protected_v2_values: Mapping[str, str]
    expected_local_raw_path: str


@dataclass(frozen=True)
class CsvDocument:
    """Decoded CSV bytes plus format metadata and logical rows."""

    path: Path
    raw_bytes: bytes
    sha256: str
    columns: tuple[str, ...]
    rows: tuple[dict[str, str], ...]
    has_utf8_bom: bool
    newline: str
    ends_with_newline: bool


@dataclass(frozen=True)
class PromotionSummary:
    """Stable execution summary used by the CLI and tests."""

    mode: str
    dataset_id: str
    input_rows: int
    input_columns: int
    output_columns: int
    target_rows_matched: int
    promotion_fields_modified: int
    input_sha256: str
    proposal_sha256: str
    output_sha256: str
    registry_updated: bool
    training_acceptance: str


@dataclass(frozen=True)
class PromotionResult:
    """In-memory promotion result; dry-run never writes proposed bytes."""

    classification: str
    summary: PromotionSummary
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
        raise RegistryIntakePromotionError(
            f"{label} is outside project root: {resolved}"
        ) from exc
    return resolved


def _validate_sha256(value: object, label: str) -> str:
    digest = str(value).strip().lower()
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise RegistryIntakePromotionError(f"{label} must be a SHA256")
    return digest


def _validate_relative_posix_path(value: str, label: str) -> PurePosixPath:
    candidate = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or candidate.is_absolute()
        or ".." in candidate.parts
        or (candidate.parts and ":" in candidate.parts[0])
    ):
        raise RegistryIntakePromotionError(
            f"{label} must be a project-relative POSIX path"
        )
    return candidate


def load_promotion_config(
    config_path: Path,
    project_root: Path,
) -> RegistryIntakePromotionConfig:
    """Load, validate, and resolve one promotion config inside the project root."""

    root = project_root.resolve()
    resolved_config = _resolve_within_project(config_path, root, "config path")
    if not resolved_config.is_file():
        raise RegistryIntakePromotionError(f"config not found: {resolved_config}")

    data = yaml.safe_load(resolved_config.read_text(encoding="utf-8")) or {}
    required = {
        "registry_csv",
        "proposal_csv",
        "target_dataset_id",
        "expected_registry_dataset_id_order",
        "expected_registry_sha256",
        "expected_proposal_sha256",
        "expected_registry_columns",
        "expected_proposal_columns",
        "promotion_columns",
        "identity_columns",
        "protected_v2_columns",
        "expected_protected_v2_values",
        "expected_local_raw_path",
    }
    missing = sorted(required - set(data))
    if missing:
        raise RegistryIntakePromotionError(
            f"config missing required keys: {missing}"
        )

    registry_columns = tuple(str(value) for value in data["expected_registry_columns"])
    proposal_columns = tuple(str(value) for value in data["expected_proposal_columns"])
    promotion_columns = tuple(str(value) for value in data["promotion_columns"])
    identity_columns = tuple(str(value) for value in data["identity_columns"])
    protected_columns = tuple(str(value) for value in data["protected_v2_columns"])
    protected_values = {
        str(key): str(value)
        for key, value in dict(data["expected_protected_v2_values"]).items()
    }
    raw_dataset_id_order = data["expected_registry_dataset_id_order"]
    if isinstance(raw_dataset_id_order, (str, bytes)):
        raise RegistryIntakePromotionError(
            "expected_registry_dataset_id_order must be a sequence"
        )
    expected_dataset_id_order = tuple(
        str(value).strip() for value in raw_dataset_id_order
    )

    if len(registry_columns) != 42 or len(set(registry_columns)) != len(registry_columns):
        raise RegistryIntakePromotionError(
            "expected_registry_columns must contain 42 unique columns"
        )
    if len(proposal_columns) != 30 or len(set(proposal_columns)) != len(proposal_columns):
        raise RegistryIntakePromotionError(
            "expected_proposal_columns must contain 30 unique columns"
        )
    if promotion_columns != PROMOTION_COLUMNS:
        raise RegistryIntakePromotionError(
            "promotion_columns do not match the fixed 11-field contract"
        )
    if identity_columns != IDENTITY_COLUMNS:
        raise RegistryIntakePromotionError(
            "identity_columns do not match the fixed 19-field contract"
        )
    if protected_columns != PROTECTED_V2_COLUMNS:
        raise RegistryIntakePromotionError(
            "protected_v2_columns do not match the fixed 12-field contract"
        )
    if set(proposal_columns) != set(PROMOTION_COLUMNS) | set(IDENTITY_COLUMNS):
        raise RegistryIntakePromotionError(
            "proposal schema does not match the fixed 30-field contract"
        )
    if tuple(registry_columns[:30]) != proposal_columns:
        raise RegistryIntakePromotionError(
            "Registry legacy columns must exactly match proposal columns"
        )
    if tuple(registry_columns[30:]) != PROTECTED_V2_COLUMNS:
        raise RegistryIntakePromotionError(
            "Registry v2 columns do not match the protected 12-field contract"
        )
    if set(protected_values) != set(PROTECTED_V2_COLUMNS):
        raise RegistryIntakePromotionError(
            "expected_protected_v2_values must define every protected field"
        )
    if protected_values["training_acceptance"] != "NOT_YET_APPROVED":
        raise RegistryIntakePromotionError(
            "training_acceptance must remain NOT_YET_APPROVED"
        )
    if not expected_dataset_id_order:
        raise RegistryIntakePromotionError(
            "expected_registry_dataset_id_order must not be empty"
        )
    if any(not value for value in expected_dataset_id_order):
        raise RegistryIntakePromotionError(
            "expected_registry_dataset_id_order must not contain empty values"
        )
    target_dataset_id = str(data["target_dataset_id"]).strip()
    if not target_dataset_id:
        raise RegistryIntakePromotionError(
            "target_dataset_id must not be empty"
        )

    expected_local_raw_path = str(data["expected_local_raw_path"])
    _validate_relative_posix_path(
        expected_local_raw_path,
        "expected_local_raw_path",
    )

    return RegistryIntakePromotionConfig(
        project_root=root,
        registry_csv=_resolve_within_project(
            data["registry_csv"],
            root,
            "Registry path",
        ),
        proposal_csv=_resolve_within_project(
            data["proposal_csv"],
            root,
            "proposal path",
        ),
        target_dataset_id=target_dataset_id,
        expected_registry_dataset_id_order=expected_dataset_id_order,
        expected_registry_sha256=_validate_sha256(
            data["expected_registry_sha256"],
            "expected_registry_sha256",
        ),
        expected_proposal_sha256=_validate_sha256(
            data["expected_proposal_sha256"],
            "expected_proposal_sha256",
        ),
        expected_registry_columns=registry_columns,
        expected_proposal_columns=proposal_columns,
        promotion_columns=promotion_columns,
        identity_columns=identity_columns,
        protected_v2_columns=protected_columns,
        expected_protected_v2_values=protected_values,
        expected_local_raw_path=expected_local_raw_path,
    )


def _detect_newline(text: str, label: str) -> tuple[str, bool]:
    record_newlines: list[str] = []
    in_quotes = False
    index = 0
    last_record_ended_at = -1

    while index < len(text):
        character = text[index]
        if character == '"':
            if in_quotes and index + 1 < len(text) and text[index + 1] == '"':
                index += 2
                continue
            in_quotes = not in_quotes
            index += 1
            continue

        if character == "\r":
            if index + 1 < len(text) and text[index + 1] == "\n":
                if not in_quotes:
                    record_newlines.append("\r\n")
                    last_record_ended_at = index + 2
                index += 2
                continue
            if not in_quotes:
                raise RegistryIntakePromotionError(
                    f"{label} contains unsupported bare CR line endings"
                )

        if character == "\n" and not in_quotes:
            record_newlines.append("\n")
            last_record_ended_at = index + 1

        index += 1

    distinct_newlines = set(record_newlines)
    if len(distinct_newlines) > 1:
        raise RegistryIntakePromotionError(
            f"{label} contains mixed record line endings"
        )

    newline = record_newlines[0] if record_newlines else "\n"
    return newline, last_record_ended_at == len(text)


def _read_csv(path: Path, label: str) -> CsvDocument:
    if not path.is_file():
        raise RegistryIntakePromotionError(f"{label} not found: {path}")

    raw = path.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    try:
        text = raw.decode("utf-8-sig" if has_bom else "utf-8")
    except UnicodeDecodeError as exc:
        raise RegistryIntakePromotionError(
            f"{label} must use UTF-8 with optional BOM"
        ) from exc

    newline, ends_with_newline = _detect_newline(text, label)
    try:
        parsed = list(csv.reader(io.StringIO(text, newline="")))
    except csv.Error as exc:
        raise RegistryIntakePromotionError(f"invalid {label} CSV: {exc}") from exc

    if not parsed or not parsed[0]:
        raise RegistryIntakePromotionError(f"{label} CSV is empty")

    columns = tuple(parsed[0])
    if len(set(columns)) != len(columns):
        raise RegistryIntakePromotionError(
            f"{label} contains duplicate header names"
        )

    rows: list[dict[str, str]] = []
    for index, values in enumerate(parsed[1:], start=2):
        if len(values) != len(columns):
            raise RegistryIntakePromotionError(
                f"{label} row {index} has {len(values)} values; "
                f"expected {len(columns)}"
            )
        rows.append(dict(zip(columns, values, strict=True)))

    return CsvDocument(
        path=path,
        raw_bytes=raw,
        sha256=hashlib.sha256(raw).hexdigest(),
        columns=columns,
        rows=tuple(rows),
        has_utf8_bom=has_bom,
        newline=newline,
        ends_with_newline=ends_with_newline,
    )


def _target_indexes(
    rows: Sequence[Mapping[str, str]],
    dataset_id: str,
) -> tuple[int, ...]:
    return tuple(
        index
        for index, row in enumerate(rows)
        if row.get("dataset_id", "") == dataset_id
    )


def _validate_documents(
    registry: CsvDocument,
    proposal: CsvDocument,
    config: RegistryIntakePromotionConfig,
) -> tuple[int, dict[str, str], dict[str, str]]:
    if registry.columns != config.expected_registry_columns:
        raise RegistryIntakePromotionError(
            "Registry schema or column order does not match the exact 42-column contract"
        )
    if proposal.columns != config.expected_proposal_columns:
        raise RegistryIntakePromotionError(
            "proposal schema or column order does not match the exact 30-column contract"
        )
    if proposal.sha256 != config.expected_proposal_sha256:
        raise RegistryIntakePromotionError(
            "proposal SHA256 mismatch: "
            f"expected={config.expected_proposal_sha256} actual={proposal.sha256}"
        )

    actual_dataset_id_order = tuple(
        row.get("dataset_id", "") for row in registry.rows
    )
    if actual_dataset_id_order != config.expected_registry_dataset_id_order:
        raise RegistryIntakePromotionError(
            "Registry dataset_id order mismatch: "
            f"expected={config.expected_registry_dataset_id_order} "
            f"actual={actual_dataset_id_order}"
        )

    registry_indexes = _target_indexes(registry.rows, config.target_dataset_id)
    if len(registry_indexes) != 1:
        raise RegistryIntakePromotionError(
            "target dataset must appear exactly once in Registry: "
            f"{config.target_dataset_id}; matched={len(registry_indexes)}"
        )

    proposal_indexes = _target_indexes(proposal.rows, config.target_dataset_id)
    if len(proposal_indexes) != 1 or len(proposal.rows) != 1:
        raise RegistryIntakePromotionError(
            "proposal must contain exactly one target row: "
            f"{config.target_dataset_id}; rows={len(proposal.rows)} "
            f"matched={len(proposal_indexes)}"
        )

    target_index = registry_indexes[0]
    registry_row = registry.rows[target_index]
    proposal_row = proposal.rows[proposal_indexes[0]]

    for column in config.identity_columns:
        if registry_row[column] != proposal_row[column]:
            raise RegistryIntakePromotionError(
                "identity field mismatch: "
                f"{column}; Registry={registry_row[column]!r} "
                f"proposal={proposal_row[column]!r}"
            )

    for column, expected in config.expected_protected_v2_values.items():
        actual = registry_row[column]
        if actual != expected:
            if column == "training_acceptance":
                raise RegistryIntakePromotionError(
                    "training_acceptance must remain NOT_YET_APPROVED"
                )
            raise RegistryIntakePromotionError(
                "protected Registry v2 field mismatch: "
                f"{column}; expected={expected!r} actual={actual!r}"
            )

    _validate_local_raw_path(proposal_row["local_raw_path"], config)
    return target_index, dict(registry_row), dict(proposal_row)


def _validate_local_raw_path(
    value: str,
    config: RegistryIntakePromotionConfig,
) -> None:
    if not value:
        raise RegistryIntakePromotionError("local_raw_path must not be empty")

    actual = Path(value).resolve()
    root = config.project_root.resolve()
    try:
        actual.relative_to(root)
    except ValueError as exc:
        raise RegistryIntakePromotionError(
            f"local_raw_path is outside project root: {actual}"
        ) from exc

    relative = _validate_relative_posix_path(
        config.expected_local_raw_path,
        "expected_local_raw_path",
    )
    expected = (root / Path(*relative.parts)).resolve()
    if actual != expected:
        raise RegistryIntakePromotionError(
            f"local_raw_path mismatch: expected={expected} actual={actual}"
        )
    if not actual.is_dir():
        raise RegistryIntakePromotionError(
            f"local_raw_path does not exist as a directory: {actual}"
        )


def _serialize_registry(
    source: CsvDocument,
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


def _build_output_rows(
    registry: CsvDocument,
    target_index: int,
    proposal_row: Mapping[str, str],
    config: RegistryIntakePromotionConfig,
) -> tuple[dict[str, str], ...]:
    output: list[dict[str, str]] = []
    for index, source_row in enumerate(registry.rows):
        row = dict(source_row)
        if index == target_index:
            for column in config.promotion_columns:
                row[column] = proposal_row[column]
        output.append(
            {column: row[column] for column in config.expected_registry_columns}
        )
    return tuple(output)


def _validate_output(
    source: CsvDocument,
    output_rows: Sequence[Mapping[str, str]],
    target_index: int,
    proposal_row: Mapping[str, str],
    config: RegistryIntakePromotionConfig,
) -> None:
    if len(output_rows) != len(source.rows):
        raise RegistryIntakePromotionError(
            "Registry row count changed during promotion build"
        )

    for index, row in enumerate(output_rows):
        if tuple(row.keys()) != config.expected_registry_columns:
            raise RegistryIntakePromotionError(
                f"Registry output row {index + 2} has unexpected columns"
            )

        if index != target_index:
            if dict(row) != source.rows[index]:
                raise RegistryIntakePromotionError(
                    f"non-target Registry row changed: row={index + 2}"
                )
            continue

        for column in config.identity_columns:
            if row[column] != source.rows[index][column]:
                raise RegistryIntakePromotionError(
                    f"identity field changed during promotion: {column}"
                )
        for column in config.protected_v2_columns:
            if row[column] != source.rows[index][column]:
                raise RegistryIntakePromotionError(
                    f"protected Registry v2 field changed during promotion: {column}"
                )
        for column in config.promotion_columns:
            if row[column] != proposal_row[column]:
                raise RegistryIntakePromotionError(
                    f"promotion field mismatch after build: {column}"
                )

    if output_rows[target_index]["training_acceptance"] != "NOT_YET_APPROVED":
        raise RegistryIntakePromotionError(
            "training_acceptance must remain NOT_YET_APPROVED"
        )


def _promotion_match_count(
    registry_row: Mapping[str, str],
    proposal_row: Mapping[str, str],
    config: RegistryIntakePromotionConfig,
) -> int:
    return sum(
        registry_row[column] == proposal_row[column]
        for column in config.promotion_columns
    )


def _summary(
    *,
    mode: str,
    config: RegistryIntakePromotionConfig,
    source: CsvDocument,
    proposal: CsvDocument,
    output_sha256: str,
    registry_updated: bool,
    promotion_fields_modified: int,
) -> PromotionSummary:
    return PromotionSummary(
        mode=mode,
        dataset_id=config.target_dataset_id,
        input_rows=len(source.rows),
        input_columns=len(source.columns),
        output_columns=len(source.columns),
        target_rows_matched=len(
            _target_indexes(source.rows, config.target_dataset_id)
        ),
        promotion_fields_modified=promotion_fields_modified,
        input_sha256=source.sha256,
        proposal_sha256=proposal.sha256,
        output_sha256=output_sha256,
        registry_updated=registry_updated,
        training_acceptance="NOT_YET_APPROVED",
    )


def _write_csv_atomically(path: Path, payload: bytes) -> str:
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=".registry_v2_intake_promotion_",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())

        if temporary.read_bytes() != payload:
            raise RegistryIntakePromotionError(
                "staged Registry bytes do not match proposed output"
            )

        try:
            os.replace(temporary, path)
        except OSError as exc:
            raise RegistryIntakePromotionError(
                f"atomic replacement failed: {exc}"
            ) from exc

        temporary = None
        return hashlib.sha256(payload).hexdigest()
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def promote_external_dataset_registry_v2_intake(
    config_path: Path,
    project_root: Path,
    *,
    execute: bool = False,
) -> PromotionResult:
    """Validate and propose or atomically execute one Registry v2 intake promotion."""

    config = load_promotion_config(config_path, project_root)
    registry = _read_csv(config.registry_csv, "Registry")
    proposal = _read_csv(config.proposal_csv, "proposal")
    target_index, registry_row, proposal_row = _validate_documents(
        registry,
        proposal,
        config,
    )

    mode = "EXECUTE" if execute else "DRY_RUN"
    match_count = _promotion_match_count(registry_row, proposal_row, config)

    if registry.sha256 != config.expected_registry_sha256:
        if match_count == len(config.promotion_columns):
            summary = _summary(
                mode=mode,
                config=config,
                source=registry,
                proposal=proposal,
                output_sha256=registry.sha256,
                registry_updated=False,
                promotion_fields_modified=0,
            )
            return PromotionResult(
                ALREADY_APPLIED_CLASSIFICATION,
                summary,
                registry.columns,
                registry.rows,
                registry.raw_bytes,
            )
        if match_count > 0:
            mismatched = [
                column
                for column in config.promotion_columns
                if registry_row[column] != proposal_row[column]
            ]
            raise RegistryIntakePromotionError(
                "promotion field mismatch in partially applied Registry: "
                f"{mismatched}"
            )
        raise RegistryIntakePromotionError(
            "Registry SHA256 mismatch: "
            f"expected={config.expected_registry_sha256} actual={registry.sha256}"
        )

    if match_count == len(config.promotion_columns):
        summary = _summary(
            mode=mode,
            config=config,
            source=registry,
            proposal=proposal,
            output_sha256=registry.sha256,
            registry_updated=False,
            promotion_fields_modified=0,
        )
        return PromotionResult(
            ALREADY_APPLIED_CLASSIFICATION,
            summary,
            registry.columns,
            registry.rows,
            registry.raw_bytes,
        )

    output_rows = _build_output_rows(
        registry,
        target_index,
        proposal_row,
        config,
    )
    _validate_output(
        registry,
        output_rows,
        target_index,
        proposal_row,
        config,
    )
    output_bytes = _serialize_registry(
        registry,
        config.expected_registry_columns,
        output_rows,
    )
    output_sha256 = hashlib.sha256(output_bytes).hexdigest()
    classification = (
        EXECUTE_CLASSIFICATION if execute else DRY_RUN_CLASSIFICATION
    )

    if execute:
        current_registry = _read_csv(config.registry_csv, "Registry")
        current_proposal = _read_csv(config.proposal_csv, "proposal")
        if current_registry.raw_bytes != registry.raw_bytes:
            raise RegistryIntakePromotionError(
                "Registry changed between validation and execution"
            )
        if current_proposal.raw_bytes != proposal.raw_bytes:
            raise RegistryIntakePromotionError(
                "proposal changed between validation and execution"
            )

        _write_csv_atomically(config.registry_csv, output_bytes)
        try:
            written = _read_csv(config.registry_csv, "Registry")
            if written.raw_bytes != output_bytes:
                raise RegistryIntakePromotionError(
                    "post-write Registry bytes mismatch"
                )
            written_target_index, _, written_proposal_row = _validate_documents(
                written,
                proposal,
                config,
            )
            _validate_output(
                registry,
                written.rows,
                written_target_index,
                written_proposal_row,
                config,
            )
            if written.sha256 != output_sha256:
                raise RegistryIntakePromotionError(
                    "post-write Registry SHA256 mismatch"
                )
        except Exception as exc:
            try:
                _write_csv_atomically(config.registry_csv, registry.raw_bytes)
            except Exception as rollback_exc:
                raise RegistryIntakePromotionError(
                    "post-write verification failed and rollback failed: "
                    f"{rollback_exc}"
                ) from exc
            raise RegistryIntakePromotionError(
                f"post-write verification failed: {exc}"
            ) from exc

    summary = _summary(
        mode=mode,
        config=config,
        source=registry,
        proposal=proposal,
        output_sha256=output_sha256,
        registry_updated=execute,
        promotion_fields_modified=len(config.promotion_columns),
    )
    return PromotionResult(
        classification,
        summary,
        config.expected_registry_columns,
        output_rows,
        output_bytes,
    )
