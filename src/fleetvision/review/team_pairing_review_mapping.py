from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml


class TeamPairingMappingValidationError(ValueError):
    """Raised when a Team Pairing Audit value violates the approved contract."""


BATCH_STATUS_LABELS: Mapping[str, str] = {
    "pending": "尚未完成",
    "confirmed": "已確認",
    "split_required": "需要拆分",
    "merge_required": "需要合併",
    "exclude": "排除",
    "uncertain": "無法確定",
}

STAGE_LABELS: Mapping[str, str] = {
    "before": "借車前",
    "after": "還車後",
    "unknown": "未知",
}

ANGLE_STATUS_LABELS: Mapping[str, str] = {
    "pending": "尚未完成",
    "reviewed": "已完成",
    "needs_adjudication": "待裁決",
}

ANGLE_LABELS: Mapping[str, str] = {
    "front_left": "左前",
    "front_right": "右前",
    "rear_left": "左後",
    "rear_right": "右後",
    "front": "正前",
    "rear": "正後",
    "left_side": "左側",
    "right_side": "右側",
    "closeup": "局部特寫",
    "interior": "車內",
    "other": "其他",
    "unknown": "未知",
}

PAIR_STATUS_LABELS: Mapping[str, str] = {
    "pending": "尚未完成",
    "confirmed": "已確認",
    "rejected": "拒絕配對",
    "uncertain": "無法確定",
}

EXISTING_DAMAGE_LABELS: Mapping[str, str] = {
    "yes": "可見既有車損",
    "no": "未見既有車損",
    "uncertain": "無法確定",
}

NEW_DAMAGE_LABELS: Mapping[str, str] = {
    "none": "無新增車損",
    "suspected": "疑似新增車損",
    "uncertain": "無法確定",
}

DEMO_ROLE_LABELS: Mapping[str, str] = {
    "none": "非展示案例",
    "primary": "主要展示案例",
    "backup": "備用展示案例",
}

CONTROLLED_OPTIONS: Mapping[str, tuple[str, ...]] = {
    "manual_batch_status": tuple(BATCH_STATUS_LABELS),
    "manual_stage": tuple(STAGE_LABELS),
    "angle_review_status": tuple(ANGLE_STATUS_LABELS),
    "manual_angle": tuple(ANGLE_LABELS),
    "manual_pair_status": tuple(PAIR_STATUS_LABELS),
    "manual_existing_damage_visible": tuple(EXISTING_DAMAGE_LABELS),
    "manual_new_damage_status": tuple(NEW_DAMAGE_LABELS),
    "manual_demo_role": tuple(DEMO_ROLE_LABELS),
}

VEHICLE_ID_PATTERN = re.compile(r"^TEAMCAR-[0-9]{3}$")
EXPECTED_SOURCE_RELATIVE_PATH = PurePosixPath("dataset/01_raw/04_team")


@dataclass(frozen=True)
class TeamPairingAuditConfig:
    schema_version: str
    project_root: Path
    config_path: Path
    source_relative_path: PurePosixPath
    output_relative_path: PurePosixPath
    source_root: Path
    output_root: Path
    supported_extensions: tuple[str, ...]
    batch_gap_minutes: int
    pair_max_elapsed_hours: int
    phash_distance_threshold: int
    contact_sheet_columns: int
    contact_sheet_thumbnail_size: int
    timezone: str
    reviewer: str
    backup_every_successful_saves: int
    backup_retention: int
    max_unreadable_rate: float
    frozen_test_access: bool


@dataclass(frozen=True)
class BatchReviewSelection:
    manual_batch_status: str = "pending"
    manual_vehicle_id: str = ""
    manual_stage: str = "unknown"
    manual_notes: str = ""


@dataclass(frozen=True)
class AngleReviewSelection:
    review_status: str = "pending"
    manual_angle: str = "unknown"
    manual_notes: str = ""


@dataclass(frozen=True)
class PairReviewSelection:
    manual_pair_status: str = "pending"
    manual_existing_damage_visible: str = "uncertain"
    manual_new_damage_status: str = "uncertain"
    manual_demo_role: str = "none"
    manual_notes: str = ""


@dataclass(frozen=True)
class CanonicalBatchFields:
    manual_batch_status: str
    manual_vehicle_id: str
    manual_stage: str
    manual_notes: str
    review_reviewer: str
    reviewed_at_utc: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class CanonicalAngleFields:
    review_status: str
    manual_angle: str
    manual_notes: str
    review_reviewer: str
    reviewed_at_utc: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class CanonicalPairFields:
    manual_pair_status: str
    manual_existing_damage_visible: str
    manual_new_damage_status: str
    manual_demo_role: str
    manual_notes: str
    derived_case_classification: str
    review_reviewer: str
    reviewed_at_utc: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def _normalize(value: object) -> str:
    return str(value or "").strip()


def _require_controlled(field: str, value: object) -> str:
    normalized = _normalize(value)
    if normalized not in CONTROLLED_OPTIONS[field]:
        raise TeamPairingMappingValidationError(
            f"{field}={normalized!r} 不是核准的 controlled value"
        )
    return normalized


def _require_safe_relative(value: object, label: str) -> PurePosixPath:
    raw = _normalize(value).replace("\\", "/")
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise TeamPairingMappingValidationError(f"{label} 必須是安全相對路徑")
    return path


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _require_positive_int(value: object, label: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise TeamPairingMappingValidationError(f"{label} 必須是正整數") from exc
    if parsed <= 0:
        raise TeamPairingMappingValidationError(f"{label} 必須是正整數")
    return parsed


def _normalize_extensions(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise TeamPairingMappingValidationError("supported_extensions 必須是非空白 list")
    normalized = tuple(str(item).strip().lower() for item in value)
    if any(not item.startswith(".") or len(item) < 2 for item in normalized):
        raise TeamPairingMappingValidationError("supported_extensions 每一項必須以 . 開頭")
    if len(normalized) != len(set(normalized)):
        raise TeamPairingMappingValidationError("supported_extensions 不可重複")
    return normalized


def load_team_pairing_audit_config(
    config_path: Path,
    project_root: Path,
) -> TeamPairingAuditConfig:
    project_root = project_root.resolve()
    resolved_config = (
        config_path.resolve()
        if config_path.is_absolute()
        else (project_root / config_path).resolve()
    )
    if not resolved_config.is_file():
        raise TeamPairingMappingValidationError(f"Team Pairing config 不存在：{resolved_config}")
    if not _is_relative_to(resolved_config, project_root):
        raise TeamPairingMappingValidationError("config 必須位於 project root 內")

    raw = yaml.safe_load(resolved_config.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise TeamPairingMappingValidationError("Team Pairing config 必須是 YAML mapping")

    try:
        schema_version = _normalize(raw["schema_version"])
        source_relative = _require_safe_relative(raw["source_relative_path"], "source_relative_path")
        output_relative = _require_safe_relative(raw["output_relative_path"], "output_relative_path")
        supported_extensions = _normalize_extensions(raw["supported_extensions"])
        batch_gap_minutes = _require_positive_int(raw["batch_gap_minutes"], "batch_gap_minutes")
        pair_max_elapsed_hours = _require_positive_int(
            raw["pair_max_elapsed_hours"], "pair_max_elapsed_hours"
        )
        phash_distance_threshold = int(raw["phash_distance_threshold"])
        contact_sheet_columns = _require_positive_int(
            raw["contact_sheet_columns"], "contact_sheet_columns"
        )
        contact_sheet_thumbnail_size = _require_positive_int(
            raw["contact_sheet_thumbnail_size"], "contact_sheet_thumbnail_size"
        )
        timezone_name = _normalize(raw["timezone"])
        reviewer = _normalize(raw["reviewer"])
        backup_every = _require_positive_int(
            raw["backup_every_successful_saves"], "backup_every_successful_saves"
        )
        backup_retention = _require_positive_int(raw["backup_retention"], "backup_retention")
        max_unreadable_rate = float(raw["max_unreadable_rate"])
        frozen_test_access = raw["frozen_test_access"]
    except KeyError as exc:
        raise TeamPairingMappingValidationError(f"config 缺少必要欄位：{exc.args[0]}") from exc
    except (TypeError, ValueError) as exc:
        raise TeamPairingMappingValidationError(f"config 數值格式無效：{exc}") from exc

    if schema_version != "1":
        raise TeamPairingMappingValidationError("schema_version 必須是 1")
    if source_relative != EXPECTED_SOURCE_RELATIVE_PATH:
        raise TeamPairingMappingValidationError(
            "source_relative_path 必須固定為 dataset/01_raw/04_team"
        )
    if frozen_test_access is not False:
        raise TeamPairingMappingValidationError("Frozen Test access 必須固定為 false")
    if not reviewer:
        raise TeamPairingMappingValidationError("reviewer 不可空白")
    try:
        ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise TeamPairingMappingValidationError("timezone 不是有效 IANA timezone") from exc
    if not 0 <= phash_distance_threshold <= 64:
        raise TeamPairingMappingValidationError("phash_distance_threshold 必須介於 0 與 64")
    if not 0.0 <= max_unreadable_rate <= 1.0:
        raise TeamPairingMappingValidationError("max_unreadable_rate 必須介於 0 與 1")

    source_root = (project_root / Path(*source_relative.parts)).resolve()
    output_root = (project_root / Path(*output_relative.parts)).resolve()
    raw_root = (project_root / "dataset/01_raw").resolve()

    if not _is_relative_to(source_root, project_root):
        raise TeamPairingMappingValidationError("source root 必須位於 project root 內")
    if not _is_relative_to(output_root, project_root):
        raise TeamPairingMappingValidationError("output root 必須位於 project root 內")
    if output_root == raw_root or _is_relative_to(output_root, raw_root):
        raise TeamPairingMappingValidationError("output root 不得位於 dataset/01_raw")
    if output_root == source_root or _is_relative_to(output_root, source_root):
        raise TeamPairingMappingValidationError("output root 不得位於 source root")

    return TeamPairingAuditConfig(
        schema_version=schema_version,
        project_root=project_root,
        config_path=resolved_config,
        source_relative_path=source_relative,
        output_relative_path=output_relative,
        source_root=source_root,
        output_root=output_root,
        supported_extensions=supported_extensions,
        batch_gap_minutes=batch_gap_minutes,
        pair_max_elapsed_hours=pair_max_elapsed_hours,
        phash_distance_threshold=phash_distance_threshold,
        contact_sheet_columns=contact_sheet_columns,
        contact_sheet_thumbnail_size=contact_sheet_thumbnail_size,
        timezone=timezone_name,
        reviewer=reviewer,
        backup_every_successful_saves=backup_every,
        backup_retention=backup_retention,
        max_unreadable_rate=max_unreadable_rate,
        frozen_test_access=False,
    )


def normalize_vehicle_id(value: object) -> str:
    normalized = _normalize(value).upper()
    if not VEHICLE_ID_PATTERN.fullmatch(normalized):
        raise TeamPairingMappingValidationError(
            "vehicle ID 必須使用 TEAMCAR-000 格式（三位數字）"
        )
    return normalized


def validate_batch_selection(selection: BatchReviewSelection) -> None:
    status = _require_controlled("manual_batch_status", selection.manual_batch_status)
    stage = _require_controlled("manual_stage", selection.manual_stage)
    notes = _normalize(selection.manual_notes)
    vehicle = _normalize(selection.manual_vehicle_id)

    if vehicle:
        normalize_vehicle_id(vehicle)

    if status == "pending":
        if vehicle or stage != "unknown":
            raise TeamPairingMappingValidationError("pending batch 不得預先指定 vehicle 或 stage")
        return

    if status == "confirmed":
        if not vehicle:
            raise TeamPairingMappingValidationError("confirmed batch 必須指定 vehicle ID")
        if stage not in {"before", "after"}:
            raise TeamPairingMappingValidationError("confirmed batch stage 必須是 before/after")
        return

    if not notes:
        raise TeamPairingMappingValidationError("此 batch disposition 必須填寫具體說明")


def validate_angle_selection(selection: AngleReviewSelection) -> None:
    status = _require_controlled("angle_review_status", selection.review_status)
    angle = _require_controlled("manual_angle", selection.manual_angle)
    notes = _normalize(selection.manual_notes)

    if status == "pending":
        if angle != "unknown":
            raise TeamPairingMappingValidationError("pending angle 不得預先指定正式角度")
        return

    if status == "needs_adjudication":
        if angle != "unknown" or not notes:
            raise TeamPairingMappingValidationError("待裁決角度必須維持 unknown 並填寫具體說明")
        return

    if angle == "unknown" and not notes:
        raise TeamPairingMappingValidationError("reviewed unknown angle 必須填寫具體說明")


def derive_pair_classification(
    manual_pair_status: object,
    manual_existing_damage_visible: object,
    manual_new_damage_status: object,
) -> str:
    status = _require_controlled("manual_pair_status", manual_pair_status)
    existing = _require_controlled(
        "manual_existing_damage_visible", manual_existing_damage_visible
    )
    new_damage = _require_controlled("manual_new_damage_status", manual_new_damage_status)

    if status != "confirmed":
        return "MANUAL_REVIEW_REQUIRED"
    if new_damage == "suspected":
        return "NEW_DAMAGE_CANDIDATE"
    if new_damage == "none" and existing == "no":
        return "NO_NEW_DAMAGE"
    if new_damage == "none" and existing == "yes":
        return "EXISTING_DAMAGE_UNCHANGED"
    return "MANUAL_REVIEW_REQUIRED"


def validate_pair_selection(selection: PairReviewSelection) -> None:
    status = _require_controlled("manual_pair_status", selection.manual_pair_status)
    existing = _require_controlled(
        "manual_existing_damage_visible", selection.manual_existing_damage_visible
    )
    new_damage = _require_controlled(
        "manual_new_damage_status", selection.manual_new_damage_status
    )
    demo_role = _require_controlled("manual_demo_role", selection.manual_demo_role)
    notes = _normalize(selection.manual_notes)

    if status == "pending":
        if existing != "uncertain" or new_damage != "uncertain" or demo_role != "none":
            raise TeamPairingMappingValidationError("pending pair 不得預先填入正式結論")
        return

    if status in {"rejected", "uncertain"}:
        if demo_role != "none":
            raise TeamPairingMappingValidationError("未確認 pair 的 demo role 必須是 none")
        if not notes:
            raise TeamPairingMappingValidationError("rejected/uncertain pair 必須填寫具體說明")
        return

    classification = derive_pair_classification(status, existing, new_damage)
    if classification == "MANUAL_REVIEW_REQUIRED" and not notes:
        raise TeamPairingMappingValidationError("不確定 pair 結論必須填寫具體說明")
    if demo_role != "none" and classification not in {
        "NO_NEW_DAMAGE",
        "EXISTING_DAMAGE_UNCHANGED",
    }:
        raise TeamPairingMappingValidationError(
            "demo role 只允許可靠的 NO_NEW_DAMAGE 或 EXISTING_DAMAGE_UNCHANGED pair"
        )


def _review_identity(reviewer: object, reviewed_at: datetime) -> tuple[str, str]:
    reviewer_value = _normalize(reviewer)
    if not reviewer_value:
        raise TeamPairingMappingValidationError("reviewer 不可空白")
    if reviewed_at.tzinfo is None or reviewed_at.utcoffset() is None:
        raise TeamPairingMappingValidationError("reviewed_at 必須包含時區")
    return reviewer_value, reviewed_at.astimezone(timezone.utc).isoformat()


def derive_canonical_batch_fields(
    selection: BatchReviewSelection,
    *,
    reviewer: str,
    reviewed_at: datetime,
) -> CanonicalBatchFields:
    validate_batch_selection(selection)
    reviewer_value, reviewed_at_utc = _review_identity(reviewer, reviewed_at)
    vehicle = _normalize(selection.manual_vehicle_id)
    return CanonicalBatchFields(
        manual_batch_status=_normalize(selection.manual_batch_status),
        manual_vehicle_id="" if not vehicle else normalize_vehicle_id(vehicle),
        manual_stage=_normalize(selection.manual_stage),
        manual_notes=_normalize(selection.manual_notes),
        review_reviewer=reviewer_value,
        reviewed_at_utc=reviewed_at_utc,
    )


def derive_canonical_angle_fields(
    selection: AngleReviewSelection,
    *,
    reviewer: str,
    reviewed_at: datetime,
) -> CanonicalAngleFields:
    validate_angle_selection(selection)
    reviewer_value, reviewed_at_utc = _review_identity(reviewer, reviewed_at)
    return CanonicalAngleFields(
        review_status=_normalize(selection.review_status),
        manual_angle=_normalize(selection.manual_angle),
        manual_notes=_normalize(selection.manual_notes),
        review_reviewer=reviewer_value,
        reviewed_at_utc=reviewed_at_utc,
    )


def derive_canonical_pair_fields(
    selection: PairReviewSelection,
    *,
    reviewer: str,
    reviewed_at: datetime,
) -> CanonicalPairFields:
    validate_pair_selection(selection)
    reviewer_value, reviewed_at_utc = _review_identity(reviewer, reviewed_at)
    return CanonicalPairFields(
        manual_pair_status=_normalize(selection.manual_pair_status),
        manual_existing_damage_visible=_normalize(
            selection.manual_existing_damage_visible
        ),
        manual_new_damage_status=_normalize(selection.manual_new_damage_status),
        manual_demo_role=_normalize(selection.manual_demo_role),
        manual_notes=_normalize(selection.manual_notes),
        derived_case_classification=derive_pair_classification(
            selection.manual_pair_status,
            selection.manual_existing_damage_visible,
            selection.manual_new_damage_status,
        ),
        review_reviewer=reviewer_value,
        reviewed_at_utc=reviewed_at_utc,
    )
