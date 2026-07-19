from datetime import datetime
import importlib
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from team_pairing_audit_fixtures import write_team_pairing_config


def mapping():
    return importlib.import_module("fleetvision.review.team_pairing_review_mapping")


def test_load_config_resolves_safe_paths_and_normalizes_extensions(tmp_path: Path) -> None:
    m = mapping()
    project_root = tmp_path / "FleetVision"
    config_path = write_team_pairing_config(project_root / "configs/data/team_pairing_audit_config.yaml")

    config = m.load_team_pairing_audit_config(config_path, project_root)

    assert config.source_root == (project_root / "dataset/01_raw/04_team").resolve()
    assert config.output_root == (project_root / "outputs/phase05s/team_pairing_audit").resolve()
    assert config.supported_extensions == (".jpg", ".jpeg", ".png", ".webp", ".jfif")
    assert config.backup_every_successful_saves == 10
    assert config.backup_retention == 20


def test_load_config_rejects_output_under_raw_dataset(tmp_path: Path) -> None:
    m = mapping()
    project_root = tmp_path / "FleetVision"
    config_path = write_team_pairing_config(
        project_root / "configs/data/team_pairing_audit_config.yaml",
        output_relative_path="dataset/01_raw/generated",
    )

    with pytest.raises(m.TeamPairingMappingValidationError, match="dataset/01_raw"):
        m.load_team_pairing_audit_config(config_path, project_root)


def test_load_config_rejects_parent_traversal_and_frozen_test_access(tmp_path: Path) -> None:
    m = mapping()
    project_root = tmp_path / "FleetVision"
    unsafe_path = write_team_pairing_config(
        project_root / "configs/data/unsafe.yaml",
        source_relative_path="../outside",
    )
    with pytest.raises(m.TeamPairingMappingValidationError, match="安全相對路徑"):
        m.load_team_pairing_audit_config(unsafe_path, project_root)

    frozen_path = write_team_pairing_config(
        project_root / "configs/data/frozen.yaml",
        frozen_test_access=True,
    )
    with pytest.raises(m.TeamPairingMappingValidationError, match="Frozen Test"):
        m.load_team_pairing_audit_config(frozen_path, project_root)


def test_normalize_vehicle_id_uses_controlled_teamcar_pattern() -> None:
    m = mapping()
    assert m.normalize_vehicle_id(" teamcar-007 ") == "TEAMCAR-007"
    with pytest.raises(m.TeamPairingMappingValidationError, match="TEAMCAR-000"):
        m.normalize_vehicle_id("CAR7")


def test_confirmed_batch_requires_vehicle_and_before_or_after_stage() -> None:
    m = mapping()
    with pytest.raises(m.TeamPairingMappingValidationError, match="vehicle ID"):
        m.validate_batch_selection(m.BatchReviewSelection(manual_batch_status="confirmed", manual_stage="before"))

    with pytest.raises(m.TeamPairingMappingValidationError, match="before/after"):
        m.validate_batch_selection(
            m.BatchReviewSelection(
                manual_batch_status="confirmed",
                manual_vehicle_id="TEAMCAR-001",
                manual_stage="unknown",
            )
        )

    m.validate_batch_selection(
        m.BatchReviewSelection(
            manual_batch_status="confirmed",
            manual_vehicle_id="teamcar-001",
            manual_stage="after",
        )
    )


def test_split_merge_exclude_and_uncertain_batches_require_notes() -> None:
    m = mapping()
    for status in ("split_required", "merge_required", "exclude", "uncertain"):
        with pytest.raises(m.TeamPairingMappingValidationError, match="具體說明"):
            m.validate_batch_selection(m.BatchReviewSelection(manual_batch_status=status))


def test_reviewed_unknown_angle_requires_notes() -> None:
    m = mapping()
    with pytest.raises(m.TeamPairingMappingValidationError, match="具體說明"):
        m.validate_angle_selection(m.AngleReviewSelection(review_status="reviewed", manual_angle="unknown"))

    m.validate_angle_selection(
        m.AngleReviewSelection(
            review_status="reviewed",
            manual_angle="unknown",
            manual_notes="照片只拍到局部，無法可靠判定角度",
        )
    )


def test_pair_classification_is_derived_from_confirmed_human_fields() -> None:
    m = mapping()
    assert m.derive_pair_classification("confirmed", "no", "none") == "NO_NEW_DAMAGE"
    assert m.derive_pair_classification("confirmed", "yes", "none") == "EXISTING_DAMAGE_UNCHANGED"
    assert m.derive_pair_classification("confirmed", "yes", "suspected") == "NEW_DAMAGE_CANDIDATE"
    assert m.derive_pair_classification("uncertain", "no", "none") == "MANUAL_REVIEW_REQUIRED"


def test_demo_role_requires_confirmed_reliable_no_new_damage_pair() -> None:
    m = mapping()
    with pytest.raises(m.TeamPairingMappingValidationError, match="demo role"):
        m.validate_pair_selection(
            m.PairReviewSelection(
                manual_pair_status="confirmed",
                manual_existing_damage_visible="no",
                manual_new_damage_status="suspected",
                manual_demo_role="primary",
                manual_notes="疑似新增刮痕",
            )
        )

    m.validate_pair_selection(
        m.PairReviewSelection(
            manual_pair_status="confirmed",
            manual_existing_damage_visible="yes",
            manual_new_damage_status="none",
            manual_demo_role="backup",
        )
    )


def test_canonical_fields_auto_populate_reviewer_and_timezone_timestamp() -> None:
    m = mapping()
    reviewed_at = datetime(2026, 7, 19, 15, 30, tzinfo=ZoneInfo("Asia/Taipei"))
    batch = m.derive_canonical_batch_fields(
        m.BatchReviewSelection(
            manual_batch_status="confirmed",
            manual_vehicle_id="teamcar-003",
            manual_stage="before",
        ),
        reviewer="Vincent",
        reviewed_at=reviewed_at,
    )
    assert batch.manual_vehicle_id == "TEAMCAR-003"
    assert batch.review_reviewer == "Vincent"
    assert batch.reviewed_at_utc.endswith("+00:00")

    pair = m.derive_canonical_pair_fields(
        m.PairReviewSelection(
            manual_pair_status="confirmed",
            manual_existing_damage_visible="no",
            manual_new_damage_status="none",
            manual_demo_role="primary",
        ),
        reviewer="Vincent",
        reviewed_at=reviewed_at,
    )
    assert pair.derived_case_classification == "NO_NEW_DAMAGE"
    assert pair.reviewed_at_utc.endswith("+00:00")


def test_canonical_mapping_rejects_naive_timestamp() -> None:
    m = mapping()
    with pytest.raises(m.TeamPairingMappingValidationError, match="時區"):
        m.derive_canonical_batch_fields(
            m.BatchReviewSelection(),
            reviewer="Vincent",
            reviewed_at=datetime(2026, 7, 19, 15, 30),
        )
