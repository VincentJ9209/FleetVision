from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

import fleetvision.review.annotation_correction_promotion as promotion_module
from annotation_correction_promotion_fixtures import build_phase04_5n_fixture
from fleetvision.review.annotation_correction_promotion import (
    PromotionAuthorizationError,
    PromotionExecutionError,
    PromotionPreflightError,
    PromotionRequest,
    execute_atomic_promotion,
    prepare_promotion_preflight,
    verify_n1_workspace,
    verify_repository_promotion_state,
)
from fleetvision.review.annotation_correction_promotion_contract import (
    Phase04_5NConfig,
    load_phase04_5n_config,
    sha256_file,
)
from fleetvision.review.annotation_correction_staging import (
    prepare_staged_correction_workspace,
)


@dataclass(frozen=True)
class PromotionFixture:
    config: Phase04_5NConfig
    project_root: Path
    n1_workspace_root: Path
    canonical_path: Path
    source_sha256: str
    staged_sha256: str
    repository_head: str
    remote_root: Path


def _run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} failed ({result.returncode})\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
    return result.stdout.strip()


def _write_manifest(path: Path, root: Path, members: list[str]) -> None:
    rows = []
    for relative in sorted(members):
        member = root / relative
        rows.append(
            {
                "relative_path": relative,
                "size_bytes": member.stat().st_size,
                "sha256": sha256_file(member),
            }
        )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("relative_path", "size_bytes", "sha256"),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def _refresh_n1_manifests(workspace_root: Path) -> None:
    all_files = sorted(
        path.relative_to(workspace_root).as_posix()
        for path in workspace_root.rglob("*")
        if path.is_file()
    )
    workspace_manifest = "evidence/workspace_manifest.csv"
    sha_manifest = "evidence/SHA256SUMS.csv"
    _write_manifest(
        workspace_root / workspace_manifest,
        workspace_root,
        [
            relative
            for relative in all_files
            if relative not in {workspace_manifest, sha_manifest}
        ],
    )
    all_files = sorted(
        path.relative_to(workspace_root).as_posix()
        for path in workspace_root.rglob("*")
        if path.is_file()
    )
    _write_manifest(
        workspace_root / sha_manifest,
        workspace_root,
        [relative for relative in all_files if relative != sha_manifest],
    )


def _rewrite_json(path: Path, **updates: Any) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(updates)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _initialize_git_repository(project_root: Path, remote_root: Path) -> str:
    test_sentinel = (
        project_root
        / "dataset/02_interim/99_external/roboflow/rf_car_damage_seg_v1"
        / "canonical_coco/test/_annotations.coco.json"
    )
    if test_sentinel.exists():
        test_sentinel.unlink()
        parent = test_sentinel.parent
        while parent != project_root and parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent

    _run_git(project_root, "init")
    _run_git(project_root, "config", "user.email", "fleetvision-tests@example.invalid")
    _run_git(project_root, "config", "user.name", "FleetVision Tests")
    _run_git(project_root, "checkout", "-b", "main")
    _run_git(project_root, "add", "configs", "dataset")
    _run_git(project_root, "commit", "-m", "fixture baseline")

    subprocess.run(
        ["git", "init", "--bare", str(remote_root)],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    _run_git(project_root, "remote", "add", "origin", str(remote_root))
    _run_git(project_root, "push", "-u", "origin", "main")
    return _run_git(project_root, "rev-parse", "HEAD")


@pytest.fixture
def promotion_fixture(tmp_path: Path) -> PromotionFixture:
    fixture = build_phase04_5n_fixture(tmp_path)
    config = load_phase04_5n_config(fixture.config_path, fixture.project_root)
    prepared = prepare_staged_correction_workspace(
        config,
        fixture.completed_review_root,
        timestamp="20260715_040000000",
    )
    remote_root = tmp_path / "origin.git"
    repository_head = _initialize_git_repository(fixture.project_root, remote_root)
    return PromotionFixture(
        config=config,
        project_root=fixture.project_root,
        n1_workspace_root=prepared.workspace_root,
        canonical_path=fixture.canonical_valid_coco,
        source_sha256=prepared.source_coco_sha256,
        staged_sha256=prepared.staged_coco_sha256,
        repository_head=repository_head,
        remote_root=remote_root,
    )


def _make_request(
    fixture: PromotionFixture,
    *,
    authorization_phrase: str = "",
    execute: bool = False,
    expected_repository_head: str | None = None,
    expected_canonical_sha256: str | None = None,
    expected_staged_sha256: str | None = None,
    timestamp: str = "20260715_041000000",
) -> PromotionRequest:
    return PromotionRequest(
        project_root=fixture.project_root,
        n1_workspace_root=fixture.n1_workspace_root,
        expected_repository_head=(
            fixture.repository_head
            if expected_repository_head is None
            else expected_repository_head
        ),
        expected_canonical_sha256=(
            fixture.source_sha256
            if expected_canonical_sha256 is None
            else expected_canonical_sha256
        ),
        expected_staged_sha256=(
            fixture.staged_sha256
            if expected_staged_sha256 is None
            else expected_staged_sha256
        ),
        authorization_phrase=authorization_phrase,
        execute=execute,
        timestamp=timestamp,
    )


def test_n2_requires_exact_authorization_phrase(
    promotion_fixture: PromotionFixture,
) -> None:
    request = _make_request(promotion_fixture, authorization_phrase="", execute=True)
    with pytest.raises(PromotionAuthorizationError, match="authorization"):
        prepare_promotion_preflight(promotion_fixture.config, request)


def test_n2_accepts_exact_authorization_without_mutating_canonical(
    promotion_fixture: PromotionFixture,
) -> None:
    before = promotion_fixture.canonical_path.read_bytes()
    request = _make_request(
        promotion_fixture,
        authorization_phrase=promotion_fixture.config.n2_authorization_phrase,
        execute=True,
    )
    preflight = prepare_promotion_preflight(promotion_fixture.config, request)
    assert preflight.staged_coco_sha256 == promotion_fixture.staged_sha256
    assert preflight.current_canonical_sha256 == promotion_fixture.source_sha256
    assert promotion_fixture.canonical_path.read_bytes() == before


def test_n2_dry_run_allows_empty_expected_values_and_is_read_only(
    promotion_fixture: PromotionFixture,
) -> None:
    before = promotion_fixture.canonical_path.read_bytes()
    request = _make_request(
        promotion_fixture,
        expected_repository_head="",
        expected_canonical_sha256="",
        expected_staged_sha256="",
    )
    preflight = prepare_promotion_preflight(promotion_fixture.config, request)
    assert preflight.repository_state.head == promotion_fixture.repository_head
    assert promotion_fixture.canonical_path.read_bytes() == before


def test_n2_rejects_tampered_n1_manifest(
    promotion_fixture: PromotionFixture,
) -> None:
    path = promotion_fixture.n1_workspace_root / "diff/annotation_correction_diff.json"
    path.write_text(path.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(PromotionPreflightError, match="SHA256"):
        prepare_promotion_preflight(
            promotion_fixture.config,
            _make_request(promotion_fixture),
        )


def test_n2_rejects_current_canonical_hash_drift(
    promotion_fixture: PromotionFixture,
) -> None:
    promotion_fixture.canonical_path.write_bytes(
        promotion_fixture.canonical_path.read_bytes() + b"\n"
    )
    with pytest.raises(PromotionPreflightError, match="canonical source SHA256"):
        prepare_promotion_preflight(
            promotion_fixture.config,
            _make_request(promotion_fixture),
        )


def test_n2_rejects_dirty_repository_outside_allowlist(
    promotion_fixture: PromotionFixture,
) -> None:
    (promotion_fixture.project_root / "unexpected.txt").write_text(
        "dirty", encoding="utf-8"
    )
    with pytest.raises(PromotionPreflightError, match="worktree"):
        verify_repository_promotion_state(
            promotion_fixture.project_root,
            expected_head=promotion_fixture.repository_head,
            allowed_status_prefixes=("outputs/metadata/external_assets/",),
        )


def test_n2_repository_guard_accepts_allowed_external_assets(
    promotion_fixture: PromotionFixture,
) -> None:
    allowed = (
        promotion_fixture.project_root
        / "outputs/metadata/external_assets/protected.bin"
    )
    allowed.parent.mkdir(parents=True)
    allowed.write_bytes(b"protected")
    state = verify_repository_promotion_state(
        promotion_fixture.project_root,
        expected_head=promotion_fixture.repository_head,
        allowed_status_prefixes=("outputs/metadata/external_assets/",),
    )
    assert state.allowed_status_paths == (
        "outputs/metadata/external_assets/protected.bin",
    )


def test_n2_rejects_branch_not_main(promotion_fixture: PromotionFixture) -> None:
    _run_git(promotion_fixture.project_root, "checkout", "-b", "feature/not-main")
    with pytest.raises(PromotionPreflightError, match="branch"):
        verify_repository_promotion_state(
            promotion_fixture.project_root,
            expected_head=promotion_fixture.repository_head,
            allowed_status_prefixes=("outputs/metadata/external_assets/",),
        )


def test_n2_rejects_local_origin_disagreement(
    promotion_fixture: PromotionFixture,
) -> None:
    config_path = promotion_fixture.project_root / "configs/data/phase04_5n_test_config.yaml"
    config_path.write_text(config_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    _run_git(promotion_fixture.project_root, "add", str(config_path))
    _run_git(promotion_fixture.project_root, "commit", "-m", "local only")
    local_head = _run_git(promotion_fixture.project_root, "rev-parse", "HEAD")
    with pytest.raises(PromotionPreflightError, match="origin/main"):
        verify_repository_promotion_state(
            promotion_fixture.project_root,
            expected_head=local_head,
            allowed_status_prefixes=("outputs/metadata/external_assets/",),
        )


def test_n2_rejects_remote_main_disagreement(
    promotion_fixture: PromotionFixture,
) -> None:
    original_head = promotion_fixture.repository_head
    config_path = promotion_fixture.project_root / "configs/data/phase04_5n_test_config.yaml"
    config_path.write_text(config_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    _run_git(promotion_fixture.project_root, "add", str(config_path))
    _run_git(promotion_fixture.project_root, "commit", "-m", "remote advance")
    advanced_head = _run_git(promotion_fixture.project_root, "rev-parse", "HEAD")
    _run_git(promotion_fixture.project_root, "push", "origin", "main")
    _run_git(promotion_fixture.project_root, "reset", "--hard", original_head)
    _run_git(
        promotion_fixture.project_root,
        "update-ref",
        "refs/remotes/origin/main",
        original_head,
    )
    assert advanced_head != original_head
    with pytest.raises(PromotionPreflightError, match="remote main"):
        verify_repository_promotion_state(
            promotion_fixture.project_root,
            expected_head=original_head,
            allowed_status_prefixes=("outputs/metadata/external_assets/",),
        )


def test_n2_rejects_expected_head_mismatch(
    promotion_fixture: PromotionFixture,
) -> None:
    with pytest.raises(PromotionPreflightError, match="expected repository HEAD"):
        verify_repository_promotion_state(
            promotion_fixture.project_root,
            expected_head="0" * 40,
            allowed_status_prefixes=("outputs/metadata/external_assets/",),
        )


def test_n2_rejects_nonempty_staged_index(
    promotion_fixture: PromotionFixture,
) -> None:
    config_path = promotion_fixture.project_root / "configs/data/phase04_5n_test_config.yaml"
    config_path.write_text(config_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    _run_git(promotion_fixture.project_root, "add", str(config_path))
    with pytest.raises(PromotionPreflightError, match="staged index"):
        verify_repository_promotion_state(
            promotion_fixture.project_root,
            expected_head=promotion_fixture.repository_head,
            allowed_status_prefixes=("outputs/metadata/external_assets/",),
        )


def test_n2_rejects_staged_sha_mismatch(
    promotion_fixture: PromotionFixture,
) -> None:
    request = _make_request(
        promotion_fixture,
        authorization_phrase=promotion_fixture.config.n2_authorization_phrase,
        execute=True,
        expected_staged_sha256="F" * 64,
    )
    with pytest.raises(PromotionPreflightError, match="staged SHA256"):
        prepare_promotion_preflight(promotion_fixture.config, request)


def test_n2_rejects_n1_classification_not_pass(
    promotion_fixture: PromotionFixture,
) -> None:
    gate = promotion_fixture.n1_workspace_root / "evidence/gate_result.json"
    _rewrite_json(gate, classification="PHASE_04_5N_STAGED_ANNOTATION_CORRECTIONS_BLOCKED")
    _refresh_n1_manifests(promotion_fixture.n1_workspace_root)
    with pytest.raises(PromotionPreflightError, match="classification"):
        verify_n1_workspace(
            promotion_fixture.config,
            promotion_fixture.n1_workspace_root,
        )


def test_n2_rejects_changed_count_not_two(
    promotion_fixture: PromotionFixture,
) -> None:
    gate = promotion_fixture.n1_workspace_root / "evidence/gate_result.json"
    _rewrite_json(gate, changed_annotation_count=1)
    _refresh_n1_manifests(promotion_fixture.n1_workspace_root)
    with pytest.raises(PromotionPreflightError, match="changed annotation count"):
        verify_n1_workspace(
            promotion_fixture.config,
            promotion_fixture.n1_workspace_root,
        )


def test_n2_rejects_missing_manifest(promotion_fixture: PromotionFixture) -> None:
    (promotion_fixture.n1_workspace_root / "evidence/SHA256SUMS.csv").unlink()
    with pytest.raises(PromotionPreflightError, match="manifest"):
        verify_n1_workspace(
            promotion_fixture.config,
            promotion_fixture.n1_workspace_root,
        )


def test_n2_rejects_repeat_promotion_evidence_path_collision(
    promotion_fixture: PromotionFixture,
) -> None:
    collision = (
        promotion_fixture.config.n2_evidence_base_root
        / f"{promotion_fixture.config.n2_evidence_prefix}_20260715_041000000"
    )
    collision.mkdir(parents=True)
    with pytest.raises(PromotionPreflightError, match="evidence workspace"):
        prepare_promotion_preflight(
            promotion_fixture.config,
            _make_request(promotion_fixture),
        )


def test_n2_rejects_current_canonical_already_equal_to_staged(
    promotion_fixture: PromotionFixture,
) -> None:
    staged = (
        promotion_fixture.n1_workspace_root
        / "staged/staged_corrected_validation_coco.json"
    )
    shutil.copyfile(staged, promotion_fixture.canonical_path)
    request = _make_request(
        promotion_fixture,
        expected_canonical_sha256=promotion_fixture.staged_sha256,
    )
    with pytest.raises(PromotionPreflightError, match="already equals staged"):
        prepare_promotion_preflight(promotion_fixture.config, request)


def test_n2_rejects_test_split_contract_even_when_filename_contains_test_set(
    promotion_fixture: PromotionFixture,
) -> None:
    contract = (
        promotion_fixture.n1_workspace_root
        / "canonical_snapshot/canonical_source_contract.json"
    )
    _rewrite_json(contract, canonical_source_split="test")
    _refresh_n1_manifests(promotion_fixture.n1_workspace_root)
    with pytest.raises(PromotionPreflightError, match="test split"):
        verify_n1_workspace(
            promotion_fixture.config,
            promotion_fixture.n1_workspace_root,
        )



def _prepare_execute_preflight(
    fixture: PromotionFixture,
    *,
    timestamp: str,
):
    return prepare_promotion_preflight(
        fixture.config,
        _make_request(
            fixture,
            authorization_phrase=fixture.config.n2_authorization_phrase,
            execute=True,
            timestamp=timestamp,
        ),
    )


def test_atomic_promotion_creates_verified_backup_and_replaces_canonical(
    promotion_fixture: PromotionFixture,
) -> None:
    preflight = _prepare_execute_preflight(
        promotion_fixture,
        timestamp="20260715_042000000",
    )

    result = execute_atomic_promotion(promotion_fixture.config, preflight)

    assert result.classification == "PHASE_04_5N_ANNOTATION_CORRECTIONS_PROMOTED"
    assert result.backup_verified is True
    assert result.atomic_promotion_verified is True
    assert result.post_promotion_semantic_validation == "PASS"
    assert result.promoted_annotation_count == 2
    assert sha256_file(result.canonical_path) == result.after_sha256
    assert result.after_sha256 == promotion_fixture.staged_sha256
    assert sha256_file(result.backup_path) == result.before_sha256
    assert result.before_sha256 == promotion_fixture.source_sha256
    assert result.changed_native_annotation_ids == (101, 202)

    expected_files = {
        "source/n1_gate_result.json",
        "source/n1_workspace_manifest.csv",
        "source/n1_sha256sums.csv",
        "backup/canonical_validation_coco.before.json",
        "evidence/preflight.json",
        "evidence/promotion_result.json",
        "evidence/workspace_manifest.csv",
        "evidence/SHA256SUMS.csv",
    }
    actual_files = {
        path.relative_to(result.evidence_workspace_root).as_posix()
        for path in result.evidence_workspace_root.rglob("*")
        if path.is_file()
    }
    assert actual_files == expected_files
    payload = json.loads(result.result_path.read_text(encoding="utf-8"))
    assert payload["OUTCOME"] == "PASS"
    assert payload["CLASSIFICATION"] == result.classification
    assert payload["BACKUP_VERIFIED"] == "YES"
    assert payload["ATOMIC_PROMOTION_VERIFIED"] == "YES"
    assert payload["POST_PROMOTION_SEMANTIC_VALIDATION"] == "PASS"
    assert payload["TEST_SPLIT_READ"] == "NO"
    assert payload["TRAINING_STARTED"] == "NO"


def test_post_replace_failure_restores_original_bytes(
    promotion_fixture: PromotionFixture,
) -> None:
    original = promotion_fixture.canonical_path.read_bytes()
    preflight = _prepare_execute_preflight(
        promotion_fixture,
        timestamp="20260715_042000001",
    )

    def fail_after_replace(stage: str) -> None:
        if stage == "after_replace_before_postverify":
            raise RuntimeError("injected post-replace failure")

    with pytest.raises(PromotionExecutionError, match="restored and verified"):
        execute_atomic_promotion(
            promotion_fixture.config,
            preflight,
            fault_injector=fail_after_replace,
        )

    assert promotion_fixture.canonical_path.read_bytes() == original
    rollback = json.loads(
        (preflight.evidence_workspace_root / "evidence/rollback_result.json").read_text(
            encoding="utf-8"
        )
    )
    assert rollback["status"] == "RESTORED_AND_VERIFIED"
    assert rollback["restored_sha256"] == promotion_fixture.source_sha256


def test_backup_hash_mismatch_blocks_before_replace(
    promotion_fixture: PromotionFixture,
) -> None:
    original = promotion_fixture.canonical_path.read_bytes()
    preflight = _prepare_execute_preflight(
        promotion_fixture,
        timestamp="20260715_042000002",
    )

    def corrupt_backup(stage: str) -> None:
        if stage == "after_backup_copy_before_verify":
            backup = (
                preflight.evidence_workspace_root
                / "backup/canonical_validation_coco.before.json"
            )
            backup.write_bytes(backup.read_bytes() + b"corrupt")

    with pytest.raises(PromotionExecutionError, match="backup SHA256"):
        execute_atomic_promotion(
            promotion_fixture.config,
            preflight,
            fault_injector=corrupt_backup,
        )
    assert promotion_fixture.canonical_path.read_bytes() == original


def test_temp_file_hash_mismatch_blocks_before_replace(
    promotion_fixture: PromotionFixture,
) -> None:
    original = promotion_fixture.canonical_path.read_bytes()
    preflight = _prepare_execute_preflight(
        promotion_fixture,
        timestamp="20260715_042000003",
    )

    def corrupt_temp(stage: str) -> None:
        if stage == "after_temp_copy_before_verify":
            temp_files = list(
                promotion_fixture.canonical_path.parent.glob(
                    ".phase04_5n_promotion_*.tmp"
                )
            )
            assert len(temp_files) == 1
            temp_files[0].write_bytes(temp_files[0].read_bytes() + b"corrupt")

    with pytest.raises(PromotionExecutionError, match="temporary staged SHA256"):
        execute_atomic_promotion(
            promotion_fixture.config,
            preflight,
            fault_injector=corrupt_temp,
        )
    assert promotion_fixture.canonical_path.read_bytes() == original
    assert not list(
        promotion_fixture.canonical_path.parent.glob(".phase04_5n_promotion_*.tmp")
    )


def test_os_replace_failure_keeps_original_canonical(
    promotion_fixture: PromotionFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = promotion_fixture.canonical_path.read_bytes()
    preflight = _prepare_execute_preflight(
        promotion_fixture,
        timestamp="20260715_042000004",
    )

    def fail_replace(source: object, destination: object) -> None:
        raise OSError("replace denied")

    monkeypatch.setattr(promotion_module.os, "replace", fail_replace)
    with pytest.raises(PromotionExecutionError, match="replace denied"):
        execute_atomic_promotion(promotion_fixture.config, preflight)
    assert promotion_fixture.canonical_path.read_bytes() == original


def test_rollback_temp_copy_failure_is_reported_without_false_success(
    promotion_fixture: PromotionFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preflight = _prepare_execute_preflight(
        promotion_fixture,
        timestamp="20260715_042000005",
    )
    original_copy = promotion_module._copy_file_with_fsync
    calls = 0

    def fail_third_copy(source: Path, destination: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise OSError("rollback temp copy denied")
        original_copy(source, destination)

    monkeypatch.setattr(promotion_module, "_copy_file_with_fsync", fail_third_copy)

    def fail_postverify(stage: str) -> None:
        if stage == "after_replace_before_postverify":
            raise RuntimeError("force rollback")

    with pytest.raises(PromotionExecutionError, match="restore failed"):
        execute_atomic_promotion(
            promotion_fixture.config,
            preflight,
            fault_injector=fail_postverify,
        )

    assert sha256_file(promotion_fixture.canonical_path) == promotion_fixture.staged_sha256
    rollback = json.loads(
        (preflight.evidence_workspace_root / "evidence/rollback_result.json").read_text(
            encoding="utf-8"
        )
    )
    assert rollback["status"] == "RESTORE_FAILED"
    assert "rollback temp copy denied" in rollback["error"]


def test_rollback_hash_mismatch_is_reported_without_false_success(
    promotion_fixture: PromotionFixture,
) -> None:
    preflight = _prepare_execute_preflight(
        promotion_fixture,
        timestamp="20260715_042000006",
    )

    def corrupt_backup_and_fail(stage: str) -> None:
        if stage == "after_replace_before_postverify":
            backup = (
                preflight.evidence_workspace_root
                / "backup/canonical_validation_coco.before.json"
            )
            backup.write_bytes(backup.read_bytes() + b"corrupt")
            raise RuntimeError("force rollback with corrupt backup")

    with pytest.raises(PromotionExecutionError, match="restore failed"):
        execute_atomic_promotion(
            promotion_fixture.config,
            preflight,
            fault_injector=corrupt_backup_and_fail,
        )

    assert sha256_file(promotion_fixture.canonical_path) == promotion_fixture.staged_sha256
    rollback = json.loads(
        (preflight.evidence_workspace_root / "evidence/rollback_result.json").read_text(
            encoding="utf-8"
        )
    )
    assert rollback["status"] == "RESTORE_FAILED"
    assert "backup SHA256" in rollback["error"]


def test_execute_rechecks_evidence_workspace_no_overwrite(
    promotion_fixture: PromotionFixture,
) -> None:
    original = promotion_fixture.canonical_path.read_bytes()
    preflight = _prepare_execute_preflight(
        promotion_fixture,
        timestamp="20260715_042000007",
    )
    preflight.evidence_workspace_root.mkdir(parents=True)

    with pytest.raises(PromotionExecutionError, match="evidence workspace"):
        execute_atomic_promotion(promotion_fixture.config, preflight)
    assert promotion_fixture.canonical_path.read_bytes() == original


def test_second_execution_is_blocked_after_success(
    promotion_fixture: PromotionFixture,
) -> None:
    preflight = _prepare_execute_preflight(
        promotion_fixture,
        timestamp="20260715_042000008",
    )
    execute_atomic_promotion(promotion_fixture.config, preflight)

    with pytest.raises(PromotionExecutionError, match="evidence workspace"):
        execute_atomic_promotion(promotion_fixture.config, preflight)
    assert sha256_file(promotion_fixture.canonical_path) == promotion_fixture.staged_sha256


def test_canonical_symlink_or_reparse_guard_blocks_before_write(
    promotion_fixture: PromotionFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = promotion_fixture.canonical_path.read_bytes()
    preflight = _prepare_execute_preflight(
        promotion_fixture,
        timestamp="20260715_042000009",
    )
    original_detector = promotion_module._is_symlink_or_reparse

    def detect_canonical_as_reparse(path: Path) -> bool:
        if path.absolute() == promotion_fixture.canonical_path.absolute():
            return True
        return original_detector(path)

    monkeypatch.setattr(
        promotion_module,
        "_is_symlink_or_reparse",
        detect_canonical_as_reparse,
    )
    with pytest.raises(PromotionExecutionError, match="symlink|reparse"):
        execute_atomic_promotion(promotion_fixture.config, preflight)
    assert promotion_fixture.canonical_path.read_bytes() == original
    assert not preflight.evidence_workspace_root.exists()


def test_execute_atomic_promotion_invokes_no_downstream_command(
    promotion_fixture: PromotionFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preflight = _prepare_execute_preflight(
        promotion_fixture,
        timestamp="20260715_042000010",
    )

    def forbidden_subprocess(*args: object, **kwargs: object) -> object:
        raise AssertionError("downstream command invocation is forbidden")

    monkeypatch.setattr(promotion_module.subprocess, "run", forbidden_subprocess)
    result = execute_atomic_promotion(promotion_fixture.config, preflight)
    assert result.classification == promotion_fixture.config.n2_gate_classification
