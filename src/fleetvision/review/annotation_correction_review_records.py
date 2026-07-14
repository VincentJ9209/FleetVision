from __future__ import annotations

import hashlib
import io
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import pandas as pd
import yaml


class ValidationRecordSourceError(RuntimeError):
    """Raised when validation GT/prediction records cannot be verified."""


@dataclass(frozen=True)
class VerifiedValidationRecords:
    ground_truth: pd.DataFrame
    predictions: pd.DataFrame
    origin: str
    source_zip_sha256: str


@dataclass(frozen=True)
class SourceRecordContract:
    zip_filename: str
    zip_sha256: str
    ground_truth_relpath: str
    predictions_relpath: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _safe_relative(value: object, label: str) -> PurePosixPath:
    pure = PurePosixPath(str(value).replace("\\", "/").strip())
    if pure.is_absolute() or not pure.parts or ".." in pure.parts:
        raise ValidationRecordSourceError(f"{label} 必須是安全相對路徑")
    return pure


def load_source_record_contract(project_root: Path) -> SourceRecordContract:
    path = project_root.resolve() / "configs/data/validation_error_human_review_config.yaml"
    if not path.is_file():
        raise ValidationRecordSourceError(f"04.5K source contract 不存在：{path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    try:
        expected = raw["expected_source"]
        source_files = raw["source_files"]
        contract = SourceRecordContract(
            zip_filename=str(expected["zip_filename"]).strip(),
            zip_sha256=str(expected["zip_sha256"]).strip().upper(),
            ground_truth_relpath=_safe_relative(
                source_files["ground_truth"], "ground_truth"
            ).as_posix(),
            predictions_relpath=_safe_relative(
                source_files["predictions"], "predictions"
            ).as_posix(),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationRecordSourceError(f"04.5K source contract 結構無效：{exc}") from exc
    if (
        not contract.zip_filename
        or len(contract.zip_sha256) != 64
        or any(char not in "0123456789ABCDEF" for char in contract.zip_sha256)
    ):
        raise ValidationRecordSourceError("04.5K source ZIP identity 無效")
    return contract


def _find_relative(root: Path, relative: str) -> list[Path]:
    pure = _safe_relative(relative, "record path")
    candidates: set[Path] = set()
    directories = [root]
    directories.extend(path for path in root.rglob("*") if path.is_dir())
    for directory in directories:
        candidate = directory / Path(*pure.parts)
        if candidate.is_file():
            candidates.add(candidate.resolve())
    return sorted(candidates)


def _read_frame(path: Path) -> pd.DataFrame:
    return (
        pd.read_csv(
            path,
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
        .fillna("")
        .astype(str)
    )


def _verified_zip_member_bytes(
    source_zip: Path,
    contract: SourceRecordContract,
    relative: str,
) -> bytes:
    source_zip = source_zip.resolve()
    if not source_zip.is_file():
        raise ValidationRecordSourceError(f"04.5K source ZIP 不存在：{source_zip}")
    if source_zip.name != contract.zip_filename:
        raise ValidationRecordSourceError(
            f"04.5K source ZIP filename 不符：{source_zip.name}"
        )
    actual_hash = _sha256(source_zip)
    if actual_hash != contract.zip_sha256:
        raise ValidationRecordSourceError(
            f"04.5K source ZIP SHA256 不符：actual={actual_hash}"
        )

    expected = _safe_relative(relative, "ZIP member").as_posix()
    with zipfile.ZipFile(source_zip, mode="r") as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise ValidationRecordSourceError(f"04.5K source ZIP CRC failure：{bad_member}")
        candidates: list[zipfile.ZipInfo] = []
        for member in archive.infolist():
            normalized = member.filename.replace("\\", "/")
            pure = PurePosixPath(normalized)
            unix_mode = member.external_attr >> 16
            is_symlink = (unix_mode & 0o170000) == 0o120000
            if pure.is_absolute() or ".." in pure.parts or is_symlink:
                raise ValidationRecordSourceError(
                    f"04.5K source ZIP 含不安全成員：{member.filename}"
                )
            if member.is_dir():
                continue
            if normalized == expected or normalized.endswith("/" + expected):
                candidates.append(member)
        if len(candidates) != 1:
            raise ValidationRecordSourceError(
                f"04.5K source ZIP 必須唯一包含 {expected}；matched={len(candidates)}"
            )
        return archive.read(candidates[0])


def _read_frame_from_zip(
    source_zip: Path,
    contract: SourceRecordContract,
    relative: str,
) -> pd.DataFrame:
    payload = _verified_zip_member_bytes(source_zip, contract, relative)
    return (
        pd.read_csv(
            io.BytesIO(payload),
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
        .fillna("")
        .astype(str)
    )


def load_verified_validation_records(
    *,
    extracted_root: Path,
    project_root: Path,
    source_04_5k_zip: Path | None,
) -> VerifiedValidationRecords:
    contract = load_source_record_contract(project_root)
    gt_matches = _find_relative(extracted_root, contract.ground_truth_relpath)
    pred_matches = _find_relative(extracted_root, contract.predictions_relpath)

    if len(gt_matches) == 1 and len(pred_matches) == 1:
        return VerifiedValidationRecords(
            ground_truth=_read_frame(gt_matches[0]),
            predictions=_read_frame(pred_matches[0]),
            origin="F2_EXTRACTED_VERIFIED_SNAPSHOT",
            source_zip_sha256=contract.zip_sha256,
        )
    if gt_matches or pred_matches:
        raise ValidationRecordSourceError(
            "F2 extracted record snapshot 不完整或不唯一："
            f"ground_truth={len(gt_matches)} predictions={len(pred_matches)}"
        )
    if source_04_5k_zip is None:
        raise ValidationRecordSourceError(
            "F2 snapshot 未包含 validation records，必須提供已驗證的 04.5K source ZIP"
        )

    return VerifiedValidationRecords(
        ground_truth=_read_frame_from_zip(
            source_04_5k_zip, contract, contract.ground_truth_relpath
        ),
        predictions=_read_frame_from_zip(
            source_04_5k_zip, contract, contract.predictions_relpath
        ),
        origin="VERIFIED_04_5K_SOURCE_ZIP",
        source_zip_sha256=contract.zip_sha256,
    )
