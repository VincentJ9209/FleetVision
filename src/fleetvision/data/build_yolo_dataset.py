"""Build a YOLOv8 detection dataset from raw YOLO label files.

Phase 06 intentionally supports only one minimal and stable input format:

- annotation task manifest CSV with image paths
- raw YOLO label txt files

It does not parse CVAT or Label Studio exports directly. Export those tools to
YOLO txt first, then use this builder.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

DEFAULT_CONFIG = Path("configs/data/yolo_dataset_config.yaml")
DEFAULT_CLASS_NAMES = ["damage"]
SPLITS = ("train", "val", "test")


@dataclass(frozen=True)
class YoloDatasetConfig:
    annotation_manifest_csv: Path
    yolo_labels_raw_dir: Path
    output_root: Path
    summary_csv: Path
    copy_images: bool
    strict_missing_labels: bool
    label_name_strategy: str
    split_ratios: dict[str, float]
    split_seed: int
    class_names: list[str]
    required_manifest_columns: list[str]
    allowed_image_extensions: set[str]


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    markers = ["PROJECT_CONTEXT_BRIEF.md", "src/fleetvision", "configs/data"]
    for path in [current, *current.parents]:
        if all((path / marker).exists() for marker in markers):
            return path
    return current


def resolve_path(path: Path, project_root: Path) -> Path:
    return path if path.is_absolute() else project_root / path


def load_config(config_path: Path, project_root: Path) -> YoloDatasetConfig:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file) or {}

    split = raw.get("split", {}) or {}
    split_ratios = {
        "train": float(split.get("train", 0.8)),
        "val": float(split.get("val", 0.1)),
        "test": float(split.get("test", 0.1)),
    }
    validate_split_ratios(split_ratios)

    class_names = list(raw.get("class_names", DEFAULT_CLASS_NAMES))
    if class_names != ["damage"]:
        raise ValueError("Phase 06 v1 supports exactly one class: damage")

    required_manifest_columns = list(raw.get("required_manifest_columns", ["image_id", "original_path", "filename"]))
    allowed_extensions = {
        ext.lower() if str(ext).startswith(".") else f".{str(ext).lower()}"
        for ext in raw.get("allowed_image_extensions", [".jpg", ".jpeg", ".png", ".bmp", ".webp"])
    }

    label_name_strategy = str(raw.get("label_name_strategy", "filename_stem"))
    if label_name_strategy not in {"filename_stem", "image_id"}:
        raise ValueError("label_name_strategy must be 'filename_stem' or 'image_id'")

    return YoloDatasetConfig(
        annotation_manifest_csv=resolve_path(Path(raw.get("annotation_manifest_csv", "dataset/04_annotations/annotation_task_manifest.csv")), project_root),
        yolo_labels_raw_dir=resolve_path(Path(raw.get("yolo_labels_raw_dir", "dataset/04_annotations/yolo_labels_raw")), project_root),
        output_root=resolve_path(Path(raw.get("output_root", "dataset/05_yolo/v001_damage_detect")), project_root),
        summary_csv=resolve_path(Path(raw.get("summary_csv", "outputs/metadata/yolo_dataset_summary.csv")), project_root),
        copy_images=bool(raw.get("copy_images", True)),
        strict_missing_labels=bool(raw.get("strict_missing_labels", True)),
        label_name_strategy=label_name_strategy,
        split_ratios=split_ratios,
        split_seed=int(split.get("seed", 42)),
        class_names=class_names,
        required_manifest_columns=required_manifest_columns,
        allowed_image_extensions=allowed_extensions,
    )


def validate_split_ratios(split_ratios: dict[str, float]) -> None:
    if set(split_ratios) != set(SPLITS):
        raise ValueError("Split ratios must define train, val, and test")
    if any(value < 0 for value in split_ratios.values()):
        raise ValueError("Split ratios must be non-negative")
    total = sum(split_ratios.values())
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"Split ratios must sum to 1.0, got {total}")


def stable_hash(value: str, seed: int) -> str:
    return hashlib.sha1(f"{seed}|{value}".encode("utf-8")).hexdigest()


def assign_splits(dataframe: pd.DataFrame, seed: int, ratios: dict[str, float]) -> pd.DataFrame:
    if dataframe.empty:
        dataframe["split"] = []
        return dataframe

    work = dataframe.copy()
    key = work["image_id"].fillna(work["filename"]).astype(str)
    work["_split_hash"] = key.map(lambda value: stable_hash(value, seed))
    work = work.sort_values(["_split_hash", "filename"]).reset_index(drop=True)

    n_rows = len(work)
    n_train = int(n_rows * ratios["train"])
    n_val = int(n_rows * ratios["val"])
    if n_rows > 0 and n_train == 0 and ratios["train"] > 0:
        n_train = 1
    if n_train + n_val > n_rows:
        n_val = max(0, n_rows - n_train)

    split_values = []
    for index in range(n_rows):
        if index < n_train:
            split_values.append("train")
        elif index < n_train + n_val:
            split_values.append("val")
        else:
            split_values.append("test")
    work["split"] = split_values
    return work.drop(columns=["_split_hash"])


def validate_manifest(dataframe: pd.DataFrame, required_columns: list[str], allowed_extensions: set[str]) -> None:
    missing = [column for column in required_columns if column not in dataframe.columns]
    if missing:
        raise ValueError(f"Annotation manifest is missing required columns: {missing}")

    for column in ["image_id", "original_path", "filename"]:
        if column in dataframe.columns and dataframe[column].astype(str).str.strip().eq("").any():
            raise ValueError(f"Annotation manifest contains empty values in required column: {column}")

    invalid_extensions = sorted({Path(value).suffix.lower() for value in dataframe["filename"].astype(str) if Path(value).suffix.lower() not in allowed_extensions})
    if invalid_extensions:
        raise ValueError(f"Unsupported image extensions in manifest: {invalid_extensions}")

    duplicate_image_ids = dataframe["image_id"].duplicated().sum()
    if duplicate_image_ids:
        raise ValueError(f"Annotation manifest contains duplicated image_id values: {duplicate_image_ids}")


def label_path_for_row(row: pd.Series, labels_dir: Path, strategy: str) -> Path:
    if strategy == "image_id":
        stem = str(row["image_id"])
    else:
        stem = Path(str(row["filename"])).stem
    return labels_dir / f"{stem}.txt"


def validate_yolo_label_file(label_path: Path) -> tuple[int, list[str]]:
    errors: list[str] = []
    if not label_path.exists():
        return 0, [f"missing label file: {label_path}"]

    lines = [line.strip() for line in label_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for line_number, line in enumerate(lines, start=1):
        parts = line.split()
        if len(parts) != 5:
            errors.append(f"{label_path.name}:{line_number} expected 5 columns, got {len(parts)}")
            continue
        class_id_raw, *bbox_raw = parts
        try:
            class_id = int(class_id_raw)
        except ValueError:
            errors.append(f"{label_path.name}:{line_number} class id is not an integer: {class_id_raw}")
            continue
        if class_id != 0:
            errors.append(f"{label_path.name}:{line_number} unsupported class id {class_id}; expected 0 for damage")

        try:
            x_center, y_center, width, height = [float(value) for value in bbox_raw]
        except ValueError:
            errors.append(f"{label_path.name}:{line_number} bbox values must be numeric")
            continue
        if not (0.0 <= x_center <= 1.0):
            errors.append(f"{label_path.name}:{line_number} x_center must be in [0, 1]")
        if not (0.0 <= y_center <= 1.0):
            errors.append(f"{label_path.name}:{line_number} y_center must be in [0, 1]")
        if not (0.0 < width <= 1.0):
            errors.append(f"{label_path.name}:{line_number} width must be in (0, 1]")
        if not (0.0 < height <= 1.0):
            errors.append(f"{label_path.name}:{line_number} height must be in (0, 1]")
    return len(lines), errors


def ensure_output_dirs(output_root: Path) -> None:
    for kind in ["images", "labels"]:
        for split in SPLITS:
            (output_root / kind / split).mkdir(parents=True, exist_ok=True)


def write_data_yaml(output_root: Path, class_names: list[str]) -> Path:
    data_yaml = output_root / "data.yaml"
    payload = {
        "path": str(output_root.as_posix()),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": {index: name for index, name in enumerate(class_names)},
    }
    data_yaml.parent.mkdir(parents=True, exist_ok=True)
    with data_yaml.open("w", encoding="utf-8") as file:
        yaml.safe_dump(payload, file, sort_keys=False, allow_unicode=True)
    return data_yaml


def copy_or_verify_image(source_path: Path, destination_path: Path, copy_images: bool) -> bool:
    if not source_path.exists():
        if copy_images:
            raise FileNotFoundError(f"Image file not found: {source_path}")
        return False
    if copy_images:
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)
        return True
    return False


def build_yolo_dataset(config: YoloDatasetConfig, project_root: Path) -> dict[str, Any]:
    if not config.annotation_manifest_csv.exists():
        raise FileNotFoundError(f"Annotation manifest not found: {config.annotation_manifest_csv}")
    if not config.yolo_labels_raw_dir.exists():
        raise FileNotFoundError(f"YOLO labels raw directory not found: {config.yolo_labels_raw_dir}")

    manifest = pd.read_csv(config.annotation_manifest_csv)
    validate_manifest(manifest, config.required_manifest_columns, config.allowed_image_extensions)
    manifest = assign_splits(manifest, config.split_seed, config.split_ratios)

    ensure_output_dirs(config.output_root)
    data_yaml = write_data_yaml(config.output_root, config.class_names)

    summary_rows: list[dict[str, Any]] = []
    validation_errors: list[str] = []

    for _, row in manifest.iterrows():
        split = str(row["split"])
        image_source = resolve_path(Path(str(row["original_path"])), project_root)
        image_destination = config.output_root / "images" / split / str(row["filename"])
        label_source = label_path_for_row(row, config.yolo_labels_raw_dir, config.label_name_strategy)
        label_destination = config.output_root / "labels" / split / f"{Path(str(row['filename'])).stem}.txt"

        object_count, label_errors = validate_yolo_label_file(label_source)
        if label_errors:
            validation_errors.extend([f"image_id={row['image_id']}: {error}" for error in label_errors])
            if config.strict_missing_labels:
                continue

        image_copied = copy_or_verify_image(image_source, image_destination, config.copy_images)
        label_destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(label_source, label_destination)

        summary_rows.append(
            {
                "image_id": row["image_id"],
                "filename": row["filename"],
                "split": split,
                "image_source": str(image_source.as_posix()),
                "image_output": str(image_destination.as_posix()),
                "label_source": str(label_source.as_posix()),
                "label_output": str(label_destination.as_posix()),
                "object_count": object_count,
                "image_copied": image_copied,
            }
        )

    if validation_errors and config.strict_missing_labels:
        preview = " | ".join(validation_errors[:10])
        raise ValueError(f"YOLO label validation failed with {len(validation_errors)} error(s): {preview}")

    summary = pd.DataFrame(summary_rows)
    config.summary_csv.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(config.summary_csv, index=False, encoding="utf-8-sig")

    split_counts = summary["split"].value_counts().to_dict() if not summary.empty else {}
    return {
        "total_manifest_rows": int(len(manifest)),
        "written_rows": int(len(summary)),
        "split_counts": {split: int(split_counts.get(split, 0)) for split in SPLITS},
        "data_yaml": data_yaml,
        "summary_csv": config.summary_csv,
        "output_root": config.output_root,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a YOLOv8 dataset from raw YOLO labels.")
    parser.add_argument("--project-root", type=Path, default=None, help="FleetVision project root. Default: auto-detect.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Path to YOLO dataset config YAML.")
    parser.add_argument("--manifest", type=Path, default=None, help="Override annotation task manifest CSV.")
    parser.add_argument("--labels-dir", type=Path, default=None, help="Override raw YOLO labels directory.")
    parser.add_argument("--output-root", type=Path, default=None, help="Override YOLO dataset output root.")
    parser.add_argument("--summary-output", type=Path, default=None, help="Override summary CSV output path.")
    parser.add_argument("--no-copy-images", action="store_true", help="Validate images and labels without copying images into the YOLO dataset output.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = find_project_root(args.project_root)
    config_path = resolve_path(args.config, project_root)
    config = load_config(config_path, project_root)

    if args.manifest is not None:
        config = YoloDatasetConfig(**{**config.__dict__, "annotation_manifest_csv": resolve_path(args.manifest, project_root)})
    if args.labels_dir is not None:
        config = YoloDatasetConfig(**{**config.__dict__, "yolo_labels_raw_dir": resolve_path(args.labels_dir, project_root)})
    if args.output_root is not None:
        config = YoloDatasetConfig(**{**config.__dict__, "output_root": resolve_path(args.output_root, project_root)})
    if args.summary_output is not None:
        config = YoloDatasetConfig(**{**config.__dict__, "summary_csv": resolve_path(args.summary_output, project_root)})
    if args.no_copy_images:
        config = YoloDatasetConfig(**{**config.__dict__, "copy_images": False})

    result = build_yolo_dataset(config, project_root)
    print(f"total_manifest_rows: {result['total_manifest_rows']}")
    print(f"written_rows: {result['written_rows']}")
    for split, count in result["split_counts"].items():
        print(f"{split}_rows: {count}")
    print(f"output_root: {result['output_root']}")
    print(f"data_yaml: {result['data_yaml']}")
    print(f"summary_csv: {result['summary_csv']}")


if __name__ == "__main__":
    main()
