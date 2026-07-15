
from __future__ import annotations

import csv
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import yaml
from PIL import Image


CASE_IDS = ("l_687b939a3a89bb8e", "l_e5875a8f94620ff1")
FINGERPRINTS = (
    "C28DE952BFEB7B1C2C0F25BA348B8AF69E87032774714AC95D36B29A944A5FC4",
    "EC8ABCDC49879C817480F1A09FD71E376C5CA47EDB730D5DA699B5298BA13095",
)
IMAGE_IDS = (
    "147_jpg.rf.83b3e9e399d2f3546d5676a902148f0c.jpg",
    "test_set_188_jpg.rf.ed3c01d255f1c18dd0c5dd2667c7a096.jpg",
)


@dataclass(frozen=True)
class Phase04_5NFixture:
    project_root: Path
    config_path: Path
    completed_review_root: Path
    canonical_valid_coco: Path
    canonical_test_coco: Path
    source_image_root: Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_manifest(path: Path, base_root: Path, relative_paths: list[str]) -> None:
    rows: list[dict[str, Any]] = []
    for relative_path in relative_paths:
        member = base_root / Path(relative_path)
        rows.append(
            {
                "relative_path": Path(relative_path).as_posix(),
                "size_bytes": member.stat().st_size,
                "sha256": _sha256(member),
            }
        )
    _write_csv(path, rows, ["relative_path", "size_bytes", "sha256"])


def write_fixture_coco(path: Path) -> None:
    payload = {
        "images": [
            {"id": 11, "file_name": IMAGE_IDS[0], "width": 640, "height": 640},
            {"id": 22, "file_name": IMAGE_IDS[1], "width": 640, "height": 640},
        ],
        "annotations": [
            {
                "id": 101,
                "image_id": 11,
                "category_id": 1,
                "bbox": [68.0, 334.0, 150.71, 188.466],
                "area": 28405.67286,
                "segmentation": [],
                "iscrowd": 0,
            },
            {
                "id": 201,
                "image_id": 22,
                "category_id": 1,
                "bbox": [357.999999968, 368.999999968, 171.487, 92.593],
                "area": 15878.552891,
                "segmentation": [],
                "iscrowd": 0,
            },
            {
                "id": 202,
                "image_id": 22,
                "category_id": 1,
                "bbox": [97.0, 342.0, 392.962, 172.222],
                "area": 67679.980364,
                "segmentation": [],
                "iscrowd": 0,
            },
            {
                "id": 203,
                "image_id": 22,
                "category_id": 1,
                "bbox": [160.999999968, 435.0, 117.333, 99.074],
                "area": 11624.249442,
                "segmentation": [],
                "iscrowd": 0,
            },
        ],
        "categories": [{"id": 1, "name": "damage", "supercategory": "none"}],
    }
    _write_json(path, payload)


def write_fixture_original_images(source_image_root: Path) -> None:
    source_image_root.mkdir(parents=True, exist_ok=True)
    for index, case_id in enumerate(CASE_IDS):
        image = Image.new("RGB", (640, 640), (40 + index * 30, 80, 120))
        image.save(source_image_root / f"{case_id}.jpg", format="JPEG", quality=90)


def _reviewed_rows() -> list[dict[str, str]]:
    return [
        {
            "schema_version": "1",
            "correction_review_batch_id": "phase04_5m_annotation_correction_review_fixture",
            "correction_case_id": "m_57c102ad6b7c8376",
            "review_case_id": CASE_IDS[0],
            "image_id": IMAGE_IDS[0],
            "source_split": "valid",
            "source_case_fingerprint": "A1DB4261A756EDADEE26303852357A549F6BF26A243DA58964F24068EB4878A2",
            "original_annotation_defect_type": "wrong_damage_scope",
            "original_review_notes": "模型框的是對的",
            "source_gt_bbox_records_json": json.dumps(
                [{"bbox_id": "gt_001", "x1": 68.0, "x2": 218.71, "y1": 334.0, "y2": 522.466}],
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            "source_prediction_bbox_records_json": json.dumps(
                [{"bbox_id": "pred_001", "confidence": 0.53, "x1": 74.18, "x2": 285.65, "y1": 192.35, "y2": 519.73}],
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            "correction_review_status": "reviewed",
            "correction_decision": "CONFIRM_GT_CORRECTION_REQUIRED",
            "correction_operation": "RESIZE_OR_REDRAW_BBOX",
            "target_gt_bbox_ids_json": '["gt_001"]',
            "replacement_bbox_coordinates_json": '{"x1":74.2,"x2":285.65,"y1":192.4,"y2":579.75}',
            "correction_reason": "fixture",
            "correction_reviewer": "Vincent",
            "correction_reviewed_at_utc": "2026-07-15T02:01:01+08:00",
            "proposal_fingerprint": FINGERPRINTS[0],
        },
        {
            "schema_version": "1",
            "correction_review_batch_id": "phase04_5m_annotation_correction_review_fixture",
            "correction_case_id": "m_ccb31aa1a564a66a",
            "review_case_id": CASE_IDS[1],
            "image_id": IMAGE_IDS[1],
            "source_split": "valid",
            "source_case_fingerprint": "CBA679CAEEA26A3218D14C620E4908FFB3210FE27D6ACE4E6FF1446C97BAFF8A",
            "original_annotation_defect_type": "extra_bbox",
            "original_review_notes": "重複標註",
            "source_gt_bbox_records_json": json.dumps(
                [
                    {"bbox_id": "gt_001", "x1": 358.0, "x2": 529.487, "y1": 369.0, "y2": 461.593},
                    {"bbox_id": "gt_002", "x1": 97.0, "x2": 489.962, "y1": 342.0, "y2": 514.222},
                    {"bbox_id": "gt_003", "x1": 161.0, "x2": 278.333, "y1": 435.0, "y2": 534.074},
                ],
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            "source_prediction_bbox_records_json": json.dumps(
                [{"bbox_id": "pred_001", "confidence": 0.21, "x1": 358.42, "x2": 584.61, "y1": 350.57, "y2": 468.24}],
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            "correction_review_status": "reviewed",
            "correction_decision": "CONFIRM_GT_CORRECTION_REQUIRED",
            "correction_operation": "RESIZE_OR_REDRAW_BBOX",
            "target_gt_bbox_ids_json": '["gt_002"]',
            "replacement_bbox_coordinates_json": '{"x1":97.0,"x2":490.0,"y1":350.0,"y2":468.0}',
            "correction_reason": "fixture",
            "correction_reviewer": "Vincent",
            "correction_reviewed_at_utc": "2026-07-15T02:23:37+08:00",
            "proposal_fingerprint": FINGERPRINTS[1],
        },
    ]


REVIEWED_FIELDS = [
    "schema_version",
    "correction_review_batch_id",
    "correction_case_id",
    "review_case_id",
    "image_id",
    "source_split",
    "source_case_fingerprint",
    "original_annotation_defect_type",
    "original_review_notes",
    "source_gt_bbox_records_json",
    "source_prediction_bbox_records_json",
    "correction_review_status",
    "correction_decision",
    "correction_operation",
    "target_gt_bbox_ids_json",
    "replacement_bbox_coordinates_json",
    "correction_reason",
    "correction_reviewer",
    "correction_reviewed_at_utc",
    "proposal_fingerprint",
]


def _source_rows(reviewed_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in reviewed_rows:
        rows.append(
            {
                "schema_version": "1",
                "correction_review_batch_id": row["correction_review_batch_id"],
                "correction_case_id": row["correction_case_id"],
                "source_f2_gate_sha256": "CFC0B10B8EC161FC12D47AE2774D0A3670FEBCB1C4523D89562228FABACAFC24",
                "source_findings_report_sha256": "5AB6D8E24081A6ADB7B1D20BFE81194129EB566575A4DF61D8E490939815C6F0",
                "source_case_fingerprint": row["source_case_fingerprint"],
                "review_case_id": row["review_case_id"],
                "image_id": row["image_id"],
                "image_width": "640",
                "image_height": "640",
                "source_split": row["source_split"],
                "original_image_relpath": f"assets/original/{row['review_case_id']}.jpg",
                "gt_overlay_relpath": f"assets/gt_overlay/{row['review_case_id']}.jpg",
                "prediction_overlay_relpath": f"assets/prediction_overlay/{row['review_case_id']}.jpg",
                "combined_overlay_relpath": f"assets/combined_overlay/{row['review_case_id']}.jpg",
                "original_annotation_defect_type": row["original_annotation_defect_type"],
                "original_review_notes": row["original_review_notes"],
                "gt_bbox_records_json": row["source_gt_bbox_records_json"],
                "prediction_bbox_records_json": row["source_prediction_bbox_records_json"],
            }
        )
    return rows


SOURCE_FIELDS = [
    "schema_version",
    "correction_review_batch_id",
    "correction_case_id",
    "source_f2_gate_sha256",
    "source_findings_report_sha256",
    "source_case_fingerprint",
    "review_case_id",
    "image_id",
    "image_width",
    "image_height",
    "source_split",
    "original_image_relpath",
    "gt_overlay_relpath",
    "prediction_overlay_relpath",
    "combined_overlay_relpath",
    "original_annotation_defect_type",
    "original_review_notes",
    "gt_bbox_records_json",
    "prediction_bbox_records_json",
]


def write_fixture_completed_review(completed_review_root: Path) -> None:
    reviewed_rows = _reviewed_rows()
    exports = completed_review_root / "exports"
    source = completed_review_root / "source"

    _write_csv(
        exports / "annotation_correction_proposals_reviewed.csv",
        reviewed_rows,
        REVIEWED_FIELDS,
    )
    _write_json(
        exports / "annotation_correction_proposals_reviewed.json",
        {"schema_version": "1", "proposal_count": 2, "proposals": reviewed_rows},
    )
    _write_json(
        exports / "correction_review_export_result.json",
        {
            "gate_id": "PHASE_04_5M_ANNOTATION_CORRECTION_REVIEW_EXPORT",
            "outcome": "PASS",
            "classification": "PHASE_04_5M_ANNOTATION_CORRECTION_PROPOSALS_REVIEWED",
            "review_cases": 2,
            "reviewed": 2,
            "pending": 0,
            "needs_adjudication": 0,
            "test_split_read": False,
            "model_inference_executed": False,
            "canonical_annotation_modified": False,
            "canonical_coco_modified": False,
            "dataset_modified": False,
            "registry_modified": False,
            "fixed_splits_modified": False,
            "training_started": False,
            "retraining_status": "NOT_YET_APPROVED",
            "deployment_acceptance": "NOT_YET_APPROVED",
        },
    )

    source_rows = _source_rows(reviewed_rows)
    _write_csv(source / "correction_review_source.csv", source_rows, SOURCE_FIELDS)
    _write_json(
        source / "source_contract.json",
        {
            "schema_version": "1",
            "correction_review_batch_id": "phase04_5m_annotation_correction_review_fixture",
            "review_case_ids": list(CASE_IDS),
            "source_record_origin": "VERIFIED_04_5K_SOURCE_ZIP",
        },
    )

    for category in ("gt_overlay", "prediction_overlay", "combined_overlay"):
        directory = completed_review_root / "assets" / category
        directory.mkdir(parents=True, exist_ok=True)
        for case_id in CASE_IDS:
            shutil.copy2(
                completed_review_root / "assets" / "original" / f"{case_id}.jpg",
                directory / f"{case_id}.jpg",
            )

    source_members = [
        f"assets/original/{CASE_IDS[0]}.jpg",
        f"assets/original/{CASE_IDS[1]}.jpg",
        f"assets/gt_overlay/{CASE_IDS[0]}.jpg",
        f"assets/gt_overlay/{CASE_IDS[1]}.jpg",
        f"assets/prediction_overlay/{CASE_IDS[0]}.jpg",
        f"assets/prediction_overlay/{CASE_IDS[1]}.jpg",
        f"assets/combined_overlay/{CASE_IDS[0]}.jpg",
        f"assets/combined_overlay/{CASE_IDS[1]}.jpg",
        "source/correction_review_source.csv",
        "source/source_contract.json",
    ]
    _write_manifest(source / "source_manifest.csv", completed_review_root, source_members)

    export_members = [
        "annotation_correction_proposals_reviewed.csv",
        "annotation_correction_proposals_reviewed.json",
        "correction_review_export_result.json",
    ]
    _write_manifest(exports / "SHA256SUMS.csv", exports, export_members)


def write_fixture_config(
    config_path: Path,
    project_root: Path,
    canonical_valid_coco: Path,
) -> None:
    relative_candidate = canonical_valid_coco.relative_to(project_root).as_posix()
    payload = {
        "schema_version": "1",
        "predecessor": {
            "expected_classification": "PHASE_04_5M_ANNOTATION_CORRECTION_PROPOSALS_REVIEWED",
            "expected_review_cases": 2,
            "expected_reviewed": 2,
            "expected_pending": 0,
            "expected_needs_adjudication": 0,
            "required_export_files": [
                "exports/annotation_correction_proposals_reviewed.csv",
                "exports/annotation_correction_proposals_reviewed.json",
                "exports/correction_review_export_result.json",
                "exports/SHA256SUMS.csv",
                "source/source_contract.json",
                "source/source_manifest.csv",
                "source/correction_review_source.csv",
            ],
            "expected_proposals": [
                {
                    "review_case_id": CASE_IDS[0],
                    "correction_case_id": "m_57c102ad6b7c8376",
                    "image_id": IMAGE_IDS[0],
                    "source_split": "valid",
                    "operation": "RESIZE_OR_REDRAW_BBOX",
                    "target_gt_bbox_ids": ["gt_001"],
                    "proposal_fingerprint": FINGERPRINTS[0],
                },
                {
                    "review_case_id": CASE_IDS[1],
                    "correction_case_id": "m_ccb31aa1a564a66a",
                    "image_id": IMAGE_IDS[1],
                    "source_split": "valid",
                    "operation": "RESIZE_OR_REDRAW_BBOX",
                    "target_gt_bbox_ids": ["gt_002"],
                    "proposal_fingerprint": FINGERPRINTS[1],
                },
            ],
        },
        "canonical_source": {
            "dataset_id": "rf_car_damage_seg_v1",
            "required_split": "valid",
            "required_category_name": "damage",
            "approved_candidates": [relative_candidate],
            "coordinate_tolerance_pixels": 0.001,
            "allowed_changed_fields": ["bbox", "area"],
        },
        "n1": {
            "workspace_base_root": str(project_root.parent / "Phase04_5N"),
            "workspace_prefix": "phase04_5n_staged_annotation_corrections",
            "gate_classification": "PHASE_04_5N_STAGED_ANNOTATION_CORRECTIONS_VALIDATED",
            "staged_coco_name": "staged_corrected_validation_coco.json",
        },
        "n2": {
            "evidence_base_root": str(project_root.parent / "Phase04_5N_Promotion"),
            "evidence_prefix": "phase04_5n_annotation_correction_promotion",
            "authorization_phrase": "PHASE_04_5N_2_CANONICAL_PROMOTION_AUTHORIZED",
            "gate_classification": "PHASE_04_5N_ANNOTATION_CORRECTIONS_PROMOTED",
        },
        "safety": {
            "test_split_read": False,
            "model_inference_executed": False,
            "dataset_materialization_executed": False,
            "registry_modified": False,
            "fixed_splits_modified": False,
            "training_started": False,
            "retraining_status": "NOT_YET_APPROVED",
            "deployment_acceptance": "NOT_YET_APPROVED",
        },
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def build_phase04_5n_fixture(tmp_path: Path) -> Phase04_5NFixture:
    """Build a two-case valid-split fixture matching the approved 04.5M export."""
    project_root = tmp_path / "FleetVision"
    completed_review_root = tmp_path / "phase04_5m_completed"
    canonical_valid_coco = (
        project_root
        / "dataset/02_interim/99_external/roboflow/rf_car_damage_seg_v1"
        / "canonical_coco/valid/_annotations.coco.json"
    )
    canonical_test_coco = (
        project_root
        / "dataset/02_interim/99_external/roboflow/rf_car_damage_seg_v1"
        / "canonical_coco/test/_annotations.coco.json"
    )
    source_image_root = completed_review_root / "assets/original"
    config_path = project_root / "configs/data/phase04_5n_test_config.yaml"
    for directory in (
        canonical_valid_coco.parent,
        canonical_test_coco.parent,
        source_image_root,
        config_path.parent,
        completed_review_root / "exports",
        completed_review_root / "source",
    ):
        directory.mkdir(parents=True, exist_ok=True)
    write_fixture_coco(canonical_valid_coco)
    canonical_test_coco.write_text(
        "THIS_TEST_SPLIT_SENTINEL_MUST_NEVER_BE_OPENED",
        encoding="utf-8",
    )
    write_fixture_original_images(source_image_root)
    write_fixture_completed_review(completed_review_root)
    write_fixture_config(config_path, project_root, canonical_valid_coco)
    return Phase04_5NFixture(
        project_root=project_root,
        config_path=config_path,
        completed_review_root=completed_review_root,
        canonical_valid_coco=canonical_valid_coco,
        canonical_test_coco=canonical_test_coco,
        source_image_root=source_image_root,
    )


@pytest.fixture
def phase04_5n_fixture(tmp_path: Path) -> Phase04_5NFixture:
    return build_phase04_5n_fixture(tmp_path)


def refresh_completed_export_checksums(completed_review_root: Path) -> None:
    exports = completed_review_root / "exports"
    _write_manifest(
        exports / "SHA256SUMS.csv",
        exports,
        [
            "annotation_correction_proposals_reviewed.csv",
            "annotation_correction_proposals_reviewed.json",
            "correction_review_export_result.json",
        ],
    )


def refresh_source_checksums(completed_review_root: Path) -> None:
    source = completed_review_root / "source"
    existing_rows = list(csv.DictReader((source / "source_manifest.csv").open(encoding="utf-8")))
    _write_manifest(
        source / "source_manifest.csv",
        completed_review_root,
        [row["relative_path"] for row in existing_rows],
    )


def rewrite_export_result(completed_review_root: Path, **updates: Any) -> None:
    path = completed_review_root / "exports/correction_review_export_result.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(updates)
    _write_json(path, payload)


def load_reviewed_rows(completed_review_root: Path) -> list[dict[str, str]]:
    path = completed_review_root / "exports/annotation_correction_proposals_reviewed.csv"
    return list(csv.DictReader(path.open(encoding="utf-8", newline="")))


def write_reviewed_rows(completed_review_root: Path, rows: list[dict[str, str]]) -> None:
    exports = completed_review_root / "exports"
    _write_csv(exports / "annotation_correction_proposals_reviewed.csv", rows, REVIEWED_FIELDS)
    _write_json(
        exports / "annotation_correction_proposals_reviewed.json",
        {"schema_version": "1", "proposal_count": len(rows), "proposals": rows},
    )


def add_second_existing_valid_candidate(fixture: Phase04_5NFixture) -> None:
    second = fixture.project_root / "dataset/alternate/valid/_annotations.coco.json"
    second.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(fixture.canonical_valid_coco, second)
    payload = yaml.safe_load(fixture.config_path.read_text(encoding="utf-8"))
    payload["canonical_source"]["approved_candidates"].append(
        second.relative_to(fixture.project_root).as_posix()
    )
    fixture.config_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
