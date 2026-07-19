from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fleetvision.data.team_pairing_audit import (
    INVENTORY_COLUMNS,
    atomic_write_csv,
    atomic_write_json,
    build_capture_batch_candidates,
    build_team_image_inventory,
    create_batch_contact_sheet,
    sha256_file,
    write_capture_batch_artifacts,
)
from fleetvision.review.team_pairing_review_app import (
    TeamPairingReviewRuntime,
    load_team_pairing_review_runtime,
)
from fleetvision.review.team_pairing_review_mapping import (
    TeamPairingAuditConfig,
    TeamPairingMappingValidationError,
    load_team_pairing_audit_config,
)


class TeamPairingOperationalError(RuntimeError):
    """Raised when the operational prepare workflow cannot complete safely."""


@dataclass(frozen=True)
class TeamPairingPreparedWorkspace:
    workspace_root: Path
    candidates_dir: Path
    contact_sheet_dir: Path
    review_database: Path
    candidate_manifest: Path
    image_count: int
    batch_count: int


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _validate_workspace_root(
    workspace_root: Path,
    config: TeamPairingAuditConfig,
) -> Path:
    workspace = workspace_root.resolve()
    output_root = config.output_root.resolve()
    if not _is_relative_to(workspace, output_root):
        raise TeamPairingOperationalError(
            "workspace 必須位於 approved Team Pairing output root"
        )
    if workspace == output_root:
        raise TeamPairingOperationalError(
            "workspace 不可直接等於 output root；必須使用獨立 run directory"
        )
    if workspace.exists():
        raise TeamPairingOperationalError(
            f"workspace 已存在；禁止覆蓋：{workspace}"
        )
    return workspace


def _manifest_payload(
    *,
    config: TeamPairingAuditConfig,
    inventory_path: Path,
    batch_path: Path,
    member_path: Path,
    image_count: int,
    batch_count: int,
    created_at_utc: str,
) -> dict[str, Any]:
    return {
        "schema_version": config.schema_version,
        "created_at_utc": created_at_utc,
        "config_path": str(config.config_path),
        "config_sha256": sha256_file(config.config_path),
        "source_root": str(config.source_root),
        "output_root": str(config.output_root),
        "inventory_sha256": sha256_file(inventory_path),
        "batch_candidates_sha256": sha256_file(batch_path),
        "batch_members_sha256": sha256_file(member_path),
        "expected_image_count": image_count,
        "expected_batch_count": batch_count,
        "expected_pair_count": 0,
        "formal_pair_generation_executed": False,
        "frozen_test_access": False,
        "training_executed": False,
        "model_inference_executed": False,
    }


def prepare_team_pairing_workspace(
    config_path: Path,
    project_root: Path,
    *,
    workspace_root: Path,
    created_at_utc: str | None = None,
) -> TeamPairingPreparedWorkspace:
    """Create one no-overwrite Team Pairing candidate/review workspace."""

    config = load_team_pairing_audit_config(config_path, project_root)
    workspace = _validate_workspace_root(workspace_root, config)
    candidates_dir = workspace / "candidates"
    contact_sheet_dir = candidates_dir / "contact_sheets"
    source_evidence_dir = workspace / "source"
    created_at = created_at_utc or datetime.now(timezone.utc).isoformat(
        timespec="microseconds"
    )

    try:
        candidates_dir.mkdir(parents=True)
        contact_sheet_dir.mkdir(parents=True)
        source_evidence_dir.mkdir(parents=True)

        inventory = build_team_image_inventory(config)
        inventory_path = atomic_write_csv(
            inventory.rows,
            candidates_dir / "team_image_inventory.csv",
            fieldnames=INVENTORY_COLUMNS,
            config=config,
        )
        atomic_write_json(
            inventory.source_snapshot_before,
            source_evidence_dir / "source_snapshot_before.json",
            config=config,
        )
        atomic_write_json(
            inventory.source_snapshot_after,
            source_evidence_dir / "source_snapshot_after.json",
            config=config,
        )
        atomic_write_json(
            inventory.source_snapshot_verification,
            source_evidence_dir / "source_snapshot_verification.json",
            config=config,
        )

        batches = build_capture_batch_candidates(inventory.rows, config)
        written = write_capture_batch_artifacts(batches, candidates_dir, config)

        for batch in batches.batches:
            create_batch_contact_sheet(
                batch,
                batches.members,
                inventory.rows,
                contact_sheet_dir / f"{batch['batch_id']}.jpg",
                config,
            )

        manifest_path = atomic_write_json(
            _manifest_payload(
                config=config,
                inventory_path=inventory_path,
                batch_path=written["batches"],
                member_path=written["members"],
                image_count=len(inventory.rows),
                batch_count=len(batches.batches),
                created_at_utc=created_at,
            ),
            candidates_dir / "candidate_manifest.json",
            config=config,
        )

        runtime: TeamPairingReviewRuntime = load_team_pairing_review_runtime(
            config.config_path,
            config.project_root,
            workspace_root=workspace,
        )
        if runtime.store.integrity_check() != "ok":
            raise TeamPairingOperationalError("SQLite integrity check failed")

        return TeamPairingPreparedWorkspace(
            workspace_root=workspace,
            candidates_dir=candidates_dir,
            contact_sheet_dir=contact_sheet_dir,
            review_database=runtime.store.database_path,
            candidate_manifest=manifest_path,
            image_count=len(inventory.rows),
            batch_count=len(batches.batches),
        )
    except Exception:
        shutil.rmtree(workspace, ignore_errors=True)
        raise


def preflight_team_pairing_operation(
    config_path: Path,
    project_root: Path,
    *,
    workspace_root: Path | None = None,
    require_existing_workspace: bool = False,
) -> TeamPairingAuditConfig:
    """Validate common repository/config/workspace operational preconditions."""

    config = load_team_pairing_audit_config(config_path, project_root)
    if not config.source_root.is_dir():
        raise TeamPairingMappingValidationError(
            f"Team Pairing source root 不存在：{config.source_root}"
        )
    if workspace_root is not None:
        workspace = workspace_root.resolve()
        if not _is_relative_to(workspace, config.output_root.resolve()):
            raise TeamPairingOperationalError(
                "workspace 必須位於 approved Team Pairing output root"
            )
        if require_existing_workspace and not workspace.is_dir():
            raise TeamPairingOperationalError(
                f"workspace 不存在：{workspace}"
            )
    return config
