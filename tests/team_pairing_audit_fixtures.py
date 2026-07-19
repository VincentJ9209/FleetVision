from __future__ import annotations

from pathlib import Path

import yaml


def valid_team_pairing_config() -> dict[str, object]:
    return {
        "schema_version": "1",
        "source_relative_path": "dataset/01_raw/04_team",
        "output_relative_path": "outputs/phase05s/team_pairing_audit",
        "supported_extensions": [".JPG", ".jpeg", ".png", ".webp", ".jfif"],
        "batch_gap_minutes": 10,
        "pair_max_elapsed_hours": 12,
        "phash_distance_threshold": 6,
        "contact_sheet_columns": 4,
        "contact_sheet_thumbnail_size": 320,
        "timezone": "Asia/Taipei",
        "reviewer": "Vincent",
        "backup_every_successful_saves": 10,
        "backup_retention": 20,
        "max_unreadable_rate": 0.25,
        "frozen_test_access": False,
    }


def write_team_pairing_config(path: Path, **overrides: object) -> Path:
    payload = valid_team_pairing_config()
    payload.update(overrides)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path
