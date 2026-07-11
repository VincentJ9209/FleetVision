from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from fleetvision.data.intake_external_dataset import (
    ControlledIntakeConfig,
    DatasetIntakeError,
    inspect_coco_export,
    load_registry_row,
    run_controlled_intake,
    safe_extract_zip,
)


def write_registry(path: Path, *, usage_status: str = "approved_for_download") -> None:
    columns = [
        "dataset_id",
        "platform",
        "dataset_name",
        "source_url",
        "publisher",
        "license",
        "license_evidence_url",
        "license_verified",
        "search_date",
        "download_date",
        "dataset_version",
        "task_type",
        "annotation_format",
        "original_classes",
        "image_count_reported",
        "image_count_downloaded",
        "bbox_count_reported",
        "bbox_count_valid",
        "accepted_image_count",
        "rejected_image_count",
        "mapping_to_damage",
        "domain_similarity",
        "bbox_quality_status",
        "sha256_dedup_status",
        "perceptual_hash_status",
        "internal_cross_dedup_status",
        "usage_status",
        "rejection_reason",
        "local_raw_path",
        "notes",
    ]
    row = {column: "" for column in columns}
    row.update(
        {
            "dataset_id": "rf_car_damage_seg_v1",
            "platform": "roboflow",
            "dataset_name": "Car-Damage detection",
            "license": "Public Domain (Roboflow project label)",
            "license_verified": "yes",
            "dataset_version": "v1 (2023-04-04)",
            "task_type": "segmentation",
            "annotation_format": "coco",
            "original_classes": "Car-Damage",
            "usage_status": usage_status,
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([row], columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def make_coco_zip(path: Path, *, invalid_bbox: bool = False) -> None:
    coco = {
        "images": [
            {"id": 1, "file_name": "image_a.jpg", "width": 100, "height": 80},
            {"id": 2, "file_name": "image_b.jpg", "width": 60, "height": 40},
        ],
        "categories": [{"id": 1, "name": "Car-Damage"}],
        "annotations": [
            {
                "id": 10,
                "image_id": 1,
                "category_id": 1,
                "bbox": [10, 10, -5 if invalid_bbox else 20, 15],
                "area": 300,
                "iscrowd": 0,
                "segmentation": [[10, 10, 30, 10, 30, 25, 10, 25]],
            },
            {
                "id": 11,
                "image_id": 2,
                "category_id": 1,
                "bbox": [5, 5, 10, 10],
                "area": 100,
                "iscrowd": 0,
                "segmentation": [[5, 5, 15, 5, 15, 15, 5, 15]],
            },
        ],
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.roboflow.txt", "synthetic fixture")
        zf.writestr("train/_annotations.coco.json", json.dumps(coco))
        zf.writestr("train/image_a.jpg", b"same-image-bytes")
        zf.writestr("train/image_b.jpg", b"same-image-bytes")


def make_config(tmp_path: Path) -> ControlledIntakeConfig:
    return ControlledIntakeConfig(
        dataset_id="rf_car_damage_seg_v1",
        registry_csv=tmp_path / "dataset/00_catalog/external_dataset_registry.csv",
        raw_dataset_root=tmp_path / "dataset/01_raw/99_external/roboflow/rf_car_damage_seg_v1",
        metadata_root=tmp_path / "outputs/metadata/external_assets/roboflow/rf_car_damage_seg_v1",
        provider="roboflow",
        project_url="https://universe.roboflow.com/college-gxdrt/car-damage-detection-ha5mm",
        version_url="https://universe.roboflow.com/college-gxdrt/car-damage-detection-ha5mm/dataset/1",
        license_name="Public Domain",
        license_url="https://creativecommons.org/publicdomain/mark/1.0/",
        expected_classes=("Car-Damage",),
        mapped_class="damage",
        export_format="coco-segmentation",
        dataset_version="1",
        reported_project_image_count=4869,
        reported_version_image_count=11685,
        lineage_status="generated_augmented_v1",
    )


def evidence_fetcher(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if "/dataset/1" in url:
        text = "Car-Damage 11685 Outputs per training example: 3"
    else:
        text = "Car-Damage Public Domain 4869"
    destination.write_text(text, encoding="utf-8")


def test_registry_requires_approved_and_verified(tmp_path: Path) -> None:
    registry = tmp_path / "registry.csv"
    write_registry(registry, usage_status="pending")

    with pytest.raises(DatasetIntakeError, match="approved_for_download"):
        load_registry_row(registry, "rf_car_damage_seg_v1")


def test_safe_extract_rejects_parent_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("../escape.txt", "bad")

    with pytest.raises(DatasetIntakeError, match="unsafe ZIP member"):
        safe_extract_zip(archive, tmp_path / "out")


def test_inspect_coco_export_counts_and_exact_duplicates(tmp_path: Path) -> None:
    archive = tmp_path / "dataset.zip"
    extracted = tmp_path / "extracted"
    make_coco_zip(archive)
    safe_extract_zip(archive, extracted)

    result = inspect_coco_export(extracted, expected_classes=("Car-Damage",))

    assert result.summary["image_record_count"] == 2
    assert result.summary["annotation_count"] == 2
    assert result.summary["valid_bbox_count"] == 2
    assert result.summary["invalid_bbox_count"] == 0
    assert result.summary["exact_duplicate_image_count"] == 2
    assert result.summary["exact_duplicate_group_count"] == 1
    assert result.summary["class_names"] == ["Car-Damage"]


def test_inspect_coco_export_blocks_invalid_bbox(tmp_path: Path) -> None:
    archive = tmp_path / "dataset.zip"
    extracted = tmp_path / "extracted"
    make_coco_zip(archive, invalid_bbox=True)
    safe_extract_zip(archive, extracted)

    result = inspect_coco_export(extracted, expected_classes=("Car-Damage",))

    assert result.summary["invalid_bbox_count"] == 1
    assert any("non-positive bbox" in error for error in result.errors)


def test_run_controlled_intake_promotes_verified_payload(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    write_registry(config.registry_csv)
    archive = tmp_path / "roboflow-export.zip"
    make_coco_zip(archive)

    result = run_controlled_intake(
        config,
        archive_path=archive,
        evidence_fetcher=evidence_fetcher,
        now_utc="2026-07-12T00:00:00Z",
    )

    assert result["gate_classification"] == "EXTERNAL_DATASET_INTAKE_VERIFIED"
    assert config.raw_dataset_root.is_dir()
    assert config.metadata_root.is_dir()
    assert (config.raw_dataset_root / "00_download" / archive.name).is_file()
    assert (config.raw_dataset_root / "01_extracted_export" / "train" / "_annotations.coco.json").is_file()
    assert (config.metadata_root / "download_manifest.csv").is_file()
    assert (config.metadata_root / "license_evidence.md").is_file()
    assert (config.metadata_root / "image_inventory.csv").is_file()
    assert (config.metadata_root / "bbox_quality_report.csv").is_file()
    assert result["summary"]["image_record_count"] == 2
    assert result["summary"]["annotation_count"] == 2
    assert result["summary"]["invalid_bbox_count"] == 0
    assert result["summary"]["lineage_status"] == "generated_augmented_v1"
    assert result["summary"]["training_acceptance"] == "NOT_YET_APPROVED"

    manifest = pd.read_csv(config.metadata_root / "download_manifest.csv", dtype=str, keep_default_na=False)
    assert manifest.loc[0, "archive_sha256"]
    assert manifest.loc[0, "usage_status"] == "downloaded_pending_audit"
    assert manifest.loc[0, "training_acceptance"] == "NOT_YET_APPROVED"


def test_run_controlled_intake_preserves_qa_failures_for_audit(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    write_registry(config.registry_csv)
    archive = tmp_path / "roboflow-invalid.zip"
    make_coco_zip(archive, invalid_bbox=True)

    result = run_controlled_intake(
        config,
        archive_path=archive,
        evidence_fetcher=evidence_fetcher,
        now_utc="2026-07-12T00:00:00Z",
    )

    assert result["gate_classification"] == "EXTERNAL_DATASET_INTAKE_AUDIT_REQUIRED"
    assert config.raw_dataset_root.is_dir()
    assert config.metadata_root.is_dir()
    errors = pd.read_csv(config.metadata_root / "intake_errors.csv")
    assert len(errors) == 1
    assert "non-positive bbox" in errors.loc[0, "error"]
    verification = json.loads((config.metadata_root / "intake_verification.json").read_text())
    assert verification["error_count"] == 1
    assert verification["summary"]["training_acceptance"] == "NOT_YET_APPROVED"


def test_load_controlled_intake_config_resolves_project_paths(tmp_path: Path) -> None:
    from fleetvision.data.intake_external_dataset import load_controlled_intake_config

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
dataset_id: rf_car_damage_seg_v1
provider: roboflow
expected_classes: [Car-Damage]
mapped_class: damage
export_format: coco-segmentation
source:
  project_url: https://example.test/project
  version_url: https://example.test/project/dataset/1
  license_name: Public Domain
  license_url: https://example.test/license
  dataset_version: '1'
  reported_project_image_count: 4869
  reported_version_image_count: 11685
  lineage_status: generated_augmented_v1
paths:
  registry_csv: dataset/00_catalog/external_dataset_registry.csv
  raw_dataset_root: dataset/01_raw/99_external/roboflow/rf_car_damage_seg_v1
  metadata_root: outputs/metadata/external_assets/roboflow/rf_car_damage_seg_v1
""",
        encoding="utf-8",
    )

    config = load_controlled_intake_config(config_path, tmp_path)

    assert config.registry_csv == tmp_path / "dataset/00_catalog/external_dataset_registry.csv"
    assert config.raw_dataset_root == tmp_path / "dataset/01_raw/99_external/roboflow/rf_car_damage_seg_v1"
    assert config.expected_classes == ("Car-Damage",)
