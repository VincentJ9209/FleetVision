
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
import yaml

from annotation_correction_promotion_fixtures import (
    FINGERPRINTS,
    add_second_existing_valid_candidate,
    load_reviewed_rows,
    phase04_5n_fixture,
    refresh_completed_export_checksums,
    refresh_source_checksums,
    rewrite_export_result,
    write_reviewed_rows,
)

from fleetvision.review.annotation_correction_promotion_contract import (
    PromotionContractError,
    SourceAccessLedger,
    canonical_json_bytes,
    load_coco_document,
    load_phase04_5n_config,
    resolve_canonical_validation_coco,
    sha256_file,
    verify_completed_review_workspace,
)


def _config(fixture):
    return load_phase04_5n_config(fixture.config_path, fixture.project_root)


def test_completed_review_contract_accepts_exact_two_proposals(
    phase04_5n_fixture,
) -> None:
    config = _config(phase04_5n_fixture)
    verified = verify_completed_review_workspace(
        config,
        phase04_5n_fixture.completed_review_root,
    )
    assert verified.review_case_ids == (
        "l_687b939a3a89bb8e",
        "l_e5875a8f94620ff1",
    )
    assert verified.proposal_fingerprints == FINGERPRINTS


def test_completed_review_contract_rejects_wrong_classification(
    phase04_5n_fixture,
) -> None:
    rewrite_export_result(
        phase04_5n_fixture.completed_review_root,
        classification="PHASE_04_5M_ANNOTATION_CORRECTION_PROPOSALS_EXPORT_BLOCKED",
    )
    refresh_completed_export_checksums(phase04_5n_fixture.completed_review_root)
    with pytest.raises(PromotionContractError, match="classification"):
        verify_completed_review_workspace(
            _config(phase04_5n_fixture),
            phase04_5n_fixture.completed_review_root,
        )


def test_historical_test_set_filename_does_not_change_valid_split(
    phase04_5n_fixture,
) -> None:
    verified = verify_completed_review_workspace(
        _config(phase04_5n_fixture),
        phase04_5n_fixture.completed_review_root,
    )
    second = verified.proposals[1]
    assert second.image_id.startswith("test_set_")
    assert second.source_split == "valid"


def test_canonical_resolution_requires_exactly_one_existing_candidate(
    phase04_5n_fixture,
) -> None:
    source = resolve_canonical_validation_coco(_config(phase04_5n_fixture))
    assert source.relative_path.as_posix().endswith(
        "canonical_coco/valid/_annotations.coco.json"
    )


def test_canonical_resolution_rejects_multiple_candidates(
    phase04_5n_fixture,
) -> None:
    add_second_existing_valid_candidate(phase04_5n_fixture)
    with pytest.raises(PromotionContractError, match="exactly one"):
        resolve_canonical_validation_coco(_config(phase04_5n_fixture))


def test_access_ledger_never_reads_test_split(phase04_5n_fixture) -> None:
    source = resolve_canonical_validation_coco(_config(phase04_5n_fixture))
    ledger = SourceAccessLedger()
    load_coco_document(source, ledger)
    assert ledger.test_split_read is False
    assert all("/test/" not in path.as_posix() for path in ledger.paths)


def test_missing_export_checksum_member_is_rejected(phase04_5n_fixture) -> None:
    manifest = phase04_5n_fixture.completed_review_root / "exports/SHA256SUMS.csv"
    rows = list(csv.DictReader(manifest.open(encoding="utf-8")))
    rows = [row for row in rows if row["relative_path"] != "annotation_correction_proposals_reviewed.json"]
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["relative_path", "size_bytes", "sha256"])
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(PromotionContractError, match="manifest member"):
        verify_completed_review_workspace(
            _config(phase04_5n_fixture),
            phase04_5n_fixture.completed_review_root,
        )


@pytest.mark.parametrize("field,value", [("size_bytes", "1"), ("sha256", "0" * 64)])
def test_export_manifest_size_or_hash_mismatch_is_rejected(
    phase04_5n_fixture,
    field,
    value,
) -> None:
    manifest = phase04_5n_fixture.completed_review_root / "exports/SHA256SUMS.csv"
    rows = list(csv.DictReader(manifest.open(encoding="utf-8")))
    rows[0][field] = value
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["relative_path", "size_bytes", "sha256"])
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(PromotionContractError, match=field.replace("_bytes", "")):
        verify_completed_review_workspace(
            _config(phase04_5n_fixture),
            phase04_5n_fixture.completed_review_root,
        )


def test_proposal_order_change_is_rejected(phase04_5n_fixture) -> None:
    rows = load_reviewed_rows(phase04_5n_fixture.completed_review_root)
    write_reviewed_rows(phase04_5n_fixture.completed_review_root, list(reversed(rows)))
    refresh_completed_export_checksums(phase04_5n_fixture.completed_review_root)
    with pytest.raises(PromotionContractError, match="order"):
        verify_completed_review_workspace(
            _config(phase04_5n_fixture),
            phase04_5n_fixture.completed_review_root,
        )


def test_duplicate_proposal_fingerprint_is_rejected(phase04_5n_fixture) -> None:
    rows = load_reviewed_rows(phase04_5n_fixture.completed_review_root)
    rows[1]["proposal_fingerprint"] = rows[0]["proposal_fingerprint"]
    write_reviewed_rows(phase04_5n_fixture.completed_review_root, rows)
    refresh_completed_export_checksums(phase04_5n_fixture.completed_review_root)
    with pytest.raises(PromotionContractError, match="duplicate.*fingerprint"):
        verify_completed_review_workspace(
            _config(phase04_5n_fixture),
            phase04_5n_fixture.completed_review_root,
        )


@pytest.mark.parametrize(
    "field,value",
    [("pending", 1), ("needs_adjudication", 1)],
)
def test_incomplete_completed_gate_counts_are_rejected(
    phase04_5n_fixture,
    field,
    value,
) -> None:
    rewrite_export_result(phase04_5n_fixture.completed_review_root, **{field: value})
    refresh_completed_export_checksums(phase04_5n_fixture.completed_review_root)
    with pytest.raises(PromotionContractError, match=field):
        verify_completed_review_workspace(
            _config(phase04_5n_fixture),
            phase04_5n_fixture.completed_review_root,
        )


def test_source_split_not_valid_is_rejected(phase04_5n_fixture) -> None:
    rows = load_reviewed_rows(phase04_5n_fixture.completed_review_root)
    rows[1]["source_split"] = "test"
    write_reviewed_rows(phase04_5n_fixture.completed_review_root, rows)
    refresh_completed_export_checksums(phase04_5n_fixture.completed_review_root)
    with pytest.raises(PromotionContractError, match="source_split"):
        verify_completed_review_workspace(
            _config(phase04_5n_fixture),
            phase04_5n_fixture.completed_review_root,
        )


def test_source_manifest_original_image_hash_mismatch_is_rejected(
    phase04_5n_fixture,
) -> None:
    image = phase04_5n_fixture.source_image_root / "l_687b939a3a89bb8e.jpg"
    image.write_bytes(image.read_bytes() + b"tamper")
    with pytest.raises(PromotionContractError, match="size|sha256"):
        verify_completed_review_workspace(
            _config(phase04_5n_fixture),
            phase04_5n_fixture.completed_review_root,
        )


def test_candidate_outside_project_root_is_rejected(phase04_5n_fixture) -> None:
    outside = phase04_5n_fixture.project_root.parent / "outside/valid/_annotations.coco.json"
    outside.parent.mkdir(parents=True)
    outside.write_text('{"images":[],"annotations":[],"categories":[]}', encoding="utf-8")
    payload = yaml.safe_load(phase04_5n_fixture.config_path.read_text(encoding="utf-8"))
    payload["canonical_source"]["approved_candidates"] = [str(outside)]
    phase04_5n_fixture.config_path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )
    with pytest.raises(PromotionContractError, match="project root|relative"):
        load_phase04_5n_config(
            phase04_5n_fixture.config_path,
            phase04_5n_fixture.project_root,
        )


@pytest.mark.parametrize("field", ["images", "annotations", "categories"])
def test_malformed_coco_arrays_are_rejected(phase04_5n_fixture, field) -> None:
    payload = json.loads(phase04_5n_fixture.canonical_valid_coco.read_text(encoding="utf-8"))
    payload[field] = {}
    phase04_5n_fixture.canonical_valid_coco.write_text(json.dumps(payload), encoding="utf-8")
    source = resolve_canonical_validation_coco(_config(phase04_5n_fixture))
    with pytest.raises(PromotionContractError, match=field):
        load_coco_document(source, SourceAccessLedger())


def test_duplicate_image_ids_are_rejected(phase04_5n_fixture) -> None:
    payload = json.loads(phase04_5n_fixture.canonical_valid_coco.read_text(encoding="utf-8"))
    payload["images"][1]["id"] = payload["images"][0]["id"]
    phase04_5n_fixture.canonical_valid_coco.write_text(json.dumps(payload), encoding="utf-8")
    source = resolve_canonical_validation_coco(_config(phase04_5n_fixture))
    with pytest.raises(PromotionContractError, match="duplicate image"):
        load_coco_document(source, SourceAccessLedger())


def test_duplicate_annotation_ids_are_rejected(phase04_5n_fixture) -> None:
    payload = json.loads(phase04_5n_fixture.canonical_valid_coco.read_text(encoding="utf-8"))
    payload["annotations"][1]["id"] = payload["annotations"][0]["id"]
    phase04_5n_fixture.canonical_valid_coco.write_text(json.dumps(payload), encoding="utf-8")
    source = resolve_canonical_validation_coco(_config(phase04_5n_fixture))
    with pytest.raises(PromotionContractError, match="duplicate annotation"):
        load_coco_document(source, SourceAccessLedger())


def test_category_name_not_damage_is_rejected(phase04_5n_fixture) -> None:
    payload = json.loads(phase04_5n_fixture.canonical_valid_coco.read_text(encoding="utf-8"))
    payload["categories"][0]["name"] = "scratch"
    phase04_5n_fixture.canonical_valid_coco.write_text(json.dumps(payload), encoding="utf-8")
    source = resolve_canonical_validation_coco(_config(phase04_5n_fixture))
    with pytest.raises(PromotionContractError, match="damage"):
        load_coco_document(source, SourceAccessLedger())


def test_annotation_reference_to_missing_image_is_rejected(phase04_5n_fixture) -> None:
    payload = json.loads(phase04_5n_fixture.canonical_valid_coco.read_text(encoding="utf-8"))
    payload["annotations"][0]["image_id"] = 999
    phase04_5n_fixture.canonical_valid_coco.write_text(json.dumps(payload), encoding="utf-8")
    source = resolve_canonical_validation_coco(_config(phase04_5n_fixture))
    with pytest.raises(PromotionContractError, match="missing image"):
        load_coco_document(source, SourceAccessLedger())


def test_canonical_helpers_are_deterministic(phase04_5n_fixture) -> None:
    assert canonical_json_bytes({"b": 2, "a": 1}) == b'{"a":1,"b":2}'
    assert sha256_file(phase04_5n_fixture.canonical_valid_coco) == (
        sha256_file(phase04_5n_fixture.canonical_valid_coco)
    )


def test_canonical_resolution_rejects_zero_existing_candidates(
    phase04_5n_fixture,
) -> None:
    phase04_5n_fixture.canonical_valid_coco.unlink()
    with pytest.raises(PromotionContractError, match="exactly one"):
        resolve_canonical_validation_coco(_config(phase04_5n_fixture))


def test_export_manifest_path_traversal_is_rejected(phase04_5n_fixture) -> None:
    manifest = phase04_5n_fixture.completed_review_root / "exports/SHA256SUMS.csv"
    rows = list(csv.DictReader(manifest.open(encoding="utf-8")))
    rows[0]["relative_path"] = "../outside.json"
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["relative_path", "size_bytes", "sha256"],
        )
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(PromotionContractError, match="relative|root"):
        verify_completed_review_workspace(
            _config(phase04_5n_fixture),
            phase04_5n_fixture.completed_review_root,
        )


def test_reviewed_csv_json_semantic_mismatch_is_rejected(
    phase04_5n_fixture,
) -> None:
    json_path = (
        phase04_5n_fixture.completed_review_root
        / "exports/annotation_correction_proposals_reviewed.json"
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    payload["proposals"][0]["correction_reason"] = "different"
    json_path.write_text(json.dumps(payload), encoding="utf-8")
    refresh_completed_export_checksums(phase04_5n_fixture.completed_review_root)
    with pytest.raises(PromotionContractError, match="semantic identity"):
        verify_completed_review_workspace(
            _config(phase04_5n_fixture),
            phase04_5n_fixture.completed_review_root,
        )


def test_non_object_coco_root_is_rejected(phase04_5n_fixture) -> None:
    phase04_5n_fixture.canonical_valid_coco.write_text("[]", encoding="utf-8")
    source = resolve_canonical_validation_coco(_config(phase04_5n_fixture))
    with pytest.raises(PromotionContractError, match="COCO root"):
        load_coco_document(source, SourceAccessLedger())


def test_duplicate_image_file_names_are_rejected(phase04_5n_fixture) -> None:
    payload = json.loads(
        phase04_5n_fixture.canonical_valid_coco.read_text(encoding="utf-8")
    )
    payload["images"][1]["file_name"] = payload["images"][0]["file_name"]
    phase04_5n_fixture.canonical_valid_coco.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    source = resolve_canonical_validation_coco(_config(phase04_5n_fixture))
    with pytest.raises(PromotionContractError, match="duplicate image file_name"):
        load_coco_document(source, SourceAccessLedger())


def test_duplicate_category_ids_are_rejected(phase04_5n_fixture) -> None:
    payload = json.loads(
        phase04_5n_fixture.canonical_valid_coco.read_text(encoding="utf-8")
    )
    payload["categories"].append(
        {"id": payload["categories"][0]["id"], "name": "damage"}
    )
    phase04_5n_fixture.canonical_valid_coco.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    source = resolve_canonical_validation_coco(_config(phase04_5n_fixture))
    with pytest.raises(PromotionContractError, match="duplicate category"):
        load_coco_document(source, SourceAccessLedger())


def test_annotation_reference_to_missing_category_is_rejected(
    phase04_5n_fixture,
) -> None:
    payload = json.loads(
        phase04_5n_fixture.canonical_valid_coco.read_text(encoding="utf-8")
    )
    payload["annotations"][0]["category_id"] = 999
    phase04_5n_fixture.canonical_valid_coco.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    source = resolve_canonical_validation_coco(_config(phase04_5n_fixture))
    with pytest.raises(PromotionContractError, match="missing category"):
        load_coco_document(source, SourceAccessLedger())


def test_invalid_image_dimensions_are_rejected(phase04_5n_fixture) -> None:
    payload = json.loads(
        phase04_5n_fixture.canonical_valid_coco.read_text(encoding="utf-8")
    )
    payload["images"][0]["width"] = 0
    phase04_5n_fixture.canonical_valid_coco.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    source = resolve_canonical_validation_coco(_config(phase04_5n_fixture))
    with pytest.raises(PromotionContractError, match="dimensions"):
        load_coco_document(source, SourceAccessLedger())
