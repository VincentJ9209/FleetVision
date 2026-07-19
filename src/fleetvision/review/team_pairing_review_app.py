from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, MutableMapping, Sequence
from zoneinfo import ZoneInfo

from fleetvision.data.team_pairing_audit import (
    ReviewedBatchForPairing,
    build_before_after_pair_candidates,
    pairing_config_fingerprint,
    sha256_file,
)
from fleetvision.review.team_pairing_review_mapping import (
    ANGLE_LABELS,
    ANGLE_STATUS_LABELS,
    BATCH_STATUS_LABELS,
    DEMO_ROLE_LABELS,
    EXISTING_DAMAGE_LABELS,
    NEW_DAMAGE_LABELS,
    PAIR_STATUS_LABELS,
    STAGE_LABELS,
    AngleReviewSelection,
    BatchReviewSelection,
    PairReviewSelection,
    TeamPairingAuditConfig,
    TeamPairingMappingValidationError,
    derive_canonical_angle_fields,
    derive_canonical_batch_fields,
    derive_canonical_pair_fields,
    load_team_pairing_audit_config,
    normalize_vehicle_id,
)
from fleetvision.review.team_pairing_review_state import (
    BatchMemberSeed,
    CandidateBatchSeed,
    PairCandidateSeed,
    SourceImageSeed,
    StoredReview,
    TeamPairingCandidatePackage,
    TeamPairingProgressCounts,
    TeamPairingReviewStateError,
    TeamPairingReviewStateStore,
    TeamPairingWorkspaceIdentity,
)

SCREEN_LABELS: Mapping[str, str] = {
    "batch": "批次審核",
    "angle": "角度標記",
    "pair": "前後配對",
}
BATCH_FILTER_LABELS: Mapping[str, str] = {
    "all": "全部批次",
    "pending": "尚未完成",
    "confirmed": "已確認",
    "split_required": "需要拆分",
    "merge_required": "需要合併",
    "exclude": "排除",
    "uncertain": "無法確定",
}
ANGLE_FILTER_LABELS: Mapping[str, str] = {
    "all": "全部圖片",
    "pending": "尚未完成",
    "reviewed": "已完成",
    "needs_adjudication": "待裁決",
}
PAIR_FILTER_LABELS: Mapping[str, str] = {
    "all": "全部配對",
    "pending": "尚未完成",
    "confirmed": "已確認",
    "rejected": "拒絕配對",
    "uncertain": "無法確定",
}
LIVE_STATE_POLICY = "SQLITE_ONLY"
XLSX_POLICY = "COMPLETED_EXPORT_ONLY"
_PENDING_SELECTION_PREFIX = "_pending_team_pairing_selection"


@dataclass(frozen=True)
class TeamPairingReviewRuntime:
    config: TeamPairingAuditConfig
    package: TeamPairingCandidatePackage
    store: TeamPairingReviewStateStore
    image_by_id: Mapping[str, SourceImageSeed]
    batch_by_id: Mapping[str, CandidateBatchSeed]
    members_by_batch: Mapping[str, tuple[BatchMemberSeed, ...]]
    member_roles: Mapping[tuple[str, str], str]


@dataclass(frozen=True)
class BatchProgressSummary:
    total: int
    terminal: int
    pending: int
    confirmed: int
    unresolved: int


@dataclass(frozen=True)
class PairCandidateViewModel:
    pair_candidate_id: str
    pair_sequence: int
    before_batch_id: str
    after_batch_id: str
    manual_vehicle_id: str
    elapsed_seconds: int
    overlap_angles: tuple[str, ...]
    overlap_count: int
    four_angle_overlap_count: int


@dataclass(frozen=True)
class PairProgressSummary:
    total: int
    terminal: int
    pending: int
    confirmed: int
    rejected: int
    uncertain: int
    primary: int
    backup: int


@dataclass(frozen=True)
class SaveReviewResult:
    stored_review: StoredReview
    progress: TeamPairingProgressCounts


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def next_item_id(item_ids: Sequence[str], current_item_id: str, *, direction: int = 1) -> str:
    if not item_ids:
        raise ValueError("item_ids 不可空白")
    if current_item_id not in item_ids:
        return item_ids[0]
    index = item_ids.index(current_item_id)
    target = max(0, min(len(item_ids) - 1, index + direction))
    return item_ids[target]


def queue_item_selection(
    state: MutableMapping[str, object],
    mode: str,
    item_id: str,
) -> None:
    if mode not in SCREEN_LABELS:
        raise ValueError(f"不支援的 mode：{mode}")
    state[f"{_PENDING_SELECTION_PREFIX}:{mode}"] = item_id


def apply_pending_item_selection(
    state: MutableMapping[str, object],
    *,
    selector_key: str,
    item_ids: Sequence[str],
    fallback_item_id: str,
    mode: str,
) -> str:
    if not item_ids:
        raise ValueError("item_ids 不可空白")
    if mode not in SCREEN_LABELS:
        raise ValueError(f"不支援的 mode：{mode}")
    fallback = fallback_item_id if fallback_item_id in item_ids else item_ids[0]
    pending = state.pop(f"{_PENDING_SELECTION_PREFIX}:{mode}", None)
    if isinstance(pending, str) and pending in item_ids:
        state[selector_key] = pending
    current = state.get(selector_key)
    if not isinstance(current, str) or current not in item_ids:
        state[selector_key] = fallback
    return str(state[selector_key])


def item_widget_key(field: str, entity_type: str, entity_id: str) -> str:
    values = tuple(str(value).strip() for value in (field, entity_type, entity_id))
    if any(not value for value in values):
        raise ValueError("field、entity_type 與 entity_id 不可空白")
    return ":".join(values)


def runtime_session_identity(
    config_path: Path,
    project_root: Path,
    workspace_root: Path,
    candidate_manifest_sha256: str,
) -> str:
    return "|".join(
        (
            str(config_path.resolve()),
            str(project_root.resolve()),
            str(workspace_root.resolve()),
            str(candidate_manifest_sha256).strip().upper(),
        )
    )


def create_runtime(
    config: TeamPairingAuditConfig,
    package: TeamPairingCandidatePackage,
    *,
    store: TeamPairingReviewStateStore | None = None,
    member_roles: Mapping[tuple[str, str], str] | None = None,
    initialize_store: bool = True,
) -> TeamPairingReviewRuntime:
    if package.identity.source_root != str(config.source_root.resolve()):
        raise TeamPairingMappingValidationError("runtime source root 與 config 不一致")
    if package.identity.reviewer != config.reviewer:
        raise TeamPairingMappingValidationError("runtime reviewer 與 config 不一致")
    if package.identity.timezone != config.timezone:
        raise TeamPairingMappingValidationError("runtime timezone 與 config 不一致")

    state_store = store or TeamPairingReviewStateStore(
        package.workspace_root,
        identity=package.identity,
        backup_every_successful_saves=config.backup_every_successful_saves,
        backup_retention=config.backup_retention,
    )
    if initialize_store:
        state_store.initialize(package)

    members_by_batch: dict[str, list[BatchMemberSeed]] = {}
    for member in sorted(
        package.members,
        key=lambda item: (item.batch_id, item.member_sequence, item.image_id),
    ):
        members_by_batch.setdefault(member.batch_id, []).append(member)

    normalized_roles = {
        (member.batch_id, member.image_id): "candidate_representative"
        for member in package.members
    }
    if member_roles:
        normalized_roles.update(
            {
                (str(batch_id), str(image_id)): str(role)
                for (batch_id, image_id), role in member_roles.items()
            }
        )

    return TeamPairingReviewRuntime(
        config=config,
        package=package,
        store=state_store,
        image_by_id={item.image_id: item for item in package.images},
        batch_by_id={item.batch_id: item for item in package.batches},
        members_by_batch={
            batch_id: tuple(items) for batch_id, items in members_by_batch.items()
        },
        member_roles=normalized_roles,
    )


def batch_is_pair_eligible(selection: BatchReviewSelection) -> bool:
    try:
        if selection.manual_batch_status != "confirmed":
            return False
        normalize_vehicle_id(selection.manual_vehicle_id)
        return selection.manual_stage in {"before", "after"}
    except TeamPairingMappingValidationError:
        return False


def _stored_batch_selection(runtime: TeamPairingReviewRuntime, batch_id: str) -> BatchReviewSelection:
    stored = runtime.store.get_batch_review(batch_id)
    if stored.revision == 0:
        return BatchReviewSelection()
    raw = dict(stored.selection)
    try:
        return BatchReviewSelection(**raw)
    except TypeError as exc:
        raise TeamPairingMappingValidationError(
            f"既有 batch review 狀態欄位不相容：{batch_id}"
        ) from exc


def _stored_angle_selection(runtime: TeamPairingReviewRuntime, image_id: str) -> AngleReviewSelection:
    stored = runtime.store._get_review(
        entity_type="image",
        entity_id=image_id,
        table="image_reviews",
        id_column="image_id",
    )
    if stored.revision == 0:
        return AngleReviewSelection()
    raw = dict(stored.selection)
    try:
        return AngleReviewSelection(**raw)
    except TypeError as exc:
        raise TeamPairingMappingValidationError(
            f"既有 angle review 狀態欄位不相容：{image_id}"
        ) from exc


def batch_id_is_pair_eligible(runtime: TeamPairingReviewRuntime, batch_id: str) -> bool:
    return batch_is_pair_eligible(_stored_batch_selection(runtime, batch_id))


def required_angle_image_ids(
    runtime: TeamPairingReviewRuntime,
    batch_id: str,
) -> tuple[str, ...]:
    if batch_id not in runtime.batch_by_id:
        raise TeamPairingMappingValidationError(f"未知 batch ID：{batch_id}")
    if not batch_id_is_pair_eligible(runtime, batch_id):
        return ()

    eligible: list[str] = []
    for member in runtime.members_by_batch.get(batch_id, ()):
        image = runtime.image_by_id.get(member.image_id)
        role = runtime.member_roles.get((batch_id, member.image_id), "")
        if image is None:
            raise TeamPairingMappingValidationError(
                f"batch member 缺少 image evidence：{member.image_id}"
            )
        if image.is_readable and role == "candidate_representative":
            eligible.append(image.image_id)
    return tuple(eligible)


def batch_progress_summary(runtime: TeamPairingReviewRuntime) -> BatchProgressSummary:
    counts = {
        status: len(runtime.store.batch_ids(status))
        for status in BATCH_STATUS_LABELS
    }
    total = len(runtime.store.batch_ids("all"))
    pending = counts["pending"]
    confirmed = counts["confirmed"]
    unresolved = sum(
        counts[status] for status in ("split_required", "merge_required", "uncertain")
    )
    return BatchProgressSummary(
        total=total,
        terminal=total - pending,
        pending=pending,
        confirmed=confirmed,
        unresolved=unresolved,
    )


def save_batch_review_selection(
    runtime: TeamPairingReviewRuntime,
    batch_id: str,
    selection: BatchReviewSelection,
    *,
    reviewed_at: datetime | None = None,
) -> SaveReviewResult:
    if batch_id not in runtime.batch_by_id:
        raise TeamPairingMappingValidationError(f"未知 batch ID：{batch_id}")
    timestamp = reviewed_at or datetime.now(ZoneInfo(runtime.config.timezone))
    canonical = derive_canonical_batch_fields(
        selection,
        reviewer=runtime.config.reviewer,
        reviewed_at=timestamp,
    )
    stored = runtime.store.save_batch_review(batch_id, selection, canonical)
    return SaveReviewResult(stored, runtime.store.progress())


def save_angle_review_selection(
    runtime: TeamPairingReviewRuntime,
    batch_id: str,
    image_id: str,
    selection: AngleReviewSelection,
    *,
    reviewed_at: datetime | None = None,
) -> SaveReviewResult:
    if not batch_id_is_pair_eligible(runtime, batch_id):
        raise TeamPairingMappingValidationError(
            "angle review 只允許 confirmed batch"
        )
    if image_id not in required_angle_image_ids(runtime, batch_id):
        raise TeamPairingMappingValidationError(
            "image 不是可讀的 candidate representative，不能進行 angle review"
        )
    timestamp = reviewed_at or datetime.now(ZoneInfo(runtime.config.timezone))
    canonical = derive_canonical_angle_fields(
        selection,
        reviewer=runtime.config.reviewer,
        reviewed_at=timestamp,
    )
    stored = runtime.store.save_image_review(image_id, selection, canonical)
    return SaveReviewResult(stored, runtime.store.progress())


def _reviewed_angles_for_batch(
    runtime: TeamPairingReviewRuntime,
    batch_id: str,
) -> tuple[str, ...]:
    angles: set[str] = set()
    for image_id in required_angle_image_ids(runtime, batch_id):
        stored = runtime.store.get_image_review(image_id)
        if stored.revision == 0:
            continue
        selection = AngleReviewSelection(**dict(stored.selection))
        if selection.review_status == "reviewed":
            angles.add(selection.manual_angle)
    return tuple(sorted(angles))


def _reviewed_batches_for_pairing(
    runtime: TeamPairingReviewRuntime,
) -> tuple[ReviewedBatchForPairing, ...]:
    rows: list[ReviewedBatchForPairing] = []
    for batch in sorted(
        runtime.package.batches,
        key=lambda item: (item.batch_sequence, item.batch_id),
    ):
        selection = _stored_batch_selection(runtime, batch.batch_id)
        rows.append(
            ReviewedBatchForPairing(
                batch_id=batch.batch_id,
                batch_sequence=batch.batch_sequence,
                start_time=batch.start_time_utc,
                end_time=batch.end_time_utc,
                manual_batch_status=selection.manual_batch_status,
                manual_vehicle_id=selection.manual_vehicle_id,
                manual_stage=selection.manual_stage,
                reviewed_angles=_reviewed_angles_for_batch(runtime, batch.batch_id),
            )
        )
    return tuple(rows)


def pair_candidate_view_models(
    runtime: TeamPairingReviewRuntime,
) -> tuple[PairCandidateViewModel, ...]:
    return tuple(
        PairCandidateViewModel(
            pair_candidate_id=str(row["pair_candidate_id"]),
            pair_sequence=int(row["pair_sequence"]),
            before_batch_id=str(row["before_batch_id"]),
            after_batch_id=str(row["after_batch_id"]),
            manual_vehicle_id=str(row["manual_vehicle_id"]),
            elapsed_seconds=int(row["elapsed_seconds"]),
            overlap_angles=tuple(row["overlap_angles"]),
            overlap_count=int(row["overlap_count"]),
            four_angle_overlap_count=int(row["four_angle_overlap_count"]),
        )
        for row in runtime.store.pair_candidate_rows()
    )


def refresh_pair_candidates(
    runtime: TeamPairingReviewRuntime,
) -> tuple[PairCandidateViewModel, ...]:
    fingerprint = pairing_config_fingerprint(
        pair_max_elapsed_hours=runtime.config.pair_max_elapsed_hours,
        timezone_name=runtime.config.timezone,
        same_calendar_date=True,
    )
    candidates = build_before_after_pair_candidates(
        _reviewed_batches_for_pairing(runtime),
        pair_max_elapsed_hours=runtime.config.pair_max_elapsed_hours,
        timezone_name=runtime.config.timezone,
        pairing_config_fingerprint=fingerprint,
        same_calendar_date=True,
    )
    seeds = tuple(
        PairCandidateSeed(
            pair_candidate_id=item.pair_candidate_id,
            pair_sequence=item.pair_sequence,
            before_batch_id=item.before_batch_id,
            after_batch_id=item.after_batch_id,
            manual_vehicle_id=item.manual_vehicle_id,
            elapsed_seconds=item.elapsed_seconds,
            overlap_angles_json=json.dumps(
                list(item.overlap_angles),
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            overlap_count=item.overlap_count,
            four_angle_overlap_count=item.four_angle_overlap_count,
        )
        for item in candidates
    )
    runtime.store.synchronize_pair_candidates(
        seeds,
        generation_fingerprint=fingerprint,
    )
    return pair_candidate_view_models(runtime)


def pair_contact_sheet_paths(
    runtime: TeamPairingReviewRuntime,
    pair_candidate_id: str,
) -> tuple[Path, Path]:
    by_id = {item.pair_candidate_id: item for item in pair_candidate_view_models(runtime)}
    pair = by_id.get(pair_candidate_id)
    if pair is None:
        raise TeamPairingMappingValidationError(
            f"未知 pair candidate：{pair_candidate_id}"
        )
    contact_dir = runtime.package.workspace_root / "contact_sheets"
    paths = (
        (contact_dir / f"{pair.before_batch_id}.jpg").resolve(),
        (contact_dir / f"{pair.after_batch_id}.jpg").resolve(),
    )
    for path in paths:
        if not _is_relative_to(path, contact_dir.resolve()) or not path.is_file():
            raise TeamPairingMappingValidationError(
                f"pair contact sheet evidence 不存在：{path}"
            )
    return paths


def pair_selection_for_candidate(
    runtime: TeamPairingReviewRuntime,
    pair_candidate_id: str,
) -> PairReviewSelection:
    stored = runtime.store.get_pair_review(pair_candidate_id)
    if stored.revision == 0:
        return PairReviewSelection()
    try:
        return PairReviewSelection(**dict(stored.selection))
    except TypeError as exc:
        raise TeamPairingMappingValidationError(
            f"既有 pair review 狀態欄位不相容：{pair_candidate_id}"
        ) from exc


def save_pair_review_selection(
    runtime: TeamPairingReviewRuntime,
    pair_candidate_id: str,
    selection: PairReviewSelection,
    *,
    reviewed_at: datetime | None = None,
) -> SaveReviewResult:
    if pair_candidate_id not in runtime.store.pair_ids("all"):
        raise TeamPairingMappingValidationError(
            f"未知 pair candidate：{pair_candidate_id}"
        )
    timestamp = reviewed_at or datetime.now(ZoneInfo(runtime.config.timezone))
    canonical = derive_canonical_pair_fields(
        selection,
        reviewer=runtime.config.reviewer,
        reviewed_at=timestamp,
    )
    stored = runtime.store.save_pair_review(
        pair_candidate_id,
        selection,
        canonical,
    )
    return SaveReviewResult(stored, runtime.store.progress())


def pair_progress_summary(runtime: TeamPairingReviewRuntime) -> PairProgressSummary:
    pair_ids = runtime.store.pair_ids("all")
    counts = {
        status: len(runtime.store.pair_ids(status))
        for status in ("pending", "confirmed", "rejected", "uncertain")
    }
    primary = 0
    backup = 0
    for pair_id in pair_ids:
        stored = runtime.store.get_pair_review(pair_id)
        if stored.revision == 0:
            continue
        role = str(stored.canonical_fields.get("manual_demo_role", "none"))
        primary += int(role == "primary")
        backup += int(role == "backup")
    return PairProgressSummary(
        total=len(pair_ids),
        terminal=len(pair_ids) - counts["pending"],
        pending=counts["pending"],
        confirmed=counts["confirmed"],
        rejected=counts["rejected"],
        uncertain=counts["uncertain"],
        primary=primary,
        backup=backup,
    )


def resolve_preview_path(runtime: TeamPairingReviewRuntime, image_id: str) -> Path:
    image = runtime.image_by_id.get(image_id)
    if image is None:
        raise TeamPairingMappingValidationError(f"未知 image ID：{image_id}")
    relative = PurePosixPath(str(image.relative_path).replace("\\", "/"))
    if relative.is_absolute() or ".." in relative.parts:
        raise TeamPairingMappingValidationError("preview path 必須位於 approved source root")

    source_prefix = runtime.config.source_relative_path.parts
    parts = relative.parts
    if tuple(parts[: len(source_prefix)]) == tuple(source_prefix):
        parts = parts[len(source_prefix) :]
    candidate = (runtime.config.source_root / Path(*parts)).resolve()
    source_root = runtime.config.source_root.resolve()
    if not _is_relative_to(candidate, source_root):
        raise TeamPairingMappingValidationError("preview path 必須位於 approved source root")
    if not candidate.is_file():
        raise TeamPairingMappingValidationError(
            f"source preview image 不存在：{candidate}"
        )
    return candidate


def build_streamlit_command(
    *,
    python_executable: Path,
    app_script: Path,
    config_path: Path,
    project_root: Path,
    workspace_root: Path,
    address: str = "127.0.0.1",
    port: int = 8501,
) -> tuple[str, ...]:
    if address != "127.0.0.1":
        raise ValueError("Streamlit 必須只綁定 127.0.0.1")
    if not 1 <= int(port) <= 65535:
        raise ValueError("port 必須介於 1 到 65535")
    return (
        str(python_executable),
        "-m",
        "streamlit",
        "run",
        str(app_script),
        "--server.address=127.0.0.1",
        f"--server.port={int(port)}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--",
        "--config",
        str(config_path),
        "--project-root",
        str(project_root),
        "--workspace-root",
        str(workspace_root),
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise TeamPairingMappingValidationError(f"candidate artifact 不存在：{path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _required_manifest_value(manifest: Mapping[str, Any], key: str) -> str:
    value = str(manifest.get(key, "")).strip()
    if not value:
        raise TeamPairingMappingValidationError(f"candidate manifest 缺少 {key}")
    return value


def load_team_pairing_review_runtime(
    config_path: Path,
    project_root: Path,
    *,
    workspace_root: Path,
) -> TeamPairingReviewRuntime:
    config = load_team_pairing_audit_config(config_path, project_root)
    workspace = workspace_root.resolve()
    if not _is_relative_to(workspace, config.output_root.resolve()):
        raise TeamPairingMappingValidationError("workspace 必須位於 approved output root")

    candidates_dir = workspace / "candidates"
    manifest_path = candidates_dir / "candidate_manifest.json"
    if not manifest_path.is_file():
        raise TeamPairingMappingValidationError("candidate manifest 不存在")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise TeamPairingMappingValidationError("candidate manifest 必須是 JSON object")

    inventory_path = candidates_dir / "team_image_inventory.csv"
    batch_path = candidates_dir / "team_capture_batch_candidates.csv"
    member_path = candidates_dir / "team_capture_batch_members.csv"
    pair_path = candidates_dir / "team_before_after_pair_candidates.csv"

    actual_hashes = {
        "inventory_sha256": sha256_file(inventory_path),
        "batch_candidates_sha256": sha256_file(batch_path),
        "batch_members_sha256": sha256_file(member_path),
        "config_sha256": sha256_file(config.config_path),
    }
    for key, actual in actual_hashes.items():
        expected = _required_manifest_value(manifest, key).upper()
        if actual.upper() != expected:
            raise TeamPairingMappingValidationError(f"candidate artifact SHA256 mismatch：{key}")

    inventory_rows = _read_csv(inventory_path)
    batch_rows = _read_csv(batch_path)
    member_rows = _read_csv(member_path)
    pair_rows = _read_csv(pair_path) if pair_path.is_file() else []

    images = tuple(
        SourceImageSeed(
            str(row["image_id"]),
            int(row["inventory_sequence"]),
            str(row["relative_path"]),
            _as_bool(row["is_readable"]),
        )
        for row in inventory_rows
    )
    batches = tuple(
        CandidateBatchSeed(
            str(row["batch_id"]),
            int(row["batch_sequence"]),
            str(row.get("start_time") or row.get("start_time_utc") or ""),
            str(row.get("end_time") or row.get("end_time_utc") or ""),
        )
        for row in batch_rows
    )
    members = tuple(
        BatchMemberSeed(
            str(row["batch_id"]),
            str(row["image_id"]),
            int(row["member_sequence"]),
        )
        for row in member_rows
    )
    pairs = tuple(
        PairCandidateSeed(
            str(row["pair_candidate_id"]),
            int(row["pair_sequence"]),
            str(row["before_batch_id"]),
            str(row["after_batch_id"]),
        )
        for row in pair_rows
    )

    expected_counts = {
        "expected_image_count": len(images),
        "expected_batch_count": len(batches),
        "expected_pair_count": len(pairs),
    }
    for key, actual in expected_counts.items():
        if int(manifest.get(key, -1)) != actual:
            raise TeamPairingMappingValidationError(f"candidate manifest count mismatch：{key}")

    identity = TeamPairingWorkspaceIdentity(
        schema_version=config.schema_version,
        project_root=str(config.project_root.resolve()),
        source_root=str(config.source_root.resolve()),
        candidate_manifest_sha256=sha256_file(manifest_path),
        inventory_sha256=actual_hashes["inventory_sha256"],
        batch_candidates_sha256=actual_hashes["batch_candidates_sha256"],
        batch_members_sha256=actual_hashes["batch_members_sha256"],
        config_sha256=actual_hashes["config_sha256"],
        reviewer=config.reviewer,
        timezone=config.timezone,
        expected_image_count=len(images),
        expected_batch_count=len(batches),
        expected_pair_count=len(pairs),
    )
    package = TeamPairingCandidatePackage(
        workspace,
        identity,
        images,
        batches,
        members,
        pairs,
    )
    roles = {
        (str(row["batch_id"]), str(row["image_id"])): str(
            row.get("membership_role", "candidate_representative")
        )
        for row in member_rows
    }
    return create_runtime(config, package, member_roles=roles)


def _render_batch_screen(st: Any, runtime: TeamPairingReviewRuntime) -> None:
    summary = batch_progress_summary(runtime)
    columns = st.columns(5)
    columns[0].metric("候選批次", summary.total)
    columns[1].metric("已處理", summary.terminal)
    columns[2].metric("尚未完成", summary.pending)
    columns[3].metric("已確認", summary.confirmed)
    columns[4].metric("待處理拆分／合併／不確定", summary.unresolved)

    filter_name = st.selectbox(
        "篩選批次",
        options=tuple(BATCH_FILTER_LABELS),
        format_func=lambda value: BATCH_FILTER_LABELS[value],
    )
    batch_ids = list(runtime.store.batch_ids(filter_name))
    if not batch_ids:
        st.success("此篩選條件目前沒有批次。")
        return

    last_mode, last_item = runtime.store.last_viewed()
    fallback = last_item if last_mode == "batch" else batch_ids[0]
    selector_key = f"team_pairing_batch_selector:{filter_name}"
    selected = apply_pending_item_selection(
        st.session_state,
        selector_key=selector_key,
        item_ids=batch_ids,
        fallback_item_id=fallback,
        mode="batch",
    )
    selected = st.selectbox(
        "選擇批次",
        options=batch_ids,
        index=batch_ids.index(selected),
        key=selector_key,
    )
    runtime.store.set_last_viewed("batch", selected)

    batch = runtime.batch_by_id[selected]
    st.subheader(f"批次 {batch.batch_sequence}/{len(runtime.package.batches)}｜{selected}")
    st.caption(f"時間：{batch.start_time_utc} ～ {batch.end_time_utc}")
    contact_sheet = runtime.package.workspace_root / "contact_sheets" / f"{selected}.jpg"
    if contact_sheet.is_file():
        st.image(str(contact_sheet), caption="候選批次接觸表", use_container_width=True)
    else:
        st.warning("找不到 contact sheet；此為 blocking evidence，不會自動重建。")

    members = runtime.members_by_batch.get(selected, ())
    if members:
        thumbnail_columns = st.columns(min(4, len(members)))
        for index, member in enumerate(members):
            try:
                preview = resolve_preview_path(runtime, member.image_id)
            except TeamPairingMappingValidationError as exc:
                thumbnail_columns[index % len(thumbnail_columns)].error(str(exc))
            else:
                role = runtime.member_roles.get((selected, member.image_id), "")
                thumbnail_columns[index % len(thumbnail_columns)].image(
                    str(preview),
                    caption=f"{member.image_id}｜{role}",
                    use_container_width=True,
                )

    current = _stored_batch_selection(runtime, selected)
    status_options = tuple(BATCH_STATUS_LABELS)
    stage_options = tuple(STAGE_LABELS)
    status = st.selectbox(
        "批次狀態",
        options=status_options,
        index=status_options.index(current.manual_batch_status),
        format_func=lambda value: BATCH_STATUS_LABELS[value],
        key=item_widget_key("status", "batch", selected),
    )
    vehicle = st.text_input(
        "車輛代碼",
        value=current.manual_vehicle_id,
        help="使用 TEAMCAR-000 格式；不依賴 OCR 或車牌辨識。",
        key=item_widget_key("vehicle", "batch", selected),
    )
    stage = st.selectbox(
        "借還車階段",
        options=stage_options,
        index=stage_options.index(current.manual_stage),
        format_func=lambda value: STAGE_LABELS[value],
        key=item_widget_key("stage", "batch", selected),
    )
    notes = st.text_area(
        "批次備註",
        value=current.manual_notes,
        key=item_widget_key("notes", "batch", selected),
    )
    if st.button("儲存批次審核", type="primary", key=item_widget_key("save", "batch", selected)):
        try:
            result = save_batch_review_selection(
                runtime,
                selected,
                BatchReviewSelection(status, vehicle, stage, notes),
            )
        except TeamPairingMappingValidationError as exc:
            st.error(str(exc))
        else:
            st.success(f"已儲存 revision {result.stored_review.revision}")

    previous_column, next_column = st.columns(2)
    if previous_column.button("上一個批次", key=item_widget_key("previous", "batch", selected)):
        queue_item_selection(st.session_state, "batch", next_item_id(batch_ids, selected, direction=-1))
        st.rerun()
    if next_column.button("下一個批次", key=item_widget_key("next", "batch", selected)):
        queue_item_selection(st.session_state, "batch", next_item_id(batch_ids, selected, direction=1))
        st.rerun()


def _render_angle_screen(st: Any, runtime: TeamPairingReviewRuntime) -> None:
    confirmed_batches = list(runtime.store.batch_ids("confirmed"))
    if not confirmed_batches:
        st.info("目前沒有已確認且可進行角度標記的批次。")
        return
    batch_id = st.selectbox("選擇已確認批次", options=confirmed_batches)
    image_ids = list(required_angle_image_ids(runtime, batch_id))
    if not image_ids:
        st.warning("此批次沒有可讀的 candidate representative 圖片。")
        return
    _, last_item = runtime.store.last_viewed()
    selector_key = f"team_pairing_angle_selector:{batch_id}"
    selected = apply_pending_item_selection(
        st.session_state,
        selector_key=selector_key,
        item_ids=image_ids,
        fallback_item_id=last_item,
        mode="angle",
    )
    selected = st.selectbox(
        "選擇圖片",
        options=image_ids,
        index=image_ids.index(selected),
        key=selector_key,
    )
    runtime.store.set_last_viewed("image", selected)
    try:
        preview = resolve_preview_path(runtime, selected)
    except TeamPairingMappingValidationError as exc:
        st.error(str(exc))
        return
    st.image(str(preview), caption=f"{selected}｜來源唯讀預覽", use_container_width=True)

    current = _stored_angle_selection(runtime, selected)
    status_options = tuple(ANGLE_STATUS_LABELS)
    angle_options = tuple(ANGLE_LABELS)
    status = st.selectbox(
        "角度審核狀態",
        options=status_options,
        index=status_options.index(current.review_status),
        format_func=lambda value: ANGLE_STATUS_LABELS[value],
        key=item_widget_key("status", "image", selected),
    )
    angle = st.selectbox(
        "人工角度",
        options=angle_options,
        index=angle_options.index(current.manual_angle),
        format_func=lambda value: ANGLE_LABELS[value],
        key=item_widget_key("angle", "image", selected),
    )
    notes = st.text_area(
        "角度備註",
        value=current.manual_notes,
        key=item_widget_key("notes", "image", selected),
    )
    if st.button("儲存角度標記", type="primary", key=item_widget_key("save", "image", selected)):
        try:
            result = save_angle_review_selection(
                runtime,
                batch_id,
                selected,
                AngleReviewSelection(status, angle, notes),
            )
        except TeamPairingMappingValidationError as exc:
            st.error(str(exc))
        else:
            st.success(f"已儲存 revision {result.stored_review.revision}")

    previous_column, next_column = st.columns(2)
    if previous_column.button("上一張", key=item_widget_key("previous", "image", selected)):
        queue_item_selection(st.session_state, "angle", next_item_id(image_ids, selected, direction=-1))
        st.rerun()
    if next_column.button("下一張", key=item_widget_key("next", "image", selected)):
        queue_item_selection(st.session_state, "angle", next_item_id(image_ids, selected, direction=1))
        st.rerun()


def _render_pair_screen(st: Any, runtime: TeamPairingReviewRuntime) -> None:
    try:
        pairs = refresh_pair_candidates(runtime)
    except TeamPairingReviewStateError as exc:
        st.error(str(exc))
        return
    summary = pair_progress_summary(runtime)
    metrics = st.columns(4)
    metrics[0].metric("配對候選", summary.total)
    metrics[1].metric("已確認", summary.confirmed)
    metrics[2].metric("主要／備用", f"{summary.primary}/{summary.backup}")
    metrics[3].metric("尚未完成", summary.pending)
    if not pairs:
        st.info("目前沒有符合相同車輛、before/after、時間與角度重疊規則的配對候選。")
        return

    filter_name = st.selectbox(
        "篩選配對",
        options=tuple(PAIR_FILTER_LABELS),
        format_func=lambda value: PAIR_FILTER_LABELS[value],
    )
    pair_ids = list(runtime.store.pair_ids(filter_name))
    if not pair_ids:
        st.success("此篩選條件目前沒有配對。")
        return
    _, last_item = runtime.store.last_viewed()
    selector_key = f"team_pairing_pair_selector:{filter_name}"
    selected = apply_pending_item_selection(
        st.session_state,
        selector_key=selector_key,
        item_ids=pair_ids,
        fallback_item_id=last_item,
        mode="pair",
    )
    selected = st.selectbox(
        "選擇配對",
        options=pair_ids,
        index=pair_ids.index(selected),
        key=selector_key,
    )
    runtime.store.set_last_viewed("pair", selected)
    view = {item.pair_candidate_id: item for item in pairs}[selected]
    st.subheader(
        f"配對 {view.pair_sequence}/{len(pairs)}｜{view.manual_vehicle_id}"
    )
    st.caption(
        f"間隔 {view.elapsed_seconds // 60} 分鐘｜共同角度："
        + "、".join(ANGLE_LABELS.get(value, value) for value in view.overlap_angles)
    )

    try:
        before_path, after_path = pair_contact_sheet_paths(runtime, selected)
    except TeamPairingMappingValidationError as exc:
        st.error(str(exc))
        return
    evidence_columns = st.columns(2)
    evidence_columns[0].image(
        str(before_path),
        caption=f"借車前批次｜{view.before_batch_id}",
        use_container_width=True,
    )
    evidence_columns[1].image(
        str(after_path),
        caption=f"還車後批次｜{view.after_batch_id}",
        use_container_width=True,
    )

    current = pair_selection_for_candidate(runtime, selected)
    status_options = tuple(PAIR_STATUS_LABELS)
    existing_options = tuple(EXISTING_DAMAGE_LABELS)
    new_damage_options = tuple(NEW_DAMAGE_LABELS)
    role_options = tuple(DEMO_ROLE_LABELS)
    status = st.selectbox(
        "配對狀態",
        options=status_options,
        index=status_options.index(current.manual_pair_status),
        format_func=lambda value: PAIR_STATUS_LABELS[value],
        key=item_widget_key("status", "pair", selected),
    )
    existing = st.selectbox(
        "既有車損是否可見",
        options=existing_options,
        index=existing_options.index(current.manual_existing_damage_visible),
        format_func=lambda value: EXISTING_DAMAGE_LABELS[value],
        key=item_widget_key("existing", "pair", selected),
    )
    new_damage = st.selectbox(
        "新增車損判定",
        options=new_damage_options,
        index=new_damage_options.index(current.manual_new_damage_status),
        format_func=lambda value: NEW_DAMAGE_LABELS[value],
        key=item_widget_key("new_damage", "pair", selected),
    )
    role = st.selectbox(
        "展示角色",
        options=role_options,
        index=role_options.index(current.manual_demo_role),
        format_func=lambda value: DEMO_ROLE_LABELS[value],
        key=item_widget_key("demo_role", "pair", selected),
    )
    notes = st.text_area(
        "配對備註",
        value=current.manual_notes,
        key=item_widget_key("notes", "pair", selected),
    )
    if st.button("儲存配對審核", type="primary", key=item_widget_key("save", "pair", selected)):
        try:
            result = save_pair_review_selection(
                runtime,
                selected,
                PairReviewSelection(status, existing, new_damage, role, notes),
            )
        except (TeamPairingMappingValidationError, TeamPairingReviewStateError) as exc:
            st.error(str(exc))
        else:
            classification = result.stored_review.canonical_fields[
                "derived_case_classification"
            ]
            st.success(
                f"已儲存 revision {result.stored_review.revision}｜{classification}"
            )

    previous_column, next_column = st.columns(2)
    if previous_column.button("上一組", key=item_widget_key("previous", "pair", selected)):
        queue_item_selection(
            st.session_state,
            "pair",
            next_item_id(pair_ids, selected, direction=-1),
        )
        st.rerun()
    if next_column.button("下一組", key=item_widget_key("next", "pair", selected)):
        queue_item_selection(
            st.session_state,
            "pair",
            next_item_id(pair_ids, selected, direction=1),
        )
        st.rerun()


def render_app(config_path: Path, project_root: Path, *, workspace_root: Path) -> None:
    import streamlit as st

    st.set_page_config(
        page_title="FleetVision Team Pairing Audit",
        page_icon="🚗",
        layout="wide",
    )
    st.title("FleetVision｜車輛借還前後批次與角度人工審核")
    st.caption(
        "本工具只讀取 approved 04_team 圖片；live state 僅寫入本機 SQLite。"
        "XLSX 僅於完成後輸出，不作即時輸入，也不執行 OCR、模型 inference 或 Frozen Test 存取。"
    )

    resolved_config = config_path if config_path.is_absolute() else project_root / config_path
    manifest_path = workspace_root / "candidates" / "candidate_manifest.json"
    manifest_sha = sha256_file(manifest_path) if manifest_path.is_file() else "MISSING"
    identity = runtime_session_identity(
        resolved_config,
        project_root,
        workspace_root,
        manifest_sha,
    )
    runtime_key = "_team_pairing_review_runtime"
    identity_key = "_team_pairing_review_runtime_identity"
    if st.session_state.get(identity_key) != identity:
        with st.spinner("正在驗證 candidate artifacts 與 SQLite workspace identity…"):
            st.session_state[runtime_key] = load_team_pairing_review_runtime(
                resolved_config,
                project_root,
                workspace_root=workspace_root,
            )
        st.session_state[identity_key] = identity
    runtime: TeamPairingReviewRuntime = st.session_state[runtime_key]

    progress = runtime.store.progress()
    metrics = st.columns(4)
    metrics[0].metric("圖片已標記", f"{progress.images_reviewed}/{progress.images_total}")
    metrics[1].metric("批次已處理", f"{progress.batches_terminal}/{progress.batches_total}")
    metrics[2].metric("配對已處理", f"{progress.pairs_terminal}/{progress.pairs_total}")
    metrics[3].metric("成功儲存次數", runtime.store.successful_save_count())

    with st.sidebar:
        screen = st.radio(
            "作業畫面",
            options=tuple(SCREEN_LABELS),
            format_func=lambda value: SCREEN_LABELS[value],
        )
        st.info(
            "來源圖片全程唯讀；不提供 upload、delete、rename、move 或 EXIF 修改。"
        )

    if screen == "batch":
        _render_batch_screen(st, runtime)
    elif screen == "angle":
        _render_angle_screen(st, runtime)
    else:
        _render_pair_screen(st, runtime)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the local-only FleetVision Team Pairing review utility."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--workspace-root", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    render_app(
        Path(args.config),
        Path(args.project_root).resolve(),
        workspace_root=Path(args.workspace_root).resolve(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
