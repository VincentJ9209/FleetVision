from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import os
from pathlib import Path
from typing import Any

import pytest
import yaml

import fleetvision.data.promote_external_dataset_registry_v2_intake as promotion_module
from fleetvision.data.promote_external_dataset_registry_v2_intake import (
    ALREADY_APPLIED_CLASSIFICATION,
    DRY_RUN_CLASSIFICATION,
    EXECUTE_CLASSIFICATION,
    IDENTITY_COLUMNS,
    PROMOTION_COLUMNS,
    PROTECTED_V2_COLUMNS,
    RegistryIntakePromotionError,
    load_promotion_config,
    promote_external_dataset_registry_v2_intake,
)


CURRENT_COLUMNS = [
    "dataset_id",
    "platform",
    "dataset_name",
    "source_url",
    "publisher",
    "license",
    "license_evidence_url",
    "license_verified",
    "search_date",
    "download_date",
    "dataset_version",
    "task_type",
    "annotation_format",
    "original_classes",
    "image_count_reported",
    "image_count_downloaded",
    "bbox_count_reported",
    "bbox_count_valid",
    "accepted_image_count",
    "rejected_image_count",
    "mapping_to_damage",
    "domain_similarity",
    "bbox_quality_status",
    "sha256_dedup_status",
    "perceptual_hash_status",
    "internal_cross_dedup_status",
    "usage_status",
    "rejection_reason",
    "local_raw_path",
    "notes",
]

EXPECTED_PROMOTION_COLUMNS = [
    "download_date",
    "image_count_downloaded",
    "bbox_count_reported",
    "bbox_count_valid",
    "accepted_image_count",
    "rejected_image_count",
    "bbox_quality_status",
    "sha256_dedup_status",
    "usage_status",
    "local_raw_path",
    "notes",
]

EXPECTED_IDENTITY_COLUMNS = [
    "dataset_id",
    "platform",
    "dataset_name",
    "source_url",
    "publisher",
    "license",
    "license_evidence_url",
    "license_verified",
    "search_date",
    "dataset_version",
    "task_type",
    "annotation_format",
    "original_classes",
    "image_count_reported",
    "mapping_to_damage",
    "domain_similarity",
    "perceptual_hash_status",
    "internal_cross_dedup_status",
    "rejection_reason",
]

EXPECTED_PROTECTED_V2_COLUMNS = [
    "registry_schema_version",
    "lineage_status",
    "bbox_count_valid_raw",
    "bbox_count_invalid_raw",
    "bbox_quality_status_raw",
    "bbox_repair_count",
    "bbox_count_valid_interim",
    "bbox_count_invalid_interim",
    "bbox_quality_status_interim",
    "bbox_repair_status",
    "local_interim_path",
    "training_acceptance",
]

REGISTRY_COLUMNS = [*CURRENT_COLUMNS, *EXPECTED_PROTECTED_V2_COLUMNS]

PROTECTED_VALUES = {
    "registry_schema_version": "2",
    "lineage_status": "generated_augmented_v1",
    "bbox_count_valid_raw": "21616",
    "bbox_count_invalid_raw": "403",
    "bbox_quality_status_raw": "structural_qa_failed_bbox_overflow",
    "bbox_repair_count": "403",
    "bbox_count_valid_interim": "22019",
    "bbox_count_invalid_interim": "0",
    "bbox_quality_status_interim": "structural_bbox_qa_verified",
    "bbox_repair_status": "clipped_overflow_verified",
    "local_interim_path": "dataset/02_interim/99_external/roboflow/rf_car_damage_seg_v1",
    "training_acceptance": "NOT_YET_APPROVED",
}

PROMOTION_VALUES = {
    "download_date": "2026-07-11",
    "image_count_downloaded": "11675",
    "bbox_count_reported": "22019",
    "bbox_count_valid": "21616",
    "accepted_image_count": "11675",
    "rejected_image_count": "0",
    "bbox_quality_status": "downloaded_structural_qa_failed",
    "sha256_dedup_status": "external_exact_hash_inventory_complete",
    "usage_status": "downloaded",
    "notes": (
        "Controlled v1 COCO Segmentation export downloaded. Version contains "
        "generated/augmented images (3 outputs per training example); training "
        "acceptance remains pending bbox/mask QA, perceptual dedup, internal "
        "cross-dedup, and lineage review."
    ),
}


def encode_csv(
    columns: list[str],
    rows: list[dict[str, str]],
    *,
    bom: bool = True,
    newline: str = "\n",
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator=newline)
    writer.writeheader()
    writer.writerows({column: row.get(column, "") for column in columns} for row in rows)
    payload = stream.getvalue().encode("utf-8")
    return (b"\xef\xbb\xbf" + payload) if bom else payload


def parse_payload(payload: bytes) -> tuple[list[str], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig"), newline=""))
    return list(reader.fieldnames or []), list(reader)


def make_registry_row(
    project_root: Path,
    dataset_id: str = "rf_car_damage_seg_v1",
    **overrides: str,
) -> dict[str, str]:
    row = {column: "" for column in REGISTRY_COLUMNS}
    row.update(
        {
            "dataset_id": dataset_id,
            "platform": "roboflow",
            "dataset_name": "Car-Damage detection",
            "source_url": "https://universe.roboflow.com/college-gxdrt/car-damage-detection-ha5mm",
            "publisher": "College / Roboflow Universe",
            "license": "Public Domain (Roboflow project label)",
            "license_evidence_url": (
                "https://universe.roboflow.com/college-gxdrt/car-damage-detection-ha5mm"
            ),
            "license_verified": "yes",
            "search_date": "2026-07-12",
            "dataset_version": "v1 (2023-04-04)",
            "task_type": "segmentation",
            "annotation_format": (
                "coco-segmentation export planned; source instance segmentation"
            ),
            "original_classes": "Car-Damage",
            "image_count_reported": "4869 project images; 11685 generated v1 images",
            "mapping_to_damage": (
                "Car-Damage -> damage; preserve polygon/mask and derive bbox only after QA"
            ),
            "domain_similarity": "high",
            "bbox_quality_status": "pending_download_qa",
            "sha256_dedup_status": "pending",
            "perceptual_hash_status": "pending",
            "internal_cross_dedup_status": "pending",
            "usage_status": "approved_for_download",
            "notes": (
                "P1 controlled pilot only. Roboflow v1 reports 11,685 generated images "
                "with 3 outputs per training example; preserve augmentation lineage and "
                "do not describe the export as original-only. Training acceptance "
                "remains not approved."
            ),
            **PROTECTED_VALUES,
        }
    )
    row.update(overrides)
    return row


def make_proposal_row(project_root: Path, **overrides: str) -> dict[str, str]:
    registry_row = make_registry_row(project_root)
    proposal = {column: registry_row[column] for column in CURRENT_COLUMNS}
    raw_path = (
        project_root
        / "dataset/01_raw/99_external/roboflow/rf_car_damage_seg_v1"
    ).resolve()
    proposal.update(PROMOTION_VALUES)
    proposal["local_raw_path"] = str(raw_path)
    proposal.update(overrides)
    return proposal


def write_fixture(
    tmp_path: Path,
    *,
    registry_rows: list[dict[str, str]] | None = None,
    proposal_rows: list[dict[str, str]] | None = None,
    registry_columns: list[str] | None = None,
    proposal_columns: list[str] | None = None,
    registry_bom: bool = True,
    registry_newline: str = "\n",
    proposal_bom: bool = True,
    proposal_newline: str = "\n",
    expected_registry_sha256: str | None = None,
    expected_proposal_sha256: str | None = None,
) -> tuple[Path, Path, Path]:
    raw_path = (
        tmp_path
        / "dataset/01_raw/99_external/roboflow/rf_car_damage_seg_v1"
    )
    raw_path.mkdir(parents=True, exist_ok=True)

    registry = tmp_path / "dataset/00_catalog/external_dataset_registry.csv"
    registry.parent.mkdir(parents=True, exist_ok=True)
    resolved_registry_rows = (
        registry_rows
        if registry_rows is not None
        else [make_registry_row(tmp_path)]
    )
    registry_payload = encode_csv(
        registry_columns or REGISTRY_COLUMNS,
        resolved_registry_rows,
        bom=registry_bom,
        newline=registry_newline,
    )
    registry.write_bytes(registry_payload)

    proposal = (
        tmp_path
        / "outputs/metadata/external_assets/roboflow/rf_car_damage_seg_v1"
        / "registry_update_proposal.csv"
    )
    proposal.parent.mkdir(parents=True, exist_ok=True)
    proposal_payload = encode_csv(
        proposal_columns or CURRENT_COLUMNS,
        proposal_rows or [make_proposal_row(tmp_path)],
        bom=proposal_bom,
        newline=proposal_newline,
    )
    proposal.write_bytes(proposal_payload)

    config = (
        tmp_path
        / "configs/data/external_dataset_registry_v2_intake_promotion_config.yaml"
    )
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        yaml.safe_dump(
            {
                "registry_csv": "dataset/00_catalog/external_dataset_registry.csv",
                "proposal_csv": (
                    "outputs/metadata/external_assets/roboflow/"
                    "rf_car_damage_seg_v1/registry_update_proposal.csv"
                ),
                "target_dataset_id": "rf_car_damage_seg_v1",
                "expected_registry_dataset_id_order": [
                    row["dataset_id"] for row in resolved_registry_rows
                ],
                "expected_registry_sha256": (
                    expected_registry_sha256
                    or hashlib.sha256(registry_payload).hexdigest()
                ),
                "expected_proposal_sha256": (
                    expected_proposal_sha256
                    or hashlib.sha256(proposal_payload).hexdigest()
                ),
                "expected_registry_columns": REGISTRY_COLUMNS,
                "expected_proposal_columns": CURRENT_COLUMNS,
                "promotion_columns": EXPECTED_PROMOTION_COLUMNS,
                "identity_columns": EXPECTED_IDENTITY_COLUMNS,
                "protected_v2_columns": EXPECTED_PROTECTED_V2_COLUMNS,
                "expected_protected_v2_values": PROTECTED_VALUES,
                "expected_local_raw_path": (
                    "dataset/01_raw/99_external/roboflow/rf_car_damage_seg_v1"
                ),
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return config, registry, proposal


def load_cli_module() -> Any:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts/phase04_5_promote_external_dataset_registry_v2_intake.py"
    )
    spec = importlib.util.spec_from_file_location("registry_v2_intake_cli", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fixed_column_contracts() -> None:
    assert list(PROMOTION_COLUMNS) == EXPECTED_PROMOTION_COLUMNS
    assert list(IDENTITY_COLUMNS) == EXPECTED_IDENTITY_COLUMNS
    assert list(PROTECTED_V2_COLUMNS) == EXPECTED_PROTECTED_V2_COLUMNS
    assert set(PROMOTION_COLUMNS).isdisjoint(IDENTITY_COLUMNS)
    assert set(PROMOTION_COLUMNS).isdisjoint(PROTECTED_V2_COLUMNS)
    assert set(IDENTITY_COLUMNS).isdisjoint(PROTECTED_V2_COLUMNS)
    assert set(PROMOTION_COLUMNS) | set(IDENTITY_COLUMNS) == set(CURRENT_COLUMNS)


def test_dry_run_promotes_exactly_11_fields(tmp_path: Path) -> None:
    config, _, _ = write_fixture(tmp_path)
    result = promote_external_dataset_registry_v2_intake(config, tmp_path)

    assert result.classification == DRY_RUN_CLASSIFICATION
    assert result.output_columns == tuple(REGISTRY_COLUMNS)
    assert len(result.output_rows) == 1

    registry_before = make_registry_row(tmp_path)
    proposal = make_proposal_row(tmp_path)
    promoted = result.output_rows[0]

    assert {name: promoted[name] for name in PROMOTION_COLUMNS} == {
        name: proposal[name] for name in PROMOTION_COLUMNS
    }
    assert {name: promoted[name] for name in IDENTITY_COLUMNS} == {
        name: registry_before[name] for name in IDENTITY_COLUMNS
    }
    assert {name: promoted[name] for name in PROTECTED_V2_COLUMNS} == {
        name: registry_before[name] for name in PROTECTED_V2_COLUMNS
    }
    assert result.summary.registry_updated is False
    assert result.summary.promotion_fields_modified == 11
    assert result.summary.training_acceptance == "NOT_YET_APPROVED"


def test_dry_run_does_not_modify_registry_proposal_or_create_temp_files(
    tmp_path: Path,
) -> None:
    config, registry, proposal = write_fixture(tmp_path)
    registry_before = registry.read_bytes()
    proposal_before = proposal.read_bytes()

    promote_external_dataset_registry_v2_intake(config, tmp_path)

    assert registry.read_bytes() == registry_before
    assert proposal.read_bytes() == proposal_before
    assert not list(registry.parent.glob(".registry_v2_intake_promotion_*"))


def test_row_count_order_and_non_target_rows_are_preserved(tmp_path: Path) -> None:
    rows = [
        make_registry_row(tmp_path, "first_dataset"),
        make_registry_row(tmp_path),
        make_registry_row(tmp_path, "last_dataset"),
    ]
    config, _, _ = write_fixture(tmp_path, registry_rows=rows)

    result = promote_external_dataset_registry_v2_intake(config, tmp_path)

    assert [row["dataset_id"] for row in result.output_rows] == [
        "first_dataset",
        "rf_car_damage_seg_v1",
        "last_dataset",
    ]
    assert result.output_rows[0] == rows[0]
    assert result.output_rows[2] == rows[2]


def test_identity_difference_blocks(tmp_path: Path) -> None:
    proposal = make_proposal_row(tmp_path, publisher="unexpected publisher")
    config, _, _ = write_fixture(tmp_path, proposal_rows=[proposal])

    with pytest.raises(RegistryIntakePromotionError, match="identity"):
        promote_external_dataset_registry_v2_intake(config, tmp_path)


@pytest.mark.parametrize("column", EXPECTED_PROTECTED_V2_COLUMNS)
def test_every_protected_v2_field_is_preserved(
    tmp_path: Path,
    column: str,
) -> None:
    registry = make_registry_row(tmp_path)
    config, _, _ = write_fixture(tmp_path, registry_rows=[registry])

    result = promote_external_dataset_registry_v2_intake(config, tmp_path)

    assert result.output_rows[0][column] == registry[column]


def test_training_acceptance_must_be_not_yet_approved(tmp_path: Path) -> None:
    registry = make_registry_row(tmp_path, training_acceptance="APPROVED")
    config, _, _ = write_fixture(tmp_path, registry_rows=[registry])

    with pytest.raises(RegistryIntakePromotionError, match="NOT_YET_APPROVED"):
        promote_external_dataset_registry_v2_intake(config, tmp_path)


def test_raw_bbox_count_remains_21616_and_interim_remains_22019(
    tmp_path: Path,
) -> None:
    config, _, _ = write_fixture(tmp_path)

    result = promote_external_dataset_registry_v2_intake(config, tmp_path)
    row = result.output_rows[0]

    assert row["bbox_count_valid"] == "21616"
    assert row["bbox_count_valid_raw"] == "21616"
    assert row["bbox_count_valid_interim"] == "22019"


def test_notes_are_replaced_exactly_not_merged(tmp_path: Path) -> None:
    config, _, _ = write_fixture(tmp_path)

    result = promote_external_dataset_registry_v2_intake(config, tmp_path)

    assert result.output_rows[0]["notes"] == PROMOTION_VALUES["notes"]
    assert "P1 controlled pilot only" not in result.output_rows[0]["notes"]


def test_local_raw_path_must_match_existing_configured_project_path(
    tmp_path: Path,
) -> None:
    config, _, _ = write_fixture(tmp_path)

    result = promote_external_dataset_registry_v2_intake(config, tmp_path)

    expected = str(
        (
            tmp_path
            / "dataset/01_raw/99_external/roboflow/rf_car_damage_seg_v1"
        ).resolve()
    )
    assert result.output_rows[0]["local_raw_path"] == expected


def test_local_raw_path_outside_project_blocks(tmp_path: Path) -> None:
    outside = (tmp_path.parent / "outside_raw").resolve()
    outside.mkdir(exist_ok=True)
    proposal = make_proposal_row(tmp_path, local_raw_path=str(outside))
    config, _, _ = write_fixture(tmp_path, proposal_rows=[proposal])

    with pytest.raises(RegistryIntakePromotionError, match="local_raw_path"):
        promote_external_dataset_registry_v2_intake(config, tmp_path)


def test_missing_local_raw_path_blocks(tmp_path: Path) -> None:
    proposal = make_proposal_row(tmp_path)
    raw_path = Path(proposal["local_raw_path"])
    config, _, _ = write_fixture(tmp_path, proposal_rows=[proposal])
    raw_path.rmdir()

    with pytest.raises(RegistryIntakePromotionError, match="local_raw_path"):
        promote_external_dataset_registry_v2_intake(config, tmp_path)


def test_registry_sha256_mismatch_blocks_without_write(tmp_path: Path) -> None:
    config, registry, _ = write_fixture(
        tmp_path,
        expected_registry_sha256="0" * 64,
    )
    before = registry.read_bytes()

    with pytest.raises(RegistryIntakePromotionError, match="Registry SHA256"):
        promote_external_dataset_registry_v2_intake(config, tmp_path, execute=True)

    assert registry.read_bytes() == before


def test_proposal_sha256_mismatch_blocks_without_write(tmp_path: Path) -> None:
    config, registry, proposal = write_fixture(
        tmp_path,
        expected_proposal_sha256="0" * 64,
    )
    registry_before = registry.read_bytes()
    proposal_before = proposal.read_bytes()

    with pytest.raises(RegistryIntakePromotionError, match="proposal SHA256"):
        promote_external_dataset_registry_v2_intake(config, tmp_path, execute=True)

    assert registry.read_bytes() == registry_before
    assert proposal.read_bytes() == proposal_before


@pytest.mark.parametrize(
    ("registry_rows", "message"),
    [
        ([make_registry_row(Path("."), "other_dataset")], "exactly once"),
        (
            [
                make_registry_row(Path(".")),
                make_registry_row(Path(".")),
            ],
            "exactly once",
        ),
    ],
)
def test_target_registry_row_must_match_exactly_once(
    tmp_path: Path,
    registry_rows: list[dict[str, str]],
    message: str,
) -> None:
    config, _, _ = write_fixture(tmp_path, registry_rows=registry_rows)

    with pytest.raises(RegistryIntakePromotionError, match=message):
        promote_external_dataset_registry_v2_intake(config, tmp_path)


def test_proposal_must_have_exactly_one_target_row(tmp_path: Path) -> None:
    proposals = [make_proposal_row(tmp_path), make_proposal_row(tmp_path)]
    config, _, _ = write_fixture(tmp_path, proposal_rows=proposals)

    with pytest.raises(RegistryIntakePromotionError, match="proposal.*exactly one"):
        promote_external_dataset_registry_v2_intake(config, tmp_path)


def test_registry_schema_must_be_exact_42_columns(tmp_path: Path) -> None:
    config, _, _ = write_fixture(
        tmp_path,
        registry_columns=REGISTRY_COLUMNS[:-1],
    )

    with pytest.raises(RegistryIntakePromotionError, match="Registry schema"):
        promote_external_dataset_registry_v2_intake(config, tmp_path)


def test_proposal_schema_must_be_exact_30_columns(tmp_path: Path) -> None:
    config, _, _ = write_fixture(
        tmp_path,
        proposal_columns=CURRENT_COLUMNS[:-1],
    )

    with pytest.raises(RegistryIntakePromotionError, match="proposal schema"):
        promote_external_dataset_registry_v2_intake(config, tmp_path)


def test_execute_uses_atomic_replace_and_writes_verified_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, registry, proposal = write_fixture(tmp_path)
    proposal_before = proposal.read_bytes()
    real_replace = promotion_module.os.replace
    calls: list[tuple[Path, Path]] = []

    def tracked(
        source: os.PathLike[str],
        destination: os.PathLike[str],
    ) -> None:
        calls.append((Path(source), Path(destination)))
        real_replace(source, destination)

    monkeypatch.setattr(promotion_module.os, "replace", tracked)

    result = promote_external_dataset_registry_v2_intake(
        config,
        tmp_path,
        execute=True,
    )
    columns, rows = parse_payload(registry.read_bytes())

    assert result.classification == EXECUTE_CLASSIFICATION
    assert result.summary.registry_updated is True
    assert len(calls) == 1
    assert columns == REGISTRY_COLUMNS
    assert {name: rows[0][name] for name in PROMOTION_COLUMNS} == {
        name: make_proposal_row(tmp_path)[name] for name in PROMOTION_COLUMNS
    }
    assert rows[0]["training_acceptance"] == "NOT_YET_APPROVED"
    assert proposal.read_bytes() == proposal_before
    assert not list(registry.parent.glob(".registry_v2_intake_promotion_*"))


def test_replace_failure_preserves_original_and_cleans_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, registry, _ = write_fixture(tmp_path)
    before = registry.read_bytes()

    def fail(*args: Any, **kwargs: Any) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr(promotion_module.os, "replace", fail)

    with pytest.raises(
        RegistryIntakePromotionError,
        match="atomic replacement failed",
    ):
        promote_external_dataset_registry_v2_intake(
            config,
            tmp_path,
            execute=True,
        )

    assert registry.read_bytes() == before
    assert not list(registry.parent.glob(".registry_v2_intake_promotion_*"))


def test_exact_already_applied_registry_is_noop(tmp_path: Path) -> None:
    config, registry, _ = write_fixture(tmp_path)
    dry_run = promote_external_dataset_registry_v2_intake(config, tmp_path)
    registry.write_bytes(dry_run.output_bytes)
    before = registry.read_bytes()

    result = promote_external_dataset_registry_v2_intake(
        config,
        tmp_path,
        execute=True,
    )

    assert result.classification == ALREADY_APPLIED_CLASSIFICATION
    assert result.summary.registry_updated is False
    assert registry.read_bytes() == before


def test_already_applied_requires_all_11_fields_to_match(tmp_path: Path) -> None:
    config, registry, _ = write_fixture(tmp_path)
    dry_run = promote_external_dataset_registry_v2_intake(config, tmp_path)
    columns, rows = parse_payload(dry_run.output_bytes)
    rows[0]["bbox_count_valid"] = "999"
    registry.write_bytes(encode_csv(columns, rows))

    with pytest.raises(RegistryIntakePromotionError, match="promotion field"):
        promote_external_dataset_registry_v2_intake(config, tmp_path)


@pytest.mark.parametrize("bom", [False, True])
def test_registry_utf8_bom_behavior_is_preserved(
    tmp_path: Path,
    bom: bool,
) -> None:
    config, _, _ = write_fixture(tmp_path, registry_bom=bom)

    result = promote_external_dataset_registry_v2_intake(config, tmp_path)

    assert result.output_bytes.startswith(b"\xef\xbb\xbf") is bom


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_registry_line_ending_style_is_preserved(
    tmp_path: Path,
    newline: str,
) -> None:
    config, _, _ = write_fixture(tmp_path, registry_newline=newline)

    result = promote_external_dataset_registry_v2_intake(config, tmp_path)
    body = (
        result.output_bytes[3:]
        if result.output_bytes.startswith(b"\xef\xbb\xbf")
        else result.output_bytes
    )

    assert body.count(newline.encode()) >= 2
    if newline == "\r\n":
        assert body.replace(b"\r\n", b"").find(b"\n") == -1


def test_quoted_and_multiline_proposal_value_round_trips(tmp_path: Path) -> None:
    notes = 'comma, "quoted", and\nmultiline'
    proposal = make_proposal_row(tmp_path, notes=notes)
    config, _, _ = write_fixture(tmp_path, proposal_rows=[proposal])

    result = promote_external_dataset_registry_v2_intake(config, tmp_path)
    _, rows = parse_payload(result.output_bytes)

    assert rows[0]["notes"] == notes


def test_config_and_data_paths_cannot_escape_project_root(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside_config = tmp_path / "outside.yaml"
    outside_config.write_text("{}", encoding="utf-8")

    with pytest.raises(RegistryIntakePromotionError, match="outside project root"):
        load_promotion_config(outside_config, project)


def test_protected_metadata_raw_and_interim_are_not_modified(
    tmp_path: Path,
) -> None:
    config, _, proposal = write_fixture(tmp_path)

    metadata_sentinel = proposal.parent / "keep.bin"
    metadata_sentinel.write_bytes(b"protected metadata")

    raw_sentinel = (
        tmp_path
        / "dataset/01_raw/99_external/roboflow/rf_car_damage_seg_v1/keep.bin"
    )
    raw_sentinel.write_bytes(b"raw")

    interim_sentinel = (
        tmp_path
        / "dataset/02_interim/99_external/roboflow/rf_car_damage_seg_v1/keep.bin"
    )
    interim_sentinel.parent.mkdir(parents=True, exist_ok=True)
    interim_sentinel.write_bytes(b"interim")

    before = {
        metadata_sentinel: metadata_sentinel.read_bytes(),
        raw_sentinel: raw_sentinel.read_bytes(),
        interim_sentinel: interim_sentinel.read_bytes(),
        proposal: proposal.read_bytes(),
    }

    promote_external_dataset_registry_v2_intake(
        config,
        tmp_path,
        execute=True,
    )

    assert {path: path.read_bytes() for path in before} == before


def test_already_applied_rejects_registry_dataset_id_order_drift(
    tmp_path: Path,
) -> None:
    registry_rows = [
        make_registry_row(tmp_path),
        make_registry_row(tmp_path, dataset_id="other_dataset"),
    ]
    config, registry, _ = write_fixture(
        tmp_path,
        registry_rows=registry_rows,
    )
    dry_run = promote_external_dataset_registry_v2_intake(
        config,
        tmp_path,
    )
    columns, applied_rows = parse_payload(dry_run.output_bytes)
    applied_rows.reverse()
    registry.write_bytes(encode_csv(columns, applied_rows))

    with pytest.raises(
        RegistryIntakePromotionError,
        match="dataset_id order|row order",
    ):
        promote_external_dataset_registry_v2_intake(
            config,
            tmp_path,
        )


def test_registry_crlf_with_embedded_lf_multiline_value_is_supported(
    tmp_path: Path,
) -> None:
    multiline_notes = "line one\nline two"
    registry_rows = [
        make_registry_row(tmp_path),
        make_registry_row(
            tmp_path,
            dataset_id="other_dataset",
            notes=multiline_notes,
        ),
    ]
    config, _, _ = write_fixture(
        tmp_path,
        registry_rows=registry_rows,
        registry_newline="\r\n",
    )

    result = promote_external_dataset_registry_v2_intake(
        config,
        tmp_path,
    )

    assert result.output_rows[1]["notes"] == multiline_notes
    body = (
        result.output_bytes[3:]
        if result.output_bytes.startswith(b"\xef\xbb\xbf")
        else result.output_bytes
    )
    assert b"\r\n" in body
    assert b"line one\nline two" in body


def test_cli_dry_run_and_execute_are_mutually_exclusive() -> None:
    cli = load_cli_module()

    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(["--dry-run", "--execute"])


def test_cli_default_mode_is_dry_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = load_cli_module()
    config, _, _ = write_fixture(tmp_path)
    result = promote_external_dataset_registry_v2_intake(config, tmp_path)
    called: list[bool] = []

    monkeypatch.setattr(cli, "resolve_project_root", lambda value: tmp_path)
    monkeypatch.setattr(
        cli,
        "promote_external_dataset_registry_v2_intake",
        lambda *args, execute=False, **kwargs: called.append(execute) or result,
    )

    assert cli.main(["--config", str(config)]) == 0
    assert called == [False]


def test_cli_summary_contains_all_safety_flags(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cli = load_cli_module()
    config, _, _ = write_fixture(tmp_path)
    result = promote_external_dataset_registry_v2_intake(config, tmp_path)

    monkeypatch.setattr(cli, "resolve_project_root", lambda value: tmp_path)
    monkeypatch.setattr(
        cli,
        "promote_external_dataset_registry_v2_intake",
        lambda *args, **kwargs: result,
    )

    assert cli.main(["--config", str(config), "--dry-run"]) == 0
    output = capsys.readouterr().out

    for flag in [
        "REGISTRY_UPDATED: NO",
        "RAW_SOURCE_MODIFIED: NO",
        "INTERIM_SOURCE_MODIFIED: NO",
        "EXTERNAL_METADATA_MODIFIED: NO",
        "YOLO_LABELS_CREATED: NO",
        "DATASET_SPLIT_CREATED: NO",
        "MODEL_TRAINING_EXECUTED: NO",
        "TRAINING_ACCEPTANCE: NOT_YET_APPROVED",
    ]:
        assert flag in output
