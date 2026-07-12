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

import fleetvision.data.migrate_external_dataset_registry_v2 as migration_module
from fleetvision.data.migrate_external_dataset_registry_v2 import (
    NEW_COLUMNS,
    RegistryMigrationError,
    load_migration_config,
    migrate_external_dataset_registry_v2,
    read_registry,
)


CURRENT_COLUMNS = [
    "dataset_id", "platform", "dataset_name", "source_url", "publisher", "license",
    "license_evidence_url", "license_verified", "search_date", "download_date",
    "dataset_version", "task_type", "annotation_format", "original_classes",
    "image_count_reported", "image_count_downloaded", "bbox_count_reported",
    "bbox_count_valid", "accepted_image_count", "rejected_image_count",
    "mapping_to_damage", "domain_similarity", "bbox_quality_status",
    "sha256_dedup_status", "perceptual_hash_status", "internal_cross_dedup_status",
    "usage_status", "rejection_reason", "local_raw_path", "notes",
]

EXPECTED_NEW_COLUMNS = [
    "registry_schema_version", "lineage_status", "bbox_count_valid_raw",
    "bbox_count_invalid_raw", "bbox_quality_status_raw", "bbox_repair_count",
    "bbox_count_valid_interim", "bbox_count_invalid_interim",
    "bbox_quality_status_interim", "bbox_repair_status", "local_interim_path",
    "training_acceptance",
]

TARGET_VALUES = {
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


def make_row(dataset_id: str = "rf_car_damage_seg_v1", **overrides: str) -> dict[str, str]:
    row = {column: "" for column in CURRENT_COLUMNS}
    row.update(
        {
            "dataset_id": dataset_id,
            "platform": "roboflow",
            "dataset_name": "Car-Damage detection",
            "license_verified": "yes",
            "usage_status": "approved_for_download",
            "bbox_quality_status": "pending_download_qa",
            "notes": "original, quoted value",
        }
    )
    row.update(overrides)
    return row


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


def write_fixture(
    tmp_path: Path,
    *,
    rows: list[dict[str, str]] | None = None,
    columns: list[str] | None = None,
    bom: bool = True,
    newline: str = "\n",
    expected_sha256: str | None = None,
    registry_rel: str = "dataset/00_catalog/external_dataset_registry.csv",
) -> tuple[Path, Path]:
    registry = tmp_path / registry_rel
    registry.parent.mkdir(parents=True, exist_ok=True)
    payload = encode_csv(columns or CURRENT_COLUMNS, rows or [make_row()], bom=bom, newline=newline)
    registry.write_bytes(payload)
    digest = expected_sha256 or hashlib.sha256(payload).hexdigest()
    config = tmp_path / "configs/data/external_dataset_registry_v2_migration_config.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        yaml.safe_dump(
            {
                "registry_csv": registry_rel,
                "target_dataset_id": "rf_car_damage_seg_v1",
                "expected_input_sha256": digest,
                "expected_current_columns": CURRENT_COLUMNS,
                "new_columns": EXPECTED_NEW_COLUMNS,
                "target_values": TARGET_VALUES,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return config, registry


def parse_payload(payload: bytes) -> tuple[list[str], list[dict[str, str]]]:
    text = payload.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    return list(reader.fieldnames or []), list(reader)


def load_cli_module() -> Any:
    script = Path(__file__).resolve().parents[1] / "scripts/phase04_5_migrate_external_dataset_registry_v2.py"
    spec = importlib.util.spec_from_file_location("registry_v2_cli", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_new_columns_match_fixed_contract() -> None:
    assert list(NEW_COLUMNS) == EXPECTED_NEW_COLUMNS


def test_dry_run_builds_exact_42_column_proposal(tmp_path: Path) -> None:
    config, _ = write_fixture(tmp_path)
    result = migrate_external_dataset_registry_v2(config, tmp_path)
    assert result.output_columns == tuple([*CURRENT_COLUMNS, *EXPECTED_NEW_COLUMNS])
    assert len(result.output_columns) == 42
    assert result.classification == "EXTERNAL_DATASET_REGISTRY_V2_MIGRATION_DRY_RUN_VERIFIED"


def test_dry_run_does_not_modify_input_bytes_or_sha256(tmp_path: Path) -> None:
    config, registry = write_fixture(tmp_path)
    before = registry.read_bytes()
    migrate_external_dataset_registry_v2(config, tmp_path)
    assert registry.read_bytes() == before
    assert hashlib.sha256(registry.read_bytes()).hexdigest() == hashlib.sha256(before).hexdigest()
    assert not list(registry.parent.glob("*.tmp"))


def test_execute_appends_columns_in_exact_order(tmp_path: Path) -> None:
    config, registry = write_fixture(tmp_path)
    result = migrate_external_dataset_registry_v2(config, tmp_path, execute=True)
    document = read_registry(registry)
    assert document.columns == tuple([*CURRENT_COLUMNS, *EXPECTED_NEW_COLUMNS])
    assert result.summary.registry_updated is True


def test_execute_preserves_every_existing_value(tmp_path: Path) -> None:
    original = make_row(notes='comma, quote " and\nnewline', bbox_count_valid="legacy")
    config, registry = write_fixture(tmp_path, rows=[original])
    migrate_external_dataset_registry_v2(config, tmp_path, execute=True)
    _, rows = parse_payload(registry.read_bytes())
    assert {key: rows[0][key] for key in CURRENT_COLUMNS} == original


def test_target_row_gets_exact_v2_values(tmp_path: Path) -> None:
    config, _ = write_fixture(tmp_path)
    result = migrate_external_dataset_registry_v2(config, tmp_path)
    assert {key: result.output_rows[0][key] for key in EXPECTED_NEW_COLUMNS} == TARGET_VALUES


def test_non_target_rows_only_receive_schema_version(tmp_path: Path) -> None:
    rows = [make_row("other_dataset"), make_row()]
    config, _ = write_fixture(tmp_path, rows=rows)
    result = migrate_external_dataset_registry_v2(config, tmp_path)
    assert result.output_rows[0]["registry_schema_version"] == "2"
    assert all(result.output_rows[0][column] == "" for column in EXPECTED_NEW_COLUMNS[1:])


def test_row_order_is_preserved(tmp_path: Path) -> None:
    rows = [make_row("first"), make_row(), make_row("last")]
    config, _ = write_fixture(tmp_path, rows=rows)
    result = migrate_external_dataset_registry_v2(config, tmp_path)
    assert [row["dataset_id"] for row in result.output_rows] == ["first", "rf_car_damage_seg_v1", "last"]


def test_target_dataset_missing_blocks(tmp_path: Path) -> None:
    config, _ = write_fixture(tmp_path, rows=[make_row("other")])
    with pytest.raises(RegistryMigrationError, match="exactly once"):
        migrate_external_dataset_registry_v2(config, tmp_path)


def test_duplicate_target_dataset_blocks(tmp_path: Path) -> None:
    config, _ = write_fixture(tmp_path, rows=[make_row(), make_row()])
    with pytest.raises(RegistryMigrationError, match="exactly once"):
        migrate_external_dataset_registry_v2(config, tmp_path)


def test_duplicate_current_headers_block(tmp_path: Path) -> None:
    columns = [*CURRENT_COLUMNS]
    columns[-1] = columns[0]
    config, _ = write_fixture(tmp_path, columns=columns)
    with pytest.raises(RegistryMigrationError, match="duplicate header"):
        migrate_external_dataset_registry_v2(config, tmp_path)


def test_unexpected_current_column_blocks(tmp_path: Path) -> None:
    columns = [*CURRENT_COLUMNS]
    columns[-1] = "unexpected"
    config, _ = write_fixture(tmp_path, columns=columns)
    with pytest.raises(RegistryMigrationError, match="schema"):
        migrate_external_dataset_registry_v2(config, tmp_path)


def test_missing_current_column_blocks(tmp_path: Path) -> None:
    config, _ = write_fixture(tmp_path, columns=CURRENT_COLUMNS[:-1])
    with pytest.raises(RegistryMigrationError, match="schema"):
        migrate_external_dataset_registry_v2(config, tmp_path)


def test_unexpected_extra_current_column_blocks(tmp_path: Path) -> None:
    config, _ = write_fixture(tmp_path, columns=[*CURRENT_COLUMNS, "unexpected"])
    with pytest.raises(RegistryMigrationError, match="schema"):
        migrate_external_dataset_registry_v2(config, tmp_path)


def test_input_sha256_mismatch_blocks_without_write(tmp_path: Path) -> None:
    config, registry = write_fixture(tmp_path, expected_sha256="0" * 64)
    before = registry.read_bytes()
    with pytest.raises(RegistryMigrationError, match="SHA256"):
        migrate_external_dataset_registry_v2(config, tmp_path, execute=True)
    assert registry.read_bytes() == before


def test_partial_v2_schema_blocks(tmp_path: Path) -> None:
    config, _ = write_fixture(tmp_path, columns=[*CURRENT_COLUMNS, EXPECTED_NEW_COLUMNS[0]])
    with pytest.raises(RegistryMigrationError, match="schema"):
        migrate_external_dataset_registry_v2(config, tmp_path)


def test_wrong_v2_column_order_blocks(tmp_path: Path) -> None:
    wrong = [*CURRENT_COLUMNS, *reversed(EXPECTED_NEW_COLUMNS)]
    config, _ = write_fixture(tmp_path, columns=wrong)
    with pytest.raises(RegistryMigrationError, match="schema"):
        migrate_external_dataset_registry_v2(config, tmp_path)


def make_already_applied(tmp_path: Path, rows: list[dict[str, str]] | None = None) -> tuple[Path, Path, bytes]:
    config, registry = write_fixture(tmp_path, rows=rows)
    proposal = migrate_external_dataset_registry_v2(config, tmp_path)
    registry.write_bytes(proposal.output_bytes)
    return config, registry, proposal.output_bytes


def test_exact_already_migrated_registry_is_noop_without_v1_sha(tmp_path: Path) -> None:
    config, registry, migrated = make_already_applied(tmp_path)
    result = migrate_external_dataset_registry_v2(config, tmp_path, execute=True)
    assert result.classification == "EXTERNAL_DATASET_REGISTRY_V2_MIGRATION_ALREADY_APPLIED"
    assert result.summary.registry_updated is False
    assert registry.read_bytes() == migrated


def test_already_migrated_wrong_target_value_blocks(tmp_path: Path) -> None:
    config, registry, _ = make_already_applied(tmp_path)
    columns, rows = parse_payload(registry.read_bytes())
    rows[0]["bbox_repair_count"] = "402"
    registry.write_bytes(encode_csv(columns, rows))
    with pytest.raises(RegistryMigrationError, match="configured v2 value"):
        migrate_external_dataset_registry_v2(config, tmp_path)


def test_already_migrated_non_target_value_must_be_blank(tmp_path: Path) -> None:
    config, registry, _ = make_already_applied(tmp_path, [make_row("other"), make_row()])
    columns, rows = parse_payload(registry.read_bytes())
    rows[0]["lineage_status"] = "not-empty"
    registry.write_bytes(encode_csv(columns, rows))
    with pytest.raises(RegistryMigrationError, match="non-target"):
        migrate_external_dataset_registry_v2(config, tmp_path)


def test_execute_uses_os_replace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config, _ = write_fixture(tmp_path)
    real_replace = migration_module.os.replace
    calls: list[tuple[Path, Path]] = []
    def tracked(source: os.PathLike[str], destination: os.PathLike[str]) -> None:
        calls.append((Path(source), Path(destination)))
        real_replace(source, destination)
    monkeypatch.setattr(migration_module.os, "replace", tracked)
    migrate_external_dataset_registry_v2(config, tmp_path, execute=True)
    assert len(calls) == 1


def test_replace_failure_leaves_original_unchanged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config, registry = write_fixture(tmp_path)
    before = registry.read_bytes()
    def fail(*args: Any, **kwargs: Any) -> None:
        raise OSError("simulated replace failure")
    monkeypatch.setattr(migration_module.os, "replace", fail)
    with pytest.raises(RegistryMigrationError, match="atomic replacement failed"):
        migrate_external_dataset_registry_v2(config, tmp_path, execute=True)
    assert registry.read_bytes() == before


def test_temporary_file_is_cleaned_after_success_and_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config, registry = write_fixture(tmp_path)
    migrate_external_dataset_registry_v2(config, tmp_path, execute=True)
    assert not list(registry.parent.glob(".registry_v2_migration_*"))
    config, registry = write_fixture(tmp_path)
    monkeypatch.setattr(migration_module.os, "replace", lambda *args: (_ for _ in ()).throw(OSError("fail")))
    with pytest.raises(RegistryMigrationError):
        migrate_external_dataset_registry_v2(config, tmp_path, execute=True)
    assert not list(registry.parent.glob(".registry_v2_migration_*"))


def test_csv_quoted_values_round_trip(tmp_path: Path) -> None:
    value = 'comma, "quoted", and\nmultiline'
    config, _ = write_fixture(tmp_path, rows=[make_row(notes=value)])
    result = migrate_external_dataset_registry_v2(config, tmp_path)
    _, rows = parse_payload(result.output_bytes)
    assert rows[0]["notes"] == value


@pytest.mark.parametrize("bom", [False, True])
def test_utf8_bom_behavior_is_preserved(tmp_path: Path, bom: bool) -> None:
    config, _ = write_fixture(tmp_path, bom=bom)
    result = migrate_external_dataset_registry_v2(config, tmp_path)
    assert result.output_bytes.startswith(b"\xef\xbb\xbf") is bom


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_line_ending_style_is_preserved(tmp_path: Path, newline: str) -> None:
    config, _ = write_fixture(tmp_path, newline=newline)
    result = migrate_external_dataset_registry_v2(config, tmp_path)
    body = result.output_bytes[3:] if result.output_bytes.startswith(b"\xef\xbb\xbf") else result.output_bytes
    assert body.count(newline.encode()) >= 2
    if newline == "\r\n":
        assert body.replace(b"\r\n", b"").find(b"\n") == -1


def test_config_path_outside_project_root_blocks(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside.yaml"
    outside.write_text("{}", encoding="utf-8")
    with pytest.raises(RegistryMigrationError, match="outside project root"):
        load_migration_config(outside, project)


def test_registry_path_escape_blocks(tmp_path: Path) -> None:
    config, _ = write_fixture(tmp_path)
    data = yaml.safe_load(config.read_text(encoding="utf-8"))
    data["registry_csv"] = "../outside.csv"
    config.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    with pytest.raises(RegistryMigrationError, match="outside project root"):
        load_migration_config(config, tmp_path)


def test_cli_dry_run_and_execute_are_mutually_exclusive() -> None:
    cli = load_cli_module()
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(["--dry-run", "--execute"])


def test_cli_default_mode_is_dry_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cli = load_cli_module()
    called: list[bool] = []
    config, _ = write_fixture(tmp_path)
    result = migrate_external_dataset_registry_v2(config, tmp_path)
    monkeypatch.setattr(cli, "resolve_project_root", lambda value: tmp_path)
    monkeypatch.setattr(cli, "migrate_external_dataset_registry_v2", lambda *a, execute=False, **k: called.append(execute) or result)
    assert cli.main(["--config", str(config)]) == 0
    assert called == [False]


def test_real_config_parses_successfully() -> None:
    root = Path(__file__).resolve().parents[1]
    config = load_migration_config(root / "configs/data/external_dataset_registry_v2_migration_config.yaml", root)
    assert config.target_dataset_id == "rf_car_damage_seg_v1"
    assert config.expected_input_sha256 == "c20115bf7f271b455550fb0a38da43fe6b73330b26d5dc7c2c6524835b1bdc9d"


def test_cli_summary_contains_all_safety_flags(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    cli = load_cli_module()
    config, _ = write_fixture(tmp_path)
    result = migrate_external_dataset_registry_v2(config, tmp_path)
    monkeypatch.setattr(cli, "resolve_project_root", lambda value: tmp_path)
    monkeypatch.setattr(cli, "migrate_external_dataset_registry_v2", lambda *a, **k: result)
    assert cli.main(["--config", str(config), "--dry-run"]) == 0
    output = capsys.readouterr().out
    for flag in ["REGISTRY_UPDATED: NO", "RAW_SOURCE_MODIFIED: NO", "INTERIM_SOURCE_MODIFIED: NO", "EXTERNAL_METADATA_MODIFIED: NO", "YOLO_LABELS_CREATED: NO", "DATASET_SPLIT_CREATED: NO", "MODEL_TRAINING_EXECUTED: NO"]:
        assert flag in output


def test_external_assets_sentinel_is_not_modified(tmp_path: Path) -> None:
    config, _ = write_fixture(tmp_path)
    sentinel = tmp_path / "outputs/metadata/external_assets/keep.txt"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_bytes(b"keep")
    migrate_external_dataset_registry_v2(config, tmp_path, execute=True)
    assert sentinel.read_bytes() == b"keep"
    assert list(sentinel.parent.iterdir()) == [sentinel]


def test_no_raw_interim_yolo_split_or_training_artifacts_are_created(tmp_path: Path) -> None:
    config, _ = write_fixture(tmp_path)
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    migrate_external_dataset_registry_v2(config, tmp_path, execute=True)
    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    added = set(after) - set(before)
    assert not any(path.startswith("dataset/01_raw/") or path.startswith("dataset/02_interim/") or "05_yolo" in path or "training" in path for path in added)
