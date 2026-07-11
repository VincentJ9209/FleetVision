from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

from fleetvision.data.build_reviewed_dataset import build_reviewed_dataset_outputs
from fleetvision.data.promote_human_review_schema import (
    CANONICAL_OUTPUT_COLUMNS,
    PromotionConfig,
    execute_schema_promotion,
    promote_dataframe,
)
from fleetvision.data.validate_review_labels import validate_review_labels


def _row(index: int, **overrides: str) -> dict[str, str]:
    row = {
        "review_id": f"rev_{index:03d}",
        "image_id": f"img_{index:03d}",
        "source_bucket": "01_general_fleet",
        "original_path": f"dataset/01_raw/01_general_fleet/images/{index}.jpg",
        "filename": f"{index}.jpg",
        "suggested_photo_type_review": "exterior",
        "photo_type_confidence": "0.91",
        "suggested_angle_review": "front_left",
        "angle_confidence": "0.88",
        "auto_review_notes": "",
        "seed_photo_type_review": "exterior",
        "seed_angle_review": "front_left",
        "seed_is_exterior_review": "1",
        "seed_has_visible_damage_review": "0",
        "seed_severity_review": "none",
        "seed_review_status": "pending",
        "seed_reviewer": "Vincent",
        "seed_review_notes": "",
        "human_photo_type_review": "exterior",
        "human_angle_review": "front_left",
        "human_is_exterior_review": "1",
        "human_has_visible_damage_review": "0",
        "human_severity_review": "none",
        "human_review_status": "reviewed",
        "human_reviewer": "Vincent",
        "human_reviewed_at": "2026-07-11 20:00:00",
        "human_review_notes": "",
    }
    row.update(overrides)
    return row


def _source_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _row(1),
            _row(
                2,
                source_bucket="02_claimable_damage",
                human_photo_type_review="exterior",
                human_angle_review="rear_right",
                human_is_exterior_review="1",
                human_has_visible_damage_review="1",
                human_severity_review="moderate",
                human_reviewer="Allison",
                human_review_notes="rear bumper dent",
            ),
            _row(
                3,
                human_photo_type_review="irrelevant",
                human_angle_review="unknown",
                human_is_exterior_review="0",
                human_has_visible_damage_review="unknown",
                human_severity_review="unknown",
                human_reviewer="Allison",
                human_review_notes="not a vehicle image",
            ),
        ]
    )


def _config(tmp_path: Path, source_csv: Path, *, expected_rows: int = 3) -> PromotionConfig:
    return PromotionConfig(
        input_csv=source_csv,
        output_csv=tmp_path / "out" / "pilot500_review_labels_canonical.csv",
        summary_csv=tmp_path / "metadata" / "pilot500_review_schema_promotion_summary.csv",
        errors_csv=tmp_path / "metadata" / "pilot500_review_schema_promotion_errors.csv",
        manifest_csv=tmp_path / "metadata" / "pilot500_review_schema_promotion_manifest.csv",
        review_label_schema=Path(__file__).resolve().parents[1] / "configs/data/review_label_schema.yaml",
        expected_rows=expected_rows,
        required_status="reviewed",
        allow_overwrite=False,
    )


def test_promote_dataframe_maps_exact_values_and_preserves_order() -> None:
    source = _source_dataframe()

    promoted = promote_dataframe(source)

    assert promoted.columns.tolist() == CANONICAL_OUTPUT_COLUMNS
    assert promoted["review_id"].tolist() == ["rev_001", "rev_002", "rev_003"]
    assert promoted.loc[1, "photo_type_review"] == source.loc[1, "human_photo_type_review"]
    assert promoted.loc[1, "angle_review"] == source.loc[1, "human_angle_review"]
    assert promoted.loc[1, "is_exterior_review"] == source.loc[1, "human_is_exterior_review"]
    assert promoted.loc[1, "has_visible_damage_review"] == source.loc[1, "human_has_visible_damage_review"]
    assert promoted.loc[1, "severity_review"] == source.loc[1, "human_severity_review"]
    assert promoted.loc[1, "review_status"] == source.loc[1, "human_review_status"]
    assert promoted.loc[1, "reviewer"] == source.loc[1, "human_reviewer"]
    assert promoted.loc[1, "reviewed_at"] == source.loc[1, "human_reviewed_at"]
    assert promoted.loc[1, "review_notes"] == source.loc[1, "human_review_notes"]


def test_execute_schema_promotion_writes_verified_outputs(tmp_path: Path) -> None:
    source_csv = tmp_path / "formal_merge.csv"
    _source_dataframe().to_csv(source_csv, index=False, encoding="utf-8-sig")
    config = _config(tmp_path, source_csv)

    result = execute_schema_promotion(config)

    assert result.is_valid is True
    assert result.row_count == 3
    assert result.unique_review_id_count == 3
    assert result.reviewed_count == 3
    assert result.pending_count == 0
    assert result.input_validation_error_count == 0
    assert result.output_validation_error_count == 0
    assert result.mapping_mismatch_count == 0
    assert len(result.logical_fingerprint) == 64
    assert config.output_csv.exists()
    assert config.summary_csv.exists()
    assert config.errors_csv.exists()
    assert config.manifest_csv.exists()

    promoted = pd.read_csv(config.output_csv, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    assert promoted.columns.tolist() == CANONICAL_OUTPUT_COLUMNS
    assert promoted["review_id"].tolist() == _source_dataframe()["review_id"].tolist()

    validation = validate_review_labels(
        input_csv=config.output_csv,
        schema_path=config.review_label_schema,
    )
    assert validation.is_valid is True
    assert validation.error_count == 0

    reviewed_outputs = build_reviewed_dataset_outputs(promoted)
    assert reviewed_outputs["summary"].loc[0, "total_rows"] == 3
    assert reviewed_outputs["summary"].loc[0, "reviewed_rows"] == 3
    assert reviewed_outputs["summary"].loc[0, "annotation_candidate_rows"] == 1

    with config.manifest_csv.open(newline="", encoding="utf-8-sig") as file:
        manifest_rows = list(csv.DictReader(file))
    assert len(manifest_rows) == 1
    manifest = manifest_rows[0]
    assert manifest["promotion_status"] == "PROMOTED_AND_VERIFIED"
    assert manifest["input_sha256"] == hashlib.sha256(source_csv.read_bytes()).hexdigest().upper()
    assert manifest["output_sha256"] == hashlib.sha256(config.output_csv.read_bytes()).hexdigest().upper()
    assert manifest["logical_fingerprint"] == result.logical_fingerprint
    assert json.loads(manifest["column_mapping_json"])["human_review_status"] == "review_status"


def test_invalid_input_does_not_leave_partial_outputs(tmp_path: Path) -> None:
    source = _source_dataframe()
    source.loc[0, "human_review_status"] = "pending"
    source.loc[0, "human_reviewed_at"] = ""
    source_csv = tmp_path / "formal_merge.csv"
    source.to_csv(source_csv, index=False, encoding="utf-8-sig")
    config = _config(tmp_path, source_csv)

    with pytest.raises(ValueError, match="human_review_status is not reviewed"):
        execute_schema_promotion(config)

    assert not config.output_csv.exists()
    assert not config.summary_csv.exists()
    assert not config.errors_csv.exists()
    assert not config.manifest_csv.exists()


def test_existing_output_requires_explicit_overwrite(tmp_path: Path) -> None:
    source_csv = tmp_path / "formal_merge.csv"
    _source_dataframe().to_csv(source_csv, index=False, encoding="utf-8-sig")
    config = _config(tmp_path, source_csv)
    config.output_csv.parent.mkdir(parents=True, exist_ok=True)
    config.output_csv.write_text("protected", encoding="utf-8")

    with pytest.raises(FileExistsError, match="already exists"):
        execute_schema_promotion(config)

    assert config.output_csv.read_text(encoding="utf-8") == "protected"
    assert not config.summary_csv.exists()
    assert not config.errors_csv.exists()
    assert not config.manifest_csv.exists()


def test_config_yaml_defaults_are_loadable(tmp_path: Path) -> None:
    from fleetvision.data.promote_human_review_schema import load_config

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "input_csv": "formal.csv",
                "output_csv": "canonical.csv",
                "summary_csv": "summary.csv",
                "errors_csv": "errors.csv",
                "manifest_csv": "manifest.csv",
                "review_label_schema": "schema.yaml",
                "expected_rows": 500,
                "required_status": "reviewed",
                "allow_overwrite": False,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    config = load_config(config_path, tmp_path)

    assert config.input_csv == tmp_path / "formal.csv"
    assert config.output_csv == tmp_path / "canonical.csv"
    assert config.expected_rows == 500
    assert config.required_status == "reviewed"
    assert config.allow_overwrite is False
