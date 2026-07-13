from __future__ import annotations

from pathlib import Path

import pytest

from fleetvision.review.validation_error_review_package import (
    PackageVerificationError,
    load_review_app_config,
    load_verified_source_package,
)
from review_app_fixtures import (
    create_review_package,
    refresh_package_integrity,
    set_workbook_value,
    write_app_config,
)


def _verified(tmp_path: Path):
    project_root, batch_root, frozen_zip = create_review_package(tmp_path)
    config_path = write_app_config(
        tmp_path,
        project_root,
        batch_root,
        frozen_zip,
    )
    config = load_review_app_config(config_path, project_root)
    return load_verified_source_package(config)


def test_verified_package_loads_pristine_source_cases(tmp_path: Path) -> None:
    package = _verified(tmp_path)

    assert package.batch_root.name == "batch_001"
    assert len(package.cases) == 2
    assert package.asset_manifest_count == 6
    assert package.checksum_entry_count == 7
    assert package.cases[0].case_index == 1
    assert package.cases[0].review_case_id == "review_000"
    assert package.cases[0].original_path.is_file()
    assert package.cases[0].overlay_path.is_file()


def test_workbook_hash_mismatch_blocks_startup(tmp_path: Path) -> None:
    project_root, batch_root, frozen_zip = create_review_package(tmp_path)
    config_path = write_app_config(
        tmp_path,
        project_root,
        batch_root,
        frozen_zip,
        workbook_sha256="0" * 64,
    )
    config = load_review_app_config(config_path, project_root)

    with pytest.raises(PackageVerificationError, match="Workbook SHA256"):
        load_verified_source_package(config)


def test_asset_manifest_detects_mutated_asset(tmp_path: Path) -> None:
    project_root, batch_root, frozen_zip = create_review_package(tmp_path)
    config_path = write_app_config(
        tmp_path,
        project_root,
        batch_root,
        frozen_zip,
    )
    original = batch_root / "assets/original/valid_000.jpg"
    original.write_bytes(original.read_bytes() + b"tamper")
    config = load_review_app_config(config_path, project_root)

    with pytest.raises(
        PackageVerificationError,
        match="asset manifest (size|SHA256) mismatch",
    ):
        load_verified_source_package(config)


def test_source_fingerprint_mutation_is_blocked(tmp_path: Path) -> None:
    project_root, batch_root, frozen_zip = create_review_package(tmp_path)
    workbook = batch_root / "workbook/validation_error_human_review.xlsx"
    set_workbook_value(
        workbook,
        "review_000",
        "auto_error_category",
        "tampered",
    )
    refresh_package_integrity(batch_root, frozen_zip)
    config_path = write_app_config(
        tmp_path,
        project_root,
        batch_root,
        frozen_zip,
    )
    config = load_review_app_config(config_path, project_root)

    with pytest.raises(PackageVerificationError, match="source fingerprint"):
        load_verified_source_package(config)


def test_non_pending_source_workbook_is_blocked(tmp_path: Path) -> None:
    project_root, batch_root, frozen_zip = create_review_package(tmp_path)
    workbook = batch_root / "workbook/validation_error_human_review.xlsx"
    set_workbook_value(
        workbook,
        "review_000",
        "review_status",
        "reviewed",
    )
    refresh_package_integrity(batch_root, frozen_zip)
    config_path = write_app_config(
        tmp_path,
        project_root,
        batch_root,
        frozen_zip,
    )
    config = load_review_app_config(config_path, project_root)

    with pytest.raises(PackageVerificationError, match="only pending"):
        load_verified_source_package(config)


def test_exact_test_path_segment_is_forbidden(tmp_path: Path) -> None:
    project_root, batch_root, frozen_zip = create_review_package(
        tmp_path,
        parent_name="test",
    )
    config_path = write_app_config(
        tmp_path,
        project_root,
        batch_root,
        frozen_zip,
    )

    with pytest.raises(PackageVerificationError, match="test split"):
        load_review_app_config(config_path, project_root)


def test_workspace_inside_repository_is_forbidden(tmp_path: Path) -> None:
    project_root, batch_root, frozen_zip = create_review_package(tmp_path)
    config_path = write_app_config(
        tmp_path,
        project_root,
        batch_root,
        frozen_zip,
        workspace_root=project_root / "local_review_workspace",
    )

    with pytest.raises(
        PackageVerificationError,
        match="outside the repository",
    ):
        load_review_app_config(config_path, project_root)
