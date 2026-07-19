from __future__ import annotations

import csv
import importlib
import json
from pathlib import Path

import pytest

from team_pairing_audit_fixtures import (
    copy_exact_image,
    create_gradient_image,
    create_rgb_image,
    create_test_project,
)


def inventory():
    return importlib.import_module("fleetvision.data.team_pairing_audit")


def mapping():
    return importlib.import_module("fleetvision.review.team_pairing_review_mapping")


def load_config(project_root: Path, config_path: Path):
    return mapping().load_team_pairing_audit_config(config_path, project_root)


def test_discovery_order_and_image_ids_are_deterministic(tmp_path: Path) -> None:
    project_root, source_root, config_path = create_test_project(tmp_path)
    create_rgb_image(source_root / "z.JPG", color=(10, 20, 30))
    create_rgb_image(source_root / "nested" / "A.png", color=(30, 20, 10))
    (source_root / "ignore.txt").write_text("not an image", encoding="utf-8")
    config = load_config(project_root, config_path)

    first = inventory().build_team_image_inventory(config)
    second = inventory().build_team_image_inventory(config)

    assert [row["relative_path"] for row in first.rows] == ["nested/A.png", "z.JPG"]
    assert [row["image_id"] for row in first.rows] == [
        row["image_id"] for row in second.rows
    ]
    assert all(row["image_id"].startswith("team_") for row in first.rows)
    assert all(len(row["image_id"]) == 25 for row in first.rows)


def test_exif_datetime_original_has_priority(tmp_path: Path) -> None:
    project_root, source_root, config_path = create_test_project(tmp_path)
    create_rgb_image(
        source_root / "exif.jpg",
        exif_values={
            36867: "2026:07:19 09:10:11",
            36868: "2026:07:19 08:10:11",
            306: "2026:07:19 07:10:11",
        },
    )
    config = load_config(project_root, config_path)

    row = inventory().build_team_image_inventory(config).rows[0]

    assert row["selected_time_source"] == "exif_datetime_original"
    assert row["selected_capture_time"] == "2026-07-19T09:10:11+08:00"
    assert row["time_confidence"] == "high"
    assert row["capture_time_parse_warning"] == ""


def test_malformed_original_uses_digitized_and_records_warning(tmp_path: Path) -> None:
    project_root, source_root, config_path = create_test_project(tmp_path)
    create_rgb_image(
        source_root / "exif.jpg",
        exif_values={
            36867: "not-a-date",
            36868: "2026:07:19 08:10:11",
        },
    )
    config = load_config(project_root, config_path)

    row = inventory().build_team_image_inventory(config).rows[0]

    assert row["selected_time_source"] == "exif_datetime_digitized"
    assert row["selected_capture_time"] == "2026-07-19T08:10:11+08:00"
    assert "DateTimeOriginal" in row["capture_time_parse_warning"]


def test_filesystem_timestamp_is_explicit_fallback(tmp_path: Path) -> None:
    project_root, source_root, config_path = create_test_project(tmp_path)
    create_rgb_image(source_root / "no_exif.png")
    config = load_config(project_root, config_path)

    row = inventory().build_team_image_inventory(config).rows[0]

    assert row["selected_time_source"] in {
        "filesystem_created_at",
        "filesystem_modified_at",
    }
    assert row["time_confidence"] == "fallback_low"
    assert "fallback" in row["capture_time_parse_warning"].lower()


def test_unreadable_image_is_retained_but_ineligible(tmp_path: Path) -> None:
    project_root, source_root, config_path = create_test_project(
        tmp_path,
        max_unreadable_rate=1.0,
    )
    create_rgb_image(source_root / "readable.jpg")
    (source_root / "broken.jpg").write_bytes(b"not-a-real-jpeg")
    config = load_config(project_root, config_path)

    result = inventory().build_team_image_inventory(config)
    broken = next(row for row in result.rows if row["filename"] == "broken.jpg")

    assert broken["is_readable"] is False
    assert broken["width"] is None
    assert broken["height"] is None
    assert broken["perceptual_hash"] == ""
    assert broken["eligible_for_batch_candidate"] is False
    assert broken["read_error"]


def test_exact_duplicates_share_group_and_only_stable_rep_is_eligible(
    tmp_path: Path,
) -> None:
    project_root, source_root, config_path = create_test_project(tmp_path)
    original = create_gradient_image(source_root / "a.jpg")
    copy_exact_image(original, source_root / "b.jpg")
    config = load_config(project_root, config_path)

    rows = inventory().build_team_image_inventory(config).rows
    a_row, b_row = rows

    assert a_row["sha256"] == b_row["sha256"]
    assert a_row["exact_duplicate_group"] == b_row["exact_duplicate_group"]
    assert a_row["exact_duplicate_group"].startswith("exact_")
    assert a_row["representative_for_exact_group"] is True
    assert b_row["representative_for_exact_group"] is False
    assert a_row["eligible_for_batch_candidate"] is True
    assert b_row["eligible_for_batch_candidate"] is False


def test_near_duplicate_group_is_stable_representative_centered() -> None:
    rows = [
        {
            "image_id": "team_a",
            "relative_path": "a.jpg",
            "is_readable": True,
            "sha256": "A" * 64,
            "perceptual_hash": "0000000000000000",
        },
        {
            "image_id": "team_b",
            "relative_path": "b.jpg",
            "is_readable": True,
            "sha256": "B" * 64,
            "perceptual_hash": "0000000000000001",
        },
        {
            "image_id": "team_c",
            "relative_path": "c.jpg",
            "is_readable": True,
            "sha256": "C" * 64,
            "perceptual_hash": "0000000000000003",
        },
    ]

    audited = inventory().assign_duplicate_groups(rows, phash_distance_threshold=1)
    by_id = {row["image_id"]: row for row in audited}

    assert by_id["team_a"]["near_duplicate_group_candidate"]
    assert (
        by_id["team_a"]["near_duplicate_group_candidate"]
        == by_id["team_b"]["near_duplicate_group_candidate"]
    )
    assert by_id["team_c"]["near_duplicate_group_candidate"] == ""


def test_phash_is_deterministic_64_bit_hex(tmp_path: Path) -> None:
    image_path = create_gradient_image(tmp_path / "gradient.png", delta=2)

    first = inventory().compute_phash64(image_path)
    second = inventory().compute_phash64(image_path)

    assert first == second
    assert len(first) == 16
    int(first, 16)


def test_source_snapshot_detects_byte_mutation(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    image_path = create_rgb_image(source_root / "a.jpg")
    before = inventory().build_source_snapshot(source_root)
    image_path.write_bytes(image_path.read_bytes() + b"mutation")
    after = inventory().build_source_snapshot(source_root)

    with pytest.raises(inventory().SourceMutationError, match="byte-identical"):
        inventory().verify_source_snapshots(before, after)


def test_atomic_csv_json_writes_are_no_overwrite_and_block_raw(tmp_path: Path) -> None:
    project_root, source_root, config_path = create_test_project(tmp_path)
    create_rgb_image(source_root / "a.jpg")
    config = load_config(project_root, config_path)
    output_dir = config.output_root / "unit"
    csv_path = output_dir / "rows.csv"
    json_path = output_dir / "summary.json"

    inventory().atomic_write_csv(
        [{"a": "1", "b": "2"}],
        csv_path,
        fieldnames=("a", "b"),
        config=config,
    )
    inventory().atomic_write_json({"ok": True}, json_path, config=config)

    with csv_path.open(newline="", encoding="utf-8") as handle:
        assert list(csv.DictReader(handle)) == [{"a": "1", "b": "2"}]
    assert json.loads(json_path.read_text(encoding="utf-8")) == {"ok": True}

    with pytest.raises(FileExistsError):
        inventory().atomic_write_json({"ok": False}, json_path, config=config)

    raw_output = project_root / "dataset" / "01_raw" / "forbidden.json"
    with pytest.raises(inventory().TeamPairingAuditError, match="output root"):
        inventory().atomic_write_json({"ok": False}, raw_output, config=config)


def test_zero_supported_images_is_blocked(tmp_path: Path) -> None:
    project_root, source_root, config_path = create_test_project(tmp_path)
    (source_root / "notes.txt").write_text("no supported images", encoding="utf-8")
    config = load_config(project_root, config_path)

    with pytest.raises(inventory().TeamPairingAuditError, match="zero supported images"):
        inventory().build_team_image_inventory(config)


def test_full_inventory_build_keeps_all_source_bytes_unchanged(tmp_path: Path) -> None:
    project_root, source_root, config_path = create_test_project(tmp_path)
    create_gradient_image(source_root / "a.png")
    create_gradient_image(source_root / "b.png", delta=3)
    config = load_config(project_root, config_path)
    before = inventory().build_source_snapshot(source_root)

    result = inventory().build_team_image_inventory(config)
    after = inventory().build_source_snapshot(source_root)

    verification = inventory().verify_source_snapshots(before, after)
    assert verification["byte_identical"] is True
    assert result.source_snapshot_verification["byte_identical"] is True
    assert all(
        row["source_snapshot_sha256"] == before["snapshot_sha256"]
        for row in result.rows
    )


def _batch_row(
    image_id: str,
    selected_capture_time: str,
    *,
    relative_path: str | None = None,
    time_confidence: str = "high",
    exact_duplicate_group: str = "",
    representative: bool = True,
    eligible: bool = True,
) -> dict[str, object]:
    relative = relative_path or f"{image_id}.jpg"
    return {
        "image_id": image_id,
        "filename": Path(relative).name,
        "relative_path": relative,
        "original_path": f"dataset/01_raw/04_team/{relative}",
        "is_readable": True,
        "selected_capture_time": selected_capture_time,
        "selected_time_source": "exif_datetime_original" if selected_capture_time else "missing",
        "time_confidence": time_confidence,
        "exact_duplicate_group": exact_duplicate_group,
        "representative_for_exact_group": representative,
        "eligible_for_batch_candidate": eligible,
        "width": 64,
        "height": 48,
        "sha256": image_id.upper().ljust(64, "0")[:64],
    }


class TestCaptureBatchCandidates:
    def test_exactly_ten_minutes_remains_one_batch(self, tmp_path: Path) -> None:
        project_root, _, config_path = create_test_project(tmp_path)
        config = load_config(project_root, config_path)
        rows = [
            _batch_row("team_a", "2026-07-19T09:00:00+08:00"),
            _batch_row("team_b", "2026-07-19T09:10:00+08:00"),
        ]

        result = inventory().build_capture_batch_candidates(rows, config)

        assert len(result.batches) == 1
        assert result.batches[0]["duration_seconds"] == 600
        assert result.batches[0]["image_count"] == 2

    def test_more_than_ten_minutes_starts_new_batch(self, tmp_path: Path) -> None:
        project_root, _, config_path = create_test_project(tmp_path)
        config = load_config(project_root, config_path)
        rows = [
            _batch_row("team_a", "2026-07-19T09:00:00+08:00"),
            _batch_row("team_b", "2026-07-19T09:10:01+08:00"),
        ]

        result = inventory().build_capture_batch_candidates(rows, config)

        assert len(result.batches) == 2
        assert [batch["image_count"] for batch in result.batches] == [1, 1]

    def test_calendar_date_boundary_always_splits(self, tmp_path: Path) -> None:
        project_root, _, config_path = create_test_project(tmp_path)
        config = load_config(project_root, config_path)
        rows = [
            _batch_row("team_a", "2026-07-19T23:59:00+08:00"),
            _batch_row("team_b", "2026-07-20T00:01:00+08:00"),
        ]

        result = inventory().build_capture_batch_candidates(rows, config)

        assert len(result.batches) == 2

    def test_low_confidence_and_missing_times_are_isolated(self, tmp_path: Path) -> None:
        project_root, _, config_path = create_test_project(tmp_path)
        config = load_config(project_root, config_path)
        rows = [
            _batch_row("team_high", "2026-07-19T09:00:00+08:00"),
            _batch_row(
                "team_low",
                "2026-07-19T09:01:00+08:00",
                time_confidence="fallback_low",
            ),
            _batch_row("team_missing", "", time_confidence="missing"),
        ]

        result = inventory().build_capture_batch_candidates(rows, config)

        assert len(result.batches) == 3
        assert sum(
            batch["batch_confidence"] == "manual_review_required"
            for batch in result.batches
        ) == 2

    def test_exact_duplicate_members_remain_traceable_but_not_double_counted(
        self,
        tmp_path: Path,
    ) -> None:
        project_root, _, config_path = create_test_project(tmp_path)
        config = load_config(project_root, config_path)
        rows = [
            _batch_row(
                "team_rep",
                "2026-07-19T09:00:00+08:00",
                exact_duplicate_group="exact_same",
            ),
            _batch_row(
                "team_duplicate",
                "2026-07-19T09:00:00+08:00",
                exact_duplicate_group="exact_same",
                representative=False,
                eligible=False,
            ),
            _batch_row("team_other", "2026-07-19T09:05:00+08:00"),
        ]

        result = inventory().build_capture_batch_candidates(rows, config)

        assert len(result.batches) == 1
        assert result.batches[0]["image_count"] == 2
        assert len(result.members) == 3
        duplicate = next(
            member for member in result.members if member["image_id"] == "team_duplicate"
        )
        assert duplicate["membership_role"] == "exact_duplicate_trace"
        assert duplicate["batch_id"] == result.batches[0]["batch_id"]

    def test_batch_ids_and_member_order_are_deterministic(self, tmp_path: Path) -> None:
        project_root, _, config_path = create_test_project(tmp_path)
        config = load_config(project_root, config_path)
        rows = [
            _batch_row("team_b", "2026-07-19T09:05:00+08:00", relative_path="b.jpg"),
            _batch_row("team_a", "2026-07-19T09:00:00+08:00", relative_path="a.jpg"),
        ]

        first = inventory().build_capture_batch_candidates(rows, config)
        second = inventory().build_capture_batch_candidates(list(reversed(rows)), config)

        assert first.batches == second.batches
        assert first.members == second.members
        assert first.batches[0]["batch_id"].startswith("batch_")
        assert len(first.batches[0]["batch_id"]) == 26

    def test_contact_sheet_is_deterministic_and_source_remains_unchanged(
        self,
        tmp_path: Path,
    ) -> None:
        project_root, source_root, config_path = create_test_project(
            tmp_path,
            contact_sheet_columns=4,
            contact_sheet_thumbnail_size=80,
        )
        for index in range(5):
            create_rgb_image(
                source_root / f"image_{index}.jpg",
                color=(20 + index, 60 + index, 100 + index),
            )
        config = load_config(project_root, config_path)
        inventory_result = inventory().build_team_image_inventory(config)
        rows = []
        for index, raw in enumerate(inventory_result.rows):
            row = dict(raw)
            row["selected_capture_time"] = f"2026-07-19T09:0{index}:00+08:00"
            row["selected_time_source"] = "exif_datetime_original"
            row["time_confidence"] = "high"
            rows.append(row)
        batch_result = inventory().build_capture_batch_candidates(rows, config)
        before = inventory().build_source_snapshot(source_root)

        first = inventory().create_batch_contact_sheet(
            batch_result.batches[0],
            list(reversed(batch_result.members)),
            rows,
            config.output_root / "sheets" / "first.jpg",
            config,
        )
        second = inventory().create_batch_contact_sheet(
            batch_result.batches[0],
            batch_result.members,
            rows,
            config.output_root / "sheets" / "second.jpg",
            config,
        )
        after = inventory().build_source_snapshot(source_root)

        with inventory().Image.open(first) as sheet:
            assert sheet.size == (440, 360)
        assert inventory().sha256_file(first) == inventory().sha256_file(second)
        assert inventory().verify_source_snapshots(before, after)["byte_identical"] is True

    def test_batch_candidate_csv_artifacts_are_atomic_and_no_overwrite(
        self,
        tmp_path: Path,
    ) -> None:
        project_root, _, config_path = create_test_project(tmp_path)
        config = load_config(project_root, config_path)
        rows = [
            _batch_row("team_a", "2026-07-19T09:00:00+08:00"),
            _batch_row("team_b", "2026-07-19T09:05:00+08:00"),
        ]
        result = inventory().build_capture_batch_candidates(rows, config)
        candidates_dir = config.output_root / "workspace" / "candidates"

        paths = inventory().write_capture_batch_artifacts(result, candidates_dir, config)

        with paths["batches"].open(newline="", encoding="utf-8") as handle:
            assert tuple(next(csv.reader(handle))) == inventory().BATCH_CANDIDATE_COLUMNS
        with paths["members"].open(newline="", encoding="utf-8") as handle:
            assert tuple(next(csv.reader(handle))) == inventory().BATCH_MEMBER_COLUMNS
        with pytest.raises(FileExistsError):
            inventory().write_capture_batch_artifacts(result, candidates_dir, config)
