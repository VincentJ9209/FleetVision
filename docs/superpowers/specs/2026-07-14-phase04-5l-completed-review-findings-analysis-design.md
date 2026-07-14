# Phase 04.5L Completed Review Findings Analysis Design

## 1. Document status

- Project: `FleetVision / Project_FleetVision`
- Technical phase: `04.5L — Validation Error Human Review`
- Design status: **APPROVED**
- Approved execution approach: **A — existing completed-review validation plus controlled severity-scope review**
- Repository checkpoint before this design: `419c930d1e0577141c45984a78821a603cf07426`
- Authorized Gate: `PHASE_04_5L_COMPLETED_REVIEW_VALIDATION_AND_FINDINGS_ANALYSIS`

This design defines the validation, summarization, severity-scope review, and final findings workflow for the completed 130-case Phase 04.5L human review. It does not authorize training, model inference, annotation mutation, dataset mutation, Registry mutation, fixed-split mutation, or deployment acceptance.

## 2. Goal

Validate the frozen completed-review artifact, run the existing canonical export / validator / summarizer workflow, conduct a separate controlled severity-scope review for all 130 cases, and produce a defensible findings package that distinguishes product-relevant light-to-moderate exterior damage from heavy boundary cases and catastrophic out-of-scope cases.

The Gate must answer:

1. Whether the completed human review is structurally and semantically valid.
2. What error dispositions, root causes, annotation-quality findings, recommended actions, and retraining priorities were recorded.
3. Which cases are in scope, boundary heavy damage, or catastrophic out of scope for FleetVision v1.
4. Whether annotation correction, data composition changes, threshold analysis, or a future retraining proposal is justified.

## 3. Authoritative inputs

### 3.1 Repository state

Expected repository checkpoint before implementation begins:

```text
419c930d1e0577141c45984a78821a603cf07426
```

Expected branch:

```text
main
```

The working tree must be clean or contain only the protected untracked directory:

```text
outputs/metadata/external_assets/
```

### 3.2 Completed Workbook

```text
G:\Project\FleetVision_Review_Packages\Phase04_5L\phase04_5l_20260714_v1_review_workspace\exports\validation_error_human_review_completed.xlsx
```

Expected size:

```text
31871231 bytes
```

Expected SHA256:

```text
C9DF0A38B115406791DF03BFDC714901A66A47BE95CE0E2047E573FCC8D6FB6C
```

Expected logical fingerprint:

```text
F87882E8F6DBF20B6603FC5106BE5A78BD61E4A22A6500E9586E51498B4AAC35
```

### 3.3 Source Workbook

Expected SHA256:

```text
5DC9C1FDA69865D36C60EACB90A0AEA0FC9F4B263F30281723BB0E1172549DE5
```

### 3.4 Frozen formal package

Authoritative path:

```text
G:\Project\FleetVision_Review_Packages\Phase04_5L\phase04_5l_20260714_v1_PACKAGE.zip
```

Expected SHA256:

```text
6D6243FE8F3E12910C03A5EDCFF178CE20B180473EED43DED2B36301A877B42A
```

The original immutable handoff snapshot contains a historical nested-path error. The controlling correction is:

```text
docs/00_project_management/handoffs/2026-07-14_phase04_5l_completed_review_path_erratum.md
```

### 3.5 Review completion state

- Review cases: `130`
- Reviewed: `130`
- Pending: `0`
- Needs adjudication: `0`
- Reviewer: `Vincent`
- Export classification: `LOCAL_REVIEW_APP_COMPLETED_WORKBOOK_EXPORTED`

## 4. Non-negotiable safety boundaries

The Gate must fail closed if any prohibited action is attempted.

- `TEST_SPLIT_READ: NO`
- `MODEL_INFERENCE_EXECUTED: NO`
- `ANNOTATION_MODIFIED: NO`
- `TRAINING_STARTED: NO`
- `RETRAINING_STATUS: NOT_YET_APPROVED`
- `DEPLOYMENT_ACCEPTANCE: NOT_YET_APPROVED`
- Do not rerun completed Workbook export.
- Do not overwrite, open-and-save, or manually edit the completed Workbook.
- Do not modify the source Workbook, frozen package, SQLite state, audit event log, or backups.
- Do not modify GT, canonical COCO, raw datasets, Registry, or fixed splits.
- Do not declare threshold `0.20` as a deployment threshold.
- Do not delete catastrophic cases. Preserve them as out-of-scope / OOD governance material.
- Generated Workbooks, CSV files, images, reports, and evidence remain outside the repository and are not committed by default.

## 5. Gate decomposition

The authorized Gate is implemented as two controlled sub-Gates.

### 5.1 F1 — Completed Review Validation and Findings Preparation

F1 is automated and read-only with respect to all frozen inputs.

F1 must:

1. Verify local, `origin/main`, and GitHub remote HEAD agreement.
2. Verify the initial worktree boundary.
3. Recalculate and verify the completed Workbook SHA256 and size.
4. Verify the source Workbook and frozen package SHA256 values.
5. Verify the completed review logical fingerprint.
6. Create a new no-overwrite analysis workspace outside the repository.
7. Copy frozen inputs into an isolated `input_snapshot` directory and verify byte identity after copying.
8. Run the existing canonical export workflow against the copied completed Workbook.
9. Run the existing completed-review validator.
10. Run the existing summarizer only after validator PASS.
11. Generate a new severity-scope review Workbook and supporting source CSV from the validated canonical review result and the frozen review assets.
12. Produce F1 evidence and checksums.

F1 must stop before severity-scope classification is complete.

Recommended F1 PASS classification:

```text
PHASE_04_5L_COMPLETED_REVIEW_VALIDATED_AND_SCOPE_REVIEW_PACKAGE_CREATED
```

### 5.2 F2 — Severity Scope Review Completion and Final Findings

F2 begins only after the reviewer completes all severity-scope fields in the generated scope Workbook.

F2 must:

1. Re-verify all authoritative input hashes.
2. Verify the F1 scope Workbook source identity and case ordering.
3. Verify exactly 130 unique reviewed cases.
4. Verify zero pending scope classifications.
5. Verify all controlled values and conditional semantics.
6. Export a canonical severity-scope classification CSV without overwriting existing files.
7. Produce severity-scope distributions and cross-tabulations.
8. Combine existing completed-review findings with severity-scope findings.
9. Produce a final findings report and recommendation classification.
10. Produce complete evidence and checksum manifests.

Recommended F2 PASS classification:

```text
PHASE_04_5L_COMPLETED_REVIEW_VALIDATION_AND_FINDINGS_ANALYSIS_COMPLETED
```

F2 PASS does not approve retraining or deployment.

## 6. Analysis workspace

Create a new timestamped, no-overwrite workspace outside the repository:

```text
G:\Project\FleetVision_Review_Packages\Phase04_5L\
phase04_5l_20260714_v1_review_workspace\analysis\
phase04_5l_completed_review_findings_<timestamp>\
```

Required structure:

```text
input_snapshot\
  completed_workbook\
  formal_package\

canonical\
  validation_error_human_review.csv
  annotation_correction_proposals.csv

reports\
  validation_report.json
  validation_errors.csv
  review_summary.json
  review_summary.md
  data_improvement_action_queue.csv
  data_improvement_action_summary.csv

scope_review\
  severity_scope_review.xlsx
  severity_scope_review_source.csv
  scope_asset_manifest.csv

final_findings\
  severity_scope_classification.csv
  severity_scope_summary.json
  severity_scope_summary.md
  phase04_5l_findings_report.json
  phase04_5l_findings_report.md
  retraining_recommendation.json

evidence\
  source_hashes.csv
  workspace_before.csv
  workspace_after.csv
  gate_result.json
  SHA256SUMS.csv
```

No command may overwrite an existing analysis workspace or existing output file.

## 7. Existing completed-review workflow

The design reuses the existing Phase 04.5L workflow rather than replacing it.

Required order:

1. Export canonical review CSV from the copied completed Workbook.
2. Run the existing validator.
3. Continue only when validator classification is:

```text
VALIDATION_ERROR_HUMAN_REVIEW_VERIFIED
```

4. Run the existing summarizer.

Expected summarizer outputs:

```text
canonical/annotation_correction_proposals.csv
reports/review_summary.json
reports/review_summary.md
reports/data_improvement_action_queue.csv
reports/data_improvement_action_summary.csv
```

All annotation correction proposals remain:

```text
proposal_status=PROPOSED_NOT_APPLIED
```

The workflow must never apply annotation changes.

## 8. Severity-scope review schema

### 8.1 Required scope fields

Each case receives these new human-review fields:

```text
scope_review_status
scope_group
scope_reason
operability
scope_confidence
scope_reviewer_notes
scope_reviewer
scope_reviewed_at_utc
```

### 8.2 Controlled values

#### `scope_review_status`

```text
pending
reviewed
needs_adjudication
```

F2 requires all rows to be `reviewed`.

#### `scope_group`

```text
IN_SCOPE_LIGHT_MODERATE
BOUNDARY_HEAVY_DAMAGE
OUT_OF_SCOPE_CATASTROPHIC
```

#### `operability`

```text
drivable_or_likely_drivable
uncertain
non_drivable_or_likely_non_drivable
```

#### `scope_reason`

```text
light_surface_damage
moderate_external_damage
heavy_external_damage
structural_damage
catastrophic_collision
extensive_multi_panel_damage
vehicle_integrity_compromised
insufficient_visual_evidence
other
```

#### `scope_confidence`

```text
high
medium
low
```

### 8.3 Conditional rules

- `scope_reviewer` and `scope_reviewed_at_utc` are required for every reviewed row.
- `scope_reviewer_notes` is required when `scope_confidence=low`.
- `scope_reviewer_notes` is required when `scope_reason=other`.
- `OUT_OF_SCOPE_CATASTROPHIC` requires at least one of:
  - `structural_damage`
  - `catastrophic_collision`
  - `extensive_multi_panel_damage`
  - `vehicle_integrity_compromised`
- `OUT_OF_SCOPE_CATASTROPHIC` should normally use `non_drivable_or_likely_non_drivable` or `uncertain`; a `drivable_or_likely_drivable` value requires nonblank notes.
- `IN_SCOPE_LIGHT_MODERATE` cannot use `catastrophic_collision` or `vehicle_integrity_compromised`.
- `BOUNDARY_HEAVY_DAMAGE` represents substantial but still product-adjacent exterior damage and cannot be used merely because the image is visually dramatic.
- `insufficient_visual_evidence` requires `scope_confidence=low` and nonblank notes.
- Severity alone does not make an image invalid.

## 9. Classification guidance

### 9.1 `IN_SCOPE_LIGHT_MODERATE`

Use when the case represents the intended FleetVision v1 inspection scenario:

- scratches, scuffs, small dents, or localized exterior damage;
- damage affecting a limited area or panel;
- vehicle structure appears intact;
- the case is consistent with rental / fleet handover or return inspection.

### 9.2 `BOUNDARY_HEAVY_DAMAGE`

Use when the case is substantially damaged but remains a meaningful boundary example for exterior damage detection:

- large dents or multiple damaged exterior panels;
- severe localized damage without clear catastrophic structural collapse;
- likely major repair but still recognizable as a product-adjacent damage-detection case;
- ambiguous operability where the image does not prove catastrophic loss.

### 9.3 `OUT_OF_SCOPE_CATASTROPHIC`

Use when the case is inconsistent with the FleetVision v1 product target:

- major structural deformation;
- rollover, crush, catastrophic collision, or large-scale vehicle destruction;
- widespread integrity loss;
- vehicle appears non-drivable or likely non-drivable;
- the visual scenario is materially different from routine exterior inspection.

These cases remain preserved for OOD, robustness, and governance analysis.

## 10. Scope Workbook design

The F1 scope Workbook contains one case per row and must preserve the 130-case identity and ordering.

Each row displays or links to:

- original image;
- GT / prediction overlay;
- case ID and source identity;
- original error type and metrics;
- existing human-review disposition;
- primary and secondary root cause;
- annotation quality and defect type;
- recommended action;
- retraining priority;
- reviewer notes;
- the new severity-scope fields.

Source and existing human-review fields are locked and visually distinguished from editable scope fields.

The first implementation does not include bbox editing, annotation editing, model inference, login, multiuser review, cloud synchronization, or mobile UI.

## 11. F2 validation contract

F2 PASS requires:

```text
rows = 130
unique case identities = 130
scope reviewed = 130
pending = 0
needs adjudication = 0
invalid controlled values = 0
conditional-rule violations = 0
source-field changes = 0
row insertions = 0
row deletions = 0
row reordering = 0
```

The exported severity-scope CSV must be deterministic and UTF-8-SIG round-trip safe.

## 12. Final analysis outputs

The final report must include:

1. `error_disposition` distribution.
2. `primary_root_cause` distribution.
3. `secondary_root_cause` distribution.
4. `annotation_quality` distribution.
5. Annotation defect type distribution.
6. `recommended_action` distribution.
7. `retraining_priority` distribution.
8. Annotation correction proposal count and case list.
9. Severity-scope group counts and percentages.
10. Operability and scope-reason distributions.
11. Scope group × error disposition cross-tabulation.
12. Scope group × root cause cross-tabulation.
13. Scope group × annotation quality cross-tabulation.
14. Scope group × recommended action cross-tabulation.
15. Scope group × retraining priority cross-tabulation.
16. Comparison between all 130 cases and the `IN_SCOPE_LIGHT_MODERATE` subset.
17. Assessment of whether catastrophic / heavy cases distort the apparent error profile.
18. Assessment of whether threshold candidate `0.20` is sensitive to out-of-scope composition.
19. Ranked recommendations for annotation correction, data acquisition, scope rebalancing, preprocessing investigation, threshold analysis, and model strategy.

## 13. Recommendation classification

The final report may issue exactly one primary recommendation:

```text
NO_RETRAINING_RECOMMENDED
DATA_CORRECTION_REQUIRED_BEFORE_RETRAINING
SCOPE_REBALANCING_REQUIRED_BEFORE_RETRAINING
RETRAINING_PROPOSAL_JUSTIFIED
ADDITIONAL_REVIEW_REQUIRED
```

The recommendation is advisory. It does not change:

```text
RETRAINING_STATUS=NOT_YET_APPROVED
DEPLOYMENT_ACCEPTANCE=NOT_YET_APPROVED
```

## 14. Error handling and fail-closed behavior

The implementation must stop without partial promotion when any of the following occurs:

- repository HEAD mismatch;
- unexpected worktree modifications;
- source hash mismatch;
- completed Workbook size or fingerprint mismatch;
- output workspace already exists;
- canonical exporter or validator failure;
- source identity mismatch between Workbook, canonical CSV, and scope Workbook;
- missing image or overlay asset;
- duplicate or missing case identity;
- unexpected row-order change;
- invalid controlled value;
- scope semantic-rule violation;
- attempted overwrite;
- detected test path, inference execution, annotation mutation, or training command.

On failure, the Gate retains evidence but must not modify the frozen inputs or promote incomplete outputs as canonical.

## 15. Testing strategy

Implementation must use test-driven development.

Required test categories:

1. Authoritative hash and path validation.
2. No-overwrite workspace creation.
3. Completed Workbook identity and fingerprint checks.
4. Canonical export integration against a controlled fixture.
5. Existing validator and summarizer orchestration order.
6. Scope schema controlled values.
7. Scope conditional semantics.
8. Source-field and row-order immutability.
9. Deterministic canonical severity-scope CSV export.
10. Distribution and cross-tabulation correctness.
11. Recommendation classification rules.
12. Prohibited-boundary checks for test split, inference, annotation mutation, and training.
13. Windows PowerShell 5.1 launcher compatibility.
14. Failure recovery and evidence creation.

Focused tests and the full repository test suite must pass before implementation closure.

## 16. Repository and output boundaries

Repository commits may include only:

- implementation source code;
- configuration;
- tests;
- operational documentation;
- this design spec;
- implementation plan;
- governance checkpoint updates when separately authorized.

The analysis workspace, Workbooks, canonical outputs, images, reports, and Gate evidence remain outside the repository.

No command may use:

```text
git reset --hard
git clean
git add .
git add -A
```

Only exact-path staging is permitted.

## 17. Completion criteria

The overall Gate is complete only when:

1. F1 completed-review validation passes.
2. Existing canonical review outputs are produced in the isolated analysis workspace.
3. The scope-review package is generated and source-verified.
4. All 130 scope classifications are completed.
5. F2 validation passes with zero blockers.
6. Final findings and recommendation outputs are generated.
7. Frozen artifacts remain byte-identical.
8. Repository and protected assets remain unchanged except for separately authorized implementation commits.
9. `TEST_SPLIT_READ`, `MODEL_INFERENCE_EXECUTED`, `ANNOTATION_MODIFIED`, and `TRAINING_STARTED` all remain `NO`.
10. Retraining and deployment acceptance remain `NOT_YET_APPROVED`.

## 18. Next process checkpoint

After this spec is committed and reviewed, the next authorized activity is to create a detailed implementation plan at:

```text
docs/superpowers/plans/2026-07-14-phase04-5l-completed-review-findings-analysis.md
```

No implementation work begins until the written spec is reviewed and approved.
