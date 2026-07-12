from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
import yaml
from PIL import Image, ImageDraw

import fleetvision.data.audit_external_dataset_deduplication as dedup_module
from fleetvision.data.audit_external_dataset_deduplication import (
    CandidateOverflowError,
    ConfigInputError,
    DeduplicationAuditError,
    HashingIntegrityError,
    ImageHashRecord,
    OutputPromotionError,
    build_deduplication_audit,
    compute_dhash_hex,
    compute_phash_hex,
    hamming_distance_hex,
    load_deduplication_config,
    sha256_file,
)


DATASET_ID = "rf_car_damage_seg_v1"


def make_image(path: Path, *, pattern: str = "gradient", size: tuple[int, int] = (64, 48)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(image)
    if pattern == "gradient":
        for x in range(size[0]):
            shade = int(255 * x / max(1, size[0] - 1))
            draw.line((x, 0, x, size[1]), fill=(shade, shade, shade))
    elif pattern == "checker":
        for y in range(0, size[1], 8):
            for x in range(0, size[0], 8):
                if (x // 8 + y // 8) % 2:
                    draw.rectangle((x, y, x + 7, y + 7), fill="black")
    elif pattern == "diagonal":
        draw.line((0, 0, size[0] - 1, size[1] - 1), fill="black", width=5)
    image.save(path)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def config_payload(tmp_path: Path) -> dict[str, Any]:
    return {
        "dataset_id": DATASET_ID,
        "internal_metadata_path": "outputs/metadata/image_metadata.csv",
        "external_image_inventory_path": "outputs/metadata/external_assets/inventory.csv",
        "external_raw_root": "dataset/01_raw/99_external/roboflow/dataset",
        "output_root": "outputs/metadata/external_dedup/roboflow/dataset",
        "hashing": {
            "sha256_chunk_size_bytes": 64,
            "phash_size": 8,
            "dhash_size": 8,
            "verify_external_sha256": True,
        },
        "candidate_rules": {
            "phash_hamming_distance_max": 6,
            "dhash_hamming_distance_max": 8,
            "aspect_ratio_relative_difference_max": 0.10,
            "exclude_exact_matches_from_perceptual_candidates": True,
            "max_candidates_per_record": 500,
            "candidate_overflow_policy": "fail",
        },
        "scope": {
            "external_external_exact": True,
            "internal_external_exact": True,
            "external_external_perceptual": True,
            "internal_external_perceptual": True,
            "internal_internal_exact": False,
            "internal_internal_perceptual": False,
        },
        "execution": {
            "overwrite_existing_output": False,
            "fail_on_any_hash_error": True,
            "write_error_report_on_failure": True,
        },
    }


def write_config(tmp_path: Path, payload: dict[str, Any] | None = None) -> Path:
    path = tmp_path / "configs/dedup.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload or config_payload(tmp_path), sort_keys=False), encoding="utf-8")
    return path


def write_fixture(
    tmp_path: Path,
    *,
    internal_patterns: tuple[str, ...] = ("gradient",),
    external_patterns: tuple[str, ...] = ("checker",),
    external_sizes: tuple[tuple[int, int], ...] | None = None,
) -> tuple[Path, list[Path], list[Path]]:
    internal_paths: list[Path] = []
    internal_rows: list[dict[str, Any]] = []
    for index, pattern in enumerate(internal_patterns, start=1):
        path = tmp_path / f"dataset/01_raw/internal/internal_{index}.png"
        make_image(path, pattern=pattern)
        internal_paths.append(path)
        with Image.open(path) as image:
            width, height = image.size
        internal_rows.append(
            {
                "image_id": f"i{index}",
                "source_bucket": "01_general_fleet",
                "original_path": path.relative_to(tmp_path).as_posix(),
                "filename": path.name,
                "extension": ".png",
                "file_size_bytes": path.stat().st_size,
                "width": width,
                "height": height,
                "aspect_ratio": width / height,
                "is_readable": True,
                "created_at": "",
                "modified_at": "",
                "notes": "",
            }
        )

    external_paths: list[Path] = []
    external_rows: list[dict[str, Any]] = []
    sizes = external_sizes or tuple((64, 48) for _ in external_patterns)
    for index, (pattern, size) in enumerate(zip(external_patterns, sizes, strict=True), start=1):
        relative = Path(f"train/external_{index}.png")
        path = (
            tmp_path
            / "dataset/01_raw/99_external/roboflow/dataset/01_extracted_export"
            / relative
        )
        make_image(path, pattern=pattern, size=size)
        external_paths.append(path)
        with Image.open(path) as image:
            width, height = image.size
        external_rows.append(
            {
                "split": "train",
                "annotation_json": "train/_annotations.coco.json",
                "image_id": f"e{index}",
                "file_name": path.name,
                "relative_image_path": relative.as_posix(),
                "width": width,
                "height": height,
                "file_exists": True,
                "size_bytes": path.stat().st_size,
                "sha256": file_sha256(path),
            }
        )

    internal_csv = tmp_path / "outputs/metadata/image_metadata.csv"
    external_csv = tmp_path / "outputs/metadata/external_assets/inventory.csv"
    internal_csv.parent.mkdir(parents=True, exist_ok=True)
    external_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        internal_rows,
        columns=[
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
        ],
    ).to_csv(internal_csv, index=False, encoding="utf-8-sig")
    pd.DataFrame(
        external_rows,
        columns=[
            "split",
            "annotation_json",
            "image_id",
            "file_name",
            "relative_image_path",
            "width",
            "height",
            "file_exists",
            "size_bytes",
            "sha256",
        ],
    ).to_csv(external_csv, index=False, encoding="utf-8-sig")
    return write_config(tmp_path), internal_paths, external_paths


def load_config(tmp_path: Path, config_path: Path | None = None):
    return load_deduplication_config(config_path or write_config(tmp_path), project_root=tmp_path)


def record(
    record_id: str,
    *,
    scope: str,
    phash: str,
    dhash: str,
    sha256: str = "A" * 64,
    aspect_ratio: float = 1.0,
) -> ImageHashRecord:
    return ImageHashRecord(
        record_id=record_id,
        source_scope=scope,
        dataset_id=DATASET_ID if scope == "external" else "",
        source_bucket="train" if scope == "external" else "01_general_fleet",
        image_id=record_id.rsplit(":", 1)[-1],
        relative_image_path=f"fixtures/{record_id.rsplit(':', 1)[-1]}.png",
        absolute_image_path=Path("C:/fixtures") / f"{record_id.rsplit(':', 1)[-1]}.png",
        file_size_bytes=1,
        width=10,
        height=10,
        aspect_ratio=aspect_ratio,
        sha256=sha256,
        phash_hex=phash,
        dhash_hex=dhash,
        hash_status="success",
        error_reason="",
    )


def load_cli_module() -> Any:
    script = Path(__file__).resolve().parents[1] / "scripts/phase04_5_audit_external_dataset_deduplication.py"
    spec = importlib.util.spec_from_file_location("phase04_5_dedup_cli", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_valid_config_resolves_paths(tmp_path: Path) -> None:
    config = load_config(tmp_path)
    assert config.dataset_id == DATASET_ID
    assert config.internal_metadata_path == tmp_path / "outputs/metadata/image_metadata.csv"
    assert config.phash_size == 8


def test_unknown_config_key_is_rejected(tmp_path: Path) -> None:
    payload = config_payload(tmp_path)
    payload["unexpected"] = True
    with pytest.raises(ConfigInputError, match="unknown keys"):
        load_config(tmp_path, write_config(tmp_path, payload))


@pytest.mark.parametrize(
    ("section", "key", "value"),
    [
        ("hashing", "phash_size", 0),
        ("candidate_rules", "phash_hamming_distance_max", 65),
        ("candidate_rules", "aspect_ratio_relative_difference_max", 1.1),
        ("candidate_rules", "candidate_overflow_policy", "truncate"),
    ],
)
def test_invalid_config_thresholds_are_rejected(
    tmp_path: Path, section: str, key: str, value: Any
) -> None:
    payload = config_payload(tmp_path)
    payload[section][key] = value
    with pytest.raises(ConfigInputError):
        load_config(tmp_path, write_config(tmp_path, payload))


def test_output_root_must_stay_in_approved_derived_area(tmp_path: Path) -> None:
    payload = config_payload(tmp_path)
    payload["output_root"] = "dataset/01_raw/unsafe-output"
    with pytest.raises(ConfigInputError, match="output_root must be under"):
        load_config(tmp_path, write_config(tmp_path, payload))


def test_empty_collections_execute_with_header_only_outputs(tmp_path: Path) -> None:
    config_path, _, _ = write_fixture(tmp_path, internal_patterns=(), external_patterns=())
    result = build_deduplication_audit(load_config(tmp_path, config_path), execute=True)
    assert result.total_image_count == 0
    assert pd.read_csv(result.output_root / "image_hash_inventory.csv").empty


def test_sha256_streaming_returns_uppercase(tmp_path: Path) -> None:
    path = tmp_path / "payload.bin"
    path.write_bytes(b"abcdefghij")
    assert sha256_file(path, chunk_size=3) == hashlib.sha256(b"abcdefghij").hexdigest().upper()


def test_dhash_is_deterministic_fixed_width() -> None:
    image = Image.new("L", (16, 16))
    assert compute_dhash_hex(image, hash_size=8) == compute_dhash_hex(image, hash_size=8)
    assert len(compute_dhash_hex(image, hash_size=8)) == 16
    assert compute_dhash_hex(image, hash_size=8).upper() == compute_dhash_hex(image, hash_size=8)


def test_phash_is_deterministic_fixed_width() -> None:
    image = Image.new("L", (16, 16))
    assert compute_phash_hex(image, hash_size=8) == compute_phash_hex(image, hash_size=8)
    assert len(compute_phash_hex(image, hash_size=8)) == 16
    assert compute_phash_hex(image, hash_size=8).upper() == compute_phash_hex(image, hash_size=8)


def test_hamming_distance_hex() -> None:
    assert hamming_distance_hex("00", "0F") == 4
    with pytest.raises(DeduplicationAuditError):
        hamming_distance_hex("0", "00")


def test_exact_groups_and_cross_source_classification(tmp_path: Path) -> None:
    config_path, internal, external = write_fixture(tmp_path, external_patterns=("checker", "gradient"))
    external[1].write_bytes(internal[0].read_bytes())
    inventory = pd.read_csv(tmp_path / "outputs/metadata/external_assets/inventory.csv")
    inventory.loc[1, "size_bytes"] = external[1].stat().st_size
    inventory.loc[1, "sha256"] = file_sha256(external[1])
    inventory.to_csv(tmp_path / "outputs/metadata/external_assets/inventory.csv", index=False, encoding="utf-8-sig")
    result = build_deduplication_audit(load_config(tmp_path, config_path), execute=True)
    groups = pd.read_csv(result.output_root / "exact_duplicate_groups.csv")
    assert len(groups) == 1
    assert bool(groups.loc[0, "cross_source"])
    summary = pd.read_csv(result.output_root / "deduplication_summary.csv")
    assert int(summary.loc[0, "internal_external_exact_group_count"]) == 1


def test_internal_internal_exact_is_disabled(tmp_path: Path) -> None:
    config_path, internal, _ = write_fixture(tmp_path, internal_patterns=("gradient", "checker"), external_patterns=())
    internal[1].write_bytes(internal[0].read_bytes())
    metadata = pd.read_csv(tmp_path / "outputs/metadata/image_metadata.csv")
    metadata.loc[1, "file_size_bytes"] = internal[1].stat().st_size
    metadata.to_csv(tmp_path / "outputs/metadata/image_metadata.csv", index=False, encoding="utf-8-sig")
    result = build_deduplication_audit(load_config(tmp_path, config_path), execute=True)
    assert pd.read_csv(result.output_root / "exact_duplicate_groups.csv").empty


def test_external_external_exact_is_enabled(tmp_path: Path) -> None:
    config_path, _, external = write_fixture(tmp_path, internal_patterns=(), external_patterns=("gradient", "checker"))
    external[1].write_bytes(external[0].read_bytes())
    inventory = pd.read_csv(tmp_path / "outputs/metadata/external_assets/inventory.csv")
    inventory.loc[1, "size_bytes"] = external[1].stat().st_size
    inventory.loc[1, "sha256"] = file_sha256(external[1])
    inventory.to_csv(tmp_path / "outputs/metadata/external_assets/inventory.csv", index=False, encoding="utf-8-sig")
    result = build_deduplication_audit(load_config(tmp_path, config_path), execute=True)
    assert len(pd.read_csv(result.output_root / "exact_duplicate_groups.csv")) == 1


def test_small_perceptual_variation_creates_candidate(tmp_path: Path) -> None:
    config_path, internal, external = write_fixture(tmp_path, external_patterns=("gradient",))
    with Image.open(external[0]) as image:
        changed = image.copy()
    changed.putpixel((32, 24), (130, 130, 130))
    changed.save(external[0])
    inventory = pd.read_csv(tmp_path / "outputs/metadata/external_assets/inventory.csv")
    inventory.loc[0, "size_bytes"] = external[0].stat().st_size
    inventory.loc[0, "sha256"] = file_sha256(external[0])
    inventory.to_csv(tmp_path / "outputs/metadata/external_assets/inventory.csv", index=False, encoding="utf-8-sig")
    result = build_deduplication_audit(load_config(tmp_path, config_path), execute=True)
    assert len(pd.read_csv(result.output_root / "perceptual_duplicate_candidates.csv")) == 1


def test_different_image_is_excluded_from_perceptual_candidates(tmp_path: Path) -> None:
    config_path, _, _ = write_fixture(tmp_path, internal_patterns=("gradient",), external_patterns=("checker",))
    result = build_deduplication_audit(load_config(tmp_path, config_path), execute=True)
    assert pd.read_csv(result.output_root / "perceptual_duplicate_candidates.csv").empty


def test_exact_match_is_excluded_from_perceptual_candidates(tmp_path: Path) -> None:
    config_path, internal, external = write_fixture(tmp_path, external_patterns=("checker",))
    external[0].write_bytes(internal[0].read_bytes())
    inventory = pd.read_csv(tmp_path / "outputs/metadata/external_assets/inventory.csv")
    inventory.loc[0, "size_bytes"] = external[0].stat().st_size
    inventory.loc[0, "sha256"] = file_sha256(external[0])
    inventory.to_csv(tmp_path / "outputs/metadata/external_assets/inventory.csv", index=False, encoding="utf-8-sig")
    result = build_deduplication_audit(load_config(tmp_path, config_path), execute=True)
    assert pd.read_csv(result.output_root / "perceptual_duplicate_candidates.csv").empty


def test_aspect_ratio_filter_excludes_candidate(tmp_path: Path) -> None:
    config_path, _, _ = write_fixture(
        tmp_path,
        internal_patterns=("gradient",),
        external_patterns=("gradient",),
        external_sizes=((64, 24),),
    )
    result = build_deduplication_audit(load_config(tmp_path, config_path), execute=True)
    assert pd.read_csv(result.output_root / "perceptual_duplicate_candidates.csv").empty


def test_band_index_is_complete_within_threshold(tmp_path: Path) -> None:
    config = load_config(tmp_path)
    left = record("external:x:a", scope="external", phash="0000000000000000", dhash="0" * 16, sha256="A" * 64)
    right = record("external:x:b", scope="external", phash="000000000000003F", dhash="0" * 16, sha256="B" * 64)
    pairs = dedup_module._generate_perceptual_candidates([left, right], config)
    assert [(row["left_record_id"], row["right_record_id"]) for row in pairs] == [(left.record_id, right.record_id)]


def test_candidate_pairs_are_not_duplicated(tmp_path: Path) -> None:
    config = load_config(tmp_path)
    records = [
        record(f"external:x:{name}", scope="external", phash="0" * 16, dhash="0" * 16, sha256=name * 64)
        for name in ("A", "B", "C")
    ]
    pairs = dedup_module._generate_perceptual_candidates(records, config)
    ids = [(row["left_record_id"], row["right_record_id"]) for row in pairs]
    assert len(ids) == len(set(ids)) == 3


def test_disabled_internal_scope_does_not_enumerate_quadratic_pairs(tmp_path: Path) -> None:
    config = replace(load_config(tmp_path), max_candidates_per_record=1)
    records = [
        record(
            f"internal:{index:04d}",
            scope="internal",
            phash="0" * 16,
            dhash="0" * 16,
            sha256=f"{index:064X}",
        )
        for index in range(1200)
    ]
    started = time.perf_counter()
    assert dedup_module._generate_perceptual_candidates(records, config) == []
    assert time.perf_counter() - started < 2.0


def test_candidate_overflow_fails_closed(tmp_path: Path) -> None:
    config = replace(load_config(tmp_path), max_candidates_per_record=1)
    records = [
        record(f"external:x:{name}", scope="external", phash="0" * 16, dhash="0" * 16, sha256=name * 64)
        for name in ("A", "B", "C")
    ]
    with pytest.raises(CandidateOverflowError):
        dedup_module._generate_perceptual_candidates(records, config)


def test_duplicate_record_ids_are_rejected(tmp_path: Path) -> None:
    config_path, _, _ = write_fixture(tmp_path, internal_patterns=("gradient", "checker"), external_patterns=())
    frame = pd.read_csv(tmp_path / "outputs/metadata/image_metadata.csv")
    frame.loc[1, "image_id"] = frame.loc[0, "image_id"]
    frame.to_csv(tmp_path / "outputs/metadata/image_metadata.csv", index=False, encoding="utf-8-sig")
    with pytest.raises(ConfigInputError, match="duplicate.*image_id"):
        build_deduplication_audit(load_config(tmp_path, config_path), execute=True)


def test_missing_file_fails_without_formal_output(tmp_path: Path) -> None:
    config_path, internal, _ = write_fixture(tmp_path)
    internal[0].unlink()
    config = load_config(tmp_path, config_path)
    with pytest.raises(HashingIntegrityError, match="missing"):
        build_deduplication_audit(config, execute=True)
    assert not config.output_root.exists()
    failure_staging = list(config.output_root.parent.glob(f".{config.output_root.name}.staging-*"))
    assert len(failure_staging) == 1
    errors = pd.read_csv(failure_staging[0] / "deduplication_errors.csv")
    assert errors.loc[0, "error_code"] == "HashingIntegrityError"


def test_corrupt_image_fails_without_formal_output(tmp_path: Path) -> None:
    config_path, internal, _ = write_fixture(tmp_path)
    internal[0].write_bytes(b"not-an-image")
    config = load_config(tmp_path, config_path)
    with pytest.raises(HashingIntegrityError, match="unreadable"):
        build_deduplication_audit(config, execute=True)
    assert not config.output_root.exists()


def test_external_sha_mismatch_fails_without_formal_output(tmp_path: Path) -> None:
    config_path, _, _ = write_fixture(tmp_path)
    frame = pd.read_csv(tmp_path / "outputs/metadata/external_assets/inventory.csv")
    frame.loc[0, "sha256"] = "0" * 64
    frame.to_csv(tmp_path / "outputs/metadata/external_assets/inventory.csv", index=False, encoding="utf-8-sig")
    config = load_config(tmp_path, config_path)
    with pytest.raises(HashingIntegrityError, match="SHA256 mismatch"):
        build_deduplication_audit(config, execute=True)
    assert not config.output_root.exists()


def test_missing_external_sha_is_rejected(tmp_path: Path) -> None:
    config_path, _, _ = write_fixture(tmp_path)
    frame = pd.read_csv(tmp_path / "outputs/metadata/external_assets/inventory.csv")
    frame.loc[0, "sha256"] = ""
    frame.to_csv(tmp_path / "outputs/metadata/external_assets/inventory.csv", index=False, encoding="utf-8-sig")
    with pytest.raises(ConfigInputError, match="invalid external SHA256"):
        build_deduplication_audit(load_config(tmp_path, config_path), execute=True)


def test_dry_run_validates_inputs_and_writes_nothing(tmp_path: Path) -> None:
    config_path, _, _ = write_fixture(tmp_path)
    config = load_config(tmp_path, config_path)
    result = build_deduplication_audit(config, execute=False)
    assert result.executed is False
    assert not config.output_root.exists()


def test_dry_run_rejects_missing_external_image(tmp_path: Path) -> None:
    config_path, _, external = write_fixture(tmp_path)
    external[0].unlink()
    with pytest.raises(ConfigInputError, match="external image missing"):
        build_deduplication_audit(load_config(tmp_path, config_path), execute=False)


def test_execute_writes_all_outputs_atomically(tmp_path: Path) -> None:
    config_path, _, _ = write_fixture(tmp_path)
    result = build_deduplication_audit(load_config(tmp_path, config_path), execute=True)
    assert sorted(path.name for path in result.output_root.iterdir()) == [
        "deduplication_errors.csv",
        "deduplication_summary.csv",
        "deduplication_verification.json",
        "exact_duplicate_groups.csv",
        "exact_duplicate_members.csv",
        "image_hash_inventory.csv",
        "perceptual_duplicate_candidates.csv",
    ]


def test_existing_output_fails_without_overwrite(tmp_path: Path) -> None:
    config_path, _, _ = write_fixture(tmp_path)
    config = load_config(tmp_path, config_path)
    config.output_root.mkdir(parents=True)
    marker = config.output_root / "keep.txt"
    marker.write_text("keep", encoding="utf-8")
    with pytest.raises(OutputPromotionError, match="already exists"):
        build_deduplication_audit(config, execute=True)
    assert marker.read_text(encoding="utf-8") == "keep"


def test_overwrite_promotes_only_after_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path, _, _ = write_fixture(tmp_path)
    config = load_config(tmp_path, config_path)
    config.output_root.mkdir(parents=True)
    marker = config.output_root / "keep.txt"
    marker.write_text("keep", encoding="utf-8")
    monkeypatch.setattr(dedup_module, "_write_success_outputs", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("fixture failure")))
    with pytest.raises(OutputPromotionError, match="fixture failure"):
        build_deduplication_audit(config, execute=True, overwrite=True)
    assert marker.read_text(encoding="utf-8") == "keep"


def test_overwrite_backup_cleanup_failure_does_not_report_promotion_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path, _, _ = write_fixture(tmp_path)
    config = load_config(tmp_path, config_path)
    config.output_root.mkdir(parents=True)
    (config.output_root / "old.txt").write_text("old", encoding="utf-8")
    real_rmtree = dedup_module.shutil.rmtree

    def fail_backup_cleanup(path: Path, *args: Any, **kwargs: Any) -> None:
        if Path(path).name.startswith(f".{config.output_root.name}.backup-"):
            raise OSError("backup cleanup failure")
        real_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(dedup_module.shutil, "rmtree", fail_backup_cleanup)
    result = build_deduplication_audit(config, execute=True, overwrite=True)
    assert (result.output_root / "deduplication_verification.json").is_file()
    assert not (result.output_root / "old.txt").exists()


def test_failure_does_not_promote_partial_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path, _, _ = write_fixture(tmp_path)
    config = load_config(tmp_path, config_path)
    monkeypatch.setattr(dedup_module.os, "replace", lambda *args: (_ for _ in ()).throw(OSError("promotion failure")))
    with pytest.raises(OutputPromotionError, match="promotion failure"):
        build_deduplication_audit(config, execute=True)
    assert not config.output_root.exists()


def test_output_columns_and_sorting(tmp_path: Path) -> None:
    config_path, _, _ = write_fixture(tmp_path, internal_patterns=("checker", "gradient"), external_patterns=("diagonal",))
    result = build_deduplication_audit(load_config(tmp_path, config_path), execute=True)
    with (result.output_root / "image_hash_inventory.csv").open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        assert reader.fieldnames == dedup_module.IMAGE_HASH_INVENTORY_COLUMNS
    assert [row["record_id"] for row in rows] == sorted(row["record_id"] for row in rows)
    assert all(not Path(row["relative_image_path"]).is_absolute() for row in rows)
    expected_headers = {
        "exact_duplicate_groups.csv": dedup_module.EXACT_GROUP_COLUMNS,
        "exact_duplicate_members.csv": dedup_module.EXACT_MEMBER_COLUMNS,
        "perceptual_duplicate_candidates.csv": dedup_module.PERCEPTUAL_COLUMNS,
        "deduplication_summary.csv": dedup_module.SUMMARY_COLUMNS,
        "deduplication_errors.csv": dedup_module.ERROR_COLUMNS,
    }
    for filename, expected in expected_headers.items():
        with (result.output_root / filename).open(encoding="utf-8-sig", newline="") as handle:
            assert csv.DictReader(handle).fieldnames == expected


def test_verification_json_contains_hashes_and_safety_flags(tmp_path: Path) -> None:
    config_path, _, _ = write_fixture(tmp_path)
    result = build_deduplication_audit(load_config(tmp_path, config_path), execute=True)
    verification = json.loads((result.output_root / "deduplication_verification.json").read_text(encoding="utf-8"))
    assert verification["input_sha256"]["internal_metadata_path"]
    assert verification["output_sha256"]["image_hash_inventory.csv"]
    assert verification["repository_inputs_modified"] is False
    assert verification["protected_external_assets_modified"] is False
    assert verification["training_acceptance"] == "NOT_YET_APPROVED"


def test_exact_summary_respects_disabled_external_external_scope(tmp_path: Path) -> None:
    config = replace(load_config(tmp_path), external_external_exact=False)
    groups = [
        {
            "member_count": 3,
            "internal_count": 1,
            "external_count": 2,
            "cross_source": True,
        }
    ]
    summary = dedup_module._summary_row(config, [], groups, [])
    assert summary["external_external_exact_group_count"] == 0
    assert summary["external_external_exact_image_count"] == 0


@pytest.mark.parametrize(
    ("exception", "expected"),
    [
        (ConfigInputError("config"), 2),
        (HashingIntegrityError("hash"), 3),
        (CandidateOverflowError("overflow"), 4),
        (OutputPromotionError("output"), 5),
    ],
)
def test_cli_exit_codes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    exception: Exception,
    expected: int,
) -> None:
    cli = load_cli_module()
    config_path = write_config(tmp_path)
    monkeypatch.setattr(cli, "load_deduplication_config", lambda *args, **kwargs: object())
    monkeypatch.setattr(cli, "build_deduplication_audit", lambda *args, **kwargs: (_ for _ in ()).throw(exception))
    assert cli.main(["--project-root", str(tmp_path), "--config", str(config_path)]) == expected
    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert payload["exit_code"] == expected


def test_cli_dry_run_success_exit_code(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    config_path, _, _ = write_fixture(tmp_path)
    cli = load_cli_module()
    assert cli.main(["--project-root", str(tmp_path), "--config", str(config_path)]) == 0
    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert payload["exit_code"] == 0
    assert payload["executed"] is False


def test_protected_inputs_remain_byte_identical(tmp_path: Path) -> None:
    config_path, internal, external = write_fixture(tmp_path)
    protected = [
        tmp_path / "outputs/metadata/image_metadata.csv",
        tmp_path / "outputs/metadata/external_assets/inventory.csv",
        *internal,
        *external,
    ]
    before = {path: file_sha256(path) for path in protected}
    build_deduplication_audit(load_config(tmp_path, config_path), execute=True)
    assert {path: file_sha256(path) for path in protected} == before
