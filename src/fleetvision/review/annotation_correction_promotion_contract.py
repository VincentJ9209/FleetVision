
from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml


class PromotionContractError(ValueError):
    """Raised when Phase 04.5N evidence violates its approved contract."""


@dataclass(frozen=True)
class ExpectedReviewedProposal:
    review_case_id: str
    correction_case_id: str
    image_id: str
    source_split: str
    operation: str
    target_gt_bbox_ids: tuple[str, ...]
    proposal_fingerprint: str


@dataclass(frozen=True)
class Phase04_5NConfig:
    project_root: Path
    expected_classification: str
    expected_review_cases: int
    expected_reviewed: int
    expected_pending: int
    expected_needs_adjudication: int
    required_export_files: tuple[Path, ...]
    expected_proposals: tuple[ExpectedReviewedProposal, ...]
    canonical_candidates: tuple[Path, ...]
    required_split: str
    required_category_name: str
    coordinate_tolerance_pixels: float
    allowed_changed_fields: tuple[str, ...]
    n1_workspace_base_root: Path
    n1_workspace_prefix: str
    n1_gate_classification: str
    staged_coco_name: str
    n2_evidence_base_root: Path
    n2_evidence_prefix: str
    n2_authorization_phrase: str
    n2_gate_classification: str


@dataclass(frozen=True)
class ReviewedProposal:
    review_case_id: str
    correction_case_id: str
    image_id: str
    source_split: str
    source_case_fingerprint: str
    source_gt_bbox_records_json: str
    correction_operation: str
    target_gt_bbox_ids_json: str
    replacement_bbox_coordinates_json: str
    proposal_fingerprint: str


@dataclass(frozen=True)
class VerifiedCompletedReview:
    workspace_root: Path
    proposals: tuple[ReviewedProposal, ...]
    review_case_ids: tuple[str, ...]
    proposal_fingerprints: tuple[str, ...]
    source_manifest_sha256: str
    export_manifest_sha256: str
    export_result_sha256: str


@dataclass(frozen=True)
class CanonicalCocoSource:
    path: Path
    relative_path: Path
    size_bytes: int
    sha256: str
    split: str


@dataclass(frozen=True)
class CocoDocument:
    payload: dict[str, object]
    images_by_id: dict[int, dict[str, object]]
    images_by_file_name: dict[str, dict[str, object]]
    annotations_by_id: dict[int, dict[str, object]]
    categories_by_id: dict[int, dict[str, object]]


class SourceAccessLedger:
    """Records approved source reads and rejects every non-valid split."""

    def __init__(self) -> None:
        self._records: list[tuple[Path, str]] = []

    def record(self, path: Path, split: str) -> None:
        normalized_split = str(split).strip().lower()
        if normalized_split != "valid":
            raise PromotionContractError(
                f"SourceAccessLedger rejected non-valid split: {split!r}"
            )
        normalized = Path(path).resolve()
        if "test" in {part.lower() for part in normalized.parts}:
            raise PromotionContractError(
                f"SourceAccessLedger rejected test split path: {normalized}"
            )
        self._records.append((normalized, normalized_split))

    @property
    def paths(self) -> tuple[Path, ...]:
        return tuple(path for path, _split in self._records)

    @property
    def test_split_read(self) -> bool:
        return any(
            split == "test" or "test" in {part.lower() for part in path.parts}
            for path, split in self._records
        )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _require_mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PromotionContractError(f"{label} must be a mapping")
    return value


def _require_sequence(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise PromotionContractError(f"{label} must be a list")
    return value


def _safe_relative_path(value: object, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise PromotionContractError(f"{label} must be a non-empty relative path")
    path = Path(value)
    if path.is_absolute() or path.drive or ".." in path.parts:
        raise PromotionContractError(f"{label} must remain relative to the approved root")
    return path


def _resolve_beneath(base: Path, relative: Path, label: str) -> Path:
    base_resolved = Path(base).resolve()
    candidate = (base_resolved / relative).resolve()
    try:
        candidate.relative_to(base_resolved)
    except ValueError as exc:
        raise PromotionContractError(
            f"{label} escapes approved root: {relative.as_posix()}"
        ) from exc
    return candidate


def _parse_int(mapping: Mapping[str, Any], key: str, label: str) -> int:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise PromotionContractError(f"{label}.{key} must be an integer")
    return value


def load_phase04_5n_config(
    config_path: Path,
    project_root: Path,
) -> Phase04_5NConfig:
    config_file = Path(config_path).resolve()
    root = Path(project_root).resolve()
    if not config_file.is_file():
        raise PromotionContractError(f"config file does not exist: {config_file}")

    raw = yaml.safe_load(config_file.read_text(encoding="utf-8"))
    top = _require_mapping(raw, "config")
    if str(top.get("schema_version")) != "1":
        raise PromotionContractError("config schema_version must be '1'")

    predecessor = _require_mapping(top.get("predecessor"), "predecessor")
    canonical = _require_mapping(top.get("canonical_source"), "canonical_source")
    n1 = _require_mapping(top.get("n1"), "n1")
    n2 = _require_mapping(top.get("n2"), "n2")
    safety = _require_mapping(top.get("safety"), "safety")

    required_export_files = tuple(
        _safe_relative_path(item, "predecessor.required_export_files")
        for item in _require_sequence(
            predecessor.get("required_export_files"),
            "predecessor.required_export_files",
        )
    )

    expected_proposals: list[ExpectedReviewedProposal] = []
    for index, item in enumerate(
        _require_sequence(
            predecessor.get("expected_proposals"),
            "predecessor.expected_proposals",
        )
    ):
        proposal = _require_mapping(item, f"expected_proposals[{index}]")
        target_ids = tuple(
            str(value)
            for value in _require_sequence(
                proposal.get("target_gt_bbox_ids"),
                f"expected_proposals[{index}].target_gt_bbox_ids",
            )
        )
        expected_proposals.append(
            ExpectedReviewedProposal(
                review_case_id=str(proposal.get("review_case_id", "")),
                correction_case_id=str(proposal.get("correction_case_id", "")),
                image_id=str(proposal.get("image_id", "")),
                source_split=str(proposal.get("source_split", "")),
                operation=str(proposal.get("operation", "")),
                target_gt_bbox_ids=target_ids,
                proposal_fingerprint=str(proposal.get("proposal_fingerprint", "")),
            )
        )

    raw_candidates = _require_sequence(
        canonical.get("approved_candidates"),
        "canonical_source.approved_candidates",
    )
    canonical_candidates: list[Path] = []
    for index, item in enumerate(raw_candidates):
        relative = _safe_relative_path(
            item,
            f"canonical_source.approved_candidates[{index}]",
        )
        candidate = _resolve_beneath(
            root,
            relative,
            f"canonical_source.approved_candidates[{index}]",
        )
        canonical_candidates.append(candidate)

    required_split = str(canonical.get("required_split", ""))
    if required_split != "valid":
        raise PromotionContractError("canonical required_split must be valid")
    required_category_name = str(canonical.get("required_category_name", ""))
    if required_category_name != "damage":
        raise PromotionContractError("canonical required_category_name must be damage")

    for key in (
        "test_split_read",
        "model_inference_executed",
        "dataset_materialization_executed",
        "registry_modified",
        "fixed_splits_modified",
        "training_started",
    ):
        if safety.get(key) is not False:
            raise PromotionContractError(f"safety.{key} must be false")
    if safety.get("retraining_status") != "NOT_YET_APPROVED":
        raise PromotionContractError("safety.retraining_status must be NOT_YET_APPROVED")
    if safety.get("deployment_acceptance") != "NOT_YET_APPROVED":
        raise PromotionContractError(
            "safety.deployment_acceptance must be NOT_YET_APPROVED"
        )

    return Phase04_5NConfig(
        project_root=root,
        expected_classification=str(predecessor.get("expected_classification", "")),
        expected_review_cases=_parse_int(
            predecessor, "expected_review_cases", "predecessor"
        ),
        expected_reviewed=_parse_int(predecessor, "expected_reviewed", "predecessor"),
        expected_pending=_parse_int(predecessor, "expected_pending", "predecessor"),
        expected_needs_adjudication=_parse_int(
            predecessor,
            "expected_needs_adjudication",
            "predecessor",
        ),
        required_export_files=required_export_files,
        expected_proposals=tuple(expected_proposals),
        canonical_candidates=tuple(canonical_candidates),
        required_split=required_split,
        required_category_name=required_category_name,
        coordinate_tolerance_pixels=float(
            canonical.get("coordinate_tolerance_pixels")
        ),
        allowed_changed_fields=tuple(
            str(value)
            for value in _require_sequence(
                canonical.get("allowed_changed_fields"),
                "canonical_source.allowed_changed_fields",
            )
        ),
        n1_workspace_base_root=Path(str(n1.get("workspace_base_root", ""))),
        n1_workspace_prefix=str(n1.get("workspace_prefix", "")),
        n1_gate_classification=str(n1.get("gate_classification", "")),
        staged_coco_name=str(n1.get("staged_coco_name", "")),
        n2_evidence_base_root=Path(str(n2.get("evidence_base_root", ""))),
        n2_evidence_prefix=str(n2.get("evidence_prefix", "")),
        n2_authorization_phrase=str(n2.get("authorization_phrase", "")),
        n2_gate_classification=str(n2.get("gate_classification", "")),
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except (OSError, csv.Error) as exc:
        raise PromotionContractError(f"cannot read CSV {path}: {exc}") from exc


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PromotionContractError(f"cannot read JSON {path}: {exc}") from exc


def _verify_manifest(
    manifest_path: Path,
    base_root: Path,
    *,
    required_members: Iterable[str],
) -> dict[str, Path]:
    rows = _read_csv(manifest_path)
    if not rows:
        raise PromotionContractError(f"manifest is empty: {manifest_path}")
    members: dict[str, Path] = {}
    for row_index, row in enumerate(rows, start=2):
        relative_text = (row.get("relative_path") or "").replace("\\", "/")
        relative = _safe_relative_path(
            relative_text,
            f"{manifest_path.name} row {row_index} relative_path",
        )
        normalized = relative.as_posix()
        if normalized in members:
            raise PromotionContractError(
                f"duplicate manifest member: {normalized}"
            )
        member = _resolve_beneath(
            base_root,
            relative,
            f"{manifest_path.name} manifest member",
        )
        if not member.is_file():
            raise PromotionContractError(f"missing manifest member: {normalized}")
        try:
            expected_size = int(row.get("size_bytes") or "")
        except ValueError as exc:
            raise PromotionContractError(
                f"invalid size for manifest member: {normalized}"
            ) from exc
        actual_size = member.stat().st_size
        if actual_size != expected_size:
            raise PromotionContractError(
                f"size mismatch for manifest member {normalized}: "
                f"expected {expected_size}, got {actual_size}"
            )
        expected_sha = (row.get("sha256") or "").upper()
        actual_sha = sha256_file(member)
        if actual_sha != expected_sha:
            raise PromotionContractError(
                f"sha256 mismatch for manifest member {normalized}"
            )
        members[normalized] = member

    missing = sorted(set(required_members) - set(members))
    if missing:
        raise PromotionContractError(
            "missing required manifest member(s): " + ", ".join(missing)
        )
    return members


def _normalize_json_row(row: Mapping[str, Any]) -> dict[str, str]:
    return {str(key): str(value) for key, value in row.items()}


def _require_gate_value(
    result: Mapping[str, Any],
    key: str,
    expected: Any,
) -> None:
    actual = result.get(key)
    if actual != expected:
        raise PromotionContractError(
            f"completed export {key} mismatch: expected {expected!r}, got {actual!r}"
        )


def verify_completed_review_workspace(
    config: Phase04_5NConfig,
    workspace_root: Path,
) -> VerifiedCompletedReview:
    root = Path(workspace_root).resolve()
    if not root.is_dir():
        raise PromotionContractError(f"completed review workspace is missing: {root}")

    resolved_required: dict[str, Path] = {}
    for relative in config.required_export_files:
        path = _resolve_beneath(root, relative, "required predecessor file")
        if not path.is_file():
            raise PromotionContractError(
                f"required predecessor file is missing: {relative.as_posix()}"
            )
        resolved_required[relative.as_posix()] = path

    exports_root = root / "exports"
    export_manifest = resolved_required["exports/SHA256SUMS.csv"]
    export_required_members = [
        relative.relative_to("exports").as_posix()
        for relative in config.required_export_files
        if relative.parts[0] == "exports" and relative.name != "SHA256SUMS.csv"
    ]
    _verify_manifest(
        export_manifest,
        exports_root,
        required_members=export_required_members,
    )

    source_manifest = resolved_required["source/source_manifest.csv"]
    source_rows = _read_csv(resolved_required["source/correction_review_source.csv"])
    source_required_members = {
        "source/source_contract.json",
        "source/correction_review_source.csv",
    }
    for row in source_rows:
        original_relpath = str(row.get("original_image_relpath", "")).replace("\\", "/")
        if not original_relpath:
            raise PromotionContractError("source row missing original_image_relpath")
        source_required_members.add(original_relpath)
    _verify_manifest(
        source_manifest,
        root,
        required_members=sorted(source_required_members),
    )

    result_path = resolved_required["exports/correction_review_export_result.json"]
    result = _require_mapping(_read_json(result_path), "completed export result")
    _require_gate_value(result, "outcome", "PASS")
    _require_gate_value(result, "classification", config.expected_classification)
    _require_gate_value(result, "review_cases", config.expected_review_cases)
    _require_gate_value(result, "reviewed", config.expected_reviewed)
    _require_gate_value(result, "pending", config.expected_pending)
    _require_gate_value(
        result,
        "needs_adjudication",
        config.expected_needs_adjudication,
    )
    for key in (
        "test_split_read",
        "model_inference_executed",
        "canonical_annotation_modified",
        "canonical_coco_modified",
        "dataset_modified",
        "registry_modified",
        "fixed_splits_modified",
        "training_started",
    ):
        _require_gate_value(result, key, False)
    _require_gate_value(result, "retraining_status", "NOT_YET_APPROVED")
    _require_gate_value(result, "deployment_acceptance", "NOT_YET_APPROVED")

    csv_rows = _read_csv(
        resolved_required["exports/annotation_correction_proposals_reviewed.csv"]
    )
    json_payload = _require_mapping(
        _read_json(
            resolved_required["exports/annotation_correction_proposals_reviewed.json"]
        ),
        "reviewed proposal JSON",
    )
    json_rows_raw = _require_sequence(
        json_payload.get("proposals"),
        "reviewed proposal JSON proposals",
    )
    if json_payload.get("proposal_count") != len(json_rows_raw):
        raise PromotionContractError("reviewed proposal JSON proposal_count mismatch")
    json_rows = [
        _normalize_json_row(_require_mapping(row, "reviewed proposal JSON row"))
        for row in json_rows_raw
    ]
    normalized_csv_rows = [_normalize_json_row(row) for row in csv_rows]
    if normalized_csv_rows != json_rows:
        raise PromotionContractError("reviewed CSV and JSON semantic identity mismatch")

    if len(csv_rows) != config.expected_review_cases:
        raise PromotionContractError(
            f"reviewed proposal count mismatch: {len(csv_rows)}"
        )
    fingerprints = [row.get("proposal_fingerprint", "") for row in csv_rows]
    if len(set(fingerprints)) != len(fingerprints):
        raise PromotionContractError("duplicate proposal fingerprint")

    actual_order = tuple(row.get("review_case_id", "") for row in csv_rows)
    expected_order = tuple(item.review_case_id for item in config.expected_proposals)
    if actual_order != expected_order:
        raise PromotionContractError(
            f"proposal order mismatch: expected {expected_order}, got {actual_order}"
        )

    source_by_case: dict[str, dict[str, str]] = {}
    for source_row in source_rows:
        case_id = source_row.get("review_case_id", "")
        if not case_id or case_id in source_by_case:
            raise PromotionContractError(
                f"duplicate or missing source review_case_id: {case_id!r}"
            )
        source_by_case[case_id] = source_row

    source_contract = _require_mapping(
        _read_json(resolved_required["source/source_contract.json"]),
        "source contract",
    )
    if tuple(source_contract.get("review_case_ids", [])) != expected_order:
        raise PromotionContractError("source contract review_case_ids order mismatch")

    proposals: list[ReviewedProposal] = []
    for index, (row, expected) in enumerate(
        zip(csv_rows, config.expected_proposals, strict=True)
    ):
        target_ids_raw = row.get("target_gt_bbox_ids_json", "")
        try:
            target_ids_value = json.loads(target_ids_raw)
        except json.JSONDecodeError as exc:
            raise PromotionContractError(
                f"proposal[{index}] target_gt_bbox_ids_json is invalid"
            ) from exc
        if not isinstance(target_ids_value, list):
            raise PromotionContractError(
                f"proposal[{index}] target_gt_bbox_ids_json must be a list"
            )

        checks = {
            "review_case_id": expected.review_case_id,
            "correction_case_id": expected.correction_case_id,
            "image_id": expected.image_id,
            "source_split": expected.source_split,
            "correction_operation": expected.operation,
            "proposal_fingerprint": expected.proposal_fingerprint,
        }
        for field, expected_value in checks.items():
            actual_value = row.get(field)
            if actual_value != expected_value:
                raise PromotionContractError(
                    f"proposal[{index}] {field} mismatch: "
                    f"expected {expected_value!r}, got {actual_value!r}"
                )
        if tuple(str(value) for value in target_ids_value) != expected.target_gt_bbox_ids:
            raise PromotionContractError(
                f"proposal[{index}] target bbox IDs mismatch"
            )
        if row.get("correction_review_status") != "reviewed":
            raise PromotionContractError(
                f"proposal[{index}] correction_review_status is not reviewed"
            )
        if row.get("source_split") != "valid":
            raise PromotionContractError(
                f"proposal[{index}] source_split must be valid"
            )

        source_row = source_by_case.get(expected.review_case_id)
        if source_row is None:
            raise PromotionContractError(
                f"missing source row for {expected.review_case_id}"
            )
        source_checks = {
            "correction_case_id": row.get("correction_case_id"),
            "image_id": row.get("image_id"),
            "source_split": row.get("source_split"),
            "source_case_fingerprint": row.get("source_case_fingerprint"),
            "gt_bbox_records_json": row.get("source_gt_bbox_records_json"),
        }
        for source_field, expected_value in source_checks.items():
            actual_value = source_row.get(source_field)
            if actual_value != expected_value:
                raise PromotionContractError(
                    f"source {source_field} mismatch for {expected.review_case_id}"
                )

        proposals.append(
            ReviewedProposal(
                review_case_id=expected.review_case_id,
                correction_case_id=expected.correction_case_id,
                image_id=expected.image_id,
                source_split=expected.source_split,
                source_case_fingerprint=str(row.get("source_case_fingerprint", "")),
                source_gt_bbox_records_json=str(
                    row.get("source_gt_bbox_records_json", "")
                ),
                correction_operation=expected.operation,
                target_gt_bbox_ids_json=target_ids_raw,
                replacement_bbox_coordinates_json=str(
                    row.get("replacement_bbox_coordinates_json", "")
                ),
                proposal_fingerprint=expected.proposal_fingerprint,
            )
        )

    return VerifiedCompletedReview(
        workspace_root=root,
        proposals=tuple(proposals),
        review_case_ids=actual_order,
        proposal_fingerprints=tuple(fingerprints),
        source_manifest_sha256=sha256_file(source_manifest),
        export_manifest_sha256=sha256_file(export_manifest),
        export_result_sha256=sha256_file(result_path),
    )


def resolve_canonical_validation_coco(
    config: Phase04_5NConfig,
) -> CanonicalCocoSource:
    existing = [candidate for candidate in config.canonical_candidates if candidate.is_file()]
    if len(existing) != 1:
        raise PromotionContractError(
            "canonical source resolution requires exactly one existing approved candidate; "
            f"found {len(existing)}"
        )
    source = existing[0].resolve()
    try:
        relative = source.relative_to(config.project_root.resolve())
    except ValueError as exc:
        raise PromotionContractError(
            f"canonical source is outside project root: {source}"
        ) from exc

    lower_parts = {part.lower() for part in relative.parts}
    if config.required_split not in lower_parts or "test" in lower_parts:
        raise PromotionContractError(
            f"canonical source path is not approved valid split: {relative.as_posix()}"
        )
    return CanonicalCocoSource(
        path=source,
        relative_path=relative,
        size_bytes=source.stat().st_size,
        sha256=sha256_file(source),
        split=config.required_split,
    )


def _unique_int_id(
    item: Mapping[str, Any],
    label: str,
    seen: set[int],
) -> int:
    value = item.get("id")
    if isinstance(value, bool) or not isinstance(value, int):
        raise PromotionContractError(f"{label} id must be an integer")
    if value in seen:
        raise PromotionContractError(f"duplicate {label} id: {value}")
    seen.add(value)
    return value


def load_coco_document(
    source: CanonicalCocoSource,
    ledger: SourceAccessLedger,
) -> CocoDocument:
    if source.path.stat().st_size != source.size_bytes:
        raise PromotionContractError("canonical source size changed before read")
    if sha256_file(source.path) != source.sha256:
        raise PromotionContractError("canonical source sha256 changed before read")
    ledger.record(source.path, source.split)

    payload_raw = _read_json(source.path)
    payload = dict(_require_mapping(payload_raw, "COCO root"))
    images = _require_sequence(payload.get("images"), "images")
    annotations = _require_sequence(payload.get("annotations"), "annotations")
    categories = _require_sequence(payload.get("categories"), "categories")

    image_ids: set[int] = set()
    annotation_ids: set[int] = set()
    category_ids: set[int] = set()
    file_names: set[str] = set()
    images_by_id: dict[int, dict[str, object]] = {}
    images_by_file_name: dict[str, dict[str, object]] = {}
    annotations_by_id: dict[int, dict[str, object]] = {}
    categories_by_id: dict[int, dict[str, object]] = {}

    for raw_image in images:
        image = dict(_require_mapping(raw_image, "image"))
        image_id = _unique_int_id(image, "image", image_ids)
        file_name = image.get("file_name")
        if not isinstance(file_name, str) or not file_name:
            raise PromotionContractError(f"image {image_id} file_name is invalid")
        if file_name in file_names:
            raise PromotionContractError(f"duplicate image file_name: {file_name}")
        file_names.add(file_name)
        width = image.get("width")
        height = image.get("height")
        if (
            isinstance(width, bool)
            or isinstance(height, bool)
            or not isinstance(width, int)
            or not isinstance(height, int)
            or width <= 0
            or height <= 0
        ):
            raise PromotionContractError(
                f"image {image_id} dimensions must be positive integers"
            )
        images_by_id[image_id] = image
        images_by_file_name[file_name] = image

    for raw_category in categories:
        category = dict(_require_mapping(raw_category, "category"))
        category_id = _unique_int_id(category, "category", category_ids)
        categories_by_id[category_id] = category
    category_names = [category.get("name") for category in categories_by_id.values()]
    if len(category_names) != 1 or category_names != ["damage"]:
        raise PromotionContractError(
            f"COCO category contract must be exactly ['damage']; got {category_names!r}"
        )

    for raw_annotation in annotations:
        annotation = dict(_require_mapping(raw_annotation, "annotation"))
        annotation_id = _unique_int_id(annotation, "annotation", annotation_ids)
        image_id = annotation.get("image_id")
        category_id = annotation.get("category_id")
        if image_id not in images_by_id:
            raise PromotionContractError(
                f"annotation {annotation_id} references missing image {image_id!r}"
            )
        if category_id not in categories_by_id:
            raise PromotionContractError(
                f"annotation {annotation_id} references missing category {category_id!r}"
            )
        annotations_by_id[annotation_id] = annotation

    return CocoDocument(
        payload=payload,
        images_by_id=images_by_id,
        images_by_file_name=images_by_file_name,
        annotations_by_id=annotations_by_id,
        categories_by_id=categories_by_id,
    )
