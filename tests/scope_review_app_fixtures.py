from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import yaml
from openpyxl import Workbook
from PIL import Image

from fleetvision.data.validation_error_review_findings import (
    SCOPE_COLUMNS,
    SCOPE_EXPORT_COLUMNS,
    SCOPE_WORKBOOK_SHEETS,
)
from fleetvision.review.severity_scope_review_package import (
    ScopeReviewAppConfig,
    ScopeSourceCase,
    VerifiedScopePackage,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def write_png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (32, 24), "white").save(path)


def make_source_row(index: int) -> dict[str, str]:
    row = {column: f"value-{index}-{column}" for column in SCOPE_EXPORT_COLUMNS}
    row.update(
        {
            "schema_version": "1",
            "review_batch_id": "batch",
            "review_case_id": f"case-{index:03d}",
            "source_case_fingerprint": f"fingerprint-{index:03d}",
            "image_id": f"image-{index:03d}",
            "auto_error_category": "false_negative",
            "auto_error_detail_ids": "fn-1",
            "error_disposition": "confirmed_model_error",
            "primary_root_cause": "small_damage",
            "recommended_action": "add_positive_sample",
            "retraining_priority": "medium",
            "original_image_relpath": f"assets/original/case-{index:03d}.png",
            "overlay_image_relpath": f"assets/overlay/case-{index:03d}.png",
            "scope_review_status": "pending",
        }
    )
    for column in SCOPE_COLUMNS[1:]:
        row[column] = ""
    return row


def write_template_workbook(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    workbook.remove(workbook.active)
    for sheet_name in SCOPE_WORKBOOK_SHEETS:
        workbook.create_sheet(sheet_name)
    review = workbook["Scope_Review"]
    headers = ["Original Preview", "Overlay Preview", *SCOPE_EXPORT_COLUMNS]
    review.append(headers)
    for row in rows:
        review.append(["", "", *[row[column] for column in SCOPE_EXPORT_COLUMNS]])
    workbook.save(path)


def create_scope_package(tmp_path: Path, *, case_count: int = 3):
    project_root = tmp_path / "repo"
    project_root.mkdir()
    findings_config = project_root / "configs/data/findings.yaml"
    findings_config.parent.mkdir(parents=True)
    findings_config.write_text("schema_version: '1'\n", encoding="utf-8")
    analysis_root = tmp_path / "analysis"
    root = analysis_root / "phase04_5l_completed_review_findings_20260714T000000Z"
    (root / "scope_review").mkdir(parents=True)
    extracted_root = root / "input_snapshot/extracted_package/package"

    rows = [make_source_row(index) for index in range(1, case_count + 1)]
    source_csv = root / "scope_review/severity_scope_review_source.csv"
    pd.DataFrame(rows, columns=SCOPE_EXPORT_COLUMNS).to_csv(
        source_csv,
        index=False,
        encoding="utf-8-sig",
        lineterminator="\n",
    )
    template = root / "scope_review/severity_scope_review.xlsx"
    write_template_workbook(template, rows)

    asset_manifest = root / "scope_review/scope_asset_manifest.csv"
    asset_rows = []
    for row in rows:
        for asset_type, column in (
            ("original", "original_image_relpath"),
            ("overlay", "overlay_image_relpath"),
        ):
            asset = extracted_root / row[column]
            write_png(asset)
            asset_rows.append(
                {
                    "review_case_id": row["review_case_id"],
                    "asset_type": asset_type,
                    "relative_path": row[column],
                    "size_bytes": str(asset.stat().st_size),
                    "sha256": sha256(asset),
                }
            )
    with asset_manifest.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "review_case_id",
                "asset_type",
                "relative_path",
                "size_bytes",
                "sha256",
            ],
        )
        writer.writeheader()
        writer.writerows(asset_rows)

    gate = {
        "outcome": "PASS",
        "classification": "PHASE_04_5L_COMPLETED_REVIEW_VALIDATED_AND_SCOPE_REVIEW_PACKAGE_CREATED",
        "review_cases": case_count,
        "scope_source_csv_sha256": sha256(source_csv),
        "scope_workbook_sha256": sha256(template),
        "scope_asset_manifest_sha256": sha256(asset_manifest),
        "test_split_read": False,
        "model_inference_executed": False,
        "annotation_modified": False,
        "training_started": False,
    }
    gate_path = root / "evidence/f1_gate_result.json"
    gate_path.parent.mkdir(parents=True)
    gate_path.write_text(json.dumps(gate), encoding="utf-8")

    manifest_path = root / "evidence/F1_SHA256SUMS.csv"
    files = [source_csv, template, asset_manifest, gate_path]
    with manifest_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["relative_path", "size_bytes", "sha256"],
        )
        writer.writeheader()
        for file in files:
            writer.writerow(
                {
                    "relative_path": file.relative_to(root).as_posix(),
                    "size_bytes": str(file.stat().st_size),
                    "sha256": sha256(file),
                }
            )

    config_path = project_root / "configs/data/severity_scope_review_app_config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "1",
                "source": {
                    "findings_config_path": str(findings_config),
                    "analysis_root": str(analysis_root),
                    "expected_case_count": case_count,
                },
                "workspace": {
                    "reviewer": "Vincent",
                    "timezone": "Asia/Taipei",
                    "backup_every_successful_saves": 2,
                    "backup_retention": 3,
                    "app_directory_name": "scope_review_app",
                    "completed_workbook_name": "severity_scope_review_completed.xlsx",
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    # The production config requires exactly 130. Tests construct the verified
    # object directly when a smaller fixture is preferable.
    config = ScopeReviewAppConfig(
        schema_version="1",
        project_root=project_root,
        findings_config_path=findings_config,
        analysis_root=analysis_root,
        expected_case_count=case_count,
        reviewer="Vincent",
        timezone="Asia/Taipei",
        backup_every_successful_saves=2,
        backup_retention=3,
        app_directory_name="scope_review_app",
        completed_workbook_name="severity_scope_review_completed.xlsx",
    )
    cases = []
    for index, row in enumerate(rows, start=1):
        cases.append(
            ScopeSourceCase(
                case_index=index,
                review_case_id=row["review_case_id"],
                image_id=row["image_id"],
                source_case_fingerprint=row["source_case_fingerprint"],
                auto_error_category=row["auto_error_category"],
                auto_error_detail_ids=row["auto_error_detail_ids"],
                error_disposition=row["error_disposition"],
                primary_root_cause=row["primary_root_cause"],
                recommended_action=row["recommended_action"],
                retraining_priority=row["retraining_priority"],
                original_relpath=row["original_image_relpath"],
                overlay_relpath=row["overlay_image_relpath"],
                original_path=extracted_root / row["original_image_relpath"],
                overlay_path=extracted_root / row["overlay_image_relpath"],
                source_row=row,
            )
        )
    package = VerifiedScopePackage(
        config=config,
        f1_workspace_root=root,
        source_csv_path=source_csv,
        template_workbook_path=template,
        asset_manifest_path=asset_manifest,
        f1_manifest_path=manifest_path,
        source_csv_sha256=sha256(source_csv),
        template_workbook_sha256=sha256(template),
        asset_manifest_sha256=sha256(asset_manifest),
        asset_root=extracted_root,
        cases=tuple(cases),
    )
    return SimpleNamespace(
        project_root=project_root,
        analysis_root=analysis_root,
        root=root,
        package=package,
        rows=rows,
        config_path=config_path,
    )
