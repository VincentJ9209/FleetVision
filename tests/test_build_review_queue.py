import csv
from pathlib import Path

import yaml

from fleetvision.data.build_review_queue import REVIEW_QUEUE_COLUMNS, build_review_queue, main


METADATA_COLUMNS = [
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
]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=METADATA_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def _metadata_rows() -> list[dict[str, object]]:
    return [
        {
            "image_id": "general-1",
            "source_bucket": "01_general_fleet",
            "original_path": "dataset/01_raw/01_general_fleet/images/general.png",
            "filename": "general.png",
            "extension": ".png",
            "file_size_bytes": 1000,
            "width": 80,
            "height": 40,
            "aspect_ratio": 2.0,
            "is_readable": True,
            "created_at": "2026-07-08T00:00:00+00:00",
            "modified_at": "2026-07-08T00:00:00+00:00",
            "notes": "",
        },
        {
            "image_id": "claim-1",
            "source_bucket": "02_claimable_damage",
            "original_path": "dataset/01_raw/02_claimable_damage/images/claim.jpg",
            "filename": "claim.jpg",
            "extension": ".jpg",
            "file_size_bytes": 2000,
            "width": 64,
            "height": 64,
            "aspect_ratio": 1.0,
            "is_readable": True,
            "created_at": "2026-07-08T00:00:00+00:00",
            "modified_at": "2026-07-08T00:00:00+00:00",
            "notes": "",
        },
        {
            "image_id": "minor-1",
            "source_bucket": "03_minor_damage",
            "original_path": "dataset/01_raw/03_minor_damage/images/minor.jpg",
            "filename": "minor.jpg",
            "extension": ".jpg",
            "file_size_bytes": 1500,
            "width": 50,
            "height": 100,
            "aspect_ratio": 0.5,
            "is_readable": True,
            "created_at": "2026-07-08T00:00:00+00:00",
            "modified_at": "2026-07-08T00:00:00+00:00",
            "notes": "",
        },
        {
            "image_id": "broken-1",
            "source_bucket": "02_claimable_damage",
            "original_path": "dataset/01_raw/02_claimable_damage/images/broken.jpg",
            "filename": "broken.jpg",
            "extension": ".jpg",
            "file_size_bytes": 12,
            "width": "",
            "height": "",
            "aspect_ratio": "",
            "is_readable": False,
            "created_at": "2026-07-08T00:00:00+00:00",
            "modified_at": "2026-07-08T00:00:00+00:00",
            "notes": "unreadable: UnidentifiedImageError",
        },
    ]


def _write_config(project_root: Path, input_csv: Path) -> Path:
    config_path = project_root / "configs" / "data" / "review_queue_config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config = {
        "input_csv": str(input_csv.relative_to(project_root)),
        "output_csv": "dataset/02_interim/03_review_queue/review_queue.csv",
        "summary_csv": "outputs/metadata/review_queue_summary.csv",
        "priority_by_source_bucket": {
            "02_claimable_damage": 10,
            "03_minor_damage": 20,
            "01_general_fleet": 30,
        },
        "default_priority": 90,
        "unreadable_priority_offset": 100,
    }
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return config_path


def test_build_review_queue_creates_expected_fields_and_priority_order(tmp_path: Path) -> None:
    input_csv = tmp_path / "outputs" / "metadata" / "image_metadata.csv"
    _write_csv(input_csv, _metadata_rows())
    config_path = _write_config(tmp_path, input_csv)

    rows = build_review_queue(
        input_csv=input_csv,
        config_path=config_path,
        project_root=tmp_path,
    )

    assert [row["filename"] for row in rows] == [
        "claim.jpg",
        "minor.jpg",
        "general.png",
        "broken.jpg",
    ]
    assert list(rows[0].keys()) == REVIEW_QUEUE_COLUMNS
    assert len({row["review_id"] for row in rows}) == 4
    assert rows[0]["priority"] == 10
    assert rows[0]["quality_status"] == "ready"
    assert rows[0]["photo_type_review"] == "unknown"
    assert rows[0]["angle_review"] == "unknown"
    assert rows[0]["is_exterior_review"] == "unknown"
    assert rows[0]["has_visible_damage_review"] == "unknown"
    assert rows[0]["severity_review"] == "unknown"
    assert rows[0]["review_status"] == "pending"
    assert rows[0]["reviewer"] == ""
    assert rows[0]["review_notes"] == ""

    unreadable = rows[-1]
    assert unreadable["filename"] == "broken.jpg"
    assert unreadable["quality_status"] == "unreadable"
    assert unreadable["priority"] == 110
    assert unreadable["priority_reason"] == "source_bucket=02_claimable_damage; unreadable"


def test_build_review_queue_respects_max_rows(tmp_path: Path) -> None:
    input_csv = tmp_path / "outputs" / "metadata" / "image_metadata.csv"
    _write_csv(input_csv, _metadata_rows())
    config_path = _write_config(tmp_path, input_csv)

    rows = build_review_queue(
        input_csv=input_csv,
        config_path=config_path,
        project_root=tmp_path,
        max_rows=2,
    )

    assert [row["filename"] for row in rows] == ["claim.jpg", "minor.jpg"]


def test_cli_writes_review_queue_and_summary(tmp_path: Path) -> None:
    input_csv = tmp_path / "outputs" / "metadata" / "image_metadata.csv"
    _write_csv(input_csv, _metadata_rows())
    config_path = _write_config(tmp_path, input_csv)

    exit_code = main(
        [
            "--config",
            str(config_path),
            "--project-root",
            str(tmp_path),
            "--max-rows",
            "3",
        ]
    )

    assert exit_code == 0
    output_csv = tmp_path / "dataset" / "02_interim" / "03_review_queue" / "review_queue.csv"
    summary_csv = tmp_path / "outputs" / "metadata" / "review_queue_summary.csv"
    assert output_csv.exists()
    assert summary_csv.exists()

    rows = _read_csv(output_csv)
    summary_rows = _read_csv(summary_csv)
    assert [row["filename"] for row in rows] == ["claim.jpg", "minor.jpg", "general.png"]
    assert {row["metric"] for row in summary_rows} >= {
        "total_rows",
        "source_bucket:01_general_fleet",
        "source_bucket:02_claimable_damage",
        "source_bucket:03_minor_damage",
        "quality_status:ready",
    }
