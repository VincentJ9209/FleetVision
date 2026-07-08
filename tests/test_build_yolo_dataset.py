from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from fleetvision.data.build_yolo_dataset import build_yolo_dataset, load_config


def create_project(tmp_path: Path) -> Path:
    root = tmp_path / "FleetVision"
    for directory in [
        "configs/data",
        "dataset/04_annotations/yolo_labels_raw",
        "dataset/04_annotations",
        "dataset/01_raw/01_general_fleet/images",
        "outputs/metadata",
        "src/fleetvision",
    ]:
        (root / directory).mkdir(parents=True, exist_ok=True)
    (root / "PROJECT_CONTEXT_BRIEF.md").write_text("FleetVision", encoding="utf-8")
    return root


def write_config(root: Path, copy_images: bool = True) -> Path:
    config_path = root / "configs/data/yolo_dataset_config.yaml"
    config_path.write_text(
        f"""
annotation_manifest_csv: dataset/04_annotations/annotation_task_manifest.csv
yolo_labels_raw_dir: dataset/04_annotations/yolo_labels_raw
output_root: dataset/05_yolo/v001_damage_detect
summary_csv: outputs/metadata/yolo_dataset_summary.csv
copy_images: {str(copy_images).lower()}
strict_missing_labels: true
label_name_strategy: filename_stem
split:
  train: 0.6
  val: 0.2
  test: 0.2
  seed: 7
class_names:
  - damage
required_manifest_columns:
  - image_id
  - original_path
  - filename
allowed_image_extensions:
  - .jpg
""".strip(),
        encoding="utf-8",
    )
    return config_path


def write_manifest_and_labels(root: Path, n_rows: int = 5) -> None:
    rows = []
    image_dir = root / "dataset/01_raw/01_general_fleet/images"
    label_dir = root / "dataset/04_annotations/yolo_labels_raw"
    for index in range(n_rows):
        filename = f"car_{index:03d}.jpg"
        image_path = image_dir / filename
        image_path.write_bytes(b"fake image bytes")
        (label_dir / f"car_{index:03d}.txt").write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")
        rows.append({"image_id": f"img_{index:03d}", "original_path": image_path.relative_to(root).as_posix(), "filename": filename})
    pd.DataFrame(rows).to_csv(root / "dataset/04_annotations/annotation_task_manifest.csv", index=False)


def test_build_yolo_dataset_writes_structure(tmp_path: Path) -> None:
    root = create_project(tmp_path)
    config_path = write_config(root)
    write_manifest_and_labels(root, n_rows=5)
    config = load_config(config_path, root)

    result = build_yolo_dataset(config, root)

    assert result["written_rows"] == 5
    output_root = root / "dataset/05_yolo/v001_damage_detect"
    for split in ["train", "val", "test"]:
        assert (output_root / "images" / split).is_dir()
        assert (output_root / "labels" / split).is_dir()
    assert (output_root / "data.yaml").exists()
    data_yaml = yaml.safe_load((output_root / "data.yaml").read_text(encoding="utf-8"))
    assert data_yaml["names"] == {0: "damage"}
    summary = pd.read_csv(root / "outputs/metadata/yolo_dataset_summary.csv")
    assert summary["object_count"].sum() == 5


def test_invalid_class_id_fails(tmp_path: Path) -> None:
    root = create_project(tmp_path)
    config_path = write_config(root)
    write_manifest_and_labels(root, n_rows=1)
    (root / "dataset/04_annotations/yolo_labels_raw/car_000.txt").write_text("1 0.5 0.5 0.2 0.2\n", encoding="utf-8")
    config = load_config(config_path, root)

    with pytest.raises(ValueError, match="unsupported class id"):
        build_yolo_dataset(config, root)


def test_missing_required_manifest_column_fails(tmp_path: Path) -> None:
    root = create_project(tmp_path)
    config_path = write_config(root)
    pd.DataFrame([{"image_id": "img_001", "filename": "car_001.jpg"}]).to_csv(root / "dataset/04_annotations/annotation_task_manifest.csv", index=False)
    config = load_config(config_path, root)

    with pytest.raises(ValueError, match="missing required columns"):
        build_yolo_dataset(config, root)


def test_no_copy_images_option(tmp_path: Path) -> None:
    root = create_project(tmp_path)
    config_path = write_config(root, copy_images=False)
    write_manifest_and_labels(root, n_rows=2)
    config = load_config(config_path, root)

    result = build_yolo_dataset(config, root)

    assert result["written_rows"] == 2
    summary = pd.read_csv(root / "outputs/metadata/yolo_dataset_summary.csv")
    assert summary["image_copied"].eq(False).all()
    assert len(list((root / "dataset/05_yolo/v001_damage_detect/labels").rglob("*.txt"))) == 2
