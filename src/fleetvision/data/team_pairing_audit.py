"""Read-only Team Pairing Audit inventory and duplicate evidence."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image

from fleetvision.review.team_pairing_review_mapping import TeamPairingAuditConfig


class TeamPairingAuditError(RuntimeError):
    """Raised when a Team Pairing Audit inventory operation fails closed."""


class SourceMutationError(TeamPairingAuditError):
    """Raised when source snapshots are not byte-identical."""


INVENTORY_COLUMNS: tuple[str, ...] = (
    "inventory_sequence",
    "image_id",
    "filename",
    "relative_path",
    "original_path",
    "extension",
    "file_size_bytes",
    "width",
    "height",
    "aspect_ratio",
    "is_readable",
    "read_error",
    "sha256",
    "perceptual_hash",
    "exif_datetime_original",
    "exif_datetime_digitized",
    "exif_datetime_other",
    "filesystem_created_at",
    "filesystem_modified_at",
    "selected_capture_time",
    "selected_time_source",
    "time_confidence",
    "capture_time_parse_warning",
    "exact_duplicate_group",
    "near_duplicate_group_candidate",
    "source_snapshot_sha256",
    "representative_for_exact_group",
    "eligible_for_batch_candidate",
    "inventory_notes",
)

_EXIF_ORIGINAL = 36867
_EXIF_DIGITIZED = 36868
_EXIF_DATETIME = 306
_EXIF_FORMATS = (
    "%Y:%m:%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
)


@dataclass(frozen=True)
class TimestampSelection:
    selected_capture_time: str
    selected_time_source: str
    time_confidence: str
    capture_time_parse_warning: str


@dataclass(frozen=True)
class InventoryBuildResult:
    rows: tuple[dict[str, Any], ...]
    source_snapshot_before: dict[str, Any]
    source_snapshot_after: dict[str, Any]
    source_snapshot_verification: dict[str, Any]


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _normalized_relative(path: Path, root: Path) -> str:
    try:
        relative = path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise TeamPairingAuditError(f"path escapes approved root: {path}") from exc
    return relative.as_posix()


def deterministic_image_id(relative_path: str) -> str:
    normalized = Path(relative_path.replace("\\", "/")).as_posix()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"team_{digest[:20]}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def discover_supported_images(
    source_root: Path,
    supported_extensions: Sequence[str],
) -> tuple[Path, ...]:
    source_root = source_root.resolve()
    if not source_root.is_dir():
        raise TeamPairingAuditError(f"source root missing: {source_root}")
    normalized_extensions = {str(value).lower() for value in supported_extensions}
    paths = [
        path
        for path in source_root.rglob("*")
        if path.is_file() and path.suffix.lower() in normalized_extensions
    ]
    return tuple(
        sorted(
            paths,
            key=lambda path: (
                _normalized_relative(path, source_root).casefold(),
                _normalized_relative(path, source_root),
            ),
        )
    )


def build_source_snapshot(source_root: Path) -> dict[str, Any]:
    source_root = source_root.resolve()
    if not source_root.is_dir():
        raise TeamPairingAuditError(f"source root missing: {source_root}")
    entries: list[dict[str, Any]] = []
    for path in sorted(
        (candidate for candidate in source_root.rglob("*") if candidate.is_file()),
        key=lambda candidate: (
            _normalized_relative(candidate, source_root).casefold(),
            _normalized_relative(candidate, source_root),
        ),
    ):
        stat = path.stat()
        entries.append(
            {
                "relative_path": _normalized_relative(path, source_root),
                "file_size_bytes": int(stat.st_size),
                "sha256": sha256_file(path),
            }
        )
    canonical = json.dumps(
        entries,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "source_root": str(source_root),
        "file_count": len(entries),
        "entries": entries,
        "snapshot_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper(),
    }


def verify_source_snapshots(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> dict[str, Any]:
    before_hash = str(before.get("snapshot_sha256", "")).upper()
    after_hash = str(after.get("snapshot_sha256", "")).upper()
    before_entries = before.get("entries")
    after_entries = after.get("entries")
    identical = bool(before_hash) and before_hash == after_hash and before_entries == after_entries
    if not identical:
        raise SourceMutationError("source snapshot verification failed: source is not byte-identical")
    return {
        "byte_identical": True,
        "before_snapshot_sha256": before_hash,
        "after_snapshot_sha256": after_hash,
        "file_count": int(before.get("file_count", 0)),
    }


def _parse_exif_datetime(
    value: object,
    *,
    timezone_name: str,
    label: str,
) -> tuple[datetime | None, str | None]:
    raw = str(value or "").strip()
    if not raw:
        return None, None
    timezone = ZoneInfo(timezone_name)
    for format_text in _EXIF_FORMATS:
        try:
            return datetime.strptime(raw, format_text).replace(tzinfo=timezone), None
        except ValueError:
            continue
    return None, f"invalid {label}: {raw!r}"


def select_capture_timestamp(
    *,
    exif_datetime_original: object,
    exif_datetime_digitized: object,
    exif_datetime_other: object,
    filesystem_created_at: datetime | None,
    filesystem_modified_at: datetime | None,
    timezone_name: str,
) -> TimestampSelection:
    warnings: list[str] = []
    candidates = (
        ("DateTimeOriginal", "exif_datetime_original", exif_datetime_original, "high"),
        ("DateTimeDigitized", "exif_datetime_digitized", exif_datetime_digitized, "high"),
        ("DateTime", "exif_datetime_other", exif_datetime_other, "medium"),
    )
    for label, source, raw_value, confidence in candidates:
        parsed, warning = _parse_exif_datetime(
            raw_value,
            timezone_name=timezone_name,
            label=label,
        )
        if warning:
            warnings.append(warning)
        if parsed is not None:
            return TimestampSelection(
                selected_capture_time=parsed.isoformat(),
                selected_time_source=source,
                time_confidence=confidence,
                capture_time_parse_warning="; ".join(warnings),
            )

    if filesystem_created_at is not None:
        warnings.append("filesystem timestamp fallback; not authoritative capture time")
        return TimestampSelection(
            selected_capture_time=filesystem_created_at.isoformat(),
            selected_time_source="filesystem_created_at",
            time_confidence="fallback_low",
            capture_time_parse_warning="; ".join(warnings),
        )
    if filesystem_modified_at is not None:
        warnings.append("filesystem timestamp fallback; not authoritative capture time")
        return TimestampSelection(
            selected_capture_time=filesystem_modified_at.isoformat(),
            selected_time_source="filesystem_modified_at",
            time_confidence="fallback_low",
            capture_time_parse_warning="; ".join(warnings),
        )
    warnings.append("missing capture timestamp; manual review required")
    return TimestampSelection(
        selected_capture_time="",
        selected_time_source="missing",
        time_confidence="missing",
        capture_time_parse_warning="; ".join(warnings),
    )


def _dct_matrix(size: int) -> np.ndarray:
    indices = np.arange(size, dtype=np.float64)
    frequencies = indices[:, None]
    matrix = np.cos((math.pi / (2.0 * size)) * (2.0 * indices + 1.0) * frequencies)
    matrix[0, :] *= math.sqrt(1.0 / size)
    matrix[1:, :] *= math.sqrt(2.0 / size)
    return matrix


def compute_phash64(image_path: Path) -> str:
    with Image.open(image_path) as image:
        grayscale = image.convert("L").resize((32, 32), Image.Resampling.LANCZOS)
        pixels = np.asarray(grayscale, dtype=np.float64)
    transform = _dct_matrix(32)
    coefficients = transform @ pixels @ transform.T
    low_frequency = coefficients[:8, :8]
    flattened = low_frequency.flatten()
    median = float(np.median(flattened[1:]))
    bits = flattened > median
    value = 0
    for bit in bits:
        value = (value << 1) | int(bool(bit))
    return f"{value:016x}"


def phash_hamming_distance(left: str, right: str) -> int:
    if len(left) != 16 or len(right) != 16:
        raise TeamPairingAuditError("pHash values must contain 16 hexadecimal characters")
    try:
        return (int(left, 16) ^ int(right, 16)).bit_count()
    except ValueError as exc:
        raise TeamPairingAuditError("pHash values must be hexadecimal") from exc


def assign_duplicate_groups(
    rows: Sequence[Mapping[str, Any]],
    *,
    phash_distance_threshold: int,
) -> list[dict[str, Any]]:
    audited = [dict(row) for row in rows]
    by_sha: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in audited:
        row.setdefault("exact_duplicate_group", "")
        row.setdefault("near_duplicate_group_candidate", "")
        row.setdefault("representative_for_exact_group", False)
        row.setdefault("eligible_for_batch_candidate", False)
        if bool(row.get("is_readable")) and str(row.get("sha256", "")):
            by_sha[str(row["sha256"]).upper()].append(row)

    representatives: list[dict[str, Any]] = []
    for sha_value in sorted(by_sha):
        members = sorted(
            by_sha[sha_value],
            key=lambda row: (str(row["relative_path"]).casefold(), str(row["relative_path"])),
        )
        representative = members[0]
        representatives.append(representative)
        if len(members) > 1:
            group_id = f"exact_{sha_value[:16].lower()}"
        else:
            group_id = ""
        for index, member in enumerate(members):
            member["exact_duplicate_group"] = group_id
            member["representative_for_exact_group"] = index == 0
            member["eligible_for_batch_candidate"] = index == 0

    representatives = sorted(
        representatives,
        key=lambda row: (str(row["relative_path"]).casefold(), str(row["relative_path"])),
    )
    assigned: set[str] = set()
    representative_groups: dict[str, str] = {}
    for representative in representatives:
        representative_id = str(representative["image_id"])
        if representative_id in assigned:
            continue
        representative_hash = str(representative.get("perceptual_hash", ""))
        if not representative_hash:
            continue
        members = [representative]
        for candidate in representatives:
            candidate_id = str(candidate["image_id"])
            if candidate_id == representative_id or candidate_id in assigned:
                continue
            candidate_hash = str(candidate.get("perceptual_hash", ""))
            if not candidate_hash:
                continue
            if phash_hamming_distance(representative_hash, candidate_hash) <= phash_distance_threshold:
                members.append(candidate)
        if len(members) <= 1:
            continue
        member_ids = sorted(str(member["image_id"]) for member in members)
        payload = "\x1f".join(member_ids)
        group_id = f"near_{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"
        for member in members:
            member_id = str(member["image_id"])
            member["near_duplicate_group_candidate"] = group_id
            representative_groups[member_id] = group_id
            assigned.add(member_id)

    representative_by_sha = {
        str(row["sha256"]).upper(): row for row in representatives if str(row.get("sha256", ""))
    }
    for row in audited:
        sha_value = str(row.get("sha256", "")).upper()
        representative = representative_by_sha.get(sha_value)
        if representative is None:
            continue
        group_id = representative_groups.get(str(representative["image_id"]), "")
        if group_id:
            row["near_duplicate_group_candidate"] = group_id
    return audited


def _stat_datetime(timestamp: float, timezone_name: str) -> datetime:
    return datetime.fromtimestamp(timestamp, tz=ZoneInfo(timezone_name))


def _extract_exif_values(image: Image.Image) -> tuple[str, str, str]:
    try:
        exif = image.getexif()
    except Exception:
        return "", "", ""
    return (
        str(exif.get(_EXIF_ORIGINAL, "") or "").strip(),
        str(exif.get(_EXIF_DIGITIZED, "") or "").strip(),
        str(exif.get(_EXIF_DATETIME, "") or "").strip(),
    )


def _build_inventory_row(
    image_path: Path,
    *,
    sequence: int,
    config: TeamPairingAuditConfig,
    source_snapshot_sha256: str,
) -> dict[str, Any]:
    relative_path = _normalized_relative(image_path, config.source_root)
    stat = image_path.stat()
    filesystem_created = _stat_datetime(stat.st_ctime, config.timezone)
    filesystem_modified = _stat_datetime(stat.st_mtime, config.timezone)
    width: int | None = None
    height: int | None = None
    aspect_ratio: float | None = None
    is_readable = True
    read_error = ""
    phash = ""
    exif_original = ""
    exif_digitized = ""
    exif_other = ""

    try:
        with Image.open(image_path) as image:
            width, height = image.size
            exif_original, exif_digitized, exif_other = _extract_exif_values(image)
        with Image.open(image_path) as verification_image:
            verification_image.verify()
        if width and height:
            aspect_ratio = round(width / height, 6)
        phash = compute_phash64(image_path)
    except Exception as exc:
        is_readable = False
        read_error = f"{exc.__class__.__name__}: {exc}"
        width = None
        height = None
        aspect_ratio = None
        phash = ""

    timestamp = select_capture_timestamp(
        exif_datetime_original=exif_original,
        exif_datetime_digitized=exif_digitized,
        exif_datetime_other=exif_other,
        filesystem_created_at=filesystem_created,
        filesystem_modified_at=filesystem_modified,
        timezone_name=config.timezone,
    )
    original_path = (
        Path(*config.source_relative_path.parts) / Path(relative_path)
    ).as_posix()
    return {
        "inventory_sequence": sequence,
        "image_id": deterministic_image_id(relative_path),
        "filename": image_path.name,
        "relative_path": relative_path,
        "original_path": original_path,
        "extension": image_path.suffix.lower(),
        "file_size_bytes": int(stat.st_size),
        "width": width,
        "height": height,
        "aspect_ratio": aspect_ratio,
        "is_readable": is_readable,
        "read_error": read_error,
        "sha256": sha256_file(image_path),
        "perceptual_hash": phash,
        "exif_datetime_original": exif_original,
        "exif_datetime_digitized": exif_digitized,
        "exif_datetime_other": exif_other,
        "filesystem_created_at": filesystem_created.isoformat(),
        "filesystem_modified_at": filesystem_modified.isoformat(),
        "selected_capture_time": timestamp.selected_capture_time,
        "selected_time_source": timestamp.selected_time_source,
        "time_confidence": timestamp.time_confidence,
        "capture_time_parse_warning": timestamp.capture_time_parse_warning,
        "exact_duplicate_group": "",
        "near_duplicate_group_candidate": "",
        "source_snapshot_sha256": source_snapshot_sha256,
        "representative_for_exact_group": False,
        "eligible_for_batch_candidate": False,
        "inventory_notes": "" if is_readable else "unreadable image retained for audit",
    }


def build_team_image_inventory(config: TeamPairingAuditConfig) -> InventoryBuildResult:
    if config.frozen_test_access:
        raise TeamPairingAuditError("Frozen Test access must remain disabled")
    before = build_source_snapshot(config.source_root)
    image_paths = discover_supported_images(config.source_root, config.supported_extensions)
    if not image_paths:
        raise TeamPairingAuditError("zero supported images found under approved source root")
    rows = [
        _build_inventory_row(
            image_path,
            sequence=index,
            config=config,
            source_snapshot_sha256=str(before["snapshot_sha256"]),
        )
        for index, image_path in enumerate(image_paths, start=1)
    ]
    rows = assign_duplicate_groups(
        rows,
        phash_distance_threshold=config.phash_distance_threshold,
    )
    unreadable_count = sum(1 for row in rows if not bool(row["is_readable"]))
    unreadable_rate = unreadable_count / len(rows)
    if unreadable_rate > config.max_unreadable_rate:
        raise TeamPairingAuditError(
            f"unreadable rate {unreadable_rate:.6f} exceeds configured maximum "
            f"{config.max_unreadable_rate:.6f}"
        )
    after = build_source_snapshot(config.source_root)
    verification = verify_source_snapshots(before, after)
    return InventoryBuildResult(
        rows=tuple(rows),
        source_snapshot_before=before,
        source_snapshot_after=after,
        source_snapshot_verification=verification,
    )


def _validate_output_target(path: Path, config: TeamPairingAuditConfig) -> Path:
    resolved = path.resolve()
    output_root = config.output_root.resolve()
    raw_root = (config.project_root / "dataset/01_raw").resolve()
    if not _is_relative_to(resolved, output_root):
        raise TeamPairingAuditError("output path must remain under approved output root")
    if resolved == raw_root or _is_relative_to(resolved, raw_root):
        raise TeamPairingAuditError("output path must not resolve under dataset/01_raw")
    return resolved


def _atomic_destination(path: Path, config: TeamPairingAuditConfig) -> tuple[Path, Path]:
    destination = _validate_output_target(path, config)
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite existing artifact: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    os.close(descriptor)
    return destination, Path(temporary_name)


def atomic_write_csv(
    rows: Iterable[Mapping[str, Any]],
    path: Path,
    *,
    fieldnames: Sequence[str],
    config: TeamPairingAuditConfig,
) -> Path:
    destination, temporary = _atomic_destination(path, config)
    try:
        with temporary.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(fieldnames), extrasaction="raise")
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return destination


def atomic_write_json(
    payload: Mapping[str, Any] | Sequence[Any],
    path: Path,
    *,
    config: TeamPairingAuditConfig,
) -> Path:
    destination, temporary = _atomic_destination(path, config)
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return destination
