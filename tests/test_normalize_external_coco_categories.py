from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest
import yaml

import fleetvision.data.normalize_external_coco_categories as normalize_module
from fleetvision.data.normalize_external_coco_categories import (
    CanonicalizationConfigError,
    CanonicalizationInputError,
    CanonicalizationOutputError,
    build_canonical_coco,
    canonicalize_coco_payload,
    load_canonicalization_config,
    sha256_file,
)


DATASET_ID = "rf_car_damage_seg_v1"


def make_payload(
    *,
    categories: list[dict[str, Any]] | None = None,
    annotation_category_ids: tuple[int, ...] = (1, 1),
) -> dict[str, Any]:
    return {
        "info": {"description": "fixture"},
        "licenses": [{"id": 1, "name": "Public Domain"}],
        "images": [
            {"id": 10, "file_name": "a.jpg", "width": 100, "height": 80, "extra": "keep"},
            {"id": 20, "file_name": "b.jpg", "width": 120, "height": 90},
        ],
        "categories": categories
        or [
            {"id": 0, "name": "damage-", "supercategory": "none"},
            {"id": 1, "name": "Car-Damage", "supercategory": "damage-"},
        ],
        "annotations": [
            {
                "id": index + 100,
                "image_id": 10 if index == 0 else 20,
                "category_id": category_id,
                "bbox": [1.5 + index, 2.5, 20.0, 10.0],
                "area": 200.0,
                "segmentation": [[1, 2, 21, 2, 21, 12, 1, 12]],
                "iscrowd": 0,
                "custom": {"keep": True},
            }
            for index, category_id in enumerate(annotation_category_ids)
        ],
    }


def config_payload(
    source_sha256: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "dataset_id": DATASET_ID,
        "source_root": "dataset/02_interim/source/cleaned_coco",
        "output_root": "dataset/02_interim/source/canonical_coco",
        "annotation_filename": "_annotations.coco.json",
        "splits": ["train", "valid", "test"],
        "source_aliases": ["Car-Damage", "damage-"],
        "source_json_sha256": source_sha256
        or {split: "0" * 64 for split in ("train", "valid", "test")},
        "canonical_category": {"id": 0, "name": "damage", "supercategory": "damage"},
        "expected": {
            "total_images": 6,
            "total_annotations": 6,
            "per_split": {
                "train": {"images": 2, "annotations": 2},
                "valid": {"images": 2, "annotations": 2},
                "test": {"images": 2, "annotations": 2},
            },
        },
        "execution": {
            "overwrite_existing_output": False,
            "write_error_report_on_failure": True,
        },
    }


def write_fixture(tmp_path: Path, *, payload: dict[str, Any] | None = None) -> Path:
    data = payload or make_payload()
    source_sha256: dict[str, str] = {}
    for split in ("train", "valid", "test"):
        path = tmp_path / f"dataset/02_interim/source/cleaned_coco/{split}/_annotations.coco.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        source_sha256[split] = hashlib.sha256(path.read_bytes()).hexdigest().upper()
    config_path = tmp_path / "configs/normalization.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        yaml.safe_dump(config_payload(source_sha256), sort_keys=False), encoding="utf-8"
    )
    return config_path


def load_config(tmp_path: Path, config_path: Path | None = None):
    return load_canonicalization_config(
        config_path or write_fixture(tmp_path), project_root=tmp_path
    )


def annotation_without_category(annotation: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in annotation.items() if key != "category_id"}


def load_cli_module() -> Any:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts/phase04_5_normalize_external_coco_categories.py"
    )
    spec = importlib.util.spec_from_file_location("phase04_5_normalize_cli", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_car_damage_normalizes_to_damage() -> None:
    result = canonicalize_coco_payload(
        make_payload(categories=[{"id": 1, "name": "Car-Damage", "supercategory": "damage-"}]),
        source_aliases=("Car-Damage", "damage-"),
        canonical_id=0,
        canonical_name="damage",
        canonical_supercategory="damage",
    )
    assert {annotation["category_id"] for annotation in result.payload["annotations"]} == {0}


def test_damage_dash_normalizes_to_damage() -> None:
    result = canonicalize_coco_payload(
        make_payload(
            categories=[{"id": 7, "name": "damage-", "supercategory": "none"}],
            annotation_category_ids=(7, 7),
        ),
        source_aliases=("Car-Damage", "damage-"),
        canonical_id=0,
        canonical_name="damage",
        canonical_supercategory="damage",
    )
    assert result.payload["categories"] == [{"id": 0, "name": "damage", "supercategory": "damage"}]


def test_multiple_aliases_merge_to_one_category_id() -> None:
    result = canonicalize_coco_payload(
        make_payload(annotation_category_ids=(0, 1)),
        source_aliases=("Car-Damage", "damage-"),
        canonical_id=0,
        canonical_name="damage",
        canonical_supercategory="damage",
    )
    assert result.source_category_distribution == {"Car-Damage": 1, "damage-": 1}
    assert {annotation["category_id"] for annotation in result.payload["annotations"]} == {0}
    assert len(result.payload["categories"]) == 1


def test_unknown_category_fails_closed() -> None:
    payload = make_payload(
        categories=[{"id": 9, "name": "wheel", "supercategory": "vehicle"}],
        annotation_category_ids=(9, 9),
    )
    with pytest.raises(CanonicalizationInputError, match="unknown category"):
        canonicalize_coco_payload(
            payload,
            source_aliases=("Car-Damage", "damage-"),
            canonical_id=0,
            canonical_name="damage",
            canonical_supercategory="damage",
        )


def test_ids_and_non_category_annotation_fields_are_preserved() -> None:
    source = make_payload(annotation_category_ids=(0, 1))
    result = canonicalize_coco_payload(
        source,
        source_aliases=("Car-Damage", "damage-"),
        canonical_id=0,
        canonical_name="damage",
        canonical_supercategory="damage",
    )
    assert [image["id"] for image in result.payload["images"]] == [10, 20]
    assert [annotation["id"] for annotation in result.payload["annotations"]] == [100, 101]
    assert [annotation_without_category(value) for value in result.payload["annotations"]] == [
        annotation_without_category(value) for value in source["annotations"]
    ]
    assert result.payload["info"] == source["info"]
    assert result.payload["licenses"] == source["licenses"]


def test_annotation_count_and_bbox_checksum_are_preserved() -> None:
    result = canonicalize_coco_payload(
        make_payload(),
        source_aliases=("Car-Damage", "damage-"),
        canonical_id=0,
        canonical_name="damage",
        canonical_supercategory="damage",
    )
    assert result.images_before == result.images_after == 2
    assert result.annotations_before == result.annotations_after == 2
    assert result.bbox_checksum_before == result.bbox_checksum_after


def test_build_keeps_source_json_byte_identical_and_writes_audit(tmp_path: Path) -> None:
    config_path = write_fixture(tmp_path)
    config = load_config(tmp_path, config_path)
    before = {
        path: sha256_file(path)
        for path in sorted(config.source_root.rglob("_annotations.coco.json"))
    }
    result = build_canonical_coco(
        config, execute=True, now_utc="2026-07-12T16:00:00Z"
    )
    assert {path: sha256_file(path) for path in before} == before
    assert (result.output_root / "canonicalization_verification.json").is_file()
    assert sorted(path.name for path in result.output_root.iterdir()) == [
        "canonicalization_errors.csv",
        "canonicalization_split_audit.csv",
        "canonicalization_verification.json",
        "test",
        "train",
        "valid",
    ]


def test_build_rejects_source_whose_sha256_differs_from_approved_contract(
    tmp_path: Path,
) -> None:
    config_path = write_fixture(tmp_path)
    config = load_config(tmp_path, config_path)
    source = config.source_root / "train" / config.annotation_filename
    source.write_text(source.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(CanonicalizationInputError, match="approved SHA256"):
        build_canonical_coco(config, execute=False)


def test_repeated_build_produces_identical_canonical_json(tmp_path: Path) -> None:
    config_path = write_fixture(tmp_path)
    config = load_config(tmp_path, config_path)
    first = build_canonical_coco(config, execute=True, now_utc="2026-07-12T16:00:00Z")
    first_hashes = {
        split: sha256_file(first.output_root / split / config.annotation_filename)
        for split in config.splits
    }
    second = build_canonical_coco(
        config,
        execute=True,
        overwrite=True,
        now_utc="2026-07-12T16:00:00Z",
    )
    assert {
        split: sha256_file(second.output_root / split / config.annotation_filename)
        for split in config.splits
    } == first_hashes


def test_existing_output_requires_explicit_overwrite(tmp_path: Path) -> None:
    config_path = write_fixture(tmp_path)
    config = load_config(tmp_path, config_path)
    config.output_root.mkdir(parents=True)
    marker = config.output_root / "keep.txt"
    marker.write_text("keep", encoding="utf-8")
    with pytest.raises(CanonicalizationOutputError, match="already exists"):
        build_canonical_coco(config, execute=True)
    assert marker.read_text(encoding="utf-8") == "keep"


def test_atomic_promotion_failure_cleans_partial_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = write_fixture(tmp_path)
    config = load_config(tmp_path, config_path)
    monkeypatch.setattr(
        normalize_module.os,
        "replace",
        lambda *args: (_ for _ in ()).throw(OSError("promotion failure")),
    )
    with pytest.raises(CanonicalizationOutputError, match="promotion failure"):
        build_canonical_coco(config, execute=True)
    assert not config.output_root.exists()


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    config_path = write_fixture(tmp_path)
    config = load_config(tmp_path, config_path)
    result = build_canonical_coco(config, execute=False)
    assert result.executed is False
    assert not config.output_root.exists()


def test_config_rejects_unknown_keys_and_unapproved_output_path(tmp_path: Path) -> None:
    config_path = write_fixture(tmp_path)
    payload = config_payload()
    payload["unknown"] = True
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(CanonicalizationConfigError, match="unknown"):
        load_config(tmp_path, config_path)

    payload = config_payload()
    payload["output_root"] = "dataset/01_raw/unsafe"
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(CanonicalizationConfigError, match="dataset/02_interim"):
        load_config(tmp_path, config_path)


def test_cli_dry_run_returns_compact_success_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config_path = write_fixture(tmp_path)
    cli = load_cli_module()
    assert cli.main(
        ["--project-root", str(tmp_path), "--config", str(config_path)]
    ) == 0
    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert payload["executed"] is False
    assert payload["total_images"] == 6
    assert payload["canonical_class_count"] == 1
