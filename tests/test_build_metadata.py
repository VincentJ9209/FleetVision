import csv
from pathlib import Path

import pytest
import yaml
from PIL import Image

from fleetvision.data.build_metadata import build_metadata, main


def _write_image(path: Path, size: tuple[int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color=(32, 96, 160)).save(path)


def _write_config(project_root: Path) -> Path:
    config_path = project_root / "configs" / "data" / "metadata_config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config = {
        "supported_extensions": [".jpg", ".jpeg", ".png"],
        "source_buckets": {
            "01_general_fleet": "dataset/01_raw/01_general_fleet/images",
            "02_claimable_damage": "dataset/01_raw/02_claimable_damage/images",
            "03_minor_damage": "dataset/01_raw/03_minor_damage/images",
        },
        "output_csv": "outputs/metadata/image_metadata.csv",
    }
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return config_path


@pytest.fixture()
def sample_project(tmp_path: Path) -> tuple[Path, Path]:
    _write_image(
        tmp_path / "dataset" / "01_raw" / "01_general_fleet" / "images" / "general.png",
        (80, 40),
    )
    _write_image(
        tmp_path / "dataset" / "01_raw" / "02_claimable_damage" / "images" / "claim.jpg",
        (32, 64),
    )
    bad_image = (
        tmp_path
        / "dataset"
        / "01_raw"
        / "03_minor_damage"
        / "images"
        / "broken.jpg"
    )
    bad_image.parent.mkdir(parents=True, exist_ok=True)
    bad_image.write_text("not an image", encoding="utf-8")
    (
        tmp_path
        / "dataset"
        / "01_raw"
        / "03_minor_damage"
        / "images"
        / "ignore.txt"
    ).write_text("ignore me", encoding="utf-8")

    return tmp_path, _write_config(tmp_path)


def test_build_metadata_scans_buckets_and_marks_unreadable_images(
    sample_project: tuple[Path, Path],
) -> None:
    project_root, config_path = sample_project

    rows = build_metadata(config_path=config_path, project_root=project_root)

    assert [row["source_bucket"] for row in rows] == [
        "01_general_fleet",
        "02_claimable_damage",
        "03_minor_damage",
    ]
    assert len({row["image_id"] for row in rows}) == 3
    assert all(row["original_path"] for row in rows)
    assert {row["filename"] for row in rows} == {"general.png", "claim.jpg", "broken.jpg"}

    general = next(row for row in rows if row["filename"] == "general.png")
    assert general["extension"] == ".png"
    assert general["width"] == 80
    assert general["height"] == 40
    assert general["aspect_ratio"] == 2.0
    assert general["is_readable"] is True
    assert general["notes"] == ""

    broken = next(row for row in rows if row["filename"] == "broken.jpg")
    assert broken["is_readable"] is False
    assert broken["width"] is None
    assert broken["height"] is None
    assert broken["aspect_ratio"] is None
    assert "unreadable" in broken["notes"]


def test_cli_writes_metadata_csv(sample_project: tuple[Path, Path]) -> None:
    project_root, config_path = sample_project

    exit_code = main(["--config", str(config_path), "--project-root", str(project_root)])

    assert exit_code == 0
    output_csv = project_root / "outputs" / "metadata" / "image_metadata.csv"
    assert output_csv.exists()

    with output_csv.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 3
    assert rows[0].keys() >= {
        "image_id",
        "source_bucket",
        "original_path",
        "filename",
        "extension",
        "file_size_bytes",
        "width",
        "height",
        "aspect_ratio",
        "is_readable",
        "created_at",
        "modified_at",
        "notes",
    }
    assert {row["source_bucket"] for row in rows} == {
        "01_general_fleet",
        "02_claimable_damage",
        "03_minor_damage",
    }
