from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

import pandas as pd
import yaml
from PIL import Image, ImageDraw

from fleetvision.review.annotation_correction_review_records import (
    ValidationRecordSourceError,
    load_verified_validation_records,
)


class CorrectionPackageVerificationError(RuntimeError):
    """Raised when Phase 04.5M source evidence cannot be trusted."""


EXPECTED_PACKAGE_CLASSIFICATION = "PHASE_04_5M_ANNOTATION_CORRECTION_REVIEW_PACKAGE_PREPARED"
GT_COLOR = (220, 20, 60)
PRED_COLOR = (30, 144, 255)
TEXT_COLOR = (255, 255, 255)


@dataclass(frozen=True)
class ExpectedCorrectionCase:
    review_case_id: str
    image_id: str
    annotation_defect_type: str
    review_notes: str


@dataclass(frozen=True)
class CorrectionReviewAppConfig:
    schema_version: str
    project_root: Path
    workspace_base_root: Path
    workspace_directory_prefix: str
    expected_f2_classification: str
    expected_primary_recommendation: str
    expected_case_count: int
    completed_scope_workbook_sha256: str
    expected_cases: tuple[ExpectedCorrectionCase, ...]
    reviewer: str
    timezone: str
    backup_every_successful_saves: int
    backup_retention: int
    reviewed_csv_name: str
    reviewed_json_name: str
    completed_workbook_name: str
    result_json_name: str


@dataclass(frozen=True)
class VerifiedF2Evidence:
    f2_root: Path
    gate_result_path: Path
    findings_report_path: Path
    recommendation_path: Path
    checksum_manifest_path: Path
    gate_result_sha256: str
    findings_report_sha256: str
    recommendation_sha256: str
    completed_scope_workbook_sha256: str


@dataclass(frozen=True)
class CorrectionSourceCase:
    case_index: int
    correction_case_id: str
    review_case_id: str
    image_id: str
    image_width: int
    image_height: int
    source_split: str
    source_case_fingerprint: str
    original_annotation_defect_type: str
    original_review_notes: str
    original_relpath: str
    gt_overlay_relpath: str
    prediction_overlay_relpath: str
    combined_overlay_relpath: str
    gt_bbox_records_json: str
    prediction_bbox_records_json: str
    original_path: Path
    gt_overlay_path: Path
    prediction_overlay_path: Path
    combined_overlay_path: Path


@dataclass(frozen=True)
class VerifiedCorrectionReviewPackage:
    config: CorrectionReviewAppConfig
    workspace_root: Path
    source_csv_path: Path
    source_manifest_path: Path
    source_contract_path: Path
    package_gate_path: Path
    checksum_manifest_path: Path
    source_csv_sha256: str
    source_manifest_sha256: str
    source_contract_sha256: str
    package_gate_sha256: str
    cases: tuple[CorrectionSourceCase, ...]

    @property
    def app_workspace_root(self) -> Path:
        return self.workspace_root / "app"

    @property
    def export_root(self) -> Path:
        return self.workspace_root / "exports"

    @property
    def case_by_review_id(self) -> Mapping[str, CorrectionSourceCase]:
        return {case.review_case_id: case for case in self.cases}

    @property
    def case_by_id(self) -> Mapping[str, CorrectionSourceCase]:
        return {case.correction_case_id: case for case in self.cases}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _resolve_path(project_root: Path, value: object) -> Path:
    path = Path(str(value))
    return (path if path.is_absolute() else project_root / path).resolve()


def _require_sha256(value: object, label: str) -> str:
    digest = str(value or "").strip().upper()
    if len(digest) != 64 or any(char not in "0123456789ABCDEF" for char in digest):
        raise CorrectionPackageVerificationError(f"{label} 不是有效 SHA256")
    return digest


def _require_safe_relative(value: str, label: str) -> PurePosixPath:
    pure = PurePosixPath(str(value).replace("\\", "/").strip())
    if pure.is_absolute() or not pure.parts or ".." in pure.parts:
        raise CorrectionPackageVerificationError(f"{label} 必須是安全相對路徑：{value}")
    return pure


def load_correction_review_config(config_path: Path, project_root: Path) -> CorrectionReviewAppConfig:
    project_root = project_root.resolve()
    path = _resolve_path(project_root, config_path)
    if not path.is_file():
        raise CorrectionPackageVerificationError(f"04.5M config 不存在：{path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    try:
        source = raw["source"]
        workspace = raw["workspace"]
        exports = raw["exports"]
        expected_cases = tuple(
            ExpectedCorrectionCase(
                review_case_id=str(row["review_case_id"]).strip(),
                image_id=str(row["image_id"]).strip(),
                annotation_defect_type=str(row["annotation_defect_type"]).strip(),
                review_notes=str(row["review_notes"]).strip(),
            )
            for row in source["expected_cases"]
        )
        config = CorrectionReviewAppConfig(
            schema_version=str(raw["schema_version"]).strip(),
            project_root=project_root,
            workspace_base_root=_resolve_path(project_root, workspace["base_root"]),
            workspace_directory_prefix=str(workspace["directory_prefix"]).strip(),
            expected_f2_classification=str(source["expected_f2_classification"]).strip(),
            expected_primary_recommendation=str(source["expected_primary_recommendation"]).strip(),
            expected_case_count=int(source["expected_case_count"]),
            completed_scope_workbook_sha256=_require_sha256(source["completed_scope_workbook_sha256"], "completed scope workbook"),
            expected_cases=expected_cases,
            reviewer=str(workspace["reviewer"]).strip(),
            timezone=str(workspace["timezone"]).strip(),
            backup_every_successful_saves=int(workspace["backup_every_successful_saves"]),
            backup_retention=int(workspace["backup_retention"]),
            reviewed_csv_name=str(exports["reviewed_csv"]).strip(),
            reviewed_json_name=str(exports["reviewed_json"]).strip(),
            completed_workbook_name=str(exports["completed_workbook"]).strip(),
            result_json_name=str(exports["result_json"]).strip(),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise CorrectionPackageVerificationError(f"04.5M config 結構無效：{exc}") from exc
    if config.schema_version != "1" or config.expected_case_count != 2:
        raise CorrectionPackageVerificationError("04.5M schema_version/expected_case_count 不符")
    if len(config.expected_cases) != 2 or len({case.review_case_id for case in config.expected_cases}) != 2:
        raise CorrectionPackageVerificationError("expected_cases 必須恰好為兩筆且 identity 唯一")
    if config.backup_every_successful_saves != 1 or config.backup_retention != 20:
        raise CorrectionPackageVerificationError("04.5M backup policy 必須固定為 every-save / retention 20")
    if config.workspace_base_root == project_root or project_root in config.workspace_base_root.parents:
        raise CorrectionPackageVerificationError("04.5M workspace 必須位於 repository 外")
    return config


def _read_checksum_manifest(path: Path, root: Path) -> dict[str, tuple[int, str]]:
    if not path.is_file():
        raise CorrectionPackageVerificationError(f"checksum manifest 不存在：{path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["relative_path", "size_bytes", "sha256"]:
            raise CorrectionPackageVerificationError("checksum manifest schema 不符")
        entries: dict[str, tuple[int, str]] = {}
        for row in reader:
            rel = _require_safe_relative(row["relative_path"], "manifest path").as_posix()
            if rel in entries:
                raise CorrectionPackageVerificationError(f"checksum manifest 重複路徑：{rel}")
            try:
                size = int(row["size_bytes"])
            except ValueError as exc:
                raise CorrectionPackageVerificationError(f"manifest size 無效：{rel}") from exc
            entries[rel] = (size, _require_sha256(row["sha256"], rel))
    for rel, (size, digest) in entries.items():
        file_path = root / Path(*PurePosixPath(rel).parts)
        if not file_path.is_file() or file_path.stat().st_size != size or sha256_file(file_path) != digest:
            raise CorrectionPackageVerificationError(f"F2 SHA256/size mismatch：{rel}")
    return entries


def verify_f2_predecessor(config: CorrectionReviewAppConfig, f2_root: Path) -> VerifiedF2Evidence:
    root = f2_root.resolve()
    if root == config.project_root or config.project_root in root.parents:
        raise CorrectionPackageVerificationError("F2 workspace 不得位於 repository 內")
    gate_path = root / "evidence/gate_result.json"
    findings_path = root / "final_findings/phase04_5l_findings_report.json"
    recommendation_path = root / "final_findings/retraining_recommendation.json"
    checksum_path = root / "evidence/SHA256SUMS.csv"
    completed_workbook = root / "scope_review_app/exports/severity_scope_review_completed.xlsx"
    for path in (gate_path, findings_path, recommendation_path, checksum_path, completed_workbook):
        if not path.is_file():
            raise CorrectionPackageVerificationError(f"F2 必要檔案不存在：{path}")
    manifest_entries = _read_checksum_manifest(checksum_path, root)
    required_manifest_paths = {
        "evidence/gate_result.json",
        "final_findings/phase04_5l_findings_report.json",
        "final_findings/retraining_recommendation.json",
    }
    missing_manifest_paths = sorted(required_manifest_paths - set(manifest_entries))
    if missing_manifest_paths:
        raise CorrectionPackageVerificationError(
            f"F2 checksum manifest 缺必要路徑：{missing_manifest_paths}"
        )
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    if gate.get("outcome") != "PASS" or gate.get("classification") != config.expected_f2_classification:
        raise CorrectionPackageVerificationError("F2 classification 不符")
    if int(gate.get("review_cases", -1)) != 130 or int(gate.get("scope_reviewed", -1)) != 130:
        raise CorrectionPackageVerificationError("F2 review counts 不符")
    if int(gate.get("pending", -1)) != 0 or int(gate.get("needs_adjudication", -1)) != 0:
        raise CorrectionPackageVerificationError("F2 review 尚未完整")
    if gate.get("primary_recommendation") != config.expected_primary_recommendation:
        raise CorrectionPackageVerificationError("F2 primary recommendation 不符")
    for key in ("test_split_read", "model_inference_executed", "annotation_modified", "training_started"):
        if gate.get(key) is not False:
            raise CorrectionPackageVerificationError(f"F2 safety flag 不符：{key}")
    if sha256_file(completed_workbook) != config.completed_scope_workbook_sha256:
        raise CorrectionPackageVerificationError("completed scope Workbook SHA256 不符")
    recommendation = json.loads(recommendation_path.read_text(encoding="utf-8"))
    if recommendation.get("primary_recommendation") != config.expected_primary_recommendation:
        raise CorrectionPackageVerificationError("retraining recommendation 不符")
    report = json.loads(findings_path.read_text(encoding="utf-8"))
    rows = report.get("annotation_correction_proposal_cases")
    if not isinstance(rows, list) or len(rows) != 2:
        raise CorrectionPackageVerificationError("correction proposal case count 必須為 2")
    actual = {
        str(row.get("review_case_id", "")): (
            str(row.get("image_id", "")),
            str(row.get("annotation_defect_type", "")),
            str(row.get("review_notes", "")),
        )
        for row in rows
    }
    expected = {
        case.review_case_id: (case.image_id, case.annotation_defect_type, case.review_notes)
        for case in config.expected_cases
    }
    if actual != expected:
        raise CorrectionPackageVerificationError("correction proposal identity 不符")
    return VerifiedF2Evidence(
        f2_root=root,
        gate_result_path=gate_path,
        findings_report_path=findings_path,
        recommendation_path=recommendation_path,
        checksum_manifest_path=checksum_path,
        gate_result_sha256=sha256_file(gate_path),
        findings_report_sha256=sha256_file(findings_path),
        recommendation_sha256=sha256_file(recommendation_path),
        completed_scope_workbook_sha256=sha256_file(completed_workbook),
    )


def stable_bbox_id(prefix: str, row_index: int) -> str:
    value = str(prefix).strip().lower()
    if value not in {"gt", "pred"} or row_index <= 0:
        raise CorrectionPackageVerificationError("bbox ID 參數無效")
    return f"{value}_{row_index:03d}"


def _find_unique(root: Path, name: str) -> Path:
    matches = [path for path in root.rglob(name) if path.is_file()]
    if len(matches) != 1:
        raise CorrectionPackageVerificationError(f"無法唯一定位 {name}；matched={len(matches)}")
    return matches[0]


def _find_asset_root(extracted_root: Path, relative_path: str) -> Path:
    pure = _require_safe_relative(relative_path, "original asset")
    roots: set[Path] = set()
    for match in extracted_root.rglob(pure.name):
        if not match.is_file():
            continue
        candidate = match
        for _ in pure.parts:
            candidate = candidate.parent
        if (candidate / Path(*pure.parts)).is_file():
            roots.add(candidate.resolve())
    if len(roots) != 1:
        raise CorrectionPackageVerificationError(f"無法唯一定位 asset root；matched={len(roots)}")
    return next(iter(roots))


def _bbox_records(
    frame: pd.DataFrame,
    image_id: str,
    prefix: str,
    width: int,
    height: int,
    *,
    minimum_confidence: float | None = None,
) -> list[dict[str, Any]]:
    subset = frame[frame["image_id"].astype(str) == image_id].copy()
    if prefix == "pred" and minimum_confidence is not None and not subset.empty:
        confidence = pd.to_numeric(subset["confidence"], errors="coerce")
        subset = subset[confidence >= minimum_confidence].copy()
    if subset.empty:
        raise CorrectionPackageVerificationError(f"找不到 {prefix} records：{image_id}")
    split_values = set(subset["split"].astype(str).str.strip())
    if split_values != {"valid"}:
        raise CorrectionPackageVerificationError(f"{prefix} source split 必須只有 valid：{sorted(split_values)}")
    records: list[dict[str, Any]] = []
    for index, row in enumerate(subset.to_dict(orient="records"), start=1):
        try:
            x1, y1, x2, y2 = (float(row[key]) for key in ("x1", "y1", "x2", "y2"))
        except (KeyError, TypeError, ValueError) as exc:
            raise CorrectionPackageVerificationError(f"{prefix} bbox 座標無效：{image_id}") from exc
        if not all(math.isfinite(value) for value in (x1, y1, x2, y2)) or not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
            raise CorrectionPackageVerificationError(f"{prefix} bbox 超出範圍：{image_id}")
        record: dict[str, Any] = {"bbox_id": stable_bbox_id(prefix, index), "x1": x1, "y1": y1, "x2": x2, "y2": y2}
        if prefix == "pred":
            try:
                record["confidence"] = float(row["confidence"])
            except (KeyError, TypeError, ValueError) as exc:
                raise CorrectionPackageVerificationError(f"prediction confidence 無效：{image_id}") from exc
        records.append(record)
    return records


def _draw_overlay(source: Path, target: Path, gt: list[dict[str, Any]], pred: list[dict[str, Any]], mode: str) -> None:
    with Image.open(source) as image:
        canvas = image.convert("RGB")
    draw = ImageDraw.Draw(canvas)
    if mode in {"gt", "combined"}:
        for row in gt:
            draw.rectangle((row["x1"], row["y1"], row["x2"], row["y2"]), outline=GT_COLOR, width=4)
            draw.text((row["x1"] + 3, row["y1"] + 3), row["bbox_id"], fill=TEXT_COLOR, stroke_width=2, stroke_fill=GT_COLOR)
    if mode in {"pred", "combined"}:
        for row in pred:
            label = f"{row['bbox_id']} {row['confidence']:.3f}"
            draw.rectangle((row["x1"], row["y1"], row["x2"], row["y2"]), outline=PRED_COLOR, width=3)
            draw.text((row["x1"] + 3, max(0, row["y1"] + 18)), label, fill=TEXT_COLOR, stroke_width=2, stroke_fill=PRED_COLOR)
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, format="JPEG", quality=95, subsampling=0, optimize=False)


def _source_fingerprint(row: Mapping[str, Any]) -> str:
    keys = (
        "schema_version", "correction_review_batch_id",
        "source_f2_gate_sha256", "source_findings_report_sha256",
        "review_case_id", "image_id", "image_width", "image_height", "source_split",
        "original_image_relpath", "gt_overlay_relpath",
        "prediction_overlay_relpath", "combined_overlay_relpath",
        "original_annotation_defect_type", "original_review_notes",
        "gt_bbox_records_json", "prediction_bbox_records_json",
    )
    payload = "\x1f".join(str(row[key]) for key in keys)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def _write_csv(path: Path, rows: list[Mapping[str, Any]], columns: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in columns})


SOURCE_COLUMNS = (
    "schema_version", "correction_review_batch_id", "correction_case_id", "source_f2_gate_sha256",
    "source_findings_report_sha256", "source_case_fingerprint", "review_case_id", "image_id",
    "image_width", "image_height", "source_split", "original_image_relpath", "gt_overlay_relpath",
    "prediction_overlay_relpath", "combined_overlay_relpath", "original_annotation_defect_type",
    "original_review_notes", "gt_bbox_records_json", "prediction_bbox_records_json",
)


def prepare_correction_review_package(
    config: CorrectionReviewAppConfig,
    f2_root: Path,
    *,
    timestamp: str | None = None,
    source_04_5k_zip: Path | None = None,
) -> VerifiedCorrectionReviewPackage:
    evidence = verify_f2_predecessor(config, f2_root)
    token = timestamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    batch_id = f"{config.workspace_directory_prefix}_{token}"
    final_root = config.workspace_base_root / batch_id
    if final_root.exists():
        raise CorrectionPackageVerificationError(f"04.5M workspace 已存在，禁止覆寫：{final_root}")
    config.workspace_base_root.mkdir(parents=True, exist_ok=True)
    staging = config.workspace_base_root / f".{batch_id}.staging-{uuid.uuid4().hex[:8]}"
    if staging.exists():
        raise CorrectionPackageVerificationError("unexpected staging collision")

    source_csv = evidence.f2_root / "scope_review/severity_scope_review_source.csv"
    extracted_root = evidence.f2_root / "input_snapshot/extracted_package"
    if not source_csv.is_file() or not extracted_root.is_dir():
        raise CorrectionPackageVerificationError("F1 source snapshot 不完整")
    source_frame = pd.read_csv(source_csv, dtype=str, keep_default_na=False, encoding="utf-8-sig").fillna("").astype(str)
    try:
        validation_records = load_verified_validation_records(
            extracted_root=extracted_root,
            project_root=config.project_root,
            source_04_5k_zip=source_04_5k_zip,
        )
    except ValidationRecordSourceError as exc:
        raise CorrectionPackageVerificationError(str(exc)) from exc
    gt_frame = validation_records.ground_truth
    pred_frame = validation_records.predictions
    for required, frame, label in (({"split", "image_id", "x1", "y1", "x2", "y2"}, gt_frame, "GT"), ({"split", "image_id", "confidence", "x1", "y1", "x2", "y2"}, pred_frame, "prediction")):
        missing = sorted(required - set(frame.columns))
        if missing:
            raise CorrectionPackageVerificationError(f"{label} records 缺欄位：{missing}")

    try:
        source_rows: list[dict[str, Any]] = []
        cases: list[CorrectionSourceCase] = []
        for case_index, expected in enumerate(config.expected_cases, start=1):
            matches = source_frame[source_frame["review_case_id"] == expected.review_case_id]
            if len(matches) != 1:
                raise CorrectionPackageVerificationError(f"scope source case identity 不唯一：{expected.review_case_id}")
            scope_row = matches.iloc[0].to_dict()
            if str(scope_row.get("image_id", "")) != expected.image_id:
                raise CorrectionPackageVerificationError(f"scope source image identity 不符：{expected.review_case_id}")
            original_rel = str(scope_row.get("original_image_relpath", "")).strip()
            if not original_rel:
                raise CorrectionPackageVerificationError("scope source 缺 original_image_relpath")
            asset_root = _find_asset_root(extracted_root, original_rel)
            original_source = asset_root / Path(*_require_safe_relative(original_rel, "original image").parts)
            if not original_source.is_file():
                raise CorrectionPackageVerificationError(f"original image 不存在：{original_source}")
            with Image.open(original_source) as image:
                width, height = image.size
            try:
                threshold_candidate = float(str(scope_row.get("threshold_candidate", "0.20") or "0.20"))
            except ValueError as exc:
                raise CorrectionPackageVerificationError(
                    f"threshold_candidate 無效：{expected.review_case_id}"
                ) from exc
            if not 0.0 <= threshold_candidate <= 1.0:
                raise CorrectionPackageVerificationError(
                    f"threshold_candidate 超出範圍：{expected.review_case_id}"
                )
            gt_records = _bbox_records(gt_frame, expected.image_id, "gt", width, height)
            pred_records = _bbox_records(
                pred_frame,
                expected.image_id,
                "pred",
                width,
                height,
                minimum_confidence=threshold_candidate,
            )
            asset_token = expected.review_case_id
            original_target = staging / f"assets/original/{asset_token}.jpg"
            gt_target = staging / f"assets/gt_overlay/{asset_token}.jpg"
            pred_target = staging / f"assets/prediction_overlay/{asset_token}.jpg"
            combined_target = staging / f"assets/combined_overlay/{asset_token}.jpg"
            preliminary: dict[str, Any] = {
                "schema_version": config.schema_version,
                "correction_review_batch_id": batch_id,
                "source_f2_gate_sha256": evidence.gate_result_sha256,
                "source_findings_report_sha256": evidence.findings_report_sha256,
                "review_case_id": expected.review_case_id,
                "image_id": expected.image_id,
                "image_width": width,
                "image_height": height,
                "source_split": "valid",
                "original_image_relpath": original_target.relative_to(staging).as_posix(),
                "gt_overlay_relpath": gt_target.relative_to(staging).as_posix(),
                "prediction_overlay_relpath": pred_target.relative_to(staging).as_posix(),
                "combined_overlay_relpath": combined_target.relative_to(staging).as_posix(),
                "original_annotation_defect_type": expected.annotation_defect_type,
                "original_review_notes": expected.review_notes,
                "gt_bbox_records_json": _canonical_json(gt_records),
                "prediction_bbox_records_json": _canonical_json(pred_records),
            }
            fingerprint = _source_fingerprint(preliminary)
            correction_case_id = "m_" + hashlib.sha256(f"{expected.review_case_id}|{fingerprint}".encode("utf-8")).hexdigest()[:16]
            original_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original_source, original_target)
            _draw_overlay(original_source, gt_target, gt_records, pred_records, "gt")
            _draw_overlay(original_source, pred_target, gt_records, pred_records, "pred")
            _draw_overlay(original_source, combined_target, gt_records, pred_records, "combined")
            row = {
                **preliminary,
                "correction_case_id": correction_case_id,
                "source_case_fingerprint": fingerprint,
            }
            source_rows.append(row)
            cases.append(CorrectionSourceCase(
                case_index=case_index,
                correction_case_id=correction_case_id,
                review_case_id=expected.review_case_id,
                image_id=expected.image_id,
                image_width=width,
                image_height=height,
                source_split="valid",
                source_case_fingerprint=fingerprint,
                original_annotation_defect_type=expected.annotation_defect_type,
                original_review_notes=expected.review_notes,
                original_relpath=row["original_image_relpath"],
                gt_overlay_relpath=row["gt_overlay_relpath"],
                prediction_overlay_relpath=row["prediction_overlay_relpath"],
                combined_overlay_relpath=row["combined_overlay_relpath"],
                gt_bbox_records_json=row["gt_bbox_records_json"],
                prediction_bbox_records_json=row["prediction_bbox_records_json"],
                original_path=final_root / row["original_image_relpath"],
                gt_overlay_path=final_root / row["gt_overlay_relpath"],
                prediction_overlay_path=final_root / row["prediction_overlay_relpath"],
                combined_overlay_path=final_root / row["combined_overlay_relpath"],
            ))

        source_csv_path = staging / "source/correction_review_source.csv"
        _write_csv(source_csv_path, source_rows, SOURCE_COLUMNS)
        contract = {
            "schema_version": config.schema_version,
            "correction_review_batch_id": batch_id,
            "review_case_ids": [case.review_case_id for case in cases],
            "source_f2_gate_sha256": evidence.gate_result_sha256,
            "source_findings_report_sha256": evidence.findings_report_sha256,
            "completed_scope_workbook_sha256": evidence.completed_scope_workbook_sha256,
            "source_record_origin": validation_records.origin,
            "source_04_5k_zip_sha256": validation_records.source_zip_sha256,
        }
        contract_path = staging / "source/source_contract.json"
        contract_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        manifest_rows: list[dict[str, Any]] = []
        for path in sorted(p for p in staging.rglob("*") if p.is_file()):
            rel = path.relative_to(staging).as_posix()
            manifest_rows.append({"relative_path": rel, "size_bytes": path.stat().st_size, "sha256": sha256_file(path)})
        manifest_path = staging / "source/source_manifest.csv"
        _write_csv(manifest_path, manifest_rows, ("relative_path", "size_bytes", "sha256"))
        gate = {
            "gate_id": "PHASE_04_5M_ANNOTATION_CORRECTION_REVIEW_PACKAGE",
            "outcome": "PASS",
            "classification": EXPECTED_PACKAGE_CLASSIFICATION,
            "review_cases": 2,
            "pending": 2,
            "test_split_read": False,
            "model_inference_executed": False,
            "annotation_modified": False,
            "dataset_modified": False,
            "registry_modified": False,
            "fixed_splits_modified": False,
            "training_started": False,
            "retraining_status": "NOT_YET_APPROVED",
            "deployment_acceptance": "NOT_YET_APPROVED",
        }
        gate_path = staging / "evidence/package_gate_result.json"
        gate_path.parent.mkdir(parents=True, exist_ok=True)
        gate_path.write_text(json.dumps(gate, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        checksum_rows = []
        for path in sorted(p for p in staging.rglob("*") if p.is_file()):
            rel = path.relative_to(staging).as_posix()
            checksum_rows.append({"relative_path": rel, "size_bytes": path.stat().st_size, "sha256": sha256_file(path)})
        checksum_path = staging / "evidence/SHA256SUMS.csv"
        _write_csv(checksum_path, checksum_rows, ("relative_path", "size_bytes", "sha256"))
        staging.replace(final_root)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return load_verified_correction_review_package(config, final_root)


def load_verified_correction_review_package(config: CorrectionReviewAppConfig, workspace_root: Path) -> VerifiedCorrectionReviewPackage:
    root = workspace_root.resolve()
    if root == config.project_root or config.project_root in root.parents:
        raise CorrectionPackageVerificationError("04.5M workspace 不得位於 repository 內")
    source_csv = root / "source/correction_review_source.csv"
    manifest = root / "source/source_manifest.csv"
    contract = root / "source/source_contract.json"
    gate = root / "evidence/package_gate_result.json"
    checksums = root / "evidence/SHA256SUMS.csv"
    for path in (source_csv, manifest, contract, gate, checksums):
        if not path.is_file():
            raise CorrectionPackageVerificationError(f"04.5M package 檔案不存在：{path}")
    _read_checksum_manifest(checksums, root)
    gate_payload = json.loads(gate.read_text(encoding="utf-8"))
    if gate_payload.get("outcome") != "PASS" or gate_payload.get("classification") != EXPECTED_PACKAGE_CLASSIFICATION:
        raise CorrectionPackageVerificationError("04.5M package Gate 不符")
    frame = pd.read_csv(source_csv, dtype=str, keep_default_na=False, encoding="utf-8-sig").fillna("").astype(str)
    if frame.columns.tolist() != list(SOURCE_COLUMNS) or len(frame) != 2:
        raise CorrectionPackageVerificationError("04.5M source CSV schema/count 不符")
    expected_order = [case.review_case_id for case in config.expected_cases]
    if frame["review_case_id"].tolist() != expected_order:
        raise CorrectionPackageVerificationError("04.5M source row order 不符")
    cases: list[CorrectionSourceCase] = []
    for index, row in enumerate(frame.to_dict(orient="records"), start=1):
        if row["source_split"] != "valid" or _source_fingerprint(row) != row["source_case_fingerprint"]:
            raise CorrectionPackageVerificationError("04.5M source fingerprint/split 不符")
        paths = [root / row[key] for key in ("original_image_relpath", "gt_overlay_relpath", "prediction_overlay_relpath", "combined_overlay_relpath")]
        if not all(path.is_file() for path in paths):
            raise CorrectionPackageVerificationError(f"04.5M case assets 不完整：{row['review_case_id']}")
        cases.append(CorrectionSourceCase(
            case_index=index,
            correction_case_id=row["correction_case_id"],
            review_case_id=row["review_case_id"],
            image_id=row["image_id"],
            image_width=int(row["image_width"]),
            image_height=int(row["image_height"]),
            source_split=row["source_split"],
            source_case_fingerprint=row["source_case_fingerprint"],
            original_annotation_defect_type=row["original_annotation_defect_type"],
            original_review_notes=row["original_review_notes"],
            original_relpath=row["original_image_relpath"],
            gt_overlay_relpath=row["gt_overlay_relpath"],
            prediction_overlay_relpath=row["prediction_overlay_relpath"],
            combined_overlay_relpath=row["combined_overlay_relpath"],
            gt_bbox_records_json=row["gt_bbox_records_json"],
            prediction_bbox_records_json=row["prediction_bbox_records_json"],
            original_path=paths[0], gt_overlay_path=paths[1], prediction_overlay_path=paths[2], combined_overlay_path=paths[3],
        ))
    return VerifiedCorrectionReviewPackage(
        config=config,
        workspace_root=root,
        source_csv_path=source_csv,
        source_manifest_path=manifest,
        source_contract_path=contract,
        package_gate_path=gate,
        checksum_manifest_path=checksums,
        source_csv_sha256=sha256_file(source_csv),
        source_manifest_sha256=sha256_file(manifest),
        source_contract_sha256=sha256_file(contract),
        package_gate_sha256=sha256_file(gate),
        cases=tuple(cases),
    )
