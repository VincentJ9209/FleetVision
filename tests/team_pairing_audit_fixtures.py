from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import yaml
from PIL import Image


def valid_team_pairing_config() -> dict[str, object]:
    return {
        "schema_version": "1",
        "source_relative_path": "dataset/01_raw/04_team",
        "output_relative_path": "outputs/phase05s/team_pairing_audit",
        "supported_extensions": [".JPG", ".jpeg", ".png", ".webp", ".jfif"],
        "batch_gap_minutes": 10,
        "pair_max_elapsed_hours": 12,
        "phash_distance_threshold": 6,
        "contact_sheet_columns": 4,
        "contact_sheet_thumbnail_size": 320,
        "timezone": "Asia/Taipei",
        "reviewer": "Vincent",
        "backup_every_successful_saves": 10,
        "backup_retention": 20,
        "max_unreadable_rate": 0.25,
        "frozen_test_access": False,
    }


def write_team_pairing_config(path: Path, **overrides: object) -> Path:
    payload = valid_team_pairing_config()
    payload.update(overrides)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def create_test_project(tmp_path: Path, **config_overrides: object) -> tuple[Path, Path, Path]:
    project_root = tmp_path / "FleetVision"
    source_root = project_root / "dataset" / "01_raw" / "04_team"
    source_root.mkdir(parents=True)
    config_path = write_team_pairing_config(
        project_root / "configs" / "data" / "team_pairing_audit_config.yaml",
        **config_overrides,
    )
    return project_root, source_root, config_path


def create_rgb_image(
    path: Path,
    *,
    color: tuple[int, int, int] = (80, 120, 160),
    size: tuple[int, int] = (64, 48),
    exif_values: dict[int, str] | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", size, color)
    if exif_values:
        exif = Image.Exif()
        for tag, value in exif_values.items():
            exif[tag] = value
        image.save(path, exif=exif)
    else:
        image.save(path)
    return path


def create_gradient_image(path: Path, *, delta: int = 0) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    height, width = 64, 64
    x = np.linspace(0, 255, width, dtype=np.uint8)
    pixels = np.tile(x, (height, 1))
    rgb = np.stack([pixels, np.flipud(pixels), pixels], axis=2)
    if delta:
        rgb = rgb.copy()
        rgb[4:8, 4:8, 0] = np.clip(
            rgb[4:8, 4:8, 0].astype(np.int16) + delta,
            0,
            255,
        ).astype(np.uint8)
    Image.fromarray(rgb, mode="RGB").save(path)
    return path


def copy_exact_image(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    return destination
