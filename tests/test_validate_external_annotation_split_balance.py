from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import zipfile
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
import yaml

from fleetvision.data.validate_external_annotation_split_balance import (
    AnnotationQaError,
    load_annotation_qa_config,
    load_canonical_coco,
    run_annotation_split_balance_qa,
    verify_plan_zip,
)


DATASET_ID = "rf_car_damage_seg_v1"
PLAN_COLUMNS = [
    "record_id",
    "canonical_source_key",
    "original_split",
    "assigned_split",
    "family_image_count",
    "is_family_medoid",
    "include_in_model_dataset",
    "plan_role",
    "image_id",
    "relative_image_path",
    "sha256",
    "width",
    "height",
]


def make_coco(*, category_name: str = "damage", invalid_bbox: bool = False) -> dict[str, Any]:
    return {
        "info": {"fixture": True},
        "licenses": [],
        "images": [{"id": 1, "file_name": "image.jpg", "width": 100, "height": 80}],
        "categories": [{"id": 0, "name": category_name, "supercategory": category_name}],
        "annotations": [
            {
                "id": 10,
                "image_id": 1,
                "category_id": 0,
                "bbox": [90, 10, 20 if invalid_bbox else 10, 10],
                "area": 100,
                "segmentation": [[90, 10, 100, 10, 100, 20, 90, 20]],
                "iscrowd": 0,
            }
        ],
    }


def write_csv_bytes(rows: list[dict[str, Any]], columns: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8-sig")


def write_plan_zip(tmp_path: Path, *, leak: bool = False) -> Path:
    rows: list[dict[str, Any]] = []
    for index, split in enumerate(("train", "valid", "test"), start=1):
        family = "family-train" if leak and split == "valid" else f"family-{split}"
        rows.append(
            {
                "record_id": f"external:{DATASET_ID}:{split}:{index}",
                "canonical_source_key": family,
                "original_split": split,
                "assigned_split": split,
                "family_image_count": 1,
                "is_family_medoid": True,
                "include_in_model_dataset": True,
                "plan_role": f"{split}_fixture",
                "image_id": index,
                "relative_image_path": f"dataset/01_raw/{split}/image.jpg",
                "sha256": f"{index:064X}",
                "width": 100,
                "height": 80,
            }
        )
    summary = {
        "dataset_id": DATASET_ID,
        "source_family_count": 3,
        "family_leakage_count": 0,
        "planned_family_counts": {"train": 1, "valid": 1, "test": 1},
        "planned_source_image_counts": {"train": 1, "valid": 1, "test": 1},
        "planned_model_included_image_counts": {"train": 1, "valid": 1, "test": 1},
        "total_model_included_images": 3,
        "total_excluded_correlated_eval_variants": 0,
        "training_acceptance": "NOT_YET_APPROVED",
    }
    entries = {
        "gate_result.json": json.dumps(
            {
                "outcome": "PASS",
                "classification": "GROUP_SAFE_SPLIT_PLAN_CREATED_PENDING_ANNOTATION_QA",
            }
        ).encode(),
        "group_safe_split_evidence/image_split_plan.csv": write_csv_bytes(rows, PLAN_COLUMNS),
        "group_safe_split_evidence/group_safe_split_plan_summary.json": json.dumps(summary).encode(),
    }
    manifest_rows = [
        {
            "relative_path": name,
            "size_bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest().upper(),
        }
        for name, payload in entries.items()
    ]
    entries["evidence_manifest.csv"] = write_csv_bytes(
        manifest_rows, ["relative_path", "size_bytes", "sha256"]
    )
    path = tmp_path / "plan.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in entries.items():
            archive.writestr(name, payload)
    return path


def write_fixture(
    tmp_path: Path,
    *,
    category_name: str = "damage",
    invalid_bbox: bool = False,
) -> tuple[Path, Path]:
    canonical_root = tmp_path / "dataset/02_interim/source/canonical_coco"
    canonical_sha256: dict[str, str] = {}
    for split in ("train", "valid", "test"):
        path = canonical_root / split / "_annotations.coco.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(make_coco(category_name=category_name, invalid_bbox=invalid_bbox)),
            encoding="utf-8",
        )
        canonical_sha256[split] = hashlib.sha256(path.read_bytes()).hexdigest().upper()
    mapping = tmp_path / "outputs/metadata/external_assets/class_mapping.csv"
    mapping.parent.mkdir(parents=True, exist_ok=True)
    mapping.write_text(
        "dataset_id,original_class,mapped_class,mapping_status,yolo_label_created\n"
        f"{DATASET_ID},Car-Damage,damage,approved_for_future_conversion,no\n",
        encoding="utf-8",
    )
    mapping_hash = hashlib.sha256(mapping.read_bytes()).hexdigest().upper()
    plan_zip = write_plan_zip(tmp_path)
    config = {
        "dataset_id": DATASET_ID,
        "canonical_coco_root": "dataset/02_interim/source/canonical_coco",
        "annotation_filename": "_annotations.coco.json",
        "splits": ["train", "valid", "test"],
        "class_mapping_path": "outputs/metadata/external_assets/class_mapping.csv",
        "class_mapping_sha256": mapping_hash,
        "split_plan_zip_sha256": hashlib.sha256(plan_zip.read_bytes()).hexdigest().upper(),
        "canonical_coco_sha256": canonical_sha256,
        "canonical_category": {"id": 0, "name": "damage", "supercategory": "damage"},
        "expected": {
            "source_images": 3,
            "source_annotations": 3,
            "source_families": 3,
            "family_leakage": 0,
            "model_included_images": 3,
            "excluded_correlated_eval_variants": 0,
            "per_split_model_images": {"train": 1, "valid": 1, "test": 1},
        },
        "review_sample_size": 2,
    }
    config_path = tmp_path / "configs/qa.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return config_path, plan_zip


def load_config(tmp_path: Path, config_path: Path):
    return load_annotation_qa_config(config_path, project_root=tmp_path)


def load_cli_module() -> Any:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts/phase04_5_validate_external_annotation_split_balance.py"
    )
    spec = importlib.util.spec_from_file_location("phase04_5_annotation_qa_cli", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_plan_zip_manifest_and_counts_are_verified(tmp_path: Path) -> None:
    config_path, plan_zip = write_fixture(tmp_path)
    config = load_config(tmp_path, config_path)
    plan = verify_plan_zip(plan_zip, config)
    assert len(plan.rows) == 3
    assert plan.family_count == 3
    assert plan.family_leakage_count == 0


def test_plan_zip_sha256_must_match_approved_contract(tmp_path: Path) -> None:
    config_path, _ = write_fixture(tmp_path)
    config = load_config(tmp_path, config_path)
    replacement_root = tmp_path / "replacement"
    replacement_root.mkdir()
    replacement = write_plan_zip(replacement_root, leak=True)
    with pytest.raises(AnnotationQaError, match="approved SHA256"):
        verify_plan_zip(replacement, config)


def test_family_leakage_fails_closed(tmp_path: Path) -> None:
    config_path, _ = write_fixture(tmp_path)
    config = load_config(tmp_path, config_path)
    plan_zip = write_plan_zip(tmp_path, leak=True)
    config = replace(
        config,
        split_plan_zip_sha256=hashlib.sha256(plan_zip.read_bytes()).hexdigest().upper(),
    )
    with pytest.raises(AnnotationQaError, match="family leakage"):
        verify_plan_zip(plan_zip, config)


def test_canonical_loader_accepts_only_damage(tmp_path: Path) -> None:
    config_path, _ = write_fixture(tmp_path)
    config = load_config(tmp_path, config_path)
    datasets = load_canonical_coco(config)
    assert sum(len(value.annotations) for value in datasets.values()) == 3
    assert {name for value in datasets.values() for name in value.category_by_id.values()} == {"damage"}


def test_canonical_loader_rejects_replaced_canonical_json(tmp_path: Path) -> None:
    config_path, _ = write_fixture(tmp_path)
    config = load_config(tmp_path, config_path)
    path = config.canonical_coco_root / "train" / config.annotation_filename
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(AnnotationQaError, match="approved SHA256"):
        load_canonical_coco(config)


@pytest.mark.parametrize("category_name", ["Car-Damage", "damage-"])
def test_canonical_loader_rejects_source_aliases(
    tmp_path: Path, category_name: str
) -> None:
    config_path, _ = write_fixture(tmp_path, category_name=category_name)
    config = load_config(tmp_path, config_path)
    with pytest.raises(AnnotationQaError, match="canonical category"):
        load_canonical_coco(config)


def test_invalid_bbox_fails_closed(tmp_path: Path) -> None:
    config_path, _ = write_fixture(tmp_path, invalid_bbox=True)
    config = load_config(tmp_path, config_path)
    with pytest.raises(AnnotationQaError, match="invalid bbox"):
        load_canonical_coco(config)


def test_full_qa_writes_structural_decision_and_review_samples(tmp_path: Path) -> None:
    config_path, plan_zip = write_fixture(tmp_path)
    config = load_config(tmp_path, config_path)
    output = tmp_path / "qa-output"
    result = run_annotation_split_balance_qa(
        config,
        plan_zip=plan_zip,
        output_root=output,
        now_utc="2026-07-12T17:00:00Z",
    )
    assert result.classification == "ANNOTATION_QA_STRUCTURALLY_READY_FOR_TARGETED_VISUAL_REVIEW"
    assert result.source_images == 3
    assert result.source_annotations == 3
    assert result.unresolved_plan_to_coco_joins == 0
    assert result.invalid_bbox_count == 0
    decision = json.loads((output / "annotation_and_split_balance_decision.json").read_text())
    assert decision["mapped_class"] == "damage"
    assert decision["yolo_class_count"] == 1
    assert (output / "smallest_bbox_review_sample.csv").is_file()
    assert (output / "largest_bbox_review_sample.csv").is_file()
    assert (output / "evidence_manifest.csv").is_file()


def test_qa_rejects_protected_output_root(tmp_path: Path) -> None:
    config_path, plan_zip = write_fixture(tmp_path)
    config = load_config(tmp_path, config_path)
    with pytest.raises(AnnotationQaError, match="protected path"):
        run_annotation_split_balance_qa(
            config,
            plan_zip=plan_zip,
            output_root=tmp_path / "dataset/01_raw/unsafe-evidence",
        )


def test_zip_packaging_never_overwrites_existing_destination(tmp_path: Path) -> None:
    cli = load_cli_module()
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "result.json").write_text("{}", encoding="utf-8")
    destination = tmp_path / "evidence.zip"
    destination.write_bytes(b"keep")
    with pytest.raises(AnnotationQaError, match="already exists"):
        cli._package_evidence(evidence, destination)
    assert destination.read_bytes() == b"keep"
    assert not Path(str(destination) + ".sha256.txt").exists()


def test_unresolved_plan_to_coco_join_fails_closed(tmp_path: Path) -> None:
    config_path, plan_zip = write_fixture(tmp_path)
    config = load_config(tmp_path, config_path)
    with zipfile.ZipFile(plan_zip, "r") as archive:
        assert archive.namelist()
    for split in ("train", "valid", "test"):
        path = config.canonical_coco_root / split / config.annotation_filename
        payload = json.loads(path.read_text())
        payload["images"][0]["file_name"] = "other.jpg"
        path.write_text(json.dumps(payload), encoding="utf-8")
    config = replace(
        config,
        canonical_coco_sha256={
            split: hashlib.sha256(
                (config.canonical_coco_root / split / config.annotation_filename).read_bytes()
            ).hexdigest().upper()
            for split in config.splits
        },
    )
    with pytest.raises(AnnotationQaError, match="unresolved plan-to-COCO"):
        run_annotation_split_balance_qa(
            config,
            plan_zip=plan_zip,
            output_root=tmp_path / "qa-output",
        )


def test_cli_runs_against_explicit_plan_zip(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config_path, plan_zip = write_fixture(tmp_path)
    cli = load_cli_module()
    output = tmp_path / "qa-output"
    assert cli.main(
        [
            "--project-root",
            str(tmp_path),
            "--config",
            str(config_path),
            "--split-plan-zip",
            str(plan_zip),
            "--output-root",
            str(output),
        ]
    ) == 0
    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert payload["exit_code"] == 0
    assert payload["classification"] == "ANNOTATION_QA_STRUCTURALLY_READY_FOR_TARGETED_VISUAL_REVIEW"
