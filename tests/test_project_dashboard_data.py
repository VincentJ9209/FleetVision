from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_ROOT = ROOT / "docs/00_project_management/project_dashboard"
VALIDATOR_PATH = ROOT / "scripts/validate_project_dashboard_data.py"


def load_validator_module():
    spec = importlib.util.spec_from_file_location("dashboard_validator", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load dashboard validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


@pytest.fixture()
def validator():
    return load_validator_module()


@pytest.fixture()
def dashboard_copy(tmp_path: Path) -> Path:
    import shutil

    destination = tmp_path / "project_dashboard"
    shutil.copytree(DASHBOARD_ROOT, destination)
    return destination


def test_committed_dashboard_documents_pass(validator) -> None:
    summary = validator.validate_dashboard_root(DASHBOARD_ROOT)
    assert summary.status == "PASS"
    assert summary.phase_count >= 14
    assert summary.gate_count >= 25
    assert summary.event_count >= 10


def test_minimum_phase_and_gate_inventory_is_present() -> None:
    status = read_json(DASHBOARD_ROOT / "data/project_status.json")
    phase_ids = {item["phase_id"] for item in status["phases"]}
    gate_ids = {item["gate_id"] for item in status["gates"]}

    assert {
        "PHASE_00",
        "PHASE_01",
        "PHASE_02",
        "PHASE_03",
        "PHASE_03_5",
        "PHASE_04",
        "PHASE_04_5",
        "PHASE_05",
        "PHASE_06",
        "PHASE_07",
        "PHASE_08",
        "PHASE_09",
        "PHASE_10",
        "FUTURE_EXTENSIONS",
    } <= phase_ids
    assert {"04.5M-0", "04.5M-1", "04.5M-2", "04.5N-1", "04.5N-2"} <= gate_ids


def test_duplicate_gate_id_blocks(validator, dashboard_copy: Path) -> None:
    status_path = dashboard_copy / "data/project_status.json"
    status = read_json(status_path)
    status["gates"].append(copy.deepcopy(status["gates"][0]))
    status["snapshot_id"] = validator.compute_snapshot_id(status)
    write_json(status_path, status)

    with pytest.raises(validator.DashboardValidationError, match="duplicate gate_id"):
        validator.validate_dashboard_root(dashboard_copy)


def test_unknown_evidence_reference_blocks(validator, dashboard_copy: Path) -> None:
    status_path = dashboard_copy / "data/project_status.json"
    status = read_json(status_path)
    status["gates"][0]["evidence_ids"] = ["missing-evidence"]
    status["snapshot_id"] = validator.compute_snapshot_id(status)
    write_json(status_path, status)

    with pytest.raises(validator.DashboardValidationError, match="unknown evidence_id"):
        validator.validate_dashboard_root(dashboard_copy)


def test_required_safety_gate_missing_blocks(validator, dashboard_copy: Path) -> None:
    status_path = dashboard_copy / "data/project_status.json"
    status = read_json(status_path)
    status["safety_gates"] = [
        item for item in status["safety_gates"] if item["key"] != "TEST_SPLIT_READ"
    ]
    status["snapshot_id"] = validator.compute_snapshot_id(status)
    write_json(status_path, status)

    with pytest.raises(validator.DashboardValidationError, match="missing safety gate"):
        validator.validate_dashboard_root(dashboard_copy)


def test_snapshot_fingerprint_mismatch_blocks(validator, dashboard_copy: Path) -> None:
    status_path = dashboard_copy / "data/project_status.json"
    status = read_json(status_path)
    status["project"]["display_name"] = "tampered"
    write_json(status_path, status)

    with pytest.raises(validator.DashboardValidationError, match="snapshot_id mismatch"):
        validator.validate_dashboard_root(dashboard_copy)


def test_result_zip_must_not_be_committable(validator, dashboard_copy: Path) -> None:
    status_path = dashboard_copy / "data/project_status.json"
    status = read_json(status_path)
    result_zip = next(item for item in status["evidence"] if item["type"] == "RESULT_ZIP")
    result_zip["commit_policy"] = "MAY_COMMIT_AFTER_REVIEW"
    status["snapshot_id"] = validator.compute_snapshot_id(status)
    write_json(status_path, status)

    with pytest.raises(validator.DashboardValidationError, match="Result ZIP"):
        validator.validate_dashboard_root(dashboard_copy)


def test_history_event_unknown_gate_blocks(validator, dashboard_copy: Path) -> None:
    history_path = dashboard_copy / "data/project_history.json"
    history = read_json(history_path)
    history["events"][0]["gate_id"] = "UNKNOWN-GATE"
    history["snapshot_id"] = validator.compute_snapshot_id(history)
    write_json(history_path, history)

    with pytest.raises(validator.DashboardValidationError, match="unknown gate_id"):
        validator.validate_dashboard_root(dashboard_copy)


def test_n1_n2_authorization_boundary_is_explicit() -> None:
    status = read_json(DASHBOARD_ROOT / "data/project_status.json")
    gates = {item["gate_id"]: item for item in status["gates"]}
    assert gates["04.5N-1"]["status"] == "PENDING_EXECUTION"
    assert gates["04.5N-2"]["status"] == "NOT_APPROVED"
    assert any("N1 PASS" in item for item in gates["04.5N-2"]["blocking_conditions"])


def test_future_n2_authorization_is_accepted_only_after_n1_pass(
    validator, dashboard_copy: Path
) -> None:
    status_path = dashboard_copy / "data/project_status.json"
    status = read_json(status_path)
    gates = {item["gate_id"]: item for item in status["gates"]}
    n1 = gates["04.5N-1"]
    n2 = gates["04.5N-2"]

    n1.update(
        status="COMPLETED",
        outcome="PASS",
        progress=100,
        trust_level="ARTIFACT_VERIFIED",
    )
    n2.update(
        status="READY",
        outcome="NOT_RUN",
        trust_level="ARTIFACT_VERIFIED",
        evidence_ids=["E-04.5N-DESIGN", "E-04.5N-N2-AUTHORIZATION"],
        authorized_actions=["Execute the separately authorized N2 promotion preflight"],
        blocking_conditions=["Fresh pre-promotion verification remains required."],
    )
    status["evidence"].append(
        {
            "evidence_id": "E-04.5N-N2-AUTHORIZATION",
            "type": "AUTHORIZATION",
            "filename": None,
            "path": "docs/00_project_management/PROJECT_STATUS.md",
            "sha256": None,
            "size_bytes": None,
            "classification": "PHASE_04_5N_2_CANONICAL_PROMOTION_AUTHORIZED",
            "created_at_utc": "2026-07-16T00:00:00Z",
            "verification_status": "REPOSITORY_VERIFIED",
            "commit_policy": "TRACKED_GOVERNANCE",
            "source_refs": [
                {
                    "type": "repository_file",
                    "path": "docs/00_project_management/PROJECT_STATUS.md",
                    "ref": "future-authorized-checkpoint",
                    "section": "N2 authorization",
                }
            ],
        }
    )

    phase = next(item for item in status["phases"] if item["phase_id"] == "PHASE_04_5")
    phase_gates = [item for item in status["gates"] if item["phase_id"] == phase["phase_id"]]
    phase["progress"] = validator._weighted_progress(phase_gates)
    status["project"]["overall_progress"] = validator._weighted_progress(status["phases"])
    status["snapshot_id"] = validator.compute_snapshot_id(status)
    write_json(status_path, status)

    summary = validator.validate_dashboard_root(dashboard_copy)
    assert summary.status == "PASS"


def test_n2_progression_without_verified_authorization_blocks(
    validator, dashboard_copy: Path
) -> None:
    status_path = dashboard_copy / "data/project_status.json"
    status = read_json(status_path)
    gates = {item["gate_id"]: item for item in status["gates"]}
    n1 = gates["04.5N-1"]
    n2 = gates["04.5N-2"]
    n1.update(status="COMPLETED", outcome="PASS", progress=100, trust_level="ARTIFACT_VERIFIED")
    n2.update(
        status="READY",
        trust_level="ARTIFACT_VERIFIED",
        blocking_conditions=["Fresh pre-promotion verification remains required."],
    )
    phase = next(item for item in status["phases"] if item["phase_id"] == "PHASE_04_5")
    phase_gates = [item for item in status["gates"] if item["phase_id"] == phase["phase_id"]]
    phase["progress"] = validator._weighted_progress(phase_gates)
    status["project"]["overall_progress"] = validator._weighted_progress(status["phases"])
    status["snapshot_id"] = validator.compute_snapshot_id(status)
    write_json(status_path, status)

    with pytest.raises(validator.DashboardValidationError, match="authorization evidence"):
        validator.validate_dashboard_root(dashboard_copy)
