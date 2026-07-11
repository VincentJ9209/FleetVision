from __future__ import annotations

import copy
import csv
import importlib.util
import json
import os
import shutil
from pathlib import Path
from typing import Any

import pytest

import fleetvision.data.repair_external_coco_bbox as repair_module
from fleetvision.data.repair_external_coco_bbox import (
    BboxRepairConfig,
    BboxRepairError,
    build_external_coco_bbox_repair,
    classify_bbox_invalid_reasons,
    clip_bbox_to_image,
    load_bbox_repair_config,
    repair_coco_payload,
    sha256_file,
)


def make_policy(tmp_path: Path, **overrides: Any) -> BboxRepairConfig:
    values: dict[str, Any] = {
        "dataset_id": "rf_car_damage_seg_v1",
        "raw_export_root": tmp_path / "dataset/01_raw/export",
        "output_root": tmp_path / "dataset/02_interim/output",
        "annotation_filename": "_annotations.coco.json",
        "splits": ("train", "valid", "test"),
        "allowed_invalid_reasons": frozenset(
            {"exceeds_image_width", "exceeds_image_height"}
        ),
        "preserve_segmentation": True,
        "preserve_area": True,
        "preserve_ids": True,
        "drop_annotations": False,
        "fail_on_unexpected_invalid_reason": True,
        "allow_overwrite": False,
        "expected_total_images": 3,
        "expected_total_annotations": 6,
        "expected_total_repaired": 3,
        "expected_total_dropped": 0,
        "expected_total_invalid_after": 0,
        "expected_per_split": {
            split: {"images": 1, "annotations": 2, "repaired": 1}
            for split in ("train", "valid", "test")
        },
        "lineage_status": "generated_augmented_v1",
        "training_acceptance": "NOT_YET_APPROVED",
        "project_root": tmp_path,
    }
    values.update(overrides)
    return BboxRepairConfig(**values)


def make_payload(
    *,
    overflow: str | None = "right",
    bbox: object | None = None,
    file_name: str = "image.jpg",
    include_image: bool = True,
) -> dict[str, Any]:
    if bbox is None:
        bbox_by_overflow = {
            None: [10, 10, 20, 15],
            "right": [90, 10, 20, 15],
            "bottom": [10, 90, 20, 20],
            "both": [90, 90, 20, 20],
        }
        bbox = bbox_by_overflow[overflow]

    images = (
        [{"id": 1, "file_name": file_name, "width": 100, "height": 100}]
        if include_image
        else []
    )
    return {
        "info": {"description": "fixture"},
        "licenses": [{"id": 1, "name": "Public Domain"}],
        "images": images,
        "categories": [{"id": 1, "name": "Car-Damage", "supercategory": "none"}],
        "annotations": [
            {
                "id": 10,
                "image_id": 1,
                "category_id": 1,
                "bbox": bbox,
                "area": 300,
                "iscrowd": 0,
                "segmentation": [[10, 10, 30, 10, 30, 25, 10, 25]],
                "custom": {"source": "fixture"},
            }
        ],
    }


def prepare_image(tmp_path: Path, file_name: str = "image.jpg") -> Path:
    image_root = tmp_path / "images"
    image_root.mkdir(parents=True, exist_ok=True)
    (image_root / file_name).write_bytes(b"fixture-image")
    return image_root


def repair_one(
    tmp_path: Path,
    payload: dict[str, Any],
    *,
    policy: BboxRepairConfig | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    image_root = prepare_image(tmp_path)
    return repair_coco_payload(
        payload,
        split="train",
        dataset_id="rf_car_damage_seg_v1",
        image_root=image_root,
        repair_policy=policy or make_policy(tmp_path),
        input_annotation_sha256="INPUTHASH",
    )


def write_split(
    raw_root: Path,
    split: str,
    *,
    overflow: str | None = "right",
    invalid_bbox: object | None = None,
) -> Path:
    split_root = raw_root / split
    split_root.mkdir(parents=True, exist_ok=True)
    (split_root / "image.jpg").write_bytes(f"{split}-image".encode())
    payload = make_payload(
        overflow=overflow,
        bbox=invalid_bbox,
    )
    payload["annotations"].append(
        {
            "id": 11,
            "image_id": 1,
            "category_id": 1,
            "bbox": [5, 5, 10, 10],
            "area": 100,
            "iscrowd": 0,
            "segmentation": [[5, 5, 15, 5, 15, 15, 5, 15]],
        }
    )
    annotation_path = split_root / "_annotations.coco.json"
    annotation_path.write_text(json.dumps(payload), encoding="utf-8")
    return annotation_path


def write_build_fixture(
    tmp_path: Path,
    *,
    bad_split: str | None = None,
    bad_bbox: object | None = None,
    output_name: str = "cleaned",
) -> tuple[Path, Path, dict[str, Path]]:
    raw_root = tmp_path / "dataset/01_raw/export"
    annotation_paths: dict[str, Path] = {}
    for split, overflow in {"train": "right", "valid": "bottom", "test": "both"}.items():
        annotation_paths[split] = write_split(
            raw_root,
            split,
            overflow=overflow,
            invalid_bbox=bad_bbox if split == bad_split else None,
        )

    config_path = tmp_path / f"configs/{output_name}.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        f"""
dataset_id: rf_car_damage_seg_v1
raw_export_root: dataset/01_raw/export
output_root: dataset/02_interim/{output_name}
annotation_filename: _annotations.coco.json
splits: [train, valid, test]
repair_policy:
  allowed_invalid_reasons: [exceeds_image_width, exceeds_image_height]
  preserve_segmentation: true
  preserve_area: true
  preserve_ids: true
  drop_annotations: false
  fail_on_unexpected_invalid_reason: true
  allow_overwrite: false
expected:
  total_images: 3
  total_annotations: 6
  total_repaired: 3
  total_dropped: 0
  total_invalid_after: 0
  per_split:
    train: {{images: 1, annotations: 2, repaired: 1}}
    valid: {{images: 1, annotations: 2, repaired: 1}}
    test: {{images: 1, annotations: 2, repaired: 1}}
lineage_status: generated_augmented_v1
training_acceptance: NOT_YET_APPROVED
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return config_path, tmp_path / f"dataset/02_interim/{output_name}", annotation_paths


def output_hashes(output_root: Path) -> dict[str, str]:
    return {
        path.relative_to(output_root).as_posix(): sha256_file(path)
        for path in sorted(output_root.rglob("*"))
        if path.is_file()
    }


def load_cli_module() -> Any:
    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts/phase04_5_repair_external_coco_bbox.py"
    )
    spec = importlib.util.spec_from_file_location("phase04_5_repair_cli", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module




@pytest.mark.parametrize("key", ["images", "annotations", "categories"])
def test_coco_collections_must_be_lists(tmp_path: Path, key: str) -> None:
    payload = make_payload()
    payload[key] = {"invalid": "mapping"}

    with pytest.raises(BboxRepairError, match=f"COCO {key} must be a list"):
        repair_one(tmp_path, payload)


@pytest.mark.parametrize("key", ["images", "annotations", "categories"])
def test_coco_collection_items_must_be_objects(tmp_path: Path, key: str) -> None:
    payload = make_payload()
    payload[key].append("invalid-item")

    with pytest.raises(BboxRepairError, match=f"COCO {key} contains non-object item"):
        repair_one(tmp_path, payload)


def test_valid_bbox_is_unchanged() -> None:
    assert classify_bbox_invalid_reasons([10, 10, 20, 15], 100, 100) == []
    assert clip_bbox_to_image([10, 10, 20, 15], 100, 100) == [10.0, 10.0, 20.0, 15.0]


def test_right_overflow_clips_width() -> None:
    assert classify_bbox_invalid_reasons([90, 10, 20, 15], 100, 100) == [
        "exceeds_image_width"
    ]
    assert clip_bbox_to_image([90, 10, 20, 15], 100, 100) == [90.0, 10.0, 10.0, 15.0]


def test_bottom_overflow_clips_height() -> None:
    assert classify_bbox_invalid_reasons([10, 90, 20, 20], 100, 100) == [
        "exceeds_image_height"
    ]
    assert clip_bbox_to_image([10, 90, 20, 20], 100, 100) == [10.0, 90.0, 20.0, 10.0]


def test_both_overflows_clip_once_and_stay_inside(tmp_path: Path) -> None:
    repaired, rows, summary = repair_one(tmp_path, make_payload(overflow="both"))

    bbox = repaired["annotations"][0]["bbox"]
    assert bbox == [90.0, 90.0, 10.0, 10.0]
    assert bbox[2] > 0 and bbox[3] > 0
    assert bbox[0] + bbox[2] <= 100
    assert bbox[1] + bbox[3] <= 100
    assert len(rows) == 1
    assert rows[0]["clipped_right"] is True
    assert rows[0]["clipped_bottom"] is True
    assert summary["repaired_count"] == 1


def test_repair_changes_only_bbox_and_preserves_order(tmp_path: Path) -> None:
    payload = make_payload(overflow="right")
    original = copy.deepcopy(payload)

    repaired, _, _ = repair_one(tmp_path, payload)

    assert payload == original
    assert list(repaired) == list(original)
    assert repaired["images"] == original["images"]
    assert repaired["categories"] == original["categories"]
    assert repaired["info"] == original["info"]
    assert repaired["licenses"] == original["licenses"]
    repaired_annotation = repaired["annotations"][0]
    original_annotation = original["annotations"][0]
    assert {
        key: value for key, value in repaired_annotation.items() if key != "bbox"
    } == {key: value for key, value in original_annotation.items() if key != "bbox"}
    assert repaired_annotation["area"] == original_annotation["area"]
    assert repaired_annotation["segmentation"] == original_annotation["segmentation"]


@pytest.mark.parametrize(
    ("bbox", "reason"),
    [
        ([-1, 10, 20, 20], "negative_x"),
        ([10, -1, 20, 20], "negative_y"),
        ([10, 10, 0, 20], "nonpositive_width"),
        ([10, 10, 20, 0], "nonpositive_height"),
        ([10, 10, -1, 20], "nonpositive_width"),
        ([10, 10, 20, -1], "nonpositive_height"),
    ],
)
def test_unapproved_numeric_invalid_reasons_are_blocked(
    tmp_path: Path,
    bbox: list[int],
    reason: str,
) -> None:
    with pytest.raises(BboxRepairError, match=reason):
        repair_one(tmp_path, make_payload(bbox=bbox))


@pytest.mark.parametrize(
    ("bbox", "reason"),
    [
        ([1, 2, 3], "malformed_bbox"),
        ([1, 2, "bad", 4], "non_numeric_bbox"),
        ([1, 2, float("nan"), 4], "non_finite_bbox"),
        ([1, 2, float("inf"), 4], "non_finite_bbox"),
    ],
)
def test_malformed_non_numeric_and_non_finite_bbox_are_blocked(
    tmp_path: Path,
    bbox: object,
    reason: str,
) -> None:
    with pytest.raises(BboxRepairError, match=reason):
        repair_one(tmp_path, make_payload(bbox=bbox))


def test_missing_image_record_is_blocked(tmp_path: Path) -> None:
    image_root = prepare_image(tmp_path)
    payload = make_payload(include_image=False)

    with pytest.raises(BboxRepairError, match="missing image record"):
        repair_coco_payload(
            payload,
            split="train",
            dataset_id="rf_car_damage_seg_v1",
            image_root=image_root,
            repair_policy=make_policy(tmp_path),
            input_annotation_sha256="INPUTHASH",
        )


def test_missing_image_file_is_blocked(tmp_path: Path) -> None:
    image_root = tmp_path / "empty"
    image_root.mkdir()

    with pytest.raises(BboxRepairError, match="missing image file"):
        repair_coco_payload(
            make_payload(),
            split="train",
            dataset_id="rf_car_damage_seg_v1",
            image_root=image_root,
            repair_policy=make_policy(tmp_path),
            input_annotation_sha256="INPUTHASH",
        )


def test_output_annotation_count_matches_input(tmp_path: Path) -> None:
    payload = make_payload(overflow="right")
    payload["annotations"].append(
        {
            "id": 11,
            "image_id": 1,
            "category_id": 1,
            "bbox": [5, 5, 10, 10],
            "area": 100,
            "iscrowd": 0,
            "segmentation": [],
        }
    )
    repaired, rows, summary = repair_one(tmp_path, payload)

    assert len(repaired["annotations"]) == len(payload["annotations"]) == 2
    assert len(rows) == 1
    assert summary["input_annotation_count"] == 2
    assert summary["output_annotation_count"] == 2
    assert summary["dropped_count"] == 0


def test_load_config_resolves_repository_relative_paths(tmp_path: Path) -> None:
    config_path, output_root, _ = write_build_fixture(tmp_path)

    config = load_bbox_repair_config(config_path, tmp_path)

    assert config.raw_export_root == tmp_path / "dataset/01_raw/export"
    assert config.output_root == output_root
    assert config.splits == ("train", "valid", "test")
    assert config.allowed_invalid_reasons == frozenset(
        {"exceeds_image_width", "exceeds_image_height"}
    )


def test_build_writes_cleaned_outputs_reports_and_relative_manifest(tmp_path: Path) -> None:
    config_path, output_root, raw_annotations = write_build_fixture(tmp_path)
    raw_hashes_before = {split: sha256_file(path) for split, path in raw_annotations.items()}

    result = build_external_coco_bbox_repair(
        config_path,
        project_root=tmp_path,
        now_utc="2026-07-12T00:00:00Z",
    )

    assert result["gate_classification"] == "EXTERNAL_COCO_BBOX_REPAIR_VERIFIED"
    assert result["summary"]["image_count"] == 3
    assert result["summary"]["input_annotation_count"] == 6
    assert result["summary"]["repaired_count"] == 3
    assert result["summary"]["output_annotation_count"] == 6
    assert result["summary"]["invalid_after_count"] == 0
    assert result["repair_log_rows"] == 3
    assert result["manifest_rows"] == 3

    for split in ("train", "valid", "test"):
        cleaned = output_root / "cleaned_coco" / split / "_annotations.coco.json"
        assert cleaned.is_file()
        payload = json.loads(cleaned.read_text(encoding="utf-8"))
        assert len(payload["annotations"]) == 2
        assert sha256_file(raw_annotations[split]) == raw_hashes_before[split]

    with (output_root / "bbox_repair_log.csv").open(encoding="utf-8-sig", newline="") as handle:
        log_rows = list(csv.DictReader(handle))
    assert len(log_rows) == 3
    assert len({(row["split"], row["annotation_id"]) for row in log_rows}) == 3

    with (output_root / "bbox_repair_summary.csv").open(encoding="utf-8-sig", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))
    assert [row["split"] for row in summary_rows] == ["train", "valid", "test", "total"]
    assert summary_rows[-1]["repaired_count"] == "3"
    assert summary_rows[-1]["dropped_count"] == "0"

    with (output_root / "cleaned_annotation_manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        manifest_rows = list(csv.DictReader(handle))
    assert len(manifest_rows) == 3
    for row in manifest_rows:
        assert not Path(row["raw_image_root"]).is_absolute()
        assert not Path(row["input_annotation_path"]).is_absolute()
        assert not Path(row["output_annotation_path"]).is_absolute()
        assert row["raw_image_root"].startswith("dataset/01_raw/")
        assert row["output_annotation_path"].startswith("dataset/02_interim/")
        assert row["training_acceptance"] == "NOT_YET_APPROVED"


def test_build_blocks_existing_output_root_without_overwrite(tmp_path: Path) -> None:
    config_path, output_root, _ = write_build_fixture(tmp_path)
    output_root.mkdir(parents=True)
    marker = output_root / "keep.txt"
    marker.write_text("do not overwrite", encoding="utf-8")

    with pytest.raises(BboxRepairError, match="output root already exists"):
        build_external_coco_bbox_repair(config_path, project_root=tmp_path)

    assert marker.read_text(encoding="utf-8") == "do not overwrite"


def test_unexpected_invalid_reason_leaves_no_formal_output(tmp_path: Path) -> None:
    config_path, output_root, _ = write_build_fixture(
        tmp_path,
        bad_split="train",
        bad_bbox=[-1, 10, 20, 20],
    )

    with pytest.raises(BboxRepairError, match="negative_x"):
        build_external_coco_bbox_repair(config_path, project_root=tmp_path)

    assert not output_root.exists()


def test_expected_per_split_mismatch_is_blocked_before_output(tmp_path: Path) -> None:
    config_path, output_root, _ = write_build_fixture(tmp_path)
    text = config_path.read_text(encoding="utf-8")
    config_path.write_text(
        text.replace("train: {images: 1, annotations: 2, repaired: 1}",
                     "train: {images: 2, annotations: 2, repaired: 1}"),
        encoding="utf-8",
    )

    with pytest.raises(BboxRepairError, match="split=train image_count mismatch"):
        build_external_coco_bbox_repair(config_path, project_root=tmp_path)

    assert not output_root.exists()


def test_transaction_failure_removes_all_partial_formal_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path, output_root, _ = write_build_fixture(tmp_path)
    real_replace = repair_module.os.replace
    calls = 0

    def fail_on_second_replace(source: os.PathLike[str], destination: os.PathLike[str]) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated promotion failure")
        real_replace(source, destination)

    monkeypatch.setattr(repair_module.os, "replace", fail_on_second_replace)

    with pytest.raises(OSError, match="simulated promotion failure"):
        build_external_coco_bbox_repair(config_path, project_root=tmp_path)

    assert not output_root.exists()


def test_raw_hash_change_during_promotion_removes_formal_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path, output_root, raw_annotations = write_build_fixture(tmp_path)
    real_promote = repair_module._promote_transactionally

    def promote_then_mutate(mapping: dict[Path, Path]) -> None:
        real_promote(mapping)
        raw_annotations["train"].write_text("{}", encoding="utf-8")

    monkeypatch.setattr(repair_module, "_promote_transactionally", promote_then_mutate)

    with pytest.raises(BboxRepairError, match="raw input annotation SHA256 changed"):
        build_external_coco_bbox_repair(config_path, project_root=tmp_path)

    assert not output_root.exists()


def test_same_input_and_fixed_timestamp_produce_deterministic_outputs(tmp_path: Path) -> None:
    config_path, output_root, _ = write_build_fixture(tmp_path)

    build_external_coco_bbox_repair(
        config_path,
        project_root=tmp_path,
        now_utc="2026-07-12T00:00:00Z",
    )
    first_hashes = output_hashes(output_root)
    shutil.rmtree(output_root)

    build_external_coco_bbox_repair(
        config_path,
        project_root=tmp_path,
        now_utc="2026-07-12T00:00:00Z",
    )
    second_hashes = output_hashes(output_root)

    assert first_hashes == second_hashes


def test_cli_success_and_blocked_exit_codes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cli = load_cli_module()
    monkeypatch.setattr(cli, "find_project_root", lambda value: tmp_path)
    monkeypatch.setattr(cli, "resolve_path", lambda value, root: tmp_path / "config.yaml")
    monkeypatch.setattr(
        cli,
        "build_external_coco_bbox_repair",
        lambda *args, **kwargs: {
            "gate_classification": "EXTERNAL_COCO_BBOX_REPAIR_VERIFIED",
            "dataset_id": "rf_car_damage_seg_v1",
            "summary": {
                "input_annotation_count": 22019,
                "repaired_count": 403,
                "dropped_count": 0,
                "output_annotation_count": 22019,
                "invalid_after_count": 0,
            },
        },
    )

    assert cli.main([]) == 0
    success_output = capsys.readouterr().out
    assert "Gate classification: EXTERNAL_COCO_BBOX_REPAIR_VERIFIED" in success_output
    assert "STOPPED_BEFORE_EXTERNAL_DATASET_REGISTRY_PROMOTION_GATE" in success_output

    def blocked(*args: Any, **kwargs: Any) -> None:
        raise BboxRepairError("fixture blocked")

    monkeypatch.setattr(cli, "build_external_coco_bbox_repair", blocked)
    assert cli.main([]) == 2
    blocked_output = capsys.readouterr().out
    assert "Gate classification: EXTERNAL_COCO_BBOX_REPAIR_BLOCKED" in blocked_output
    assert "ERROR: fixture blocked" in blocked_output
