#!/usr/bin/env python3
"""Validate FleetVision Local Project Dashboard JSON data.

The browser is intentionally read-only. This script is the repository-side,
fail-closed validation boundary for schema, identity, references, progress,
and safety invariants.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker


REQUIRED_SAFETY_GATES = {
    "TEST_SPLIT_READ",
    "MODEL_INFERENCE_EXECUTED",
    "CANONICAL_ANNOTATION_MODIFIED",
    "CANONICAL_COCO_MODIFIED",
    "DATASET_MODIFIED",
    "REGISTRY_MODIFIED",
    "FIXED_SPLITS_MODIFIED",
    "TRAINING_STARTED",
    "RETRAINING_STATUS",
    "DEPLOYMENT_ACCEPTANCE",
}


class DashboardValidationError(ValueError):
    """Raised when dashboard data violates a formal contract."""


class ValidationSummary:
    """Compact validation result used by CLI and tests."""

    __slots__ = ("status", "phase_count", "gate_count", "evidence_count", "event_count")

    def __init__(
        self,
        *,
        status: str,
        phase_count: int,
        gate_count: int,
        evidence_count: int,
        event_count: int,
    ) -> None:
        self.status = status
        self.phase_count = phase_count
        self.gate_count = gate_count
        self.evidence_count = evidence_count
        self.event_count = event_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "phase_count": self.phase_count,
            "gate_count": self.gate_count,
            "evidence_count": self.evidence_count,
            "event_count": self.event_count,
        }


def canonical_json_bytes(value: object) -> bytes:
    """Return deterministic UTF-8 JSON bytes for hashing."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def compute_snapshot_id(document: dict[str, Any]) -> str:
    """Compute the dashboard snapshot fingerprint excluding snapshot_id itself."""

    normalized = copy.deepcopy(document)
    normalized.pop("snapshot_id", None)
    digest = hashlib.sha256(canonical_json_bytes(normalized)).hexdigest().upper()
    return f"sha256:{digest}"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise DashboardValidationError(f"required file missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DashboardValidationError(
            f"invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(value, dict):
        raise DashboardValidationError(f"root JSON value must be an object: {path}")
    return value


def _format_jsonschema_error(error: Any) -> str:
    location = ".".join(str(part) for part in error.absolute_path) or "<root>"
    return f"{location}: {error.message}"


def _validate_schema(document: dict[str, Any], schema: dict[str, Any], label: str) -> None:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda item: list(item.absolute_path))
    if errors:
        details = "; ".join(_format_jsonschema_error(item) for item in errors[:12])
        raise DashboardValidationError(f"{label} schema validation failed: {details}")


def _require_unique(records: Iterable[dict[str, Any]], key: str, label: str) -> set[str]:
    values: set[str] = set()
    for record in records:
        value = record[key]
        if value in values:
            raise DashboardValidationError(f"duplicate {key}: {value} ({label})")
        values.add(value)
    return values


def _validate_snapshot_id(document: dict[str, Any], label: str) -> None:
    expected = compute_snapshot_id(document)
    if document.get("snapshot_id") != expected:
        raise DashboardValidationError(
            f"{label} snapshot_id mismatch: expected {expected}, got {document.get('snapshot_id')}"
        )


def _weighted_progress(records: list[dict[str, Any]]) -> float:
    total_weight = sum(float(item["weight"]) for item in records)
    if total_weight <= 0:
        return 0.0
    completed = sum(float(item["weight"]) * float(item["progress"]) for item in records)
    return completed / total_weight


def _assert_close(actual: float, expected: float, label: str, tolerance: float = 0.01) -> None:
    if not math.isclose(actual, expected, abs_tol=tolerance):
        raise DashboardValidationError(
            f"{label} mismatch: expected {expected:.4f}, got {actual:.4f}"
        )


def _validate_status_cross_references(status: dict[str, Any]) -> tuple[set[str], set[str], set[str]]:
    phases = status["phases"]
    gates = status["gates"]
    evidence = status["evidence"]

    phase_ids = _require_unique(phases, "phase_id", "phases")
    gate_ids = _require_unique(gates, "gate_id", "gates")
    evidence_ids = _require_unique(evidence, "evidence_id", "evidence")
    _require_unique(status["warnings"], "warning_id", "warnings")
    _require_unique(status["repository"]["candidate_worktrees"], "worktree_id", "candidate worktrees")

    safety_keys = _require_unique(status["safety_gates"], "key", "safety gates")
    missing = sorted(REQUIRED_SAFETY_GATES - safety_keys)
    if missing:
        raise DashboardValidationError(f"missing safety gate(s): {', '.join(missing)}")

    gates_by_phase: dict[str, list[dict[str, Any]]] = {phase_id: [] for phase_id in phase_ids}
    for gate in gates:
        if gate["phase_id"] not in phase_ids:
            raise DashboardValidationError(
                f"gate {gate['gate_id']} references unknown phase_id: {gate['phase_id']}"
            )
        gates_by_phase[gate["phase_id"]].append(gate)
        for evidence_id in gate["evidence_ids"]:
            if evidence_id not in evidence_ids:
                raise DashboardValidationError(
                    f"gate {gate['gate_id']} references unknown evidence_id: {evidence_id}"
                )

    for phase in phases:
        declared = phase["gate_ids"]
        if len(declared) != len(set(declared)):
            raise DashboardValidationError(f"phase {phase['phase_id']} contains duplicate gate_ids")
        for gate_id in declared:
            if gate_id not in gate_ids:
                raise DashboardValidationError(
                    f"phase {phase['phase_id']} references unknown gate_id: {gate_id}"
                )
        actual = [gate["gate_id"] for gate in gates_by_phase[phase["phase_id"]]]
        if set(declared) != set(actual):
            raise DashboardValidationError(
                f"phase {phase['phase_id']} gate_ids do not match gates assigned to the phase"
            )
        expected_progress = _weighted_progress(gates_by_phase[phase["phase_id"]])
        _assert_close(float(phase["progress"]), expected_progress, f"phase {phase['phase_id']} progress")

    expected_overall = _weighted_progress(phases)
    _assert_close(
        float(status["project"]["overall_progress"]),
        expected_overall,
        "overall progress",
    )

    for item in evidence:
        if item["type"] == "RESULT_ZIP" and item["commit_policy"] != "DO_NOT_COMMIT":
            raise DashboardValidationError(
                f"Result ZIP {item['evidence_id']} must use commit_policy=DO_NOT_COMMIT"
            )

    alignment = status["state_alignment"]["value"]
    candidates = status["repository"]["candidate_worktrees"]
    any_uncommitted = any(not item["implementation_committed"] for item in candidates if item["purpose"] != "DASHBOARD")
    if alignment == "SYNCED" and any_uncommitted:
        raise DashboardValidationError(
            "formal/candidate authority conflict: alignment cannot be SYNCED with uncommitted candidate work"
        )

    gates_by_id = {item["gate_id"]: item for item in gates}
    evidence_by_id = {item["evidence_id"]: item for item in evidence}
    n1 = gates_by_id.get("04.5N-1")
    n2 = gates_by_id.get("04.5N-2")
    if n1 is not None and n2 is not None:
        if n2["status"] == "NOT_APPROVED":
            if not any("N1 PASS" in text for text in n2["blocking_conditions"]):
                raise DashboardValidationError(
                    "04.5N-2 must explicitly state that N1 PASS does not authorize N2"
                )
        else:
            if n1["status"] != "COMPLETED" or n1["outcome"] != "PASS":
                raise DashboardValidationError(
                    "04.5N-2 cannot progress before a completed N1 PASS"
                )
            authorization_evidence = [
                evidence_by_id[evidence_id]
                for evidence_id in n2["evidence_ids"]
                if evidence_by_id[evidence_id]["type"] == "AUTHORIZATION"
                and evidence_by_id[evidence_id]["verification_status"]
                in {"REPOSITORY_VERIFIED", "ARTIFACT_VERIFIED"}
            ]
            if not authorization_evidence:
                raise DashboardValidationError(
                    "04.5N-2 progression requires verified authorization evidence"
                )

    return phase_ids, gate_ids, evidence_ids


def _validate_history_cross_references(
    history: dict[str, Any],
    phase_ids: set[str],
    gate_ids: set[str],
    evidence_ids: set[str],
) -> None:
    events = history["events"]
    event_ids = _require_unique(events, "event_id", "history events")
    seen: set[str] = set()
    last_recorded: str | None = None

    for event in events:
        if event["phase_id"] not in phase_ids:
            raise DashboardValidationError(
                f"history event {event['event_id']} references unknown phase_id: {event['phase_id']}"
            )
        if event["gate_id"] not in gate_ids:
            raise DashboardValidationError(
                f"history event {event['event_id']} references unknown gate_id: {event['gate_id']}"
            )
        for evidence_id in event["evidence_ids"]:
            if evidence_id not in evidence_ids:
                raise DashboardValidationError(
                    f"history event {event['event_id']} references unknown evidence_id: {evidence_id}"
                )
        recorded_at = event["recorded_at_utc"]
        if last_recorded is not None and recorded_at < last_recorded:
            raise DashboardValidationError("history events must be ordered by recorded_at_utc")
        last_recorded = recorded_at

        corrects = event["corrects_event_id"]
        if corrects is not None:
            if event["event_type"] != "CORRECTION":
                raise DashboardValidationError(
                    f"history event {event['event_id']} has corrects_event_id but is not CORRECTION"
                )
            if corrects not in seen:
                raise DashboardValidationError(
                    f"history correction {event['event_id']} references missing or future event: {corrects}"
                )
        seen.add(event["event_id"])

    if seen != event_ids:
        raise DashboardValidationError("history event identity validation failed")


def validate_dashboard_data(
    *,
    status_path: Path,
    history_path: Path,
    status_schema_path: Path,
    history_schema_path: Path,
) -> ValidationSummary:
    """Validate dashboard documents and return a structured summary."""

    status = _load_json(status_path)
    history = _load_json(history_path)
    status_schema = _load_json(status_schema_path)
    history_schema = _load_json(history_schema_path)

    _validate_schema(status, status_schema, "project_status")
    _validate_schema(history, history_schema, "project_history")
    _validate_snapshot_id(status, "project_status")
    _validate_snapshot_id(history, "project_history")

    phase_ids, gate_ids, evidence_ids = _validate_status_cross_references(status)
    _validate_history_cross_references(history, phase_ids, gate_ids, evidence_ids)

    return ValidationSummary(
        status="PASS",
        phase_count=len(status["phases"]),
        gate_count=len(status["gates"]),
        evidence_count=len(status["evidence"]),
        event_count=len(history["events"]),
    )


def validate_dashboard_root(dashboard_root: Path) -> ValidationSummary:
    """Validate the standard Dashboard layout rooted at dashboard_root."""

    return validate_dashboard_data(
        status_path=dashboard_root / "data/project_status.json",
        history_path=dashboard_root / "data/project_history.json",
        status_schema_path=dashboard_root / "schemas/project_status.schema.json",
        history_schema_path=dashboard_root / "schemas/project_history.schema.json",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dashboard-root",
        type=Path,
        default=Path("docs/00_project_management/project_dashboard"),
        help="Dashboard directory containing data/ and schemas/.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit one machine-readable JSON result.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        summary = validate_dashboard_root(args.dashboard_root.resolve())
    except DashboardValidationError as exc:
        result = {"status": "BLOCKED", "error": str(exc)}
        if args.json:
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        else:
            print("============================================================")
            print(" FleetVision Project Dashboard Data Validation")
            print("============================================================")
            print("Outcome: BLOCKED")
            print(f"Error:   {exc}")
        return 1

    if args.json:
        print(json.dumps(summary.to_dict(), ensure_ascii=False, sort_keys=True))
    else:
        print("============================================================")
        print(" FleetVision Project Dashboard Data Validation")
        print("============================================================")
        print("Outcome:        PASS")
        print(f"Phases:         {summary.phase_count}")
        print(f"Gates:          {summary.gate_count}")
        print(f"Evidence items: {summary.evidence_count}")
        print(f"History events: {summary.event_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
