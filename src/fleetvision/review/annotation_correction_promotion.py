from __future__ import annotations

import csv
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from fleetvision.review.annotation_correction_promotion_contract import (
    CanonicalCocoSource,
    Phase04_5NConfig,
    SourceAccessLedger,
    load_coco_document,
    resolve_canonical_validation_coco,
    sha256_file,
)
from fleetvision.review.annotation_correction_staging import (
    NativeAnnotationMapping,
    SemanticValidationResult,
    StagedCocoValidationError,
    validate_staged_coco,
)


class PromotionPreflightError(RuntimeError):
    """Raised when N2 preflight evidence or repository state is not promotable."""


class PromotionAuthorizationError(PromotionPreflightError):
    """Raised when an execute request lacks the exact approved authorization."""


class PromotionExecutionError(RuntimeError):
    """Raised when an authorized atomic promotion cannot complete safely."""


@dataclass(frozen=True)
class VerifiedN1Workspace:
    config: Phase04_5NConfig
    root: Path
    gate_result_path: Path
    gate_result: Mapping[str, object]
    canonical_snapshot_path: Path
    canonical_snapshot_sha256: str
    staged_coco_path: Path
    staged_coco_sha256: str
    changed_native_annotation_ids: tuple[int, ...]
    mappings: tuple[NativeAnnotationMapping, ...]
    semantic_validation: SemanticValidationResult


@dataclass(frozen=True)
class RepositoryPromotionState:
    project_root: Path
    branch: str
    head: str
    origin_main: str
    remote_main: str
    staged_paths: tuple[str, ...]
    allowed_status_paths: tuple[str, ...]


@dataclass(frozen=True)
class PromotionRequest:
    project_root: Path
    n1_workspace_root: Path
    expected_repository_head: str
    expected_canonical_sha256: str
    expected_staged_sha256: str
    authorization_phrase: str
    execute: bool
    timestamp: str


@dataclass(frozen=True)
class PromotionPreflight:
    config: Phase04_5NConfig
    request: PromotionRequest
    verified_n1: VerifiedN1Workspace
    repository_state: RepositoryPromotionState
    current_canonical_path: Path
    current_canonical_sha256: str
    staged_coco_path: Path
    staged_coco_sha256: str
    evidence_workspace_root: Path


@dataclass(frozen=True)
class PromotionResult:
    classification: str
    canonical_path: Path
    backup_path: Path
    evidence_workspace_root: Path
    result_path: Path
    before_sha256: str
    staged_sha256: str
    after_sha256: str
    backup_sha256: str
    promoted_annotation_count: int
    changed_native_annotation_ids: tuple[int, ...]
    backup_verified: bool
    atomic_promotion_verified: bool
    post_promotion_semantic_validation: str


@dataclass(frozen=True)
class RollbackResult:
    status: str
    canonical_path: Path
    backup_path: Path
    expected_before_sha256: str
    restored_sha256: str | None
    result_path: Path
    error: str | None


_SHA256_RE = re.compile(r"^[0-9A-Fa-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9A-Fa-f]{40}$")
_TIMESTAMP_RE = re.compile(r"^\d{8}_\d{9}$")
_MANIFEST_FIELDS = ("relative_path", "size_bytes", "sha256")


def _read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PromotionPreflightError(f"failed to read {label}: {path}: {exc}") from exc


def _require_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise PromotionPreflightError(f"{label} must be an object")
    return value


def _require_sha256(value: object, label: str) -> str:
    text = str(value).strip()
    if _SHA256_RE.fullmatch(text) is None:
        raise PromotionPreflightError(f"{label} must be a 64-character SHA256")
    return text.upper()


def _require_git_sha(value: object, label: str) -> str:
    text = str(value).strip()
    if _GIT_SHA_RE.fullmatch(text) is None:
        raise PromotionPreflightError(f"{label} must be a 40-character Git SHA")
    return text.lower()


def _safe_workspace_member(root: Path, relative_text: str, label: str) -> Path:
    relative = Path(relative_text)
    if (
        not relative_text
        or relative.is_absolute()
        or relative.drive
        or ".." in relative.parts
    ):
        raise PromotionPreflightError(f"{label} is not a safe relative path: {relative_text}")
    resolved_root = root.resolve()
    candidate = (resolved_root / relative).resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise PromotionPreflightError(f"{label} escapes N1 workspace: {relative_text}") from exc
    return candidate


def _contains_test_split_segment(relative_text: str) -> bool:
    return any(part.lower() == "test" for part in Path(relative_text).parts)


def _read_manifest(path: Path, workspace_root: Path, label: str) -> tuple[dict[str, str], ...]:
    if not path.is_file():
        raise PromotionPreflightError(f"required {label} manifest is missing: {path}")
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != _MANIFEST_FIELDS:
                raise PromotionPreflightError(
                    f"{label} manifest fields must be {_MANIFEST_FIELDS!r}"
                )
            rows = tuple(dict(row) for row in reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise PromotionPreflightError(f"failed to read {label} manifest: {exc}") from exc
    if not rows:
        raise PromotionPreflightError(f"{label} manifest must not be empty")

    seen: set[str] = set()
    for row in rows:
        relative = str(row.get("relative_path", ""))
        if relative in seen:
            raise PromotionPreflightError(f"duplicate {label} manifest member: {relative}")
        seen.add(relative)
        if _contains_test_split_segment(relative):
            raise PromotionPreflightError(
                f"{label} manifest contains forbidden test split path: {relative}"
            )
        member = _safe_workspace_member(workspace_root, relative, f"{label} member")
        if not member.is_file():
            raise PromotionPreflightError(f"{label} manifest member is missing: {relative}")
        try:
            expected_size = int(str(row.get("size_bytes", "")))
        except ValueError as exc:
            raise PromotionPreflightError(
                f"{label} manifest size is invalid: {relative}"
            ) from exc
        if expected_size < 0 or member.stat().st_size != expected_size:
            raise PromotionPreflightError(f"{label} manifest SHA256/size mismatch: {relative}")
        expected_hash = _require_sha256(row.get("sha256"), f"{label} {relative} SHA256")
        if sha256_file(member) != expected_hash:
            raise PromotionPreflightError(f"{label} manifest SHA256 mismatch: {relative}")
    return rows


def _actual_workspace_files(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }


def _parse_float_tuple(value: str, label: str) -> tuple[float, float, float, float]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise PromotionPreflightError(f"{label} must be JSON") from exc
    if not isinstance(parsed, list) or len(parsed) != 4:
        raise PromotionPreflightError(f"{label} must contain four coordinates")
    try:
        return tuple(float(item) for item in parsed)  # type: ignore[return-value]
    except (TypeError, ValueError) as exc:
        raise PromotionPreflightError(f"{label} contains a non-numeric coordinate") from exc


def _parse_int(value: object, label: str) -> int:
    if isinstance(value, bool):
        raise PromotionPreflightError(f"{label} must be an integer")
    try:
        parsed = int(str(value))
    except (TypeError, ValueError) as exc:
        raise PromotionPreflightError(f"{label} must be an integer") from exc
    return parsed


def _load_mappings(path: Path) -> tuple[NativeAnnotationMapping, ...]:
    if not path.is_file():
        raise PromotionPreflightError(f"mapping CSV is missing: {path}")
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = tuple(dict(row) for row in csv.DictReader(handle))
    except (OSError, UnicodeError, csv.Error) as exc:
        raise PromotionPreflightError(f"failed to read mapping CSV: {exc}") from exc
    if len(rows) != 2:
        raise PromotionPreflightError("mapping CSV must contain exactly two rows")

    mappings: list[NativeAnnotationMapping] = []
    for index, row in enumerate(rows):
        prefix = f"mapping row {index}"
        source_split = str(row.get("source_split", ""))
        if source_split != "valid":
            raise PromotionPreflightError(
                f"{prefix} references forbidden test split or non-valid split"
            )
        mappings.append(
            NativeAnnotationMapping(
                phase04_5m_review_case_id=str(row.get("phase04_5m_review_case_id", "")),
                correction_case_id=str(row.get("correction_case_id", "")),
                proposal_fingerprint=_require_sha256(
                    row.get("proposal_fingerprint"),
                    f"{prefix} proposal fingerprint",
                ),
                source_split=source_split,
                image_id=str(row.get("image_id", "")),
                local_gt_bbox_id=str(row.get("local_gt_bbox_id", "")),
                native_image_id=_parse_int(row.get("native_coco_image_id"), f"{prefix} image ID"),
                native_annotation_id=_parse_int(
                    row.get("native_coco_annotation_id"),
                    f"{prefix} annotation ID",
                ),
                native_category_id=_parse_int(
                    row.get("native_category_id"),
                    f"{prefix} category ID",
                ),
                before_bbox_xywh=_parse_float_tuple(
                    str(row.get("before_bbox_xywh", "")),
                    f"{prefix} before bbox xywh",
                ),
                before_bbox_xyxy=_parse_float_tuple(
                    str(row.get("before_bbox_xyxy", "")),
                    f"{prefix} before bbox xyxy",
                ),
                before_area=float(str(row.get("before_area", ""))),
                after_bbox_xywh=_parse_float_tuple(
                    str(row.get("after_bbox_xywh", "")),
                    f"{prefix} after bbox xywh",
                ),
                after_bbox_xyxy=_parse_float_tuple(
                    str(row.get("after_bbox_xyxy", "")),
                    f"{prefix} after bbox xyxy",
                ),
                after_area=float(str(row.get("after_area", ""))),
            )
        )
    return tuple(mappings)


def _verify_required_n1_inventory(root: Path, mappings: tuple[NativeAnnotationMapping, ...]) -> None:
    required = {
        "source/annotation_correction_proposals_reviewed.csv",
        "source/annotation_correction_proposals_reviewed.json",
        "source/correction_review_export_result.json",
        "source/source_contract.json",
        "source/source_manifest.csv",
        "canonical_snapshot/canonical_validation_coco.json",
        "canonical_snapshot/canonical_source_contract.json",
        "staged/staged_corrected_validation_coco.json",
        "diff/annotation_correction_mapping.csv",
        "diff/annotation_correction_diff.csv",
        "diff/annotation_correction_diff.json",
        "diff/annotation_correction_diff.md",
        "evidence/semantic_validation.json",
        "evidence/workspace_manifest.csv",
        "evidence/SHA256SUMS.csv",
        "evidence/gate_result.json",
    }
    for mapping in mappings:
        for kind in ("before", "after", "combined"):
            required.add(f"overlays/{kind}/{mapping.correction_case_id}.jpg")
    missing = sorted(required - _actual_workspace_files(root))
    if missing:
        raise PromotionPreflightError(f"N1 workspace required evidence is missing: {missing}")


def verify_n1_workspace(
    config: Phase04_5NConfig,
    workspace_root: Path,
) -> VerifiedN1Workspace:
    root = Path(workspace_root).resolve()
    if not root.is_dir():
        raise PromotionPreflightError(f"N1 workspace does not exist: {root}")

    workspace_manifest_path = root / "evidence/workspace_manifest.csv"
    sha_manifest_path = root / "evidence/SHA256SUMS.csv"

    workspace_rows = _read_manifest(
        workspace_manifest_path,
        root,
        "workspace",
    )
    sha_rows = _read_manifest(
        sha_manifest_path,
        root,
        "SHA256SUMS",
    )

    actual = _actual_workspace_files(root)
    workspace_expected = actual - {
        "evidence/workspace_manifest.csv",
        "evidence/SHA256SUMS.csv",
    }
    workspace_members = {str(row["relative_path"]) for row in workspace_rows}
    if workspace_members != workspace_expected:
        raise PromotionPreflightError("workspace manifest inventory mismatch")

    sha_expected = actual - {"evidence/SHA256SUMS.csv"}
    sha_members = {str(row["relative_path"]) for row in sha_rows}
    if sha_members != sha_expected:
        raise PromotionPreflightError("SHA256SUMS manifest inventory mismatch")

    gate_path = root / "evidence/gate_result.json"
    gate = _require_mapping(_read_json(gate_path, "N1 gate result"), "N1 gate result")
    if gate.get("outcome") != "PASS":
        raise PromotionPreflightError("N1 gate outcome must be PASS")
    if gate.get("classification") != config.n1_gate_classification:
        raise PromotionPreflightError("N1 gate classification does not match approved PASS")
    if _parse_int(gate.get("proposal_count"), "proposal count") != 2:
        raise PromotionPreflightError("N1 proposal count must be exactly two")
    if _parse_int(gate.get("mapped_annotation_count"), "mapped annotation count") != 2:
        raise PromotionPreflightError("N1 mapped annotation count must be exactly two")
    if _parse_int(gate.get("changed_annotation_count"), "changed annotation count") != 2:
        raise PromotionPreflightError("N1 changed annotation count must be exactly two")

    changed_raw = gate.get("changed_native_annotation_ids")
    if not isinstance(changed_raw, list) or len(changed_raw) != 2:
        raise PromotionPreflightError("N1 changed native annotation IDs must contain two IDs")
    changed_ids = tuple(_parse_int(item, "changed native annotation ID") for item in changed_raw)
    if len(set(changed_ids)) != 2:
        raise PromotionPreflightError("N1 changed native annotation IDs must be distinct")

    for key in (
        "canonical_source_modified",
        "test_split_read",
        "model_inference_executed",
        "dataset_modified",
        "registry_modified",
        "fixed_splits_modified",
        "training_started",
    ):
        if gate.get(key) is not False:
            raise PromotionPreflightError(f"N1 safety declaration {key} must be false")

    relative_source = str(gate.get("canonical_source_relative_path", ""))
    if _contains_test_split_segment(relative_source):
        raise PromotionPreflightError("N1 gate references a forbidden test split path")

    contract_path = root / "canonical_snapshot/canonical_source_contract.json"
    contract = _require_mapping(
        _read_json(contract_path, "canonical source contract"),
        "canonical source contract",
    )
    if contract.get("canonical_source_split") != "valid":
        raise PromotionPreflightError("canonical source contract references test split")
    contract_relative = str(contract.get("canonical_source_relative_path", ""))
    if _contains_test_split_segment(contract_relative):
        raise PromotionPreflightError("canonical source contract references test split path")
    if contract_relative != relative_source:
        raise PromotionPreflightError("canonical source relative path differs across N1 evidence")

    snapshot_path = root / "canonical_snapshot/canonical_validation_coco.json"
    staged_path = root / "staged/staged_corrected_validation_coco.json"
    snapshot_hash = sha256_file(snapshot_path)
    staged_hash = sha256_file(staged_path)
    gate_source_hash = _require_sha256(
        gate.get("canonical_source_sha256"),
        "N1 canonical source SHA256",
    )
    gate_staged_hash = _require_sha256(
        gate.get("staged_coco_sha256"),
        "N1 staged SHA256",
    )
    contract_source_hash = _require_sha256(
        contract.get("canonical_source_sha256"),
        "canonical source contract SHA256",
    )
    if snapshot_hash != gate_source_hash or snapshot_hash != contract_source_hash:
        raise PromotionPreflightError("N1 canonical source SHA256 evidence mismatch")
    if staged_hash != gate_staged_hash:
        raise PromotionPreflightError("N1 staged SHA256 evidence mismatch")

    mappings = _load_mappings(root / "diff/annotation_correction_mapping.csv")
    if tuple(mapping.native_annotation_id for mapping in mappings) != changed_ids:
        raise PromotionPreflightError("N1 mapping IDs do not match gate changed IDs")
    _verify_required_n1_inventory(root, mappings)

    diff = _require_mapping(
        _read_json(root / "diff/annotation_correction_diff.json", "N1 diff JSON"),
        "N1 diff JSON",
    )
    if _parse_int(diff.get("correction_count"), "N1 diff correction count") != 2:
        raise PromotionPreflightError("N1 diff correction count must be exactly two")
    corrections = diff.get("corrections")
    if not isinstance(corrections, list) or len(corrections) != 2:
        raise PromotionPreflightError("N1 diff must contain exactly two corrections")
    diff_ids: list[int] = []
    for correction in corrections:
        row = _require_mapping(correction, "N1 diff correction")
        if row.get("source_split") != "valid":
            raise PromotionPreflightError("N1 diff references forbidden test split")
        if _require_sha256(row.get("source_coco_sha256"), "diff source SHA256") != snapshot_hash:
            raise PromotionPreflightError("N1 diff source SHA256 mismatch")
        if _require_sha256(row.get("staged_coco_sha256"), "diff staged SHA256") != staged_hash:
            raise PromotionPreflightError("N1 diff staged SHA256 mismatch")
        if tuple(row.get("changed_fields", ())) != ("area", "bbox"):
            raise PromotionPreflightError("N1 diff changed fields must be area and bbox")
        diff_ids.append(_parse_int(row.get("native_coco_annotation_id"), "diff annotation ID"))
    if tuple(diff_ids) != changed_ids:
        raise PromotionPreflightError("N1 diff annotation IDs do not match gate")

    source = load_coco_document(
        CanonicalCocoSource(
            path=snapshot_path,
            relative_path=Path(relative_source),
            size_bytes=snapshot_path.stat().st_size,
            sha256=snapshot_hash,
            split="valid",
        ),
        SourceAccessLedger(),
    )
    staged_payload = _read_json(staged_path, "staged COCO")
    if not isinstance(staged_payload, dict):
        raise PromotionPreflightError("staged COCO root must be an object")
    try:
        validation = validate_staged_coco(
            source,
            staged_payload,
            mappings,
            config.allowed_changed_fields,
            tolerance=config.coordinate_tolerance_pixels,
        )
    except StagedCocoValidationError as exc:
        raise PromotionPreflightError(f"N1 semantic validation failed: {exc}") from exc
    if not validation.passed or validation.changed_annotation_count != 2:
        raise PromotionPreflightError("N1 semantic validation did not PASS")

    semantic_evidence = _require_mapping(
        _read_json(root / "evidence/semantic_validation.json", "semantic validation evidence"),
        "semantic validation evidence",
    )
    if semantic_evidence.get("passed") is not True:
        raise PromotionPreflightError("N1 semantic validation evidence is not PASS")
    if tuple(semantic_evidence.get("changed_annotation_ids", ())) != changed_ids:
        raise PromotionPreflightError("semantic evidence changed IDs mismatch")

    return VerifiedN1Workspace(
        config=config,
        root=root,
        gate_result_path=gate_path,
        gate_result=gate,
        canonical_snapshot_path=snapshot_path,
        canonical_snapshot_sha256=snapshot_hash,
        staged_coco_path=staged_path,
        staged_coco_sha256=staged_hash,
        changed_native_annotation_ids=changed_ids,
        mappings=mappings,
        semantic_validation=validation,
    )


def _run_git(project_root: Path, args: Sequence[str], label: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=project_root,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise PromotionPreflightError(
            f"Git {label} failed ({result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout.rstrip("\r\n")


def _normalize_allowed_prefixes(prefixes: tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in prefixes:
        text = str(value).replace("\\", "/").lstrip("./")
        path = Path(text)
        if not text or path.is_absolute() or path.drive or ".." in path.parts:
            raise PromotionPreflightError(f"invalid allowed worktree prefix: {value}")
        if not text.endswith("/"):
            text += "/"
        normalized.append(text)
    return tuple(normalized)


def _status_paths(output: str) -> tuple[str, ...]:
    paths: list[str] = []
    for line in output.splitlines():
        if not line:
            continue
        if len(line) < 4:
            raise PromotionPreflightError(f"unparseable Git worktree status: {line!r}")
        code = line[:2]
        path = line[3:].replace("\\", "/")
        if "R" in code or "C" in code or " -> " in path:
            raise PromotionPreflightError("Git worktree rename/copy status is not allowed")
        paths.append(path)
    return tuple(paths)


def verify_repository_promotion_state(
    project_root: Path,
    *,
    expected_head: str,
    allowed_status_prefixes: tuple[str, ...],
) -> RepositoryPromotionState:
    root = Path(project_root).resolve()
    if not root.is_dir():
        raise PromotionPreflightError(f"project root does not exist: {root}")
    expected = _require_git_sha(expected_head, "expected repository HEAD")

    branch = _run_git(root, ("branch", "--show-current"), "branch discovery")
    if branch != "main":
        raise PromotionPreflightError(f"repository branch must be main, found: {branch}")

    head = _require_git_sha(
        _run_git(root, ("rev-parse", "HEAD"), "HEAD discovery"),
        "repository HEAD",
    )
    if head != expected:
        raise PromotionPreflightError(
            f"expected repository HEAD mismatch: expected={expected}, actual={head}"
        )

    origin_main = _require_git_sha(
        _run_git(
            root,
            ("rev-parse", "refs/remotes/origin/main"),
            "origin/main discovery",
        ),
        "origin/main",
    )
    if origin_main != head:
        raise PromotionPreflightError(
            f"origin/main disagrees with local HEAD: {origin_main} != {head}"
        )

    remote_output = _run_git(
        root,
        ("ls-remote", "origin", "refs/heads/main"),
        "remote main discovery",
    )
    remote_lines = [line for line in remote_output.splitlines() if line.strip()]
    if len(remote_lines) != 1:
        raise PromotionPreflightError("remote main must resolve to exactly one ref")
    remote_fields = remote_lines[0].split()
    if len(remote_fields) != 2 or remote_fields[1] != "refs/heads/main":
        raise PromotionPreflightError("remote main response is malformed")
    remote_main = _require_git_sha(remote_fields[0], "remote main")
    if remote_main != head:
        raise PromotionPreflightError(
            f"remote main disagrees with local HEAD: {remote_main} != {head}"
        )

    staged_output = _run_git(
        root,
        ("diff", "--cached", "--name-only", "--"),
        "staged index inspection",
    )
    staged_paths = tuple(
        line.replace("\\", "/")
        for line in staged_output.splitlines()
        if line.strip()
    )
    if staged_paths:
        raise PromotionPreflightError(
            f"staged index must be empty before promotion: {staged_paths}"
        )

    status_output = _run_git(
        root,
        ("status", "--porcelain=v1", "--untracked-files=all"),
        "worktree inspection",
    )
    status_paths = _status_paths(status_output)
    prefixes = _normalize_allowed_prefixes(allowed_status_prefixes)
    unexpected = tuple(
        path
        for path in status_paths
        if not any(path.startswith(prefix) for prefix in prefixes)
    )
    if unexpected:
        raise PromotionPreflightError(
            f"repository worktree contains paths outside allowlist: {unexpected}"
        )

    return RepositoryPromotionState(
        project_root=root,
        branch=branch,
        head=head,
        origin_main=origin_main,
        remote_main=remote_main,
        staged_paths=staged_paths,
        allowed_status_paths=tuple(sorted(status_paths)),
    )


def _resolve_dry_run_head(project_root: Path) -> str:
    return _require_git_sha(
        _run_git(project_root, ("rev-parse", "HEAD"), "dry-run HEAD discovery"),
        "repository HEAD",
    )


def prepare_promotion_preflight(
    config: Phase04_5NConfig,
    request: PromotionRequest,
) -> PromotionPreflight:
    project_root = Path(request.project_root).resolve()
    if project_root != config.project_root.resolve():
        raise PromotionPreflightError("promotion request project root differs from config")
    if not _TIMESTAMP_RE.fullmatch(str(request.timestamp)):
        raise PromotionPreflightError("promotion timestamp must match YYYYMMDD_HHMMSSfff")

    if request.execute:
        if request.authorization_phrase != config.n2_authorization_phrase:
            raise PromotionAuthorizationError(
                "execute authorization phrase does not exactly match approved N2 phrase"
            )
        if not str(request.expected_repository_head).strip():
            raise PromotionPreflightError("execute requires expected repository HEAD")
        if not str(request.expected_canonical_sha256).strip():
            raise PromotionPreflightError("execute requires expected canonical SHA256")
        if not str(request.expected_staged_sha256).strip():
            raise PromotionPreflightError("execute requires expected staged SHA256")

    verified_n1 = verify_n1_workspace(config, request.n1_workspace_root)

    # Re-check canonical bytes before Git status evaluation so canonical drift and
    # an already-promoted file produce their specific safety classifications.
    canonical_source = resolve_canonical_validation_coco(config)
    current_hash = canonical_source.sha256
    staged_hash = verified_n1.staged_coco_sha256
    if current_hash == staged_hash:
        raise PromotionPreflightError("current canonical already equals staged SHA256")
    if current_hash != verified_n1.canonical_snapshot_sha256:
        raise PromotionPreflightError(
            "current canonical source SHA256 drifted from verified N1 snapshot"
        )

    expected_canonical = str(request.expected_canonical_sha256).strip()
    if expected_canonical:
        if _require_sha256(expected_canonical, "expected canonical SHA256") != current_hash:
            raise PromotionPreflightError("expected canonical SHA256 does not match current canonical")
    elif request.execute:
        raise PromotionPreflightError("execute requires expected canonical SHA256")

    expected_staged = str(request.expected_staged_sha256).strip()
    if expected_staged:
        if _require_sha256(expected_staged, "expected staged SHA256") != staged_hash:
            raise PromotionPreflightError("expected staged SHA256 does not match verified N1 staged SHA256")
    elif request.execute:
        raise PromotionPreflightError("execute requires expected staged SHA256")

    expected_head = str(request.expected_repository_head).strip()
    if not expected_head:
        expected_head = _resolve_dry_run_head(project_root)
    repository_state = verify_repository_promotion_state(
        project_root,
        expected_head=expected_head,
        allowed_status_prefixes=("outputs/metadata/external_assets/",),
    )

    evidence_root = (
        config.n2_evidence_base_root.resolve()
        / f"{config.n2_evidence_prefix}_{request.timestamp}"
    )
    if evidence_root.exists():
        raise PromotionPreflightError(
            f"promotion evidence workspace already exists: {evidence_root}"
        )

    return PromotionPreflight(
        config=config,
        request=request,
        verified_n1=verified_n1,
        repository_state=repository_state,
        current_canonical_path=canonical_source.path,
        current_canonical_sha256=current_hash,
        staged_coco_path=verified_n1.staged_coco_path,
        staged_coco_sha256=staged_hash,
        evidence_workspace_root=evidence_root,
    )


_FILE_ATTRIBUTE_REPARSE_POINT = 0x400


def _write_bytes_with_fsync(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _write_json_with_fsync(path: Path, payload: Mapping[str, object]) -> None:
    data = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    _write_bytes_with_fsync(path, data)


def _copy_file_with_fsync(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise PromotionExecutionError(f"refusing to overwrite existing file: {destination}")
    shutil.copyfile(source, destination)
    with destination.open("rb+") as handle:
        handle.flush()
        os.fsync(handle.fileno())


def _copy_evidence_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise PromotionExecutionError(f"refusing to overwrite evidence file: {destination}")
    shutil.copyfile(source, destination)
    with destination.open("rb+") as handle:
        handle.flush()
        os.fsync(handle.fileno())


def _write_manifest_file(path: Path, root: Path, members: Sequence[str]) -> None:
    if path.exists():
        raise PromotionExecutionError(f"refusing to overwrite manifest: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=_MANIFEST_FIELDS,
            lineterminator="\n",
        )
        writer.writeheader()
        for relative in sorted(members):
            member = root / relative
            writer.writerow(
                {
                    "relative_path": relative,
                    "size_bytes": member.stat().st_size,
                    "sha256": sha256_file(member),
                }
            )
        handle.flush()
        os.fsync(handle.fileno())


def _finalize_promotion_manifests(root: Path) -> None:
    workspace_manifest = "evidence/workspace_manifest.csv"
    sha_manifest = "evidence/SHA256SUMS.csv"
    files_before = sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
        and path.relative_to(root).as_posix() not in {workspace_manifest, sha_manifest}
    )
    _write_manifest_file(root / workspace_manifest, root, files_before)
    files_with_workspace_manifest = sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.relative_to(root).as_posix() != sha_manifest
    )
    _write_manifest_file(root / sha_manifest, root, files_with_workspace_manifest)


def _remove_promotion_manifests(root: Path) -> None:
    for relative in (
        "evidence/workspace_manifest.csv",
        "evidence/SHA256SUMS.csv",
    ):
        path = root / relative
        if path.exists():
            path.unlink()


def _is_symlink_or_reparse(path: Path) -> bool:
    try:
        stat_result = path.lstat()
    except OSError as exc:
        raise PromotionExecutionError(f"cannot inspect canonical path component: {path}: {exc}") from exc
    attributes = int(getattr(stat_result, "st_file_attributes", 0))
    return path.is_symlink() or bool(attributes & _FILE_ATTRIBUTE_REPARSE_POINT)


def _assert_canonical_path_is_regular(
    config: Phase04_5NConfig,
    canonical_path: Path,
) -> None:
    root = config.project_root.absolute()
    target = canonical_path.absolute()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise PromotionExecutionError(
            f"canonical path escapes project root: {target}"
        ) from exc

    approved = [
        candidate.absolute()
        for candidate in config.canonical_candidates
        if os.path.normcase(str(candidate.absolute()))
        == os.path.normcase(str(target))
    ]
    if len(approved) != 1:
        raise PromotionExecutionError(
            "canonical path is not the single approved configured candidate"
        )

    current = approved[0]
    while True:
        if _is_symlink_or_reparse(current):
            raise PromotionExecutionError(
                f"canonical path contains symlink or reparse point: {current}"
            )
        if current == root:
            break
        if current.parent == current:
            raise PromotionExecutionError("canonical path parent traversal failed")
        current = current.parent

    if not target.is_file():
        raise PromotionExecutionError(f"canonical path is not a regular file: {target}")


def _canonical_source_for_path(
    path: Path,
    *,
    project_root: Path,
    split: str,
) -> CanonicalCocoSource:
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(project_root.resolve())
    except ValueError:
        relative = Path("canonical_snapshot") / resolved.name
    return CanonicalCocoSource(
        path=resolved,
        relative_path=relative,
        size_bytes=resolved.stat().st_size,
        sha256=sha256_file(resolved),
        split=split,
    )


def _promotion_preflight_payload(preflight: PromotionPreflight) -> dict[str, object]:
    return {
        "outcome": "PASS",
        "classification": "PHASE_04_5N_PROMOTION_PREFLIGHT_VALIDATED",
        "execute": preflight.request.execute,
        "repository_head": preflight.repository_state.head,
        "origin_main": preflight.repository_state.origin_main,
        "remote_main": preflight.repository_state.remote_main,
        "canonical_path": str(preflight.current_canonical_path),
        "canonical_before_sha256": preflight.current_canonical_sha256,
        "staged_coco_path": str(preflight.staged_coco_path),
        "staged_coco_sha256": preflight.staged_coco_sha256,
        "n1_workspace_root": str(preflight.verified_n1.root),
        "changed_native_annotation_ids": list(
            preflight.verified_n1.changed_native_annotation_ids
        ),
        "timestamp": preflight.request.timestamp,
        "test_split_read": False,
        "model_inference_executed": False,
        "dataset_materialization_executed": False,
        "registry_modified": False,
        "fixed_splits_modified": False,
        "training_started": False,
        "retraining_status": "NOT_YET_APPROVED",
        "deployment_acceptance": "NOT_YET_APPROVED",
    }


def _promotion_result_payload(
    config: Phase04_5NConfig,
    preflight: PromotionPreflight,
    *,
    backup_path: Path,
    backup_sha256: str,
    after_sha256: str,
) -> dict[str, object]:
    return {
        "OUTCOME": "PASS",
        "CLASSIFICATION": config.n2_gate_classification,
        "PROMOTED_ANNOTATION_COUNT": 2,
        "BACKUP_VERIFIED": "YES",
        "ATOMIC_PROMOTION_VERIFIED": "YES",
        "POST_PROMOTION_SEMANTIC_VALIDATION": "PASS",
        "TEST_SPLIT_READ": "NO",
        "MODEL_INFERENCE_EXECUTED": "NO",
        "DATASET_MATERIALIZATION_EXECUTED": "NO",
        "REGISTRY_MODIFIED": "NO",
        "FIXED_SPLITS_MODIFIED": "NO",
        "TRAINING_STARTED": "NO",
        "RETRAINING_STATUS": "NOT_YET_APPROVED",
        "DEPLOYMENT_ACCEPTANCE": "NOT_YET_APPROVED",
        "repository_head": preflight.repository_state.head,
        "n1_workspace_root": str(preflight.verified_n1.root),
        "canonical_path": str(preflight.current_canonical_path),
        "backup_path": str(backup_path),
        "before_sha256": preflight.current_canonical_sha256,
        "staged_sha256": preflight.staged_coco_sha256,
        "after_sha256": after_sha256,
        "backup_sha256": backup_sha256,
        "changed_native_annotation_ids": list(
            preflight.verified_n1.changed_native_annotation_ids
        ),
        "timestamp": preflight.request.timestamp,
    }


def _write_rollback_payload(
    evidence_root: Path,
    *,
    status: str,
    canonical_path: Path,
    backup_path: Path,
    expected_before_sha256: str,
    restored_sha256: str | None,
    error: str | None,
) -> Path:
    result_path = evidence_root / "evidence/rollback_result.json"
    if result_path.exists():
        result_path.unlink()
    _write_json_with_fsync(
        result_path,
        {
            "status": status,
            "canonical_path": str(canonical_path),
            "backup_path": str(backup_path),
            "expected_before_sha256": expected_before_sha256,
            "restored_sha256": restored_sha256,
            "error": error,
            "test_split_read": False,
            "model_inference_executed": False,
            "dataset_materialization_executed": False,
            "registry_modified": False,
            "fixed_splits_modified": False,
            "training_started": False,
        },
    )
    return result_path


def restore_verified_backup(
    canonical_path: Path,
    backup_path: Path,
    *,
    expected_before_sha256: str,
    evidence_root: Path,
) -> RollbackResult:
    canonical = Path(canonical_path)
    backup = Path(backup_path)
    expected = _require_sha256(expected_before_sha256, "rollback expected before SHA256")
    restore_temp: Path | None = None
    restored_hash: str | None = None
    error_text: str | None = None
    status = "RESTORE_FAILED"

    try:
        if not backup.is_file():
            raise PromotionExecutionError(f"verified backup is missing: {backup}")
        backup_hash = sha256_file(backup)
        if backup_hash != expected:
            raise PromotionExecutionError(
                f"backup SHA256 mismatch during rollback: {backup_hash} != {expected}"
            )

        descriptor, temp_name = tempfile.mkstemp(
            prefix=".phase04_5n_restore_",
            suffix=".tmp",
            dir=canonical.parent,
        )
        os.close(descriptor)
        restore_temp = Path(temp_name)
        restore_temp.unlink()
        _copy_file_with_fsync(backup, restore_temp)
        if sha256_file(restore_temp) != expected:
            raise PromotionExecutionError("rollback temporary file SHA256 mismatch")

        os.replace(restore_temp, canonical)
        restore_temp = None
        restored_hash = sha256_file(canonical)
        if restored_hash != expected:
            raise PromotionExecutionError(
                f"restored canonical SHA256 mismatch: {restored_hash} != {expected}"
            )
        status = "RESTORED_AND_VERIFIED"
    except Exception as exc:  # evidence must record every rollback failure
        error_text = str(exc)
    finally:
        if restore_temp is not None and restore_temp.exists():
            restore_temp.unlink()

    result_path = _write_rollback_payload(
        Path(evidence_root),
        status=status,
        canonical_path=canonical,
        backup_path=backup,
        expected_before_sha256=expected,
        restored_sha256=restored_hash,
        error=error_text,
    )
    return RollbackResult(
        status=status,
        canonical_path=canonical,
        backup_path=backup,
        expected_before_sha256=expected,
        restored_sha256=restored_hash,
        result_path=result_path,
        error=error_text,
    )


def _validate_promoted_canonical(
    config: Phase04_5NConfig,
    preflight: PromotionPreflight,
) -> SemanticValidationResult:
    source = _canonical_source_for_path(
        preflight.verified_n1.canonical_snapshot_path,
        project_root=preflight.verified_n1.root,
        split="valid",
    )
    promoted = _canonical_source_for_path(
        preflight.current_canonical_path,
        project_root=config.project_root,
        split="valid",
    )
    source_document = load_coco_document(source, SourceAccessLedger())
    promoted_document = load_coco_document(promoted, SourceAccessLedger())
    try:
        result = validate_staged_coco(
            source_document,
            promoted_document.payload,
            preflight.verified_n1.mappings,
            config.allowed_changed_fields,
            tolerance=config.coordinate_tolerance_pixels,
        )
    except StagedCocoValidationError as exc:
        raise PromotionExecutionError(
            f"post-promotion semantic validation failed: {exc}"
        ) from exc
    if (
        not result.passed
        or result.changed_annotation_count != 2
        or result.changed_annotation_ids
        != preflight.verified_n1.changed_native_annotation_ids
    ):
        raise PromotionExecutionError(
            "post-promotion semantic validation did not match verified N1 evidence"
        )
    return result


def execute_atomic_promotion(
    config: Phase04_5NConfig,
    preflight: PromotionPreflight,
    *,
    fault_injector: Callable[[str], None] | None = None,
) -> PromotionResult:
    if config != preflight.config:
        raise PromotionExecutionError("promotion config differs from preflight config")
    if not preflight.request.execute:
        raise PromotionExecutionError("atomic promotion requires execute=True preflight")
    if preflight.evidence_workspace_root.exists():
        raise PromotionExecutionError(
            f"promotion evidence workspace already exists: {preflight.evidence_workspace_root}"
        )

    _assert_canonical_path_is_regular(config, preflight.current_canonical_path)
    if sha256_file(preflight.current_canonical_path) != preflight.current_canonical_sha256:
        raise PromotionExecutionError("canonical SHA256 drifted after preflight")
    if sha256_file(preflight.staged_coco_path) != preflight.staged_coco_sha256:
        raise PromotionExecutionError("staged SHA256 drifted after preflight")

    evidence_root = preflight.evidence_workspace_root
    evidence_root.mkdir(parents=True, exist_ok=False)
    for relative in ("source", "backup", "evidence"):
        (evidence_root / relative).mkdir()

    _copy_evidence_file(
        preflight.verified_n1.gate_result_path,
        evidence_root / "source/n1_gate_result.json",
    )
    _copy_evidence_file(
        preflight.verified_n1.root / "evidence/workspace_manifest.csv",
        evidence_root / "source/n1_workspace_manifest.csv",
    )
    _copy_evidence_file(
        preflight.verified_n1.root / "evidence/SHA256SUMS.csv",
        evidence_root / "source/n1_sha256sums.csv",
    )
    _write_json_with_fsync(
        evidence_root / "evidence/preflight.json",
        _promotion_preflight_payload(preflight),
    )

    backup_path = evidence_root / "backup/canonical_validation_coco.before.json"
    promotion_temp: Path | None = None
    replacement_happened = False

    try:
        _copy_file_with_fsync(preflight.current_canonical_path, backup_path)
        if fault_injector is not None:
            fault_injector("after_backup_copy_before_verify")
        backup_hash = sha256_file(backup_path)
        if backup_hash != preflight.current_canonical_sha256:
            raise PromotionExecutionError(
                "backup SHA256 does not equal current canonical before promotion"
            )
        if backup_path.stat().st_size != preflight.current_canonical_path.stat().st_size:
            raise PromotionExecutionError("backup size does not equal current canonical")

        descriptor, temp_name = tempfile.mkstemp(
            prefix=".phase04_5n_promotion_",
            suffix=".tmp",
            dir=preflight.current_canonical_path.parent,
        )
        os.close(descriptor)
        promotion_temp = Path(temp_name)
        promotion_temp.unlink()
        _copy_file_with_fsync(preflight.staged_coco_path, promotion_temp)
        if fault_injector is not None:
            fault_injector("after_temp_copy_before_verify")
        if sha256_file(promotion_temp) != preflight.staged_coco_sha256:
            raise PromotionExecutionError("temporary staged SHA256 mismatch")

        os.replace(promotion_temp, preflight.current_canonical_path)
        promotion_temp = None
        replacement_happened = True
        if fault_injector is not None:
            fault_injector("after_replace_before_postverify")

        after_hash = sha256_file(preflight.current_canonical_path)
        if after_hash != preflight.staged_coco_sha256:
            raise PromotionExecutionError(
                "promoted canonical SHA256 does not equal staged SHA256"
            )
        validation = _validate_promoted_canonical(config, preflight)
        if validation.changed_annotation_count != 2:
            raise PromotionExecutionError(
                "post-promotion changed annotation count is not exactly two"
            )

        result_path = evidence_root / "evidence/promotion_result.json"
        _write_json_with_fsync(
            result_path,
            _promotion_result_payload(
                config,
                preflight,
                backup_path=backup_path,
                backup_sha256=backup_hash,
                after_sha256=after_hash,
            ),
        )
        _finalize_promotion_manifests(evidence_root)

        return PromotionResult(
            classification=config.n2_gate_classification,
            canonical_path=preflight.current_canonical_path,
            backup_path=backup_path,
            evidence_workspace_root=evidence_root,
            result_path=result_path,
            before_sha256=preflight.current_canonical_sha256,
            staged_sha256=preflight.staged_coco_sha256,
            after_sha256=after_hash,
            backup_sha256=backup_hash,
            promoted_annotation_count=2,
            changed_native_annotation_ids=(
                preflight.verified_n1.changed_native_annotation_ids
            ),
            backup_verified=True,
            atomic_promotion_verified=True,
            post_promotion_semantic_validation="PASS",
        )
    except Exception as exc:
        if promotion_temp is not None and promotion_temp.exists():
            promotion_temp.unlink()
        if replacement_happened:
            rollback = restore_verified_backup(
                preflight.current_canonical_path,
                backup_path,
                expected_before_sha256=preflight.current_canonical_sha256,
                evidence_root=evidence_root,
            )
            _remove_promotion_manifests(evidence_root)
            _finalize_promotion_manifests(evidence_root)
            if rollback.status == "RESTORED_AND_VERIFIED":
                raise PromotionExecutionError(
                    f"atomic promotion failed after replacement; original canonical restored and verified: {exc}"
                ) from exc
            raise PromotionExecutionError(
                f"atomic promotion failed after replacement and restore failed: {exc}; rollback={rollback.error}"
            ) from exc

        _remove_promotion_manifests(evidence_root)
        _finalize_promotion_manifests(evidence_root)
        if isinstance(exc, PromotionExecutionError):
            raise
        raise PromotionExecutionError(f"atomic promotion failed before replacement: {exc}") from exc
