# Phase 04.5N — Controlled Annotation Correction Promotion

## Current implementation scope

Phase 04.5N is split into two independent Gates:

1. **N1 — staged correction build and validation**: creates an external, timestamped workspace and proves the exact two proposed bbox/area changes without modifying canonical annotations.
2. **N2 — atomic canonical promotion**: remains separately authorized and is not executed by the N1 tooling.

`N1 PASS does not authorize N2`.

## N1 outputs

A successful N1 fixture or future authorized production run returns:

```text
OUTCOME=PASS
CLASSIFICATION=PHASE_04_5N_STAGED_ANNOTATION_CORRECTIONS_VALIDATED
```

The generated workspace contains immutable predecessor evidence, a canonical snapshot, staged corrected validation COCO, exact mapping/diff records, deterministic overlays, semantic validation, manifests, SHA256 checksums, and `evidence/gate_result.json`.

## Safety boundary

N1 must maintain:

```text
TEST_SPLIT_READ=NO
MODEL_INFERENCE_EXECUTED=NO
CANONICAL_COCO_MODIFIED=NO
DATASET_MODIFIED=NO
REGISTRY_MODIFIED=NO
FIXED_SPLITS_MODIFIED=NO
TRAINING_STARTED=NO
RETRAINING_STATUS=NOT_YET_APPROVED
DEPLOYMENT_ACCEPTANCE=NOT_YET_APPROVED
```

Existing final workspace paths block execution. No overwrite or rerun-in-place is allowed.

## Production command — NOT AUTHORIZED BY IMPLEMENTATION PLAN

The following command is documented for a future, separately authorized N1 execution only. Do not run it during implementation closure.

```powershell
$ProjectRoot = "G:\Project\FleetVision"
Set-Location -LiteralPath $ProjectRoot

powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File "$ProjectRoot\scripts\phase04_5_stage_annotation_corrections.ps1" `
  -ProjectRoot $ProjectRoot `
  -Config "$ProjectRoot\configs\data\phase04_5n_annotation_correction_promotion_config.yaml" `
  -CompletedReviewWorkspace "G:\Project\FleetVision_Review_Packages\Phase04_5M\phase04_5m_annotation_correction_review_20260715_014932067" `
  -Timestamp (Get-Date -Format "yyyyMMdd_HHmmssfff")
```

## Failure behavior

The Python CLI prints exactly one compact JSON object:

- PASS JSON to standard output with exit code `0`;
- BLOCKED JSON to standard error with exit code `1`.

The PowerShell wrapper forwards all required parameters and does not parse or rewrite the JSON result.

## N2 read-only preflight

The N2 wrapper defaults to read-only preflight. The operator must provide one exact
verified N1 PASS workspace path; the implementation must never infer the latest workspace automatically.

```powershell
$ProjectRoot = "G:\Project\FleetVision"
Set-Location -LiteralPath $ProjectRoot
$Config = Join-Path $ProjectRoot "configs\data\phase04_5n_annotation_correction_promotion_config.yaml"
$N1Workspace = Read-Host "Paste the exact verified N1 PASS workspace path"
if ([string]::IsNullOrWhiteSpace($N1Workspace)) {
    throw "N1 workspace path is required"
}
$N1Gate = Get-Content (Join-Path $N1Workspace "evidence\gate_result.json") -Raw | ConvertFrom-Json
$Head = (git -C $ProjectRoot rev-parse HEAD).Trim()

powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File (Join-Path $ProjectRoot "scripts\phase04_5_promote_annotation_corrections.ps1") `
  -ProjectRoot $ProjectRoot `
  -Config $Config `
  -N1Workspace $N1Workspace `
  -ExpectedRepositoryHead $Head `
  -ExpectedCanonicalSha256 $N1Gate.canonical_source_sha256 `
  -ExpectedStagedSha256 $N1Gate.staged_coco_sha256 `
  -AuthorizationPhrase "" `
  -Timestamp (Get-Date -Format "yyyyMMdd_HHmmssfff") `
  -DryRun
```

A successful preflight returns:

```text
OUTCOME=PASS
CLASSIFICATION=PHASE_04_5N_PROMOTION_PREFLIGHT_VALIDATED
CANONICAL_COCO_MODIFIED=NO
```

## PRODUCTION N2 EXECUTE IS NOT AUTHORIZED BY IMPLEMENTATION PLAN

N2 execute requires a new, explicit user authorization and the exact phrase:

```text
PHASE_04_5N_2_CANONICAL_PROMOTION_AUTHORIZED
```

Only after that separate Gate may the following controlled form be used. Values
must come from the exact verified N1 gate evidence, never handwritten guesses.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File (Join-Path $ProjectRoot "scripts\phase04_5_promote_annotation_corrections.ps1") `
  -ProjectRoot $ProjectRoot `
  -Config $Config `
  -N1Workspace $N1Workspace `
  -ExpectedRepositoryHead $Head `
  -ExpectedCanonicalSha256 $N1Gate.canonical_source_sha256 `
  -ExpectedStagedSha256 $N1Gate.staged_coco_sha256 `
  -AuthorizationPhrase "PHASE_04_5N_2_CANONICAL_PROMOTION_AUTHORIZED" `
  -Timestamp (Get-Date -Format "yyyyMMdd_HHmmssfff") `
  -Execute
```

Task 8 implementation and tests use temporary fixture repositories only. They do
not execute production N1, production N2 preflight, or production canonical
promotion.

<!-- PHASE_04_5N_REQUIREMENT_TEST_MATRIX -->

## Requirement-to-test matrix for approved design sections 2–17

The implementation closure gate uses the following traceability matrix. Every
approved design section from 2 through 17 maps to at least one production
function and one focused automated test. Missing or renamed coverage blocks
closure.

| Design section | Production implementation | Focused verification |
|---|---|---|
| 2. Authoritative predecessor evidence | `verify_completed_review_workspace`, `_verify_manifest` | `test_completed_review_contract_accepts_exact_two_proposals`, `test_completed_review_contract_rejects_wrong_classification`, `test_export_manifest_size_or_hash_mismatch_is_rejected` |
| 3. Fixed correction set | `load_phase04_5n_config`, `verify_completed_review_workspace` | `test_proposal_order_change_is_rejected`, `test_duplicate_proposal_fingerprint_is_rejected`, `test_historical_test_set_filename_does_not_change_valid_split` |
| 4. Gate decomposition | `prepare_staged_correction_workspace`, `prepare_promotion_preflight`, `execute_atomic_promotion` | `test_prepare_workspace_uses_atomic_final_rename`, `test_n2_dry_run_allows_empty_expected_values_and_is_read_only`, `test_atomic_promotion_creates_verified_backup_and_replaces_canonical` |
| 5. Canonical source discovery | `resolve_canonical_validation_coco`, `load_coco_document`, `SourceAccessLedger` | `test_canonical_resolution_requires_exactly_one_existing_candidate`, `test_canonical_resolution_rejects_zero_existing_candidates`, `test_canonical_resolution_rejects_multiple_candidates`, `test_access_ledger_never_reads_test_split` |
| 6. Annotation identity mapping | `map_reviewed_proposal_to_native_annotation`, `require_distinct_native_annotation_mappings` | `test_local_gt_id_maps_to_unique_native_annotation`, `test_mapping_rejects_missing_native_match`, `test_mapping_rejects_ambiguous_native_match`, `test_distinct_mapping_gate_rejects_duplicate_native_id` |
| 7. Geometry transformation | `parse_replacement_bbox`, `xyxy_to_coco_xywh`, `apply_reviewed_geometry` | `test_xyxy_to_xywh_and_area`, `test_replacement_parser_rejects_non_finite_or_wrong_keys`, `test_mapping_rejects_out_of_bounds_replacement`, `test_apply_geometry_preserves_every_non_geometry_field` |
| 8. Staged output workspace | `prepare_staged_correction_workspace`, `_expected_workspace_files`, `_verify_manifest_rows` | `test_workspace_inventory_and_gate_evidence_are_exact`, `test_workspace_manifests_verify_every_recorded_member`, `test_existing_final_workspace_blocks_without_overwrite` |
| 9. Required N1 semantic invariants | `build_staged_coco`, `validate_staged_coco` | `test_staged_build_changes_exactly_two_annotations`, `test_non_target_annotations_are_semantically_identical`, `test_validation_rejects_id_set_changes`, `test_validation_requires_bbox_and_area_allowlist` |
| 10. Diff contract | `build_diff_rows`, `_mapping_row`, `_diff_json_row` | `test_diff_row_contract_has_exact_order_and_canonical_json`, `test_build_rejects_mapping_count_other_than_two` |
| 11. Overlay contract | `render_annotation_overlays`, `_save_deterministic_jpeg` | `test_overlay_rendering_is_deterministic`, `test_missing_original_image_blocks_official_n1_pass`, `test_overlay_exception_cleans_only_current_staging_directory` |
| 12. Write and failure model | `prepare_staged_correction_workspace`, `_write_blocked_result` | `test_prepare_workspace_uses_atomic_final_rename`, `test_source_manifest_mismatch_blocks_and_writes_evidence`, `test_no_overwrite_blocked_evidence_names_are_unique` |
| 13. N2 atomic promotion design | `verify_n1_workspace`, `prepare_promotion_preflight`, `execute_atomic_promotion`, `restore_verified_backup` | `test_n2_rejects_tampered_n1_manifest`, `test_atomic_promotion_creates_verified_backup_and_replaces_canonical`, `test_post_replace_failure_restores_original_bytes`, `test_rollback_hash_mismatch_is_reported_without_false_success` |
| 14. N2 repository and data policy | `verify_repository_promotion_state`, `_assert_canonical_path_is_regular` | `test_n2_rejects_dirty_repository_outside_allowlist`, `test_n2_rejects_branch_not_main`, `test_n2_rejects_remote_main_disagreement`, `test_canonical_symlink_or_reparse_guard_blocks_before_write` |
| 15. Test strategy | N1/N2 Python CLIs and PowerShell wrappers; JUnit-driven release checks | `test_n1_powershell_wrapper_forwards_every_required_parameter`, `test_n2_powershell_wrapper_dry_run_end_to_end`, `test_n2_powershell_wrapper_execute_end_to_end`, `test_n1_and_n2_wrappers_parse_with_windows_powershell` |
| 16. Acceptance criteria | N1 `main`, N2 CLI `main`, `_promotion_result_payload` | `test_n1_python_cli_returns_structured_pass_json`, `test_n2_python_cli_dry_run_is_read_only_and_structured`, `test_n2_python_cli_execute_promotes_only_fixture_canonical`, `test_atomic_promotion_creates_verified_backup_and_replaces_canonical` |
| 17. Safety boundary | `SourceAccessLedger`, repository guard, CLI dry-run default, no downstream invocation | `test_access_ledger_never_reads_test_split`, `test_protected_external_asset_fingerprint_change_blocks`, `test_execute_atomic_promotion_invokes_no_downstream_command`, `test_n2_python_cli_defaults_to_dry_run` |

## Implementation closure boundary

A successful Task 9 verification establishes that the implementation is ready
for controlled repository integration. It does **not** execute production N1 or
N2 and does not authorize canonical promotion, dataset materialization,
retraining, evaluation, or deployment acceptance.
