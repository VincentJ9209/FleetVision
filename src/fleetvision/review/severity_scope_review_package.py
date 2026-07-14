from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

import pandas as pd
import yaml

from fleetvision.data.validation_error_human_review import sha256_file
from fleetvision.data.validation_error_review_findings import (
    SCOPE_COLUMNS,
    SCOPE_EXPORT_COLUMNS,
)


class ScopePackageVerificationError(RuntimeError):
    """Raised when an F1 scope-review package cannot be trusted."""


EXPECTED_F1_CLASSIFICATION = (
    "PHASE_04_5L_COMPLETED_REVIEW_VALIDATED_AND_SCOPE_REVIEW_PACKAGE_CREATED"
)


@dataclass(frozen=True)
class ScopeReviewAppConfig:
    schema_version: str
    project_root: Path
    findings_config_path: Path
    analysis_root: Path
    expected_case_count: int
    reviewer: str
    timezone: str
    backup_every_successful_saves: int
    backup_retention: int
    app_directory_name: str
    completed_workbook_name: str


@dataclass(frozen=True)
class ScopeSourceCase:
    case_index: int
    review_case_id: str
    image_id: str
    source_case_fingerprint: str
    auto_error_category: str
    auto_error_detail_ids: str
    error_disposition: str
    primary_root_cause: str
    recommended_action: str
    retraining_priority: str
    original_relpath: str
    overlay_relpath: str
    original_path: Path
    overlay_path: Path
    source_row: Mapping[str, str]


@dataclass(frozen=True)
class VerifiedScopePackage:
    config: ScopeReviewAppConfig
    f1_workspace_root: Path
    source_csv_path: Path
    template_workbook_path: Path
    asset_manifest_path: Path
    f1_manifest_path: Path
    source_csv_sha256: str
    template_workbook_sha256: str
    asset_manifest_sha256: str
    asset_root: Path
    cases: tuple[ScopeSourceCase, ...]

    @property
    def app_workspace_root(self) -> Path:
        return self.f1_workspace_root / self.config.app_directory_name

    @property
    def completed_workbook_path(self) -> Path:
        return (
            self.app_workspace_root
            / "exports"
            / self.config.completed_workbook_name
        )


def _resolve_path(project_root: Path, value: str) -> Path:
    path = Path(str(value))
    return (path if path.is_absolute() else project_root / path).resolve()


def _require_safe_relative(value: str, label: str) -> PurePosixPath:
    normalized = str(value).replace("\\", "/").strip()
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or not pure.parts or ".." in pure.parts:
        raise ScopePackageVerificationError(
            f"{label} 必須是安全的相對路徑：{value}"
        )
    if any(part.lower() == "test" for part in pure.parts):
        raise ScopePackageVerificationError(
            f"{label} 不得引用 test split：{value}"
        )
    return pure


def _require_sha256(value: object, label: str) -> str:
    digest = str(value or "").strip().upper()
    if len(digest) != 64 or any(char not in "0123456789ABCDEF" for char in digest):
        raise ScopePackageVerificationError(f"{label} 不是有效 SHA256")
    return digest


def load_scope_review_app_config(
    config_path: Path,
    project_root: Path,
) -> ScopeReviewAppConfig:
    """Load static app settings without opening or mutating an F1 workspace."""

    project_root = project_root.resolve()
    path = _resolve_path(project_root, str(config_path))
    if not path.is_file():
        raise ScopePackageVerificationError(f"scope app config 不存在：{path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    try:
        source = raw["source"]
        workspace = raw["workspace"]
        config = ScopeReviewAppConfig(
            schema_version=str(raw["schema_version"]).strip(),
            project_root=project_root,
            findings_config_path=_resolve_path(
                project_root, str(source["findings_config_path"])
            ),
            analysis_root=_resolve_path(
                project_root, str(source["analysis_root"])
            ),
            expected_case_count=int(source["expected_case_count"]),
            reviewer=str(workspace["reviewer"]).strip(),
            timezone=str(workspace["timezone"]).strip(),
            backup_every_successful_saves=int(
                workspace["backup_every_successful_saves"]
            ),
            backup_retention=int(workspace["backup_retention"]),
            app_directory_name=str(workspace["app_directory_name"]).strip(),
            completed_workbook_name=str(
                workspace["completed_workbook_name"]
            ).strip(),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ScopePackageVerificationError(
            f"scope app config 結構無效：{exc}"
        ) from exc

    if config.schema_version != "1":
        raise ScopePackageVerificationError("scope app schema_version 必須是 1")
    if config.expected_case_count != 130:
        raise ScopePackageVerificationError("expected_case_count 必須是 130")
    if not config.findings_config_path.is_file():
        raise ScopePackageVerificationError(
            f"findings config 不存在：{config.findings_config_path}"
        )
    if not config.reviewer or not config.timezone:
        raise ScopePackageVerificationError("reviewer 與 timezone 不可空白")
    if config.backup_every_successful_saves <= 0 or config.backup_retention <= 0:
        raise ScopePackageVerificationError("backup 設定必須是正整數")
    if config.app_directory_name != "scope_review_app":
        raise ScopePackageVerificationError(
            "app_directory_name 必須固定為 scope_review_app"
        )
    if config.completed_workbook_name != "severity_scope_review_completed.xlsx":
        raise ScopePackageVerificationError(
            "completed_workbook_name 必須固定為 severity_scope_review_completed.xlsx"
        )
    if config.analysis_root == project_root or project_root in config.analysis_root.parents:
        raise ScopePackageVerificationError("analysis_root 必須位於 repository 外")
    return config


def discover_latest_f1_workspace(config: ScopeReviewAppConfig) -> Path:
    """Return the newest valid no-overwrite F1 PASS workspace."""

    if not config.analysis_root.is_dir():
        raise ScopePackageVerificationError(
            f"analysis root 不存在：{config.analysis_root}"
        )
    candidates = sorted(
        (
            path
            for path in config.analysis_root.iterdir()
            if path.is_dir()
            and path.name.startswith("phase04_5l_completed_review_findings_")
        ),
        key=lambda path: path.name,
        reverse=True,
    )
    for candidate in candidates:
        gate_path = candidate / "evidence/f1_gate_result.json"
        if not gate_path.is_file():
            continue
        try:
            gate = json.loads(gate_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if (
            gate.get("outcome") == "PASS"
            and gate.get("classification") == EXPECTED_F1_CLASSIFICATION
        ):
            return candidate.resolve()
    raise ScopePackageVerificationError("找不到有效的 F1 PASS workspace")


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise ScopePackageVerificationError(f"必要 CSV 不存在：{path}")
    return pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
    ).fillna("").astype(str)


def _read_f1_manifest(path: Path) -> dict[str, tuple[int, str]]:
    frame = _read_csv(path)
    if frame.columns.tolist() != ["relative_path", "size_bytes", "sha256"]:
        raise ScopePackageVerificationError("F1 checksum manifest schema 已改變")
    entries: dict[str, tuple[int, str]] = {}
    for row in frame.to_dict(orient="records"):
        relative = _require_safe_relative(
            row["relative_path"], "F1 manifest relative_path"
        ).as_posix()
        if relative in entries:
            raise ScopePackageVerificationError(
                f"F1 checksum manifest 重複路徑：{relative}"
            )
        try:
            size = int(row["size_bytes"])
        except ValueError as exc:
            raise ScopePackageVerificationError(
                f"F1 checksum manifest size 無效：{relative}"
            ) from exc
        entries[relative] = (size, _require_sha256(row["sha256"], relative))
    return entries


def _verify_f1_manifest(root: Path, manifest_path: Path) -> None:
    entries = _read_f1_manifest(manifest_path)
    for relative, (expected_size, expected_hash) in entries.items():
        path = root / Path(*PurePosixPath(relative).parts)
        if not path.is_file():
            raise ScopePackageVerificationError(f"F1 輸出遺失：{relative}")
        if path.stat().st_size != expected_size:
            raise ScopePackageVerificationError(f"F1 輸出大小改變：{relative}")
        if sha256_file(path) != expected_hash:
            raise ScopePackageVerificationError(f"F1 輸出 SHA256 改變：{relative}")


def _find_asset_root(extracted_root: Path, relative_paths: tuple[str, str]) -> Path:
    first_relative = _require_safe_relative(relative_paths[0], "original asset")
    candidate_roots: set[Path] = set()
    for match in extracted_root.rglob(first_relative.name):
        if not match.is_file():
            continue
        candidate = match
        for _ in first_relative.parts:
            candidate = candidate.parent
        if all(
            (candidate / Path(*_require_safe_relative(value, "asset").parts)).is_file()
            for value in relative_paths
        ):
            candidate_roots.add(candidate.resolve())
    if len(candidate_roots) != 1:
        raise ScopePackageVerificationError(
            f"無法唯一定位 F1 asset root；matched={len(candidate_roots)}"
        )
    return next(iter(candidate_roots))


def _load_asset_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        expected = [
            "review_case_id",
            "asset_type",
            "relative_path",
            "size_bytes",
            "sha256",
        ]
        if reader.fieldnames != expected:
            raise ScopePackageVerificationError("scope asset manifest schema 已改變")
        return [
            {key: str(value or "").strip() for key, value in row.items()}
            for row in reader
        ]


def load_verified_scope_package(
    config: ScopeReviewAppConfig,
    f1_workspace_root: Path,
) -> VerifiedScopePackage:
    """Verify immutable F1 evidence, source rows, and all preview assets."""

    root = f1_workspace_root.resolve()
    if root == config.project_root or config.project_root in root.parents:
        raise ScopePackageVerificationError("F1 workspace 不得位於 repository 內")

    gate_path = root / "evidence/f1_gate_result.json"
    f1_manifest_path = root / "evidence/F1_SHA256SUMS.csv"
    source_csv_path = root / "scope_review/severity_scope_review_source.csv"
    template_workbook_path = root / "scope_review/severity_scope_review.xlsx"
    asset_manifest_path = root / "scope_review/scope_asset_manifest.csv"
    extracted_root = root / "input_snapshot/extracted_package"

    for path in (
        gate_path,
        f1_manifest_path,
        source_csv_path,
        template_workbook_path,
        asset_manifest_path,
    ):
        if not path.is_file():
            raise ScopePackageVerificationError(f"F1 必要檔案不存在：{path}")
    if not extracted_root.is_dir():
        raise ScopePackageVerificationError(
            f"F1 extracted package 不存在：{extracted_root}"
        )

    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    if gate.get("outcome") != "PASS" or gate.get("classification") != EXPECTED_F1_CLASSIFICATION:
        raise ScopePackageVerificationError("F1 Gate 不是核准的 PASS classification")
    if int(gate.get("review_cases", -1)) != config.expected_case_count:
        raise ScopePackageVerificationError("F1 review case count 不符")
    if any(
        gate.get(key) is not False
        for key in (
            "test_split_read",
            "model_inference_executed",
            "annotation_modified",
            "training_started",
        )
    ):
        raise ScopePackageVerificationError("F1 safety declaration 不符")

    _verify_f1_manifest(root, f1_manifest_path)
    source_hash = sha256_file(source_csv_path)
    template_hash = sha256_file(template_workbook_path)
    asset_manifest_hash = sha256_file(asset_manifest_path)
    if source_hash != str(gate.get("scope_source_csv_sha256", "")).upper():
        raise ScopePackageVerificationError("F1 scope source CSV SHA256 不符")
    if template_hash != str(gate.get("scope_workbook_sha256", "")).upper():
        raise ScopePackageVerificationError("F1 scope Workbook SHA256 不符")
    if asset_manifest_hash != str(gate.get("scope_asset_manifest_sha256", "")).upper():
        raise ScopePackageVerificationError("F1 scope asset manifest SHA256 不符")

    source = _read_csv(source_csv_path)
    if source.columns.tolist() != list(SCOPE_EXPORT_COLUMNS):
        raise ScopePackageVerificationError("scope source 欄位或順序已改變")
    if len(source) != config.expected_case_count:
        raise ScopePackageVerificationError("scope source row count 不符")
    if source["review_case_id"].eq("").any() or source["review_case_id"].duplicated().any():
        raise ScopePackageVerificationError("scope source review_case_id 無效")
    if not source["scope_review_status"].eq("pending").all():
        raise ScopePackageVerificationError("F1 scope source 初始狀態必須全部 pending")
    for column in SCOPE_COLUMNS[1:]:
        if not source[column].eq("").all():
            raise ScopePackageVerificationError(
                f"F1 scope source 初始欄位必須空白：{column}"
            )

    asset_rows = _load_asset_rows(asset_manifest_path)
    if len(asset_rows) != config.expected_case_count * 2:
        raise ScopePackageVerificationError("scope asset manifest 必須每案兩個 asset")
    first = source.iloc[0]
    asset_root = _find_asset_root(
        extracted_root,
        (
            str(first["original_image_relpath"]),
            str(first["overlay_image_relpath"]),
        ),
    )

    assets_by_case: dict[str, dict[str, Path]] = {}
    expected_asset_types = {"original", "overlay"}
    for row in asset_rows:
        review_case_id = row["review_case_id"]
        asset_type = row["asset_type"]
        if asset_type not in expected_asset_types:
            raise ScopePackageVerificationError(
                f"不支援的 asset_type：{asset_type}"
            )
        relative = _require_safe_relative(
            row["relative_path"], "scope asset relative_path"
        )
        asset_path = (asset_root / Path(*relative.parts)).resolve()
        if not asset_path.is_file():
            raise ScopePackageVerificationError(f"scope asset 遺失：{asset_path}")
        try:
            expected_size = int(row["size_bytes"])
        except ValueError as exc:
            raise ScopePackageVerificationError("scope asset size 無效") from exc
        expected_hash = _require_sha256(row["sha256"], str(relative))
        if asset_path.stat().st_size != expected_size or sha256_file(asset_path) != expected_hash:
            raise ScopePackageVerificationError(
                f"scope asset evidence 不符：{relative.as_posix()}"
            )
        case_assets = assets_by_case.setdefault(review_case_id, {})
        if asset_type in case_assets:
            raise ScopePackageVerificationError(
                f"scope asset 重複：{review_case_id}/{asset_type}"
            )
        case_assets[asset_type] = asset_path

    cases: list[ScopeSourceCase] = []
    for index, row in source.iterrows():
        record = {key: str(value) for key, value in row.to_dict().items()}
        review_case_id = record["review_case_id"]
        case_assets = assets_by_case.get(review_case_id, {})
        if set(case_assets) != expected_asset_types:
            raise ScopePackageVerificationError(
                f"案例缺少 original/overlay：{review_case_id}"
            )
        cases.append(
            ScopeSourceCase(
                case_index=index + 1,
                review_case_id=review_case_id,
                image_id=record["image_id"],
                source_case_fingerprint=record["source_case_fingerprint"],
                auto_error_category=record["auto_error_category"],
                auto_error_detail_ids=record["auto_error_detail_ids"],
                error_disposition=record["error_disposition"],
                primary_root_cause=record["primary_root_cause"],
                recommended_action=record["recommended_action"],
                retraining_priority=record["retraining_priority"],
                original_relpath=record["original_image_relpath"],
                overlay_relpath=record["overlay_image_relpath"],
                original_path=case_assets["original"],
                overlay_path=case_assets["overlay"],
                source_row=record,
            )
        )

    if set(assets_by_case) != {case.review_case_id for case in cases}:
        raise ScopePackageVerificationError("asset manifest 含有未知 review_case_id")

    return VerifiedScopePackage(
        config=config,
        f1_workspace_root=root,
        source_csv_path=source_csv_path,
        template_workbook_path=template_workbook_path,
        asset_manifest_path=asset_manifest_path,
        f1_manifest_path=f1_manifest_path,
        source_csv_sha256=source_hash,
        template_workbook_sha256=template_hash,
        asset_manifest_sha256=asset_manifest_hash,
        asset_root=asset_root,
        cases=tuple(cases),
    )
