from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def write_manifest(root: Path, paths: list[Path]) -> None:
    target = root / "evidence/SHA256SUMS.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["relative_path", "size_bytes", "sha256"])
        writer.writeheader()
        for path in paths:
            writer.writerow({"relative_path": path.relative_to(root).as_posix(), "size_bytes": path.stat().st_size, "sha256": sha256(path)})


@dataclass(frozen=True)
class CorrectionFixture:
    project_root: Path
    f2_root: Path
    config_path: Path
    workspace_base: Path
    extracted_root: Path
    source_zip: Path


def build_fixture(tmp_path: Path) -> CorrectionFixture:
    project_root = tmp_path / "repo"
    f2_root = tmp_path / "f2"
    workspace_base = tmp_path / "workspaces"
    extracted = f2_root / "input_snapshot/extracted_package"
    project_root.mkdir()
    extracted.mkdir(parents=True)

    image_dir = extracted / "assets/original"
    image_dir.mkdir(parents=True)
    images = [
        "147_jpg.rf.83b3e9e399d2f3546d5676a902148f0c.jpg",
        "test_set_188_jpg.rf.ed3c01d255f1c18dd0c5dd2667c7a096.jpg",
    ]
    for index, name in enumerate(images):
        Image.new("RGB", (640, 480), (80 + index * 20, 100, 120)).save(image_dir / name, quality=95)

    records = extracted / "records"
    records.mkdir()
    with (records / "validation_ground_truth.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["split", "image_id", "x1", "y1", "x2", "y2"])
        writer.writeheader()
        writer.writerow({"split": "valid", "image_id": images[0], "x1": 20, "y1": 30, "x2": 200, "y2": 180})
        writer.writerow({"split": "valid", "image_id": images[1], "x1": 40, "y1": 50, "x2": 240, "y2": 220})
        writer.writerow({"split": "valid", "image_id": images[1], "x1": 42, "y1": 52, "x2": 238, "y2": 218})
    with (records / "validation_predictions.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["split", "image_id", "confidence", "x1", "y1", "x2", "y2"])
        writer.writeheader()
        writer.writerow({"split": "valid", "image_id": images[0], "confidence": 0.8, "x1": 18, "y1": 28, "x2": 220, "y2": 190})
        writer.writerow({"split": "valid", "image_id": images[1], "confidence": 0.7, "x1": 39, "y1": 49, "x2": 241, "y2": 221})

    source_zip = tmp_path / "04_5K_fixture_ZIP_LOG.zip"
    with zipfile.ZipFile(source_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(
            records / "validation_ground_truth.csv",
            "records/validation_ground_truth.csv",
        )
        archive.write(
            records / "validation_predictions.csv",
            "records/validation_predictions.csv",
        )

    review_config = project_root / "configs/data/validation_error_human_review_config.yaml"
    review_config.parent.mkdir(parents=True)
    review_config.write_text(
        f"""expected_source:
  zip_filename: {source_zip.name}
  zip_sha256: {sha256(source_zip)}
source_files:
  ground_truth: records/validation_ground_truth.csv
  predictions: records/validation_predictions.csv
""",
        encoding="utf-8",
    )

    scope_dir = f2_root / "scope_review"
    scope_dir.mkdir(parents=True)
    with (scope_dir / "severity_scope_review_source.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["review_case_id", "image_id", "original_image_relpath"])
        writer.writeheader()
        for review_id, image_id in zip(("l_687b939a3a89bb8e", "l_e5875a8f94620ff1"), images):
            writer.writerow({"review_case_id": review_id, "image_id": image_id, "original_image_relpath": f"assets/original/{image_id}"})

    gate_path = f2_root / "evidence/gate_result.json"
    gate_path.parent.mkdir(parents=True)
    gate_path.write_text(json.dumps({
        "outcome": "PASS",
        "classification": "PHASE_04_5L_COMPLETED_REVIEW_VALIDATION_AND_FINDINGS_ANALYSIS_COMPLETED",
        "review_cases": 130,
        "scope_reviewed": 130,
        "pending": 0,
        "needs_adjudication": 0,
        "primary_recommendation": "DATA_CORRECTION_REQUIRED_BEFORE_RETRAINING",
        "test_split_read": False,
        "model_inference_executed": False,
        "annotation_modified": False,
        "training_started": False,
    }), encoding="utf-8")
    findings = f2_root / "final_findings/phase04_5l_findings_report.json"
    findings.parent.mkdir(parents=True)
    findings.write_text(json.dumps({"annotation_correction_proposal_cases": [
        {"review_case_id": "l_687b939a3a89bb8e", "image_id": images[0], "annotation_defect_type": "wrong_damage_scope", "review_notes": "模型框的是對的"},
        {"review_case_id": "l_e5875a8f94620ff1", "image_id": images[1], "annotation_defect_type": "extra_bbox", "review_notes": "重複標註"},
    ]}, ensure_ascii=False), encoding="utf-8")
    recommendation = f2_root / "final_findings/retraining_recommendation.json"
    recommendation.write_text(json.dumps({"primary_recommendation": "DATA_CORRECTION_REQUIRED_BEFORE_RETRAINING"}), encoding="utf-8")
    workbook = f2_root / "scope_review_app/exports/severity_scope_review_completed.xlsx"
    workbook.parent.mkdir(parents=True)
    workbook.write_bytes(b"fixture-workbook")
    write_manifest(f2_root, [gate_path, findings, recommendation])

    config_path = project_root / "config.yaml"
    config_path.write_text(f'''schema_version: "1"
source:
  expected_f2_classification: PHASE_04_5L_COMPLETED_REVIEW_VALIDATION_AND_FINDINGS_ANALYSIS_COMPLETED
  expected_primary_recommendation: DATA_CORRECTION_REQUIRED_BEFORE_RETRAINING
  expected_case_count: 2
  completed_scope_workbook_sha256: {sha256(workbook)}
  expected_cases:
    - review_case_id: l_687b939a3a89bb8e
      image_id: {images[0]}
      annotation_defect_type: wrong_damage_scope
      review_notes: 模型框的是對的
    - review_case_id: l_e5875a8f94620ff1
      image_id: {images[1]}
      annotation_defect_type: extra_bbox
      review_notes: 重複標註
workspace:
  base_root: {workspace_base.as_posix()}
  directory_prefix: phase04_5m_annotation_correction_review
  reviewer: Vincent
  timezone: Asia/Taipei
  backup_every_successful_saves: 1
  backup_retention: 20
exports:
  reviewed_csv: annotation_correction_proposals_reviewed.csv
  reviewed_json: annotation_correction_proposals_reviewed.json
  completed_workbook: annotation_correction_proposals_completed.xlsx
  result_json: correction_review_export_result.json
''', encoding="utf-8")
    return CorrectionFixture(project_root, f2_root, config_path, workspace_base, extracted, source_zip)
