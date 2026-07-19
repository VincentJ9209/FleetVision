from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import importlib
import sqlite3
from pathlib import Path

import pytest

from fleetvision.review.team_pairing_review_mapping import (
    AngleReviewSelection,
    BatchReviewSelection,
    PairReviewSelection,
    derive_canonical_angle_fields,
    derive_canonical_batch_fields,
    derive_canonical_pair_fields,
)


def state_module():
    return importlib.import_module("fleetvision.review.team_pairing_review_state")


def package(tmp_path: Path, *, expected_suffix: str = "A"):
    s = state_module()
    workspace = tmp_path / "workspace"
    identity = s.TeamPairingWorkspaceIdentity(
        schema_version="1",
        project_root=str((tmp_path / "FleetVision").resolve()),
        source_root=str((tmp_path / "FleetVision/dataset/01_raw/04_team").resolve()),
        candidate_manifest_sha256=f"MANIFEST-{expected_suffix}",
        inventory_sha256=f"INVENTORY-{expected_suffix}",
        batch_candidates_sha256=f"BATCHES-{expected_suffix}",
        batch_members_sha256=f"MEMBERS-{expected_suffix}",
        config_sha256=f"CONFIG-{expected_suffix}",
        reviewer="Vincent",
        timezone="Asia/Taipei",
        expected_image_count=3,
        expected_batch_count=2,
        expected_pair_count=1,
    )
    images = (
        s.SourceImageSeed("team_001", 1, "dataset/01_raw/04_team/a.jpg", True),
        s.SourceImageSeed("team_002", 2, "dataset/01_raw/04_team/b.jpg", True),
        s.SourceImageSeed("team_003", 3, "dataset/01_raw/04_team/c.jpg", False),
    )
    batches = (
        s.CandidateBatchSeed("batch_001", 1, "2026-07-19T01:00:00+00:00", "2026-07-19T01:05:00+00:00"),
        s.CandidateBatchSeed("batch_002", 2, "2026-07-19T03:00:00+00:00", "2026-07-19T03:05:00+00:00"),
    )
    members = (
        s.BatchMemberSeed("batch_001", "team_001", 1),
        s.BatchMemberSeed("batch_001", "team_003", 2),
        s.BatchMemberSeed("batch_002", "team_002", 1),
    )
    pairs = (
        s.PairCandidateSeed("pair_001", 1, "batch_001", "batch_002"),
    )
    return s.TeamPairingCandidatePackage(workspace, identity, images, batches, members, pairs)


def store_for(pkg, *, backup_every: int = 10, retention: int = 20):
    s = state_module()
    return s.TeamPairingReviewStateStore(
        pkg.workspace_root,
        identity=pkg.identity,
        backup_every_successful_saves=backup_every,
        backup_retention=retention,
    )


def reviewed_at() -> datetime:
    return datetime(2026, 7, 19, 12, 0, tzinfo=timezone.utc)


def confirmed_batch(stage: str = "before"):
    selection = BatchReviewSelection(
        manual_batch_status="confirmed",
        manual_vehicle_id="TEAMCAR-001",
        manual_stage=stage,
    )
    canonical = derive_canonical_batch_fields(
        selection,
        reviewer="Vincent",
        reviewed_at=reviewed_at(),
    )
    return selection, canonical


def reviewed_angle(angle: str = "front_left"):
    selection = AngleReviewSelection(review_status="reviewed", manual_angle=angle)
    canonical = derive_canonical_angle_fields(
        selection,
        reviewer="Vincent",
        reviewed_at=reviewed_at(),
    )
    return selection, canonical


def confirmed_pair():
    selection = PairReviewSelection(
        manual_pair_status="confirmed",
        manual_existing_damage_visible="no",
        manual_new_damage_status="none",
        manual_demo_role="primary",
    )
    canonical = derive_canonical_pair_fields(
        selection,
        reviewer="Vincent",
        reviewed_at=reviewed_at(),
    )
    return selection, canonical


def test_initialize_creates_required_schema_and_pending_rows(tmp_path: Path) -> None:
    s = state_module()
    pkg = package(tmp_path)
    store = store_for(pkg)
    store.initialize(pkg)

    assert store.integrity_check() == "ok"
    assert store.table_names() == s.REQUIRED_TABLES
    assert store.progress() == s.TeamPairingProgressCounts(
        images_total=3,
        images_reviewed=0,
        batches_total=2,
        batches_terminal=0,
        pairs_total=1,
        pairs_terminal=0,
    )


def test_reopen_preserves_identity_progress_and_last_viewed_item(tmp_path: Path) -> None:
    pkg = package(tmp_path)
    store = store_for(pkg)
    store.initialize(pkg)
    store.set_last_viewed("batch", "batch_002")

    reopened = store_for(pkg)
    reopened.initialize(pkg)
    assert reopened.last_viewed() == ("batch", "batch_002")
    assert reopened.progress().batches_total == 2


def test_identity_mismatch_fails_closed(tmp_path: Path) -> None:
    s = state_module()
    pkg = package(tmp_path)
    store_for(pkg).initialize(pkg)
    mismatched = replace(pkg, identity=replace(pkg.identity, config_sha256="OTHER"))

    with pytest.raises(s.TeamPairingReviewStateError, match="identity"):
        store_for(mismatched).initialize(mismatched)


def test_candidate_artifact_mismatch_fails_closed(tmp_path: Path) -> None:
    s = state_module()
    pkg = package(tmp_path)
    store_for(pkg).initialize(pkg)
    changed_batches = (
        replace(pkg.batches[0], end_time_utc="2026-07-19T01:06:00+00:00"),
        pkg.batches[1],
    )
    mismatched = replace(pkg, batches=changed_batches)

    with pytest.raises(s.TeamPairingReviewStateError, match="candidate"):
        store_for(pkg).initialize(mismatched)


def test_batch_save_revision_is_monotonic_and_audit_is_contiguous(tmp_path: Path) -> None:
    pkg = package(tmp_path)
    store = store_for(pkg)
    store.initialize(pkg)
    selection, canonical = confirmed_batch()

    first = store.save_batch_review("batch_001", selection, canonical)
    second = store.save_batch_review("batch_001", selection, canonical)

    assert first.revision == 1
    assert second.revision == 2
    assert store.successful_save_count() == 2
    assert store.verify_event_log_continuity() == 2
    assert store.last_viewed() == ("batch", "batch_001")


def test_image_and_pair_saves_update_filters_and_progress(tmp_path: Path) -> None:
    pkg = package(tmp_path)
    store = store_for(pkg)
    store.initialize(pkg)
    batch_selection, batch_canonical = confirmed_batch()
    angle_selection, angle_canonical = reviewed_angle()
    pair_selection, pair_canonical = confirmed_pair()

    store.save_batch_review("batch_001", batch_selection, batch_canonical)
    store.save_image_review("team_001", angle_selection, angle_canonical)
    store.save_pair_review("pair_001", pair_selection, pair_canonical)

    assert store.batch_ids("confirmed") == ("batch_001",)
    assert store.batch_ids("confirmed", vehicle_id="TEAMCAR-001", stage="before") == ("batch_001",)
    assert store.image_ids("reviewed") == ("team_001",)
    assert store.pair_ids("confirmed") == ("pair_001",)
    progress = store.progress()
    assert progress.images_reviewed == 1
    assert progress.batches_terminal == 1
    assert progress.pairs_terminal == 1


def test_simulated_save_failure_rolls_back_row_event_and_counter(tmp_path: Path) -> None:
    s = state_module()
    pkg = package(tmp_path)
    store = store_for(pkg)
    store.initialize(pkg)
    selection, canonical = confirmed_batch()

    with pytest.raises(s.TeamPairingReviewStateError, match="simulated"):
        store.save_batch_review(
            "batch_001",
            selection,
            canonical,
            simulate_failure_after_audit=True,
        )

    assert store.get_batch_review("batch_001").revision == 0
    assert store.successful_save_count() == 0
    assert store.verify_event_log_continuity() == 0


def test_event_log_gap_and_database_log_mismatch_fail_closed(tmp_path: Path) -> None:
    s = state_module()
    pkg = package(tmp_path)
    store = store_for(pkg)
    store.initialize(pkg)
    selection, canonical = confirmed_batch()
    store.save_batch_review("batch_001", selection, canonical)

    store.event_log_path.write_text('{"event_id":2}\n', encoding="utf-8")
    with pytest.raises(s.TeamPairingReviewStateError, match="不連續"):
        store.verify_event_log_continuity()


def test_automatic_backup_occurs_on_tenth_successful_save(tmp_path: Path) -> None:
    pkg = package(tmp_path)
    store = store_for(pkg, backup_every=10)
    store.initialize(pkg)
    selection, canonical = confirmed_batch()

    for _ in range(9):
        store.save_batch_review("batch_001", selection, canonical)
    assert list(store.backup_dir.glob("*.sqlite")) == []

    store.save_batch_review("batch_001", selection, canonical)
    backups = list(store.backup_dir.glob("*.sqlite"))
    assert len(backups) == 1
    assert store.backup_integrity(backups[0]) == "ok"


def test_backup_retention_keeps_latest_twenty(tmp_path: Path) -> None:
    pkg = package(tmp_path)
    store = store_for(pkg, retention=20)
    store.initialize(pkg)

    created = [store.create_backup(timestamp=f"20260719T1200{i:02d}000000Z") for i in range(22)]
    remaining = sorted(store.backup_dir.glob("*.sqlite"))
    assert len(remaining) == 20
    assert created[-1] in remaining
    assert created[-2] in remaining


def test_corrupt_preexisting_database_is_not_overwritten(tmp_path: Path) -> None:
    s = state_module()
    pkg = package(tmp_path)
    store = store_for(pkg)
    store.review_dir.mkdir(parents=True, exist_ok=True)
    original = b"not-a-sqlite-database"
    store.database_path.write_bytes(original)

    with pytest.raises(s.TeamPairingReviewStateError, match="corrupt|SQLite"):
        store.initialize(pkg)
    assert store.database_path.read_bytes() == original


def test_reviewer_mismatch_and_unknown_ids_are_blocked(tmp_path: Path) -> None:
    s = state_module()
    pkg = package(tmp_path)
    store = store_for(pkg)
    store.initialize(pkg)
    selection, canonical = confirmed_batch()

    with pytest.raises(s.TeamPairingReviewStateError, match="reviewer"):
        store.save_batch_review("batch_001", selection, replace(canonical, review_reviewer="Other"))
    with pytest.raises(s.TeamPairingReviewStateError, match="未知"):
        store.save_batch_review("batch_missing", selection, canonical)


def test_partial_preexisting_sqlite_schema_fails_closed(tmp_path: Path) -> None:
    s = state_module()
    pkg = package(tmp_path)
    store = store_for(pkg)
    store.review_dir.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(store.database_path)
    try:
        connection.execute("CREATE TABLE unrelated(id INTEGER PRIMARY KEY)")
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(s.TeamPairingReviewStateError, match="partial|schema"):
        store.initialize(pkg)


def test_backup_integrity_explicitly_closes_connection(monkeypatch, tmp_path: Path) -> None:
    s = state_module()

    class Result:
        @staticmethod
        def fetchone():
            return ("ok",)

    class FakeConnection:
        def __init__(self) -> None:
            self.closed = False

        @staticmethod
        def execute(statement: str):
            assert statement == "PRAGMA integrity_check"
            return Result()

        def close(self) -> None:
            self.closed = True

    fake = FakeConnection()
    monkeypatch.setattr(s.sqlite3, "connect", lambda path: fake)

    assert s.TeamPairingReviewStateStore.backup_integrity(tmp_path / "backup.sqlite") == "ok"
    assert fake.closed is True
