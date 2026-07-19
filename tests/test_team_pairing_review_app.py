from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import importlib
import os
from pathlib import Path
import subprocess
import sys

import pytest

from fleetvision.review.team_pairing_review_mapping import (
    AngleReviewSelection,
    BatchReviewSelection,
    TeamPairingAuditConfig,
    TeamPairingMappingValidationError,
)
from fleetvision.review.team_pairing_review_state import (
    BatchMemberSeed,
    CandidateBatchSeed,
    SourceImageSeed,
    TeamPairingCandidatePackage,
    TeamPairingReviewStateStore,
    TeamPairingWorkspaceIdentity,
)


def app_module():
    return importlib.import_module("fleetvision.review.team_pairing_review_app")


def build_runtime(tmp_path: Path):
    app = app_module()
    project_root = (tmp_path / "FleetVision").resolve()
    source_root = project_root / "dataset" / "01_raw" / "04_team"
    output_root = project_root / "outputs" / "phase05s" / "team_pairing_audit"
    workspace_root = output_root / "workspaces" / "team_pairing_audit_demo"
    source_root.mkdir(parents=True)
    output_root.mkdir(parents=True)

    for name in ("a.jpg", "b.jpg", "c.jpg", "d.jpg"):
        (source_root / name).write_bytes(f"synthetic-{name}".encode("utf-8"))

    config_path = project_root / "configs" / "data" / "team_pairing_audit_config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("schema_version: '1'\n", encoding="utf-8")
    config = TeamPairingAuditConfig(
        schema_version="1",
        project_root=project_root,
        config_path=config_path,
        source_relative_path=app.PurePosixPath("dataset/01_raw/04_team"),
        output_relative_path=app.PurePosixPath("outputs/phase05s/team_pairing_audit"),
        source_root=source_root,
        output_root=output_root,
        supported_extensions=(".jpg",),
        batch_gap_minutes=10,
        pair_max_elapsed_hours=12,
        phash_distance_threshold=6,
        contact_sheet_columns=4,
        contact_sheet_thumbnail_size=320,
        timezone="Asia/Taipei",
        reviewer="Vincent",
        backup_every_successful_saves=10,
        backup_retention=20,
        max_unreadable_rate=0.25,
        frozen_test_access=False,
    )
    identity = TeamPairingWorkspaceIdentity(
        schema_version="1",
        project_root=str(project_root),
        source_root=str(source_root),
        candidate_manifest_sha256="MANIFEST",
        inventory_sha256="INVENTORY",
        batch_candidates_sha256="BATCHES",
        batch_members_sha256="MEMBERS",
        config_sha256="CONFIG",
        reviewer="Vincent",
        timezone="Asia/Taipei",
        expected_image_count=4,
        expected_batch_count=3,
        expected_pair_count=0,
    )
    images = (
        SourceImageSeed("team_001", 1, "a.jpg", True),
        SourceImageSeed("team_002", 2, "b.jpg", False),
        SourceImageSeed("team_003", 3, "c.jpg", True),
        SourceImageSeed("team_004", 4, "d.jpg", True),
    )
    batches = (
        CandidateBatchSeed("batch_001", 1, "2026-07-19T01:00:00+00:00", "2026-07-19T01:05:00+00:00"),
        CandidateBatchSeed("batch_002", 2, "2026-07-19T02:00:00+00:00", "2026-07-19T02:05:00+00:00"),
        CandidateBatchSeed("batch_003", 3, "2026-07-19T03:00:00+00:00", "2026-07-19T03:05:00+00:00"),
    )
    members = (
        BatchMemberSeed("batch_001", "team_001", 1),
        BatchMemberSeed("batch_001", "team_002", 2),
        BatchMemberSeed("batch_002", "team_003", 1),
        BatchMemberSeed("batch_003", "team_004", 1),
    )
    package = TeamPairingCandidatePackage(
        workspace_root=workspace_root,
        identity=identity,
        images=images,
        batches=batches,
        members=members,
        pairs=(),
    )
    store = TeamPairingReviewStateStore(
        workspace_root,
        identity=identity,
        backup_every_successful_saves=10,
        backup_retention=20,
    )
    store.initialize(package)
    member_roles = {
        ("batch_001", "team_001"): "candidate_representative",
        ("batch_001", "team_002"): "exact_duplicate_trace",
        ("batch_002", "team_003"): "candidate_representative",
        ("batch_003", "team_004"): "candidate_representative",
    }
    return app.create_runtime(config, package, store=store, member_roles=member_roles)


def reviewed_at() -> datetime:
    return datetime(2026, 7, 19, 12, 0, tzinfo=timezone.utc)


def test_next_item_id_clamps_and_unknown_falls_back() -> None:
    app = app_module()
    ids = ("batch_001", "batch_002")
    assert app.next_item_id(ids, "batch_001", direction=-1) == "batch_001"
    assert app.next_item_id(ids, "batch_002", direction=1) == "batch_002"
    assert app.next_item_id(ids, "missing", direction=1) == "batch_001"


def test_pending_selection_queue_and_apply() -> None:
    app = app_module()
    state: dict[str, object] = {}
    app.queue_item_selection(state, "batch", "batch_002")
    selected = app.apply_pending_item_selection(
        state,
        selector_key="batch_selector",
        item_ids=("batch_001", "batch_002"),
        fallback_item_id="batch_001",
        mode="batch",
    )
    assert selected == "batch_002"
    assert state["batch_selector"] == "batch_002"


def test_widget_key_is_entity_isolated() -> None:
    app = app_module()
    assert app.item_widget_key("status", "batch", "batch_001") != app.item_widget_key(
        "status", "batch", "batch_002"
    )
    assert app.item_widget_key("status", "batch", "batch_001") != app.item_widget_key(
        "status", "image", "batch_001"
    )


def test_runtime_session_identity_changes_for_workspace_and_manifest(tmp_path: Path) -> None:
    app = app_module()
    first = app.runtime_session_identity(tmp_path / "c", tmp_path / "r", tmp_path / "w1", "AAA")
    second = app.runtime_session_identity(tmp_path / "c", tmp_path / "r", tmp_path / "w2", "AAA")
    third = app.runtime_session_identity(tmp_path / "c", tmp_path / "r", tmp_path / "w1", "BBB")
    assert first != second
    assert first != third


def test_batch_pair_eligibility_only_confirmed_before_after_vehicle() -> None:
    app = app_module()
    assert app.batch_is_pair_eligible(
        BatchReviewSelection("confirmed", "TEAMCAR-001", "before", "")
    )
    assert app.batch_is_pair_eligible(
        BatchReviewSelection("confirmed", "teamcar-001", "after", "")
    )
    for status in ("pending", "split_required", "merge_required", "exclude", "uncertain"):
        assert not app.batch_is_pair_eligible(
            BatchReviewSelection(status, "", "unknown", "needs review" if status != "pending" else "")
        )


def test_required_angle_images_use_readable_candidate_representatives(tmp_path: Path) -> None:
    app = app_module()
    runtime = build_runtime(tmp_path)
    app.save_batch_review_selection(
        runtime,
        "batch_001",
        BatchReviewSelection("confirmed", "TEAMCAR-001", "before", ""),
        reviewed_at=reviewed_at(),
    )
    assert app.required_angle_image_ids(runtime, "batch_001") == ("team_001",)


def test_batch_progress_summary_reports_terminal_and_unresolved(tmp_path: Path) -> None:
    app = app_module()
    runtime = build_runtime(tmp_path)
    app.save_batch_review_selection(
        runtime,
        "batch_001",
        BatchReviewSelection("confirmed", "TEAMCAR-001", "before", ""),
        reviewed_at=reviewed_at(),
    )
    app.save_batch_review_selection(
        runtime,
        "batch_002",
        BatchReviewSelection("split_required", "", "unknown", "需拆分"),
        reviewed_at=reviewed_at(),
    )
    summary = app.batch_progress_summary(runtime)
    assert summary.total == 3
    assert summary.terminal == 2
    assert summary.pending == 1
    assert summary.confirmed == 1
    assert summary.unresolved == 1


def test_save_batch_selection_persists_and_normalizes_vehicle(tmp_path: Path) -> None:
    app = app_module()
    runtime = build_runtime(tmp_path)
    result = app.save_batch_review_selection(
        runtime,
        "batch_001",
        BatchReviewSelection("confirmed", " teamcar-001 ", "before", ""),
        reviewed_at=reviewed_at(),
    )
    assert result.stored_review.revision == 1
    stored = runtime.store.get_batch_review("batch_001")
    assert stored.canonical_fields["manual_vehicle_id"] == "TEAMCAR-001"
    assert result.progress.batches_terminal == 1


def test_invalid_confirmed_batch_is_blocked(tmp_path: Path) -> None:
    app = app_module()
    runtime = build_runtime(tmp_path)
    with pytest.raises(TeamPairingMappingValidationError, match="vehicle"):
        app.save_batch_review_selection(
            runtime,
            "batch_001",
            BatchReviewSelection("confirmed", "", "before", ""),
            reviewed_at=reviewed_at(),
        )


def test_split_and_merge_batches_never_become_angle_or_pair_eligible(tmp_path: Path) -> None:
    app = app_module()
    runtime = build_runtime(tmp_path)
    for batch_id, status in (("batch_001", "split_required"), ("batch_002", "merge_required")):
        app.save_batch_review_selection(
            runtime,
            batch_id,
            BatchReviewSelection(status, "", "unknown", "人工處理"),
            reviewed_at=reviewed_at(),
        )
        assert not app.batch_id_is_pair_eligible(runtime, batch_id)
        assert app.required_angle_image_ids(runtime, batch_id) == ()


def test_save_angle_requires_confirmed_batch_membership_and_readability(tmp_path: Path) -> None:
    app = app_module()
    runtime = build_runtime(tmp_path)
    with pytest.raises(TeamPairingMappingValidationError, match="confirmed"):
        app.save_angle_review_selection(
            runtime,
            "batch_001",
            "team_001",
            AngleReviewSelection("reviewed", "front_left", ""),
            reviewed_at=reviewed_at(),
        )
    app.save_batch_review_selection(
        runtime,
        "batch_001",
        BatchReviewSelection("confirmed", "TEAMCAR-001", "before", ""),
        reviewed_at=reviewed_at(),
    )
    with pytest.raises(TeamPairingMappingValidationError, match="eligible|代表|可讀"):
        app.save_angle_review_selection(
            runtime,
            "batch_001",
            "team_002",
            AngleReviewSelection("reviewed", "front_left", ""),
            reviewed_at=reviewed_at(),
        )


def test_save_angle_review_persists_and_progresses(tmp_path: Path) -> None:
    app = app_module()
    runtime = build_runtime(tmp_path)
    app.save_batch_review_selection(
        runtime,
        "batch_003",
        BatchReviewSelection("confirmed", "TEAMCAR-001", "after", ""),
        reviewed_at=reviewed_at(),
    )
    result = app.save_angle_review_selection(
        runtime,
        "batch_003",
        "team_004",
        AngleReviewSelection("reviewed", "rear_right", ""),
        reviewed_at=reviewed_at(),
    )
    assert result.stored_review.revision == 1
    assert result.progress.images_reviewed == 1


def test_preview_path_must_stay_under_approved_source_and_exist(tmp_path: Path) -> None:
    app = app_module()
    runtime = build_runtime(tmp_path)
    assert app.resolve_preview_path(runtime, "team_001").name == "a.jpg"
    escaped = replace(runtime.package.images[0], relative_path="../secret.jpg")
    bad_package = replace(runtime.package, images=(escaped,) + runtime.package.images[1:])
    bad_runtime = app.create_runtime(
        runtime.config,
        bad_package,
        store=runtime.store,
        member_roles=runtime.member_roles,
        initialize_store=False,
    )
    with pytest.raises(TeamPairingMappingValidationError, match="source root"):
        app.resolve_preview_path(bad_runtime, "team_001")


def test_streamlit_command_is_loopback_only_and_disables_usage_stats(tmp_path: Path) -> None:
    app = app_module()
    command = app.build_streamlit_command(
        python_executable=tmp_path / "python.exe",
        app_script=tmp_path / "app.py",
        config_path=tmp_path / "config.yaml",
        project_root=tmp_path,
        workspace_root=tmp_path / "workspace",
        address="127.0.0.1",
        port=8501,
    )
    joined = " ".join(command)
    assert "--server.address=127.0.0.1" in joined
    assert "--browser.gatherUsageStats=false" in joined
    with pytest.raises(ValueError, match="127.0.0.1"):
        app.build_streamlit_command(
            python_executable=tmp_path / "python.exe",
            app_script=tmp_path / "app.py",
            config_path=tmp_path / "config.yaml",
            project_root=tmp_path,
            workspace_root=tmp_path / "workspace",
            address="0.0.0.0",
            port=8501,
        )


def test_ui_labels_are_traditional_chinese_and_xlsx_is_export_only() -> None:
    app = app_module()
    assert app.SCREEN_LABELS == {
        "batch": "批次審核",
        "angle": "角度標記",
        "pair": "前後配對",
    }
    assert app.LIVE_STATE_POLICY == "SQLITE_ONLY"
    assert app.XLSX_POLICY == "COMPLETED_EXPORT_ONLY"


def test_launcher_wrapper_is_local_only_and_has_no_excel_input() -> None:
    root = Path(__file__).resolve().parents[1]
    wrapper = (root / "scripts" / "phase05s_launch_team_pairing_review_app.ps1").read_text(
        encoding="utf-8-sig"
    )
    assert "--server.address=127.0.0.1" in wrapper
    assert "0.0.0.0" not in wrapper
    assert "xlsx" not in wrapper.lower()


def test_direct_cli_help_bootstraps_local_src_without_pythonpath() -> None:
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "phase05s_run_team_pairing_review_app.py"
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "--config" in result.stdout
    assert "--project-root" in result.stdout
    assert "--workspace-root" in result.stdout


class TestPairCandidateAndReviewUi:
    @staticmethod
    def prepare_pair_runtime(tmp_path: Path):
        app = app_module()
        runtime = build_runtime(tmp_path)
        app.save_batch_review_selection(
            runtime,
            "batch_001",
            BatchReviewSelection("confirmed", "TEAMCAR-001", "before", ""),
            reviewed_at=reviewed_at(),
        )
        app.save_batch_review_selection(
            runtime,
            "batch_002",
            BatchReviewSelection("confirmed", "TEAMCAR-001", "after", ""),
            reviewed_at=reviewed_at(),
        )
        app.save_angle_review_selection(
            runtime,
            "batch_001",
            "team_001",
            AngleReviewSelection("reviewed", "front_left", ""),
            reviewed_at=reviewed_at(),
        )
        app.save_angle_review_selection(
            runtime,
            "batch_002",
            "team_003",
            AngleReviewSelection("reviewed", "front_left", ""),
            reviewed_at=reviewed_at(),
        )
        return runtime

    def test_refresh_generates_pair_from_confirmed_human_reviews(self, tmp_path: Path) -> None:
        app = app_module()
        runtime = self.prepare_pair_runtime(tmp_path)
        first = app.refresh_pair_candidates(runtime)
        second = app.refresh_pair_candidates(runtime)

        assert len(first) == 1
        assert first == second
        assert first[0].before_batch_id == "batch_001"
        assert first[0].after_batch_id == "batch_002"
        assert first[0].overlap_angles == ("front_left",)
        assert runtime.store.pair_ids("pending") == (first[0].pair_candidate_id,)

    def test_nonconfirmed_or_missing_angle_batches_are_excluded(self, tmp_path: Path) -> None:
        app = app_module()
        runtime = build_runtime(tmp_path)
        app.save_batch_review_selection(
            runtime,
            "batch_001",
            BatchReviewSelection("confirmed", "TEAMCAR-001", "before", ""),
            reviewed_at=reviewed_at(),
        )
        app.save_batch_review_selection(
            runtime,
            "batch_002",
            BatchReviewSelection("confirmed", "TEAMCAR-001", "after", ""),
            reviewed_at=reviewed_at(),
        )
        app.save_angle_review_selection(
            runtime,
            "batch_001",
            "team_001",
            AngleReviewSelection("reviewed", "front_left", ""),
            reviewed_at=reviewed_at(),
        )
        assert app.refresh_pair_candidates(runtime) == ()

    def test_pair_view_model_contains_elapsed_overlap_and_batch_evidence(self, tmp_path: Path) -> None:
        app = app_module()
        runtime = self.prepare_pair_runtime(tmp_path)
        app.refresh_pair_candidates(runtime)
        view = app.pair_candidate_view_models(runtime)[0]

        assert view.manual_vehicle_id == "TEAMCAR-001"
        assert view.elapsed_seconds == 3300
        assert view.overlap_angles == ("front_left",)
        assert view.four_angle_overlap_count == 1
        assert view.before_batch_id == "batch_001"
        assert view.after_batch_id == "batch_002"

    def test_pair_contact_sheets_are_resolved_side_by_side_and_missing_is_blocking(self, tmp_path: Path) -> None:
        app = app_module()
        runtime = self.prepare_pair_runtime(tmp_path)
        pair = app.refresh_pair_candidates(runtime)[0]
        contact_dir = runtime.package.workspace_root / "contact_sheets"
        contact_dir.mkdir(parents=True)
        before = contact_dir / "batch_001.jpg"
        after = contact_dir / "batch_002.jpg"
        before.write_bytes(b"before")
        after.write_bytes(b"after")

        assert app.pair_contact_sheet_paths(runtime, pair.pair_candidate_id) == (
            before.resolve(),
            after.resolve(),
        )
        after.unlink()
        with pytest.raises(TeamPairingMappingValidationError, match="contact sheet|evidence"):
            app.pair_contact_sheet_paths(runtime, pair.pair_candidate_id)

    def test_pair_save_derives_classification_updates_progress_and_resume(self, tmp_path: Path) -> None:
        app = app_module()
        mapping_module = importlib.import_module(
            "fleetvision.review.team_pairing_review_mapping"
        )
        runtime = self.prepare_pair_runtime(tmp_path)
        pair = app.refresh_pair_candidates(runtime)[0]
        result = app.save_pair_review_selection(
            runtime,
            pair.pair_candidate_id,
            mapping_module.PairReviewSelection(
                manual_pair_status="confirmed",
                manual_existing_damage_visible="no",
                manual_new_damage_status="none",
                manual_demo_role="primary",
            ),
            reviewed_at=reviewed_at(),
        )

        assert result.stored_review.canonical_fields[
            "derived_case_classification"
        ] == "NO_NEW_DAMAGE"
        assert result.progress.pairs_terminal == 1
        assert runtime.store.last_viewed() == ("pair", pair.pair_candidate_id)
        summary = app.pair_progress_summary(runtime)
        assert summary.total == 1
        assert summary.confirmed == 1
        assert summary.primary == 1

    def test_pair_screen_contract_is_traditional_chinese_and_side_by_side(self) -> None:
        app = app_module()
        source = Path(app.__file__).read_text(encoding="utf-8")
        assert app.SCREEN_LABELS["pair"] == "前後配對"
        assert "def _render_pair_screen" in source
        assert "借車前批次" in source
        assert "還車後批次" in source
        assert "st.columns(2)" in source
