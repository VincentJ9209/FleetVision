from __future__ import annotations

import argparse
import csv
import random
import shutil
import sys
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".jfif", ".png", ".webp", ".bmp"}
SOURCE_FOLDERS = {
    "01_general_fleet": Path("dataset/01_raw/01_general_fleet/images"),
    "02_claimable_damage": Path("dataset/01_raw/02_claimable_damage/images"),
    "03_minor_damage": Path("dataset/01_raw/03_minor_damage/images"),
}


def normalize_source(value: str) -> str:
    text = (value or "").strip().lower().replace("\\", "/")
    aliases = {
        "general_fleet": "01_general_fleet",
        "01_general_fleet": "01_general_fleet",
        "claimable": "02_claimable_damage",
        "claimable_damage": "02_claimable_damage",
        "02_claimable_damage": "02_claimable_damage",
        "minor": "03_minor_damage",
        "minor_damage": "03_minor_damage",
        "03_minor_damage": "03_minor_damage",
    }
    for key, normalized in aliases.items():
        if key in text:
            return normalized
    return text


def find_path_column(fieldnames: list[str]) -> str:
    candidates = [
        "original_path",
        "image_path",
        "relative_path",
        "file_path",
        "path",
    ]
    for name in candidates:
        if name in fieldnames:
            return name
    raise ValueError(
        "找不到圖片路徑欄位。預期其中之一："
        + ", ".join(candidates)
    )


def resolve_image_path(
    project_root: Path,
    row: dict[str, str],
    path_column: str,
) -> Path:
    raw_path = (row.get(path_column) or "").strip()
    normalized = raw_path.replace("\\", "/")

    if normalized:
        candidate = Path(normalized)
        if candidate.is_absolute() and candidate.exists():
            return candidate

        relative_candidate = project_root / normalized
        if relative_candidate.exists():
            return relative_candidate

        marker = "dataset/01_raw/"
        lower = normalized.lower()
        position = lower.find(marker)
        if position >= 0:
            candidate = project_root / normalized[position:]
            if candidate.exists():
                return candidate

    source = normalize_source(row.get("source_bucket", ""))
    filename = (row.get("filename") or "").strip()
    source_folder = SOURCE_FOLDERS.get(source)

    if source_folder and filename:
        direct = project_root / source_folder / filename
        if direct.exists():
            return direct

        matches = list((project_root / source_folder).rglob(filename))
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ValueError(f"檔名重複，無法唯一定位：{filename}")

    raise FileNotFoundError(
        f"找不到圖片：image_id={row.get('image_id', '')}, "
        f"filename={filename}, path={raw_path}"
    )


def project_relative_image_path(project_root: Path, image_path: Path) -> Path:
    try:
        return image_path.resolve().relative_to(project_root.resolve())
    except ValueError as exc:
        raise ValueError(
            f"圖片不在專案根目錄內，不能安全打包：{image_path}"
        ) from exc


def choose_rows(
    rows: list[dict[str, str]],
    total: int,
    seed: int,
) -> list[dict[str, str]]:
    rng = random.Random(seed)
    groups: dict[str, list[dict[str, str]]] = {
        key: [] for key in SOURCE_FOLDERS
    }

    for row in rows:
        source = normalize_source(row.get("source_bucket", ""))
        if source in groups:
            groups[source].append(row)

    for values in groups.values():
        rng.shuffle(values)

    # Pilot 策略：
    # 先納入所有 claimable 與 minor（最多填滿 total），
    # 剩餘名額由 general_fleet 補足，以提高車損樣本覆蓋率。
    selected: list[dict[str, str]] = []
    for source in ("02_claimable_damage", "03_minor_damage"):
        remaining = total - len(selected)
        if remaining <= 0:
            break
        selected.extend(groups[source][:remaining])

    remaining = total - len(selected)
    if remaining > 0:
        selected.extend(groups["01_general_fleet"][:remaining])

    if len(selected) < total:
        already_selected = {id(row) for row in selected}
        leftovers = [
            row
            for row in rows
            if id(row) not in already_selected
        ]
        rng.shuffle(leftovers)
        selected.extend(leftovers[: total - len(selected)])

    if len(selected) < total:
        raise ValueError(
            f"可用資料只有 {len(selected)} 筆，無法建立 {total} 筆 pilot。"
        )

    rng.shuffle(selected)
    return selected[:total]


def write_csv(
    output_path: Path,
    fieldnames: list[str],
    rows: list[dict[str, str]],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def create_zip(
    project_root: Path,
    staging_root: Path,
    zip_path: Path,
) -> None:
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(
        zip_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
    ) as archive:
        for path in sorted(staging_root.rglob("*")):
            if path.is_dir():
                continue
            relative = path.relative_to(staging_root)
            archive_name = PurePosixPath(relative.as_posix())
            archive.write(path, arcname=str(archive_name))

        # 確保空的輸出目錄存在，且 ZIP entry 使用正斜線。
        archive.writestr("outputs/metadata/", "")

    with zipfile.ZipFile(zip_path, "r") as archive:
        bad_entries = [
            name for name in archive.namelist() if "\\" in name
        ]
        if bad_entries:
            raise RuntimeError(
                "ZIP 仍含 Windows 反斜線路徑："
                + ", ".join(bad_entries[:5])
            )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="建立 FleetVision Colab Phase 03.5 pilot ZIP。"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="FleetVision 專案根目錄，預設為目前目錄。",
    )
    parser.add_argument(
        "--total",
        type=int,
        default=500,
        help="Pilot 圖片數量，預設 500。",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="固定抽樣種子，預設 42。",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="輸出 ZIP 路徑。",
    )
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    input_csv = (
        project_root
        / "dataset"
        / "00_catalog"
        / "image_review_labels.csv"
    )
    zip_path = (
        args.output.resolve()
        if args.output
        else project_root / "FleetVision_colab_pilot_500_v2.zip"
    )
    staging_root = (
        project_root
        / "outputs"
        / "tmp"
        / "FleetVision_colab_pilot_500_v2"
    )

    if not input_csv.exists():
        print(f"錯誤：找不到 {input_csv}", file=sys.stderr)
        return 1

    for relative_folder in SOURCE_FOLDERS.values():
        folder = project_root / relative_folder
        if not folder.exists():
            print(f"錯誤：找不到圖片資料夾 {folder}", file=sys.stderr)
            return 1

    with input_csv.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            print("錯誤：CSV 沒有欄位。", file=sys.stderr)
            return 1
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    path_column = find_path_column(fieldnames)
    selected = choose_rows(rows, args.total, args.seed)

    if staging_root.exists():
        shutil.rmtree(staging_root)
    staging_root.mkdir(parents=True, exist_ok=True)

    copied_rows: list[dict[str, str]] = []
    copied_paths: set[Path] = set()

    for row in selected:
        image_path = resolve_image_path(
            project_root,
            row,
            path_column,
        )
        if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            raise ValueError(f"不支援的圖片格式：{image_path}")

        relative_path = project_relative_image_path(
            project_root,
            image_path,
        )
        destination = staging_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(image_path, destination)

        copied_row = dict(row)
        copied_row[path_column] = relative_path.as_posix()
        copied_rows.append(copied_row)
        copied_paths.add(relative_path)

    pilot_csv = (
        staging_root
        / "dataset"
        / "00_catalog"
        / "image_review_labels.csv"
    )
    write_csv(pilot_csv, fieldnames, copied_rows)

    manifest_fieldnames = [
        "image_id",
        "source_bucket",
        "filename",
        "pilot_relative_path",
    ]
    manifest_rows = []
    for row in copied_rows:
        manifest_rows.append(
            {
                "image_id": row.get("image_id", ""),
                "source_bucket": row.get("source_bucket", ""),
                "filename": row.get("filename", ""),
                "pilot_relative_path": row.get(path_column, ""),
            }
        )
    write_csv(
        staging_root
        / "dataset"
        / "00_catalog"
        / "pilot_manifest.csv",
        manifest_fieldnames,
        manifest_rows,
    )

    create_zip(project_root, staging_root, zip_path)

    source_counts = Counter(
        normalize_source(row.get("source_bucket", ""))
        for row in copied_rows
    )

    print("FleetVision Colab pilot package created")
    print(f"zip: {zip_path}")
    print(f"rows: {len(copied_rows)}")
    print(f"images: {len(copied_paths)}")
    for source in SOURCE_FOLDERS:
        print(f"{source}: {source_counts.get(source, 0)}")
    print(f"size_mb: {zip_path.stat().st_size / 1024 / 1024:.2f}")
    print("zip_path_separator_check: passed")
    print("temporary_staging:", staging_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
