import csv
import json
import shutil
from pathlib import Path

import pytest

from annotation_correction_review_fixtures import build_fixture, write_manifest
from fleetvision.review.annotation_correction_review_package import (
    CorrectionPackageVerificationError,
    load_correction_review_config,
    load_verified_correction_review_package,
    prepare_correction_review_package,
    stable_bbox_id,
)


def test_prepare_package_extracts_exact_two_cases(tmp_path: Path) -> None:
    fixture = build_fixture(tmp_path)
    config = load_correction_review_config(fixture.config_path, fixture.project_root)
    package = prepare_correction_review_package(config, fixture.f2_root, timestamp="20260714T180000Z")
    assert tuple(case.review_case_id for case in package.cases) == ("l_687b939a3a89bb8e", "l_e5875a8f94620ff1")
    assert all(case.source_split == "valid" for case in package.cases)
    assert package.cases[1].image_id.startswith("test_set_")
    assert len(json.loads(package.cases[1].gt_bbox_records_json)) == 2
    reloaded = load_verified_correction_review_package(config, package.workspace_root)
    assert reloaded.source_csv_sha256 == package.source_csv_sha256


def test_package_rejects_non_valid_source_record(tmp_path: Path) -> None:
    fixture = build_fixture(tmp_path)
    path = fixture.extracted_root / "records/validation_ground_truth.csv"
    rows = list(csv.DictReader(path.open("r", encoding="utf-8-sig")))
    rows[0]["split"] = "test"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)
    config = load_correction_review_config(fixture.config_path, fixture.project_root)
    with pytest.raises(CorrectionPackageVerificationError, match="valid"):
        prepare_correction_review_package(config, fixture.f2_root, timestamp="20260714T180001Z")


def test_package_rejects_changed_f2_checksum(tmp_path: Path) -> None:
    fixture = build_fixture(tmp_path)
    path = fixture.f2_root / "final_findings/phase04_5l_findings_report.json"
    path.write_text("{}", encoding="utf-8")
    config = load_correction_review_config(fixture.config_path, fixture.project_root)
    with pytest.raises(CorrectionPackageVerificationError, match="SHA256"):
        prepare_correction_review_package(config, fixture.f2_root, timestamp="20260714T180002Z")


def test_package_is_no_overwrite(tmp_path: Path) -> None:
    fixture = build_fixture(tmp_path)
    config = load_correction_review_config(fixture.config_path, fixture.project_root)
    prepare_correction_review_package(config, fixture.f2_root, timestamp="20260714T180003Z")
    with pytest.raises(CorrectionPackageVerificationError, match="禁止覆寫"):
        prepare_correction_review_package(config, fixture.f2_root, timestamp="20260714T180003Z")


def test_bbox_ids_are_stable_and_ordered() -> None:
    assert stable_bbox_id("gt", 1) == "gt_001"
    assert stable_bbox_id("pred", 12) == "pred_012"

def test_package_loads_records_from_verified_04_5k_zip(tmp_path: Path) -> None:
    fixture = build_fixture(tmp_path)
    shutil.rmtree(fixture.extracted_root / "records")
    config = load_correction_review_config(fixture.config_path, fixture.project_root)
    package = prepare_correction_review_package(
        config,
        fixture.f2_root,
        timestamp="20260714T180004Z",
        source_04_5k_zip=fixture.source_zip,
    )
    assert len(package.cases) == 2
    contract = json.loads(package.source_contract_path.read_text(encoding="utf-8"))
    assert contract["source_record_origin"] == "VERIFIED_04_5K_SOURCE_ZIP"
    assert len(contract["source_04_5k_zip_sha256"]) == 64
