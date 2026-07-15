from __future__ import annotations

import copy
import csv
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path

import pytest

import fleetvision.review.annotation_correction_staging as staging_module

from annotation_correction_promotion_fixtures import build_phase04_5n_fixture
from fleetvision.review.annotation_correction_promotion_contract import (
    CocoDocument,
    canonical_json_bytes,
    Phase04_5NConfig,
    ReviewedProposal,
    SourceAccessLedger,
    load_coco_document,
    load_phase04_5n_config,
    resolve_canonical_validation_coco,
    verify_completed_review_workspace,
)
from fleetvision.review.annotation_correction_staging import (
    AbsoluteXYXY,
    AnnotationMappingError,
    CocoXYWH,
    apply_reviewed_geometry,
    map_reviewed_proposal_to_native_annotation,
    parse_local_gt_records,
    parse_replacement_bbox,
    require_distinct_native_annotation_mappings,
    build_diff_rows,
    build_staged_coco,
    normalized_json_value,
    validate_staged_coco,
    StagedCocoValidationError,
    xyxy_to_coco_xywh,
)


@dataclass(frozen=True)
class VerifiedMappingInputs:
    config: Phase04_5NConfig
    coco: CocoDocument
    proposals: tuple[ReviewedProposal, ...]
    source_rows: tuple[dict[str, str], ...]

    @property
    def first(self) -> tuple[ReviewedProposal, dict[str, str], CocoDocument, Phase04_5NConfig]:
        return self.proposals[0], self.source_rows[0], self.coco, self.config

    @property
    def second(self) -> tuple[ReviewedProposal, dict[str, str], CocoDocument, Phase04_5NConfig]:
        return self.proposals[1], self.source_rows[1], self.coco, self.config


@pytest.fixture
def phase04_5n_verified_inputs(tmp_path: Path) -> VerifiedMappingInputs:
    fixture = build_phase04_5n_fixture(tmp_path)
    config = load_phase04_5n_config(fixture.config_path, fixture.project_root)
    verified = verify_completed_review_workspace(config, fixture.completed_review_root)
    source = resolve_canonical_validation_coco(config)
    coco = load_coco_document(source, SourceAccessLedger())
    with (fixture.completed_review_root / "source/correction_review_source.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        source_rows = tuple(csv.DictReader(handle))
    return VerifiedMappingInputs(
        config=config,
        coco=coco,
        proposals=verified.proposals,
        source_rows=source_rows,
    )


def _replace_proposal(proposal: ReviewedProposal, **changes: str) -> ReviewedProposal:
    values = {
        "review_case_id": proposal.review_case_id,
        "correction_case_id": proposal.correction_case_id,
        "image_id": proposal.image_id,
        "source_split": proposal.source_split,
        "source_case_fingerprint": proposal.source_case_fingerprint,
        "source_gt_bbox_records_json": proposal.source_gt_bbox_records_json,
        "correction_operation": proposal.correction_operation,
        "target_gt_bbox_ids_json": proposal.target_gt_bbox_ids_json,
        "replacement_bbox_coordinates_json": proposal.replacement_bbox_coordinates_json,
        "proposal_fingerprint": proposal.proposal_fingerprint,
    }
    values.update(changes)
    return ReviewedProposal(**values)


def test_xyxy_to_xywh_and_area() -> None:
    box = AbsoluteXYXY(x1=74.2, y1=192.4, x2=285.65, y2=579.75)
    xywh = xyxy_to_coco_xywh(box)
    assert xywh.x == pytest.approx(74.2)
    assert xywh.y == pytest.approx(192.4)
    assert xywh.width == pytest.approx(211.45)
    assert xywh.height == pytest.approx(387.35)
    assert xywh.area == pytest.approx(81905.1575)


def test_local_gt_id_maps_to_unique_native_annotation(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    proposal, source_row, coco, config = phase04_5n_verified_inputs.first
    mapping = map_reviewed_proposal_to_native_annotation(
        proposal,
        source_row,
        coco,
        tolerance=config.coordinate_tolerance_pixels,
    )
    assert mapping.local_gt_bbox_id == "gt_001"
    assert mapping.native_annotation_id == 101
    assert mapping.native_image_id == 11
    assert mapping.before_bbox_xywh == pytest.approx((68.0, 334.0, 150.71, 188.466))
    assert mapping.after_bbox_xyxy == pytest.approx((74.2, 192.4, 285.65, 579.75))


def test_second_proposal_maps_to_distinct_native_annotation(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    first = map_reviewed_proposal_to_native_annotation(
        *phase04_5n_verified_inputs.first[:3],
        tolerance=phase04_5n_verified_inputs.config.coordinate_tolerance_pixels,
    )
    second = map_reviewed_proposal_to_native_annotation(
        *phase04_5n_verified_inputs.second[:3],
        tolerance=phase04_5n_verified_inputs.config.coordinate_tolerance_pixels,
    )
    assert first.native_annotation_id == 101
    assert second.native_annotation_id == 202
    assert first.native_annotation_id != second.native_annotation_id


def test_mapping_rejects_missing_native_match(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    proposal, source_row, coco, config = phase04_5n_verified_inputs.first
    coco.annotations_by_id[101]["bbox"][0] += 1.0
    with pytest.raises(AnnotationMappingError, match="zero native"):
        map_reviewed_proposal_to_native_annotation(
            proposal, source_row, coco, tolerance=config.coordinate_tolerance_pixels
        )


def test_mapping_rejects_ambiguous_native_match(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    proposal, source_row, coco, config = phase04_5n_verified_inputs.first
    duplicate = dict(coco.annotations_by_id[101])
    duplicate["id"] = 999
    coco.annotations_by_id[999] = duplicate
    with pytest.raises(AnnotationMappingError, match="multiple native"):
        map_reviewed_proposal_to_native_annotation(
            proposal, source_row, coco, tolerance=config.coordinate_tolerance_pixels
        )


def test_apply_geometry_preserves_every_non_geometry_field() -> None:
    annotation = {
        "id": 101,
        "image_id": 11,
        "category_id": 1,
        "bbox": [68.0, 334.0, 150.71, 188.466],
        "area": 28403.67,
        "segmentation": [[1.0, 2.0, 3.0, 4.0]],
        "iscrowd": 0,
        "custom": {"nested": ["preserve-me"]},
    }
    changed = apply_reviewed_geometry(
        annotation,
        AbsoluteXYXY(74.2, 192.4, 285.65, 579.75),
    )
    assert changed["id"] == 101
    assert changed["image_id"] == 11
    assert changed["category_id"] == 1
    assert changed["segmentation"] == annotation["segmentation"]
    assert changed["iscrowd"] == 0
    assert changed["custom"] == annotation["custom"]
    assert changed["custom"] is not annotation["custom"]
    assert changed["bbox"] == pytest.approx([74.2, 192.4, 211.45, 387.35])
    assert changed["area"] == pytest.approx(81905.1575)


@pytest.mark.parametrize(
    "payload",
    [
        '{"x1":0,"y1":0,"x2":NaN,"y2":10}',
        '{"x1":0,"y1":0,"x2":Infinity,"y2":10}',
        '{"x1":0,"y1":0,"x2":10}',
        '{"x1":0,"y1":0,"x2":10,"y2":10,"extra":1}',
    ],
)
def test_replacement_parser_rejects_non_finite_or_wrong_keys(payload: str) -> None:
    with pytest.raises(AnnotationMappingError):
        parse_replacement_bbox(payload)


@pytest.mark.parametrize(
    "box",
    [
        AbsoluteXYXY(10.0, 10.0, 10.0, 20.0),
        AbsoluteXYXY(10.0, 10.0, 9.0, 20.0),
        AbsoluteXYXY(10.0, 10.0, 20.0, 10.0),
        AbsoluteXYXY(10.0, 10.0, 20.0, 9.0),
    ],
)
def test_xyxy_rejects_zero_or_negative_width_height(box: AbsoluteXYXY) -> None:
    with pytest.raises(AnnotationMappingError, match="positive"):
        xyxy_to_coco_xywh(box)


def test_mapping_rejects_out_of_bounds_replacement(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    proposal, source_row, coco, config = phase04_5n_verified_inputs.first
    proposal = _replace_proposal(
        proposal,
        replacement_bbox_coordinates_json='{"x1":0,"y1":0,"x2":641,"y2":20}',
    )
    with pytest.raises(AnnotationMappingError, match="bounds"):
        map_reviewed_proposal_to_native_annotation(
            proposal, source_row, coco, tolerance=config.coordinate_tolerance_pixels
        )


def test_mapping_rejects_unknown_local_target_id(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    proposal, source_row, coco, config = phase04_5n_verified_inputs.first
    proposal = _replace_proposal(proposal, target_gt_bbox_ids_json='["gt_999"]')
    with pytest.raises(AnnotationMappingError, match="unknown local"):
        map_reviewed_proposal_to_native_annotation(
            proposal, source_row, coco, tolerance=config.coordinate_tolerance_pixels
        )


def test_mapping_rejects_multiple_local_target_ids(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    proposal, source_row, coco, config = phase04_5n_verified_inputs.first
    proposal = _replace_proposal(
        proposal, target_gt_bbox_ids_json='["gt_001","gt_002"]'
    )
    with pytest.raises(AnnotationMappingError, match="exactly one"):
        map_reviewed_proposal_to_native_annotation(
            proposal, source_row, coco, tolerance=config.coordinate_tolerance_pixels
        )


def test_mapping_rejects_non_resize_operation(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    proposal, source_row, coco, config = phase04_5n_verified_inputs.first
    proposal = _replace_proposal(proposal, correction_operation="REMOVE_DUPLICATE_BBOX")
    with pytest.raises(AnnotationMappingError, match="RESIZE_OR_REDRAW_BBOX"):
        map_reviewed_proposal_to_native_annotation(
            proposal, source_row, coco, tolerance=config.coordinate_tolerance_pixels
        )


def test_mapping_rejects_missing_image_filename(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    proposal, source_row, coco, config = phase04_5n_verified_inputs.first
    proposal = _replace_proposal(proposal, image_id="missing.jpg")
    with pytest.raises(AnnotationMappingError, match="image filename"):
        map_reviewed_proposal_to_native_annotation(
            proposal, source_row, coco, tolerance=config.coordinate_tolerance_pixels
        )


def test_mapping_rejects_image_dimension_mismatch(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    proposal, source_row, coco, config = phase04_5n_verified_inputs.first
    changed_source_row = dict(source_row)
    changed_source_row["image_width"] = "641"
    with pytest.raises(AnnotationMappingError, match="dimension"):
        map_reviewed_proposal_to_native_annotation(
            proposal,
            changed_source_row,
            coco,
            tolerance=config.coordinate_tolerance_pixels,
        )


def test_mapping_tolerance_immediately_below_difference_rejects(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    proposal, source_row, coco, _config = phase04_5n_verified_inputs.first
    coco.annotations_by_id[101]["bbox"][0] += 0.001
    with pytest.raises(AnnotationMappingError, match="zero native"):
        map_reviewed_proposal_to_native_annotation(
            proposal, source_row, coco, tolerance=0.000999
        )


def test_mapping_tolerance_immediately_above_difference_accepts(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    proposal, source_row, coco, _config = phase04_5n_verified_inputs.first
    coco.annotations_by_id[101]["bbox"][0] += 0.001
    mapping = map_reviewed_proposal_to_native_annotation(
        proposal, source_row, coco, tolerance=0.001001
    )
    assert mapping.native_annotation_id == 101


def test_parse_local_gt_records_canonicalizes_ids_and_preserves_order() -> None:
    records = parse_local_gt_records(
        '[{"bbox_id":" GT_1 ","x1":1,"y1":2,"x2":3,"y2":4},'
        '{"bbox_id":"gt_002","x1":5,"y1":6,"x2":7,"y2":8}]'
    )
    assert [record.bbox_id for record in records] == ["gt_001", "gt_002"]


def test_parse_local_gt_records_rejects_duplicate_canonical_ids() -> None:
    with pytest.raises(AnnotationMappingError, match="duplicate local"):
        parse_local_gt_records(
            '[{"bbox_id":"gt_1","x1":1,"y1":2,"x2":3,"y2":4},'
            '{"bbox_id":"GT_001","x1":5,"y1":6,"x2":7,"y2":8}]'
        )


def test_apply_geometry_rejects_when_geometry_would_not_change() -> None:
    annotation = {
        "id": 101,
        "image_id": 11,
        "category_id": 1,
        "bbox": [1.0, 2.0, 3.0, 4.0],
        "area": 12.0,
    }
    with pytest.raises(AnnotationMappingError, match="changed-key set"):
        apply_reviewed_geometry(annotation, AbsoluteXYXY(1.0, 2.0, 4.0, 6.0))


def test_xywh_type_area_property() -> None:
    assert CocoXYWH(1.0, 2.0, 3.0, 4.0).area == pytest.approx(12.0)


def test_parse_local_gt_records_rejects_non_finite_coordinates() -> None:
    with pytest.raises(AnnotationMappingError, match="finite"):
        parse_local_gt_records(
            '[{"bbox_id":"gt_001","x1":0,"y1":0,"x2":NaN,"y2":10}]'
        )


def test_mapping_rejects_out_of_bounds_local_source_geometry(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    proposal, source_row, coco, config = phase04_5n_verified_inputs.first
    proposal = _replace_proposal(
        proposal,
        source_gt_bbox_records_json=(
            '[{"bbox_id":"gt_001","x1":68,"y1":334,"x2":641,"y2":522.466}]'
        ),
    )
    changed_source_row = dict(source_row)
    changed_source_row["gt_bbox_records_json"] = proposal.source_gt_bbox_records_json
    with pytest.raises(AnnotationMappingError, match="bounds"):
        map_reviewed_proposal_to_native_annotation(
            proposal,
            changed_source_row,
            coco,
            tolerance=config.coordinate_tolerance_pixels,
        )


def test_mapping_rejects_source_row_identity_mismatch(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    proposal, source_row, coco, config = phase04_5n_verified_inputs.first
    changed_source_row = dict(source_row)
    changed_source_row["source_case_fingerprint"] = "0" * 64
    with pytest.raises(AnnotationMappingError, match="source row source_case_fingerprint"):
        map_reviewed_proposal_to_native_annotation(
            proposal,
            changed_source_row,
            coco,
            tolerance=config.coordinate_tolerance_pixels,
        )


def test_mapping_rejects_negative_tolerance(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    proposal, source_row, coco, _config = phase04_5n_verified_inputs.first
    with pytest.raises(AnnotationMappingError, match="non-negative"):
        map_reviewed_proposal_to_native_annotation(
            proposal, source_row, coco, tolerance=-0.001
        )


def test_mapping_rejects_source_gt_record_mismatch(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    proposal, source_row, coco, config = phase04_5n_verified_inputs.first
    changed_source_row = dict(source_row)
    changed_source_row["gt_bbox_records_json"] = "[]"
    with pytest.raises(AnnotationMappingError, match="source row gt_bbox_records_json"):
        map_reviewed_proposal_to_native_annotation(
            proposal,
            changed_source_row,
            coco,
            tolerance=config.coordinate_tolerance_pixels,
        )


def test_distinct_mapping_gate_accepts_two_native_ids(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    first = map_reviewed_proposal_to_native_annotation(
        *phase04_5n_verified_inputs.first[:3],
        tolerance=phase04_5n_verified_inputs.config.coordinate_tolerance_pixels,
    )
    second = map_reviewed_proposal_to_native_annotation(
        *phase04_5n_verified_inputs.second[:3],
        tolerance=phase04_5n_verified_inputs.config.coordinate_tolerance_pixels,
    )
    assert require_distinct_native_annotation_mappings((first, second)) == (
        first,
        second,
    )


def test_distinct_mapping_gate_rejects_duplicate_native_id(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    first = map_reviewed_proposal_to_native_annotation(
        *phase04_5n_verified_inputs.first[:3],
        tolerance=phase04_5n_verified_inputs.config.coordinate_tolerance_pixels,
    )
    with pytest.raises(AnnotationMappingError, match="must be distinct"):
        require_distinct_native_annotation_mappings((first, first))


def _fixture_mappings(
    inputs: VerifiedMappingInputs,
):
    mappings = tuple(
        map_reviewed_proposal_to_native_annotation(
            proposal,
            source_row,
            inputs.coco,
            tolerance=inputs.config.coordinate_tolerance_pixels,
        )
        for proposal, source_row in zip(
            inputs.proposals,
            inputs.source_rows,
            strict=True,
        )
    )
    return require_distinct_native_annotation_mappings(mappings)


def _fixture_replacements(mappings):
    return {
        mapping.native_annotation_id: AbsoluteXYXY(*mapping.after_bbox_xyxy)
        for mapping in mappings
    }


def _fixture_source_sha(coco: CocoDocument) -> str:
    return hashlib.sha256(canonical_json_bytes(coco.payload)).hexdigest().upper()


def _build_fixture_staged(
    inputs: VerifiedMappingInputs,
):
    mappings = _fixture_mappings(inputs)
    return build_staged_coco(
        inputs.coco,
        mappings,
        _fixture_replacements(mappings),
        source_sha256=_fixture_source_sha(inputs.coco),
    )


def _validate_fixture_staged_payload(
    inputs: VerifiedMappingInputs,
    payload: dict[str, object],
):
    return validate_staged_coco(
        inputs.coco,
        payload,
        _fixture_mappings(inputs),
        inputs.config.allowed_changed_fields,
        tolerance=inputs.config.coordinate_tolerance_pixels,
    )


def _annotations(payload: dict[str, object]) -> list[dict[str, object]]:
    return payload["annotations"]  # type: ignore[return-value]


def _annotation_by_id(
    payload: dict[str, object],
    annotation_id: int,
) -> dict[str, object]:
    return next(
        annotation
        for annotation in _annotations(payload)
        if annotation["id"] == annotation_id
    )


def test_staged_build_changes_exactly_two_annotations(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    build = _build_fixture_staged(phase04_5n_verified_inputs)
    assert build.validation.passed is True
    assert build.validation.proposal_count == 2
    assert build.validation.mapped_annotation_count == 2
    assert build.validation.changed_annotation_count == 2
    assert build.validation.changed_annotation_ids == (101, 202)
    assert build.validation.image_count_delta == 0
    assert build.validation.annotation_count_delta == 0
    assert build.validation.category_count_delta == 0
    assert build.validation.changed_fields == ("area", "bbox")


def test_non_target_annotations_are_semantically_identical(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    build = _build_fixture_staged(phase04_5n_verified_inputs)
    source = {
        annotation["id"]: annotation
        for annotation in phase04_5n_verified_inputs.coco.payload["annotations"]
    }
    staged = {
        annotation["id"]: annotation
        for annotation in build.payload["annotations"]
    }
    for annotation_id in set(source) - set(build.changed_annotation_ids):
        assert normalized_json_value(source[annotation_id]) == normalized_json_value(
            staged[annotation_id]
        )


def test_validation_rejects_segmentation_change(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    build = _build_fixture_staged(phase04_5n_verified_inputs)
    payload = copy.deepcopy(build.payload)
    _annotation_by_id(payload, 101)["segmentation"] = [[1, 2, 3, 4]]
    with pytest.raises(StagedCocoValidationError, match="unexpected changed fields"):
        _validate_fixture_staged_payload(phase04_5n_verified_inputs, payload)


def test_deterministic_serialization_produces_stable_hash(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    first = _build_fixture_staged(phase04_5n_verified_inputs)
    second = _build_fixture_staged(phase04_5n_verified_inputs)
    assert canonical_json_bytes(first.payload) == canonical_json_bytes(second.payload)
    first_hash = hashlib.sha256(canonical_json_bytes(first.payload)).hexdigest().upper()
    second_hash = hashlib.sha256(canonical_json_bytes(second.payload)).hexdigest().upper()
    assert first_hash == second_hash
    assert {row.staged_coco_sha256 for row in first.diff_rows} == {first_hash}


def test_validation_rejects_image_definition_change(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    payload = copy.deepcopy(_build_fixture_staged(phase04_5n_verified_inputs).payload)
    payload["images"][0]["width"] = 639
    with pytest.raises(StagedCocoValidationError, match="image definitions"):
        _validate_fixture_staged_payload(phase04_5n_verified_inputs, payload)


def test_validation_rejects_category_definition_change(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    payload = copy.deepcopy(_build_fixture_staged(phase04_5n_verified_inputs).payload)
    payload["categories"][0]["supercategory"] = "changed"
    with pytest.raises(StagedCocoValidationError, match="category definitions"):
        _validate_fixture_staged_payload(phase04_5n_verified_inputs, payload)


@pytest.mark.parametrize(
    ("section", "new_id", "message"),
    [
        ("images", 999, "image ID set"),
        ("annotations", 999, "annotation ID set"),
        ("categories", 999, "category ID set"),
    ],
)
def test_validation_rejects_id_set_changes(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
    section: str,
    new_id: int,
    message: str,
) -> None:
    payload = copy.deepcopy(_build_fixture_staged(phase04_5n_verified_inputs).payload)
    payload[section][0]["id"] = new_id
    with pytest.raises(StagedCocoValidationError, match=message):
        _validate_fixture_staged_payload(phase04_5n_verified_inputs, payload)


def test_validation_rejects_annotation_array_reordering(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    payload = copy.deepcopy(_build_fixture_staged(phase04_5n_verified_inputs).payload)
    payload["annotations"][0], payload["annotations"][1] = (
        payload["annotations"][1],
        payload["annotations"][0],
    )
    with pytest.raises(StagedCocoValidationError, match="annotation array order"):
        _validate_fixture_staged_payload(phase04_5n_verified_inputs, payload)


def test_validation_rejects_count_delta(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    payload = copy.deepcopy(_build_fixture_staged(phase04_5n_verified_inputs).payload)
    payload["annotations"].append(copy.deepcopy(payload["annotations"][-1]))
    payload["annotations"][-1]["id"] = 999
    with pytest.raises(StagedCocoValidationError, match="annotation count"):
        _validate_fixture_staged_payload(phase04_5n_verified_inputs, payload)


def test_validation_rejects_third_changed_annotation(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    payload = copy.deepcopy(_build_fixture_staged(phase04_5n_verified_inputs).payload)
    _annotation_by_id(payload, 201)["bbox"][0] += 1.0
    with pytest.raises(StagedCocoValidationError, match="non-target annotation"):
        _validate_fixture_staged_payload(phase04_5n_verified_inputs, payload)


def test_validation_rejects_duplicate_annotation_id(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    payload = copy.deepcopy(_build_fixture_staged(phase04_5n_verified_inputs).payload)
    _annotation_by_id(payload, 201)["id"] = 101
    with pytest.raises(StagedCocoValidationError, match="duplicate annotation ID"):
        _validate_fixture_staged_payload(phase04_5n_verified_inputs, payload)


def test_validation_rejects_after_bbox_mismatch(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    payload = copy.deepcopy(_build_fixture_staged(phase04_5n_verified_inputs).payload)
    _annotation_by_id(payload, 101)["bbox"][0] += 0.01
    with pytest.raises(StagedCocoValidationError, match="reviewed replacement geometry"):
        _validate_fixture_staged_payload(phase04_5n_verified_inputs, payload)


@pytest.mark.parametrize("area", [0, -1, float("nan"), float("inf")])
def test_validation_rejects_invalid_target_area(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
    area: float,
) -> None:
    payload = copy.deepcopy(_build_fixture_staged(phase04_5n_verified_inputs).payload)
    _annotation_by_id(payload, 101)["area"] = area
    with pytest.raises(StagedCocoValidationError, match="area"):
        _validate_fixture_staged_payload(phase04_5n_verified_inputs, payload)


def test_validation_rejects_area_not_matching_bbox(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    payload = copy.deepcopy(_build_fixture_staged(phase04_5n_verified_inputs).payload)
    _annotation_by_id(payload, 101)["area"] += 1.0
    with pytest.raises(StagedCocoValidationError, match="reviewed replacement geometry"):
        _validate_fixture_staged_payload(phase04_5n_verified_inputs, payload)


def test_validation_rejects_out_of_bounds_target_bbox(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    payload = copy.deepcopy(_build_fixture_staged(phase04_5n_verified_inputs).payload)
    _annotation_by_id(payload, 101)["bbox"] = [630.0, 10.0, 20.0, 20.0]
    _annotation_by_id(payload, 101)["area"] = 400.0
    with pytest.raises(StagedCocoValidationError, match="bounds"):
        _validate_fixture_staged_payload(phase04_5n_verified_inputs, payload)


def test_validation_detects_source_payload_drift_after_build(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    build = _build_fixture_staged(phase04_5n_verified_inputs)
    phase04_5n_verified_inputs.coco.payload["annotations"][1]["iscrowd"] = 1
    with pytest.raises(StagedCocoValidationError, match="non-target annotation"):
        _validate_fixture_staged_payload(
            phase04_5n_verified_inputs,
            build.payload,
        )


def test_build_rejects_missing_or_extra_replacements(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    mappings = _fixture_mappings(phase04_5n_verified_inputs)
    replacements = _fixture_replacements(mappings)
    replacements.pop(101)
    with pytest.raises(StagedCocoValidationError, match="replacement annotation IDs"):
        build_staged_coco(
            phase04_5n_verified_inputs.coco,
            mappings,
            replacements,
            source_sha256=_fixture_source_sha(phase04_5n_verified_inputs.coco),
        )
    replacements = _fixture_replacements(mappings)
    replacements[999] = AbsoluteXYXY(1, 1, 2, 2)
    with pytest.raises(StagedCocoValidationError, match="replacement annotation IDs"):
        build_staged_coco(
            phase04_5n_verified_inputs.coco,
            mappings,
            replacements,
            source_sha256=_fixture_source_sha(phase04_5n_verified_inputs.coco),
        )


def test_build_rejects_mapping_count_other_than_two(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    mappings = _fixture_mappings(phase04_5n_verified_inputs)
    with pytest.raises(StagedCocoValidationError, match="exactly two"):
        build_staged_coco(
            phase04_5n_verified_inputs.coco,
            mappings[:1],
            _fixture_replacements(mappings[:1]),
            source_sha256=_fixture_source_sha(phase04_5n_verified_inputs.coco),
        )


@pytest.mark.parametrize("source_sha", ["", "abc", "Z" * 64])
def test_build_rejects_invalid_source_sha(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
    source_sha: str,
) -> None:
    mappings = _fixture_mappings(phase04_5n_verified_inputs)
    with pytest.raises(StagedCocoValidationError, match="source SHA256"):
        build_staged_coco(
            phase04_5n_verified_inputs.coco,
            mappings,
            _fixture_replacements(mappings),
            source_sha256=source_sha,
        )


def test_validation_requires_bbox_and_area_allowlist(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    build = _build_fixture_staged(phase04_5n_verified_inputs)
    with pytest.raises(StagedCocoValidationError, match="allowed changed fields"):
        validate_staged_coco(
            phase04_5n_verified_inputs.coco,
            build.payload,
            _fixture_mappings(phase04_5n_verified_inputs),
            ("bbox",),
            tolerance=0.001,
        )


def test_normalized_json_value_is_key_order_independent_and_type_sensitive() -> None:
    assert normalized_json_value({"b": [1, 2], "a": True}) == normalized_json_value(
        {"a": True, "b": [1, 2]}
    )
    assert normalized_json_value({"value": 1}) != normalized_json_value(
        {"value": 1.0}
    )
    assert normalized_json_value([1, 2]) != normalized_json_value([2, 1])


def test_diff_row_contract_has_exact_order_and_canonical_json(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    mappings = _fixture_mappings(phase04_5n_verified_inputs)
    rows = build_diff_rows(
        mappings,
        source_coco_sha256="A" * 64,
        staged_coco_sha256="B" * 64,
    )
    assert len(rows) == 2
    payload = rows[0].as_dict()
    assert tuple(payload) == (
        "schema_version",
        "phase04_5m_review_case_id",
        "correction_case_id",
        "proposal_fingerprint",
        "source_split",
        "image_id",
        "native_coco_image_id",
        "native_coco_annotation_id",
        "native_category_id",
        "before_bbox_xywh",
        "before_bbox_xyxy",
        "before_area",
        "after_bbox_xywh",
        "after_bbox_xyxy",
        "after_area",
        "changed_fields",
        "source_coco_sha256",
        "staged_coco_sha256",
    )
    assert payload["before_bbox_xywh"] == json.dumps(
        list(mappings[0].before_bbox_xywh),
        separators=(",", ":"),
    )
    assert payload["changed_fields"] == '["area","bbox"]'
    assert payload["source_coco_sha256"] == "A" * 64
    assert payload["staged_coco_sha256"] == "B" * 64


def test_build_does_not_mutate_source_payload(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    before = canonical_json_bytes(phase04_5n_verified_inputs.coco.payload)
    _build_fixture_staged(phase04_5n_verified_inputs)
    assert canonical_json_bytes(phase04_5n_verified_inputs.coco.payload) == before


def test_validation_rejects_target_null_field_addition(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    payload = copy.deepcopy(_build_fixture_staged(phase04_5n_verified_inputs).payload)
    _annotation_by_id(payload, 101)["unexpected_null"] = None
    with pytest.raises(StagedCocoValidationError, match="unexpected changed fields"):
        _validate_fixture_staged_payload(phase04_5n_verified_inputs, payload)


def test_validation_rejects_top_level_metadata_change(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    payload = copy.deepcopy(_build_fixture_staged(phase04_5n_verified_inputs).payload)
    payload["info"] = {"description": "unexpected"}
    with pytest.raises(StagedCocoValidationError, match="top-level"):
        _validate_fixture_staged_payload(phase04_5n_verified_inputs, payload)


def test_diff_rows_require_exactly_two_distinct_mappings(
    phase04_5n_verified_inputs: VerifiedMappingInputs,
) -> None:
    mappings = _fixture_mappings(phase04_5n_verified_inputs)
    with pytest.raises(StagedCocoValidationError, match="exactly two"):
        build_diff_rows(
            mappings[:1],
            source_coco_sha256="A" * 64,
            staged_coco_sha256="B" * 64,
        )
    with pytest.raises(StagedCocoValidationError, match="distinct"):
        build_diff_rows(
            (mappings[0], mappings[0]),
            source_coco_sha256="A" * 64,
            staged_coco_sha256="B" * 64,
        )


def test_prepare_workspace_uses_atomic_final_rename(tmp_path: Path) -> None:
    fixture = build_phase04_5n_fixture(tmp_path)
    config = load_phase04_5n_config(fixture.config_path, fixture.project_root)

    result = staging_module.prepare_staged_correction_workspace(
        config,
        fixture.completed_review_root,
        timestamp="20260715_030000000",
    )

    assert result.workspace_root.name == (
        "phase04_5n_staged_annotation_corrections_20260715_030000000"
    )
    assert result.workspace_root.is_dir()
    assert not any(
        child.name.startswith(".phase04_5n_staged_annotation_corrections")
        for child in result.workspace_root.parent.iterdir()
    )


TASK4_EXPECTED_WORKSPACE_FILES = {
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
    "overlays/before/m_57c102ad6b7c8376.jpg",
    "overlays/before/m_ccb31aa1a564a66a.jpg",
    "overlays/after/m_57c102ad6b7c8376.jpg",
    "overlays/after/m_ccb31aa1a564a66a.jpg",
    "overlays/combined/m_57c102ad6b7c8376.jpg",
    "overlays/combined/m_ccb31aa1a564a66a.jpg",
    "evidence/semantic_validation.json",
    "evidence/workspace_manifest.csv",
    "evidence/SHA256SUMS.csv",
    "evidence/gate_result.json",
}


def _workspace_file_set(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _blocked_results(config: Phase04_5NConfig) -> list[Path]:
    blocked_root = config.n1_workspace_base_root / "_blocked_results"
    if not blocked_root.exists():
        return []
    return sorted(blocked_root.glob("*.json"))


def test_existing_final_workspace_blocks_without_overwrite(tmp_path: Path) -> None:
    fixture = build_phase04_5n_fixture(tmp_path)
    config = load_phase04_5n_config(fixture.config_path, fixture.project_root)
    timestamp = "20260715_030000001"
    first = staging_module.prepare_staged_correction_workspace(
        config, fixture.completed_review_root, timestamp=timestamp
    )
    first_hashes = {
        path.relative_to(first.workspace_root).as_posix(): _file_sha256(path)
        for path in first.workspace_root.rglob("*")
        if path.is_file()
    }

    with pytest.raises(staging_module.StagedWorkspaceError, match="already exists"):
        staging_module.prepare_staged_correction_workspace(
            config, fixture.completed_review_root, timestamp=timestamp
        )

    after_hashes = {
        path.relative_to(first.workspace_root).as_posix(): _file_sha256(path)
        for path in first.workspace_root.rglob("*")
        if path.is_file()
    }
    assert after_hashes == first_hashes
    assert len(_blocked_results(config)) == 1


def test_overlay_rendering_is_deterministic(tmp_path: Path) -> None:
    fixture = build_phase04_5n_fixture(tmp_path)
    config = load_phase04_5n_config(fixture.config_path, fixture.project_root)
    source_hashes = {
        path.name: _file_sha256(path)
        for path in fixture.source_image_root.glob("*.jpg")
    }

    first = staging_module.prepare_staged_correction_workspace(
        config,
        fixture.completed_review_root,
        timestamp="20260715_030000002",
    )
    second = staging_module.prepare_staged_correction_workspace(
        config,
        fixture.completed_review_root,
        timestamp="20260715_030000003",
    )

    def overlay_hashes(root: Path) -> dict[str, str]:
        return {
            path.relative_to(root / "overlays").as_posix(): _file_sha256(path)
            for path in (root / "overlays").rglob("*.jpg")
        }

    assert overlay_hashes(first.workspace_root) == overlay_hashes(second.workspace_root)
    assert len(overlay_hashes(first.workspace_root)) == 6
    assert {
        path.name: _file_sha256(path)
        for path in fixture.source_image_root.glob("*.jpg")
    } == source_hashes


def test_missing_original_image_blocks_official_n1_pass(tmp_path: Path) -> None:
    fixture = build_phase04_5n_fixture(tmp_path)
    config = load_phase04_5n_config(fixture.config_path, fixture.project_root)
    (fixture.source_image_root / "l_687b939a3a89bb8e.jpg").unlink()

    with pytest.raises(staging_module.StagedWorkspaceError, match="original image"):
        staging_module.prepare_staged_correction_workspace(
            config,
            fixture.completed_review_root,
            timestamp="20260715_030000004",
        )

    assert len(_blocked_results(config)) == 1
    assert not (
        config.n1_workspace_base_root
        / "phase04_5n_staged_annotation_corrections_20260715_030000004"
    ).exists()


def test_source_manifest_mismatch_blocks_and_writes_evidence(tmp_path: Path) -> None:
    fixture = build_phase04_5n_fixture(tmp_path)
    config = load_phase04_5n_config(fixture.config_path, fixture.project_root)
    image = fixture.source_image_root / "l_687b939a3a89bb8e.jpg"
    tampered = bytearray(image.read_bytes())
    tampered[-1] ^= 0x01
    image.write_bytes(bytes(tampered))

    with pytest.raises(staging_module.StagedWorkspaceError, match="sha256 mismatch"):
        staging_module.prepare_staged_correction_workspace(
            config,
            fixture.completed_review_root,
            timestamp="20260715_030000005",
        )

    blocked = _blocked_results(config)
    assert len(blocked) == 1
    payload = json.loads(blocked[0].read_text(encoding="utf-8"))
    assert payload["outcome"] == "BLOCKED"
    assert payload["failed_stage"] == "verify_predecessor"
    assert payload["canonical_source_modified"] is False
    assert payload["test_split_read"] is False


def test_overlay_exception_cleans_only_current_staging_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = build_phase04_5n_fixture(tmp_path)
    config = load_phase04_5n_config(fixture.config_path, fixture.project_root)
    successful = staging_module.prepare_staged_correction_workspace(
        config,
        fixture.completed_review_root,
        timestamp="20260715_030000006",
    )

    def fail_overlay(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError("forced overlay failure")

    monkeypatch.setattr(staging_module, "render_annotation_overlays", fail_overlay)
    timestamp = "20260715_030000007"
    with pytest.raises(staging_module.StagedWorkspaceError, match="forced overlay"):
        staging_module.prepare_staged_correction_workspace(
            config, fixture.completed_review_root, timestamp=timestamp
        )

    assert successful.workspace_root.is_dir()
    assert not (
        config.n1_workspace_base_root
        / f".phase04_5n_staged_annotation_corrections_{timestamp}.staging"
    ).exists()
    assert not (
        config.n1_workspace_base_root
        / f"phase04_5n_staged_annotation_corrections_{timestamp}"
    ).exists()
    assert len(_blocked_results(config)) == 1


def test_canonical_source_hash_drift_blocks_before_final_rename(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = build_phase04_5n_fixture(tmp_path)
    config = load_phase04_5n_config(fixture.config_path, fixture.project_root)
    original_sha256 = staging_module.sha256_file

    def drifting_sha256(path: Path) -> str:
        if Path(path).resolve() == fixture.canonical_valid_coco.resolve():
            return "F" * 64
        return original_sha256(path)

    monkeypatch.setattr(staging_module, "sha256_file", drifting_sha256)
    timestamp = "20260715_030000008"
    with pytest.raises(staging_module.StagedWorkspaceError, match="canonical source sha256 drift"):
        staging_module.prepare_staged_correction_workspace(
            config, fixture.completed_review_root, timestamp=timestamp
        )

    assert not (
        config.n1_workspace_base_root
        / f"phase04_5n_staged_annotation_corrections_{timestamp}"
    ).exists()
    assert len(_blocked_results(config)) == 1


def test_protected_external_asset_fingerprint_change_blocks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = build_phase04_5n_fixture(tmp_path)
    config = load_phase04_5n_config(fixture.config_path, fixture.project_root)
    protected_file = (
        fixture.project_root / "outputs/metadata/external_assets/protected.txt"
    )
    protected_file.parent.mkdir(parents=True, exist_ok=True)
    protected_file.write_text("original", encoding="utf-8")
    original_render = staging_module.render_annotation_overlays

    def mutate_protected(*args: object, **kwargs: object) -> object:
        result = original_render(*args, **kwargs)
        protected_file.write_text("changed", encoding="utf-8")
        return result

    monkeypatch.setattr(
        staging_module,
        "render_annotation_overlays",
        mutate_protected,
    )
    timestamp = "20260715_030000009"
    with pytest.raises(
        staging_module.StagedWorkspaceError,
        match="protected external assets",
    ):
        staging_module.prepare_staged_correction_workspace(
            config, fixture.completed_review_root, timestamp=timestamp
        )

    assert not (
        config.n1_workspace_base_root
        / f"phase04_5n_staged_annotation_corrections_{timestamp}"
    ).exists()
    assert len(_blocked_results(config)) == 1


def test_workspace_inventory_and_gate_evidence_are_exact(tmp_path: Path) -> None:
    fixture = build_phase04_5n_fixture(tmp_path)
    config = load_phase04_5n_config(fixture.config_path, fixture.project_root)

    result = staging_module.prepare_staged_correction_workspace(
        config,
        fixture.completed_review_root,
        timestamp="20260715_030000010",
    )

    assert _workspace_file_set(result.workspace_root) == TASK4_EXPECTED_WORKSPACE_FILES
    gate = json.loads(
        (result.workspace_root / "evidence/gate_result.json").read_text(
            encoding="utf-8"
        )
    )
    assert gate["gate_id"] == "PHASE_04_5N_STAGED_ANNOTATION_CORRECTIONS"
    assert gate["outcome"] == "PASS"
    assert gate["classification"] == (
        "PHASE_04_5N_STAGED_ANNOTATION_CORRECTIONS_VALIDATED"
    )
    assert gate["proposal_count"] == 2
    assert gate["mapped_annotation_count"] == 2
    assert gate["changed_annotation_count"] == 2
    assert gate["image_count_delta"] == 0
    assert gate["annotation_count_delta"] == 0
    assert gate["category_count_delta"] == 0
    assert gate["changed_native_annotation_ids"] == [101, 202]
    assert gate["canonical_source_modified"] is False
    assert gate["test_split_read"] is False
    assert gate["model_inference_executed"] is False
    assert gate["dataset_modified"] is False
    assert gate["registry_modified"] is False
    assert gate["fixed_splits_modified"] is False
    assert gate["training_started"] is False
    assert gate["retraining_status"] == "NOT_YET_APPROVED"
    assert gate["deployment_acceptance"] == "NOT_YET_APPROVED"
    assert gate["canonical_source_sha256"] == _file_sha256(
        fixture.canonical_valid_coco
    )
    assert gate["staged_coco_sha256"] == _file_sha256(
        result.workspace_root / "staged/staged_corrected_validation_coco.json"
    )


def test_workspace_manifests_verify_every_recorded_member(tmp_path: Path) -> None:
    fixture = build_phase04_5n_fixture(tmp_path)
    config = load_phase04_5n_config(fixture.config_path, fixture.project_root)
    result = staging_module.prepare_staged_correction_workspace(
        config,
        fixture.completed_review_root,
        timestamp="20260715_030000011",
    )

    for manifest_name in (
        "evidence/workspace_manifest.csv",
        "evidence/SHA256SUMS.csv",
    ):
        with (result.workspace_root / manifest_name).open(
            encoding="utf-8-sig", newline=""
        ) as handle:
            rows = list(csv.DictReader(handle))
        assert rows
        for row in rows:
            member = result.workspace_root / row["relative_path"]
            assert member.is_file()
            assert member.stat().st_size == int(row["size_bytes"])
            assert _file_sha256(member) == row["sha256"]

    workspace_rows = list(
        csv.DictReader(
            (result.workspace_root / "evidence/workspace_manifest.csv").open(
                encoding="utf-8-sig", newline=""
            )
        )
    )
    checksum_rows = list(
        csv.DictReader(
            (result.workspace_root / "evidence/SHA256SUMS.csv").open(
                encoding="utf-8-sig", newline=""
            )
        )
    )
    assert "evidence/workspace_manifest.csv" not in {
        row["relative_path"] for row in workspace_rows
    }
    assert "evidence/workspace_manifest.csv" in {
        row["relative_path"] for row in checksum_rows
    }
    assert "evidence/SHA256SUMS.csv" not in {
        row["relative_path"] for row in checksum_rows
    }


def test_no_overwrite_blocked_evidence_names_are_unique(tmp_path: Path) -> None:
    fixture = build_phase04_5n_fixture(tmp_path)
    config = load_phase04_5n_config(fixture.config_path, fixture.project_root)
    timestamp = "20260715_030000012"
    staging_module.prepare_staged_correction_workspace(
        config, fixture.completed_review_root, timestamp=timestamp
    )

    for _ in range(2):
        with pytest.raises(staging_module.StagedWorkspaceError, match="already exists"):
            staging_module.prepare_staged_correction_workspace(
                config, fixture.completed_review_root, timestamp=timestamp
            )

    blocked = _blocked_results(config)
    assert len(blocked) == 2
    assert blocked[0].name != blocked[1].name
