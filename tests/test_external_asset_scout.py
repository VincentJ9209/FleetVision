from __future__ import annotations

from pathlib import Path

import pandas as pd

from fleetvision.data.external_asset_scout import (
    REGISTRY_COLUMNS,
    load_config,
    run,
    validate_registry,
    write_registry_template,
)


def write_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "configs/data/external_asset_scout_config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        """
registry_csv: dataset/00_catalog/external_asset_registry.csv
summary_csv: outputs/metadata/external_asset_scout_summary.csv
external_data_roots:
  external_raw_root: dataset/01_raw/99_external
  external_yolo_labels_raw_root: dataset/04_annotations/external_yolo_labels_raw
  external_assets_metadata_root: outputs/metadata/external_assets
provider_subdirs:
  - kaggle
  - roboflow
future_yolo_dataset_roots:
  external_pretrain: dataset/05_yolo/v002_damage_detect_external_pretrain
allowed_values:
  platform: [kaggle, roboflow, huggingface, github, other]
  task_type: [object_detection, segmentation, classification, unknown]
  annotation_format: [yolo, coco, voc, cvat, labelstudio, image_only, unknown]
  decision: [pending, approved_for_download, rejected, downloaded, audited, converted]
boolean_columns:
  - has_bbox
  - has_yolo_format
  - can_map_to_damage
  - can_use_for_training
  - can_use_for_prelabel
""".strip(),
        encoding="utf-8",
    )
    return config_path


def test_run_initializes_registry_and_dirs(tmp_path: Path) -> None:
    config = load_config(write_config(tmp_path), tmp_path)

    result = run(config, overwrite=False, validate=True)

    assert result["registry_written"] is True
    assert config.registry_csv.exists()
    assert config.summary_csv.exists()
    assert list(pd.read_csv(config.registry_csv).columns) == REGISTRY_COLUMNS
    assert (tmp_path / "dataset/01_raw/99_external/kaggle").is_dir()
    assert (tmp_path / "dataset/01_raw/99_external/roboflow").is_dir()
    assert (tmp_path / "dataset/04_annotations/external_yolo_labels_raw/kaggle").is_dir()
    assert (tmp_path / "dataset/05_yolo/v002_damage_detect_external_pretrain").is_dir()


def test_registry_template_is_not_overwritten_without_flag(tmp_path: Path) -> None:
    config = load_config(write_config(tmp_path), tmp_path)
    write_registry_template(config.registry_csv, overwrite=True)
    config.registry_csv.write_text("custom\nvalue\n", encoding="utf-8")

    written = write_registry_template(config.registry_csv, overwrite=False)

    assert written is False
    assert config.registry_csv.read_text(encoding="utf-8").startswith("custom")


def test_validate_registry_accepts_valid_rows(tmp_path: Path) -> None:
    config = load_config(write_config(tmp_path), tmp_path)
    config.registry_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "asset_id": "kaggle_cardd_yolo",
                "source_name": "CarDD YOLO candidate",
                "platform": "kaggle",
                "url_or_slug": "owner/dataset-slug",
                "license": "check_required",
                "dataset_size": "unknown",
                "task_type": "object_detection",
                "annotation_format": "yolo",
                "classes": "damage candidates",
                "image_count": "unknown",
                "has_bbox": "true",
                "has_yolo_format": "true",
                "can_map_to_damage": "true",
                "can_use_for_training": "unknown",
                "can_use_for_prelabel": "true",
                "risk_notes": "license must be checked manually",
                "decision": "pending",
                "reviewer": "vincent",
                "last_checked_at": "",
            }
        ],
        columns=REGISTRY_COLUMNS,
    ).to_csv(config.registry_csv, index=False)

    errors = validate_registry(config.registry_csv, config)

    assert errors == []


def test_validate_registry_reports_invalid_values(tmp_path: Path) -> None:
    config = load_config(write_config(tmp_path), tmp_path)
    config.registry_csv.parent.mkdir(parents=True, exist_ok=True)
    row = {column: "" for column in REGISTRY_COLUMNS}
    row.update(
        {
            "asset_id": "bad_asset",
            "platform": "unknown_platform",
            "task_type": "bad_task",
            "annotation_format": "bad_format",
            "decision": "bad_decision",
            "has_bbox": "maybe",
        }
    )
    pd.DataFrame([row], columns=REGISTRY_COLUMNS).to_csv(config.registry_csv, index=False)

    errors = validate_registry(config.registry_csv, config)

    assert any("invalid platform" in error for error in errors)
    assert any("invalid task_type" in error for error in errors)
    assert any("invalid annotation_format" in error for error in errors)
    assert any("invalid decision" in error for error in errors)
    assert any("invalid has_bbox" in error for error in errors)
