# Phase 04.5M Data Correction Proposal Review Design

- Date: 2026-07-14
- Status: Approved design
- Selected approach: A — dedicated two-case correction-review application
- Predecessor Gate:
  `PHASE_04_5L_COMPLETED_REVIEW_VALIDATION_AND_FINDINGS_ANALYSIS_COMPLETED`
- Primary advisory recommendation:
  `DATA_CORRECTION_REQUIRED_BEFORE_RETRAINING`
- Implementation authorization: not granted by this specification
- Annotation promotion authorization: not granted
- Retraining authorization: not granted

## 1. Purpose

Phase 04.5M converts the two annotation-correction findings from Phase 04.5L
into reviewed, structured, auditable correction proposals.

The phase must answer two questions:

1. Does each suspected annotation defect require a GT correction?
2. When a correction is required, which existing GT bbox identity is affected
   and what exact non-destructive proposed operation should a later promotion
   Gate apply?

Phase 04.5M does not modify canonical annotations, canonical COCO, datasets,
Registry records, fixed splits, model artifacts, or training state.

## 2. Authoritative predecessor evidence

The design is bound to the following verified Phase 04.5L F2 facts:

```text
F2_CLASSIFICATION=PHASE_04_5L_COMPLETED_REVIEW_VALIDATION_AND_FINDINGS_ANALYSIS_COMPLETED
REVIEW_CASES=130
SCOPE_REVIEWED=130
PENDING=0
NEEDS_ADJUDICATION=0
PRIMARY_RECOMMENDATION=DATA_CORRECTION_REQUIRED_BEFORE_RETRAINING
COMPLETED_SCOPE_WORKBOOK_SHA256=AC0EE5882E8E6C7A3E9300BF6AD1589EC18C169681AA6720F0C36132A42B3946
ANNOTATION_CORRECTION_PROPOSAL_COUNT=2
ANNOTATION_DEFECT_SUSPECTED_COUNT=2
IN_SCOPE_CONFIRMED_MODEL_ERROR_SHARE=0.935064935065
IN_SCOPE_PRIORITY_SHARE=0.935064935065
NON_SCOPE_SHARE=0.407692307692
MAX_TOTAL_VARIATION_DISTANCE=0.155144855145
```

Scope distribution:

| Scope group | Count | Share |
|---|---:|---:|
| `IN_SCOPE_LIGHT_MODERATE` | 77 | 59.230769% |
| `BOUNDARY_HEAVY_DAMAGE` | 28 | 21.538462% |
| `OUT_OF_SCOPE_CATASTROPHIC` | 25 | 19.230769% |

The two correction cases are fixed:

| Review case ID | Image ID | Existing finding | Prior reviewer note |
|---|---|---|---|
| `l_687b939a3a89bb8e` | `147_jpg.rf.83b3e9e399d2f3546d5676a902148f0c.jpg` | `wrong_damage_scope` | 模型框的是對的 |
| `l_e5875a8f94620ff1` | `test_set_188_jpg.rf.ed3c01d255f1c18dd0c5dd2667c7a096.jpg` | `extra_bbox` | 重複標註 |

The second image filename contains the historical string `test_set`. Split
authorization must be derived only from the verified Phase 04.5K/F1 records,
which identify the source as validation-only. The filename must never be used
to infer or change split identity.

## 3. Gate decomposition

### 3.1 Phase 04.5M-0 — State synchronization and approved design

This Gate verifies the F2 artifacts, synchronizes repository-backed status,
records this approved design, commits, pushes, and reconciles the remote
checkpoint.

It does not implement the review application.

### 3.2 Phase 04.5M-1 — Correction-review package preparation

This Gate creates a timestamped, no-overwrite workspace outside the repository.
It verifies predecessor hashes and extracts only the two approved cases.

Expected classification:

```text
PHASE_04_5M_ANNOTATION_CORRECTION_REVIEW_PACKAGE_PREPARED
```

### 3.3 Phase 04.5M-2 — Human review and completed export

Vincent reviews both cases through a local Traditional Chinese Streamlit
interface. SQLite is the live state. Each successful save appends an audit
event and participates in scheduled backup creation.

Expected completed classification:

```text
PHASE_04_5M_ANNOTATION_CORRECTION_PROPOSALS_REVIEWED
```

### 3.4 Phase 04.5N — Controlled annotation correction promotion

Phase 04.5N is a separate future Gate. It may consume approved 04.5M proposals
to build and validate a staged corrected COCO copy. Promotion requires a new,
explicit authorization.

## 4. Source package and immutable evidence

The package builder may read only verified validation-only artifacts:

- Phase 04.5L F2 `evidence/gate_result.json`
- Phase 04.5L F2 `evidence/SHA256SUMS.csv`
- `final_findings/phase04_5l_findings_report.json`
- `final_findings/retraining_recommendation.json`
- F1 immutable source CSV, scope source, asset manifest, and checksums
- F1 snapshot of Phase 04.5K validation ground-truth records
- F1 snapshot of Phase 04.5K validation prediction records
- verified original images and existing review overlays

The builder must fail closed when:

- the F2 classification or recommendation changes;
- the proposal case set is not exactly the approved two-case set;
- any source hash, size, identity, or row order differs;
- source records contain any split other than `valid`;
- a required image or bbox record is missing;
- an output workspace already exists.

No source Workbook may be opened and saved merely for inspection.

## 5. Workspace layout

```text
Phase04_5M/
└─ phase04_5m_annotation_correction_review_<timestamp>/
   ├─ source/
   │  ├─ correction_review_source.csv
   │  ├─ source_manifest.csv
   │  └─ source_contract.json
   ├─ assets/
   │  ├─ original/
   │  ├─ gt_overlay/
   │  ├─ prediction_overlay/
   │  └─ combined_overlay/
   ├─ app/
   │  ├─ correction_review_state.sqlite3
   │  ├─ correction_review_events.jsonl
   │  └─ backups/
   ├─ exports/
   │  ├─ annotation_correction_proposals_reviewed.csv
   │  ├─ annotation_correction_proposals_reviewed.json
   │  ├─ annotation_correction_proposals_completed.xlsx
   │  ├─ proposed_overlay/
   │  └─ correction_review_export_result.json
   └─ evidence/
      ├─ package_gate_result.json
      ├─ completed_gate_result.json
      └─ SHA256SUMS.csv
```

Generated images, SQLite databases, Workbooks, CSVs, JSON, and manifests remain
outside Git.

## 6. Reused architecture

The implementation should reuse the stable Phase 04.5L patterns rather than
create a parallel framework:

- package and source-hash verification patterns from
  `severity_scope_review_package.py`;
- SQLite transaction, workspace identity, backup retention, and JSONL audit
  behavior from `severity_scope_review_state.py`;
- Streamlit navigation, progress, filters, and session isolation patterns from
  `severity_scope_review_app.py`;
- completed export, no-overwrite, staging cleanup, and semantic validation
  patterns from `severity_scope_review_export.py`;
- bbox IoU and validation-only source checks from
  `validation_error_human_review.py`.

Reuse must be selective. The completed 04.5L scope-review behavior must not be
regressed or broadly refactored.

## 7. Review identity and source model

Each review source row has immutable fields:

```text
schema_version
correction_review_batch_id
correction_case_id
source_f2_gate_sha256
source_findings_report_sha256
source_case_fingerprint
review_case_id
image_id
image_width
image_height
source_split
original_image_relpath
gt_overlay_relpath
prediction_overlay_relpath
combined_overlay_relpath
original_annotation_defect_type
original_review_notes
gt_bbox_records_json
prediction_bbox_records_json
```

`correction_case_id` is deterministic from the predecessor review identity and
source fingerprint. Existing GT and prediction boxes receive stable,
case-local bbox IDs.

Source fields and row order are immutable throughout review and export.

## 8. Controlled human-review fields

```text
correction_review_status
correction_decision
correction_operation
target_gt_bbox_ids
replacement_bbox_coordinates
correction_reason
correction_reviewer
correction_reviewed_at_utc
```

Approved values:

### `correction_review_status`

- `pending`
- `reviewed`
- `needs_adjudication`

### `correction_decision`

- `CONFIRM_GT_CORRECTION_REQUIRED`
- `REJECT_CORRECTION_KEEP_CURRENT_GT`
- `NEEDS_ADJUDICATION`

### `correction_operation`

- `RESIZE_OR_REDRAW_BBOX`
- `REMOVE_DUPLICATE_BBOX`
- `REMOVE_INVALID_BBOX`
- `ADD_MISSING_BBOX`
- `OTHER`
- `NOT_APPLICABLE`

`target_gt_bbox_ids` is a deterministic JSON array of existing GT bbox IDs.
`replacement_bbox_coordinates` is either blank or canonical JSON:

```json
{"x1": 0.0, "y1": 0.0, "x2": 0.0, "y2": 0.0}
```

Coordinates use the same absolute pixel coordinate system as the verified
validation GT source.

## 9. Semantic validation

- Reviewed rows require decision, operation, reason, reviewer, and a
  timezone-aware timestamp.
- `CONFIRM_GT_CORRECTION_REQUIRED` cannot use `NOT_APPLICABLE`.
- `REJECT_CORRECTION_KEEP_CURRENT_GT` must use `NOT_APPLICABLE`, must not target
  GT bbox IDs, and must not contain replacement geometry.
- `NEEDS_ADJUDICATION` maps to `correction_review_status=needs_adjudication`
  and blocks completed export.
- `REMOVE_DUPLICATE_BBOX` and `REMOVE_INVALID_BBOX` require one or more valid
  existing GT bbox IDs and no replacement geometry.
- `RESIZE_OR_REDRAW_BBOX` requires exactly one existing GT bbox ID and valid
  replacement geometry.
- `ADD_MISSING_BBOX` requires no target GT bbox ID and valid replacement
  geometry.
- `OTHER` requires a non-empty reason and an explicitly documented geometry
  contract when geometry is present.
- Replacement geometry must be finite, satisfy `x1 < x2` and `y1 < y2`, have
  positive area, and remain within image bounds.
- Target bbox IDs must exist in the source case and cannot repeat.
- The proposal must never silently copy a model prediction into GT. The reviewer
  must explicitly confirm or redraw the proposed geometry.

## 10. Traditional Chinese Streamlit interface

The application title is:

```text
FleetVision｜標註修正提案人工複核
```

Each case displays:

- original image;
- GT-only overlay with bbox IDs;
- prediction-only overlay with confidence and bbox IDs;
- combined overlay;
- source defect type and prior notes;
- existing GT bbox table;
- prediction bbox table;
- decision and operation controls;
- target GT bbox selector;
- replacement coordinate editor;
- correction reason;
- progress and save status.

The UI supports previous/next navigation, direct case jump, status filtering,
resume, and a visible `2/2` completion summary.

The application may suggest an operation based on the predecessor finding, but
must not pre-save or pre-confirm a correction:

- `wrong_damage_scope` may visually prioritize `RESIZE_OR_REDRAW_BBOX`;
- `extra_bbox` may visually prioritize `REMOVE_DUPLICATE_BBOX`.

## 11. SQLite, audit, and backup contract

The live state uses a workspace-specific SQLite database.

A successful save is one transaction that:

1. validates workspace identity and immutable source fingerprint;
2. validates controlled values and conditional semantics;
3. inserts or updates the case review;
4. increments a monotonic event sequence;
5. commits;
6. appends the corresponding JSONL audit event;
7. triggers a backup at the configured interval.

For this two-case workflow, the default backup interval is every successful
save and the default retention is 20. This ensures that both case decisions
have independent recovery points.

A database/event mismatch, sequence discontinuity, workspace identity mismatch,
or source hash change fails closed.

## 12. Completed export contract

Export is allowed only when:

```text
total=2
reviewed=2
pending=0
needs_adjudication=0
```

The exporter creates no-overwrite CSV, JSON, XLSX, proposed overlays, export
evidence, and checksums.

The completed proposal export must include before/proposed-after records but
must not create a promoted COCO file. Each proposal includes:

- source case and image identity;
- source GT bbox records;
- decision and operation;
- target GT bbox IDs;
- replacement geometry when applicable;
- reviewer rationale and timestamp;
- source hashes;
- deterministic proposal fingerprint.

The XLSX is an archive and inspection artifact only. It is not a live review
state and is never reimported as the source of truth.

## 13. Failure and recovery

- All package and export writes use staging followed by atomic rename.
- Existing final paths block execution.
- Failure removes only the current operation's staging files.
- Source artifacts, prior SQLite backups, audit events, and successful exports
  are never deleted.
- A blocked Gate writes a no-overwrite evidence JSON containing the failed
  stage and safety declarations.
- Rerunning a successful package or export is prohibited; a new timestamped
  workspace requires a new governance decision.

## 14. Test strategy

Minimum focused tests:

- F2 classification, recommendation, count, and hash verification;
- exact two-case extraction;
- validation-only source enforcement;
- historical `test_set_` filename accepted only when source split is verified
  as `valid`;
- source identity and row-order immutability;
- deterministic bbox IDs and case fingerprints;
- bbox geometry and image-bound validation;
- controlled values and conditional semantics;
- SQLite initialize, save, resume, and workspace mismatch;
- monotonic JSONL audit continuity;
- every-save backup and retention;
- Streamlit navigation, filter, progress, and session isolation;
- incomplete/adjudication export blocked;
- completed export no-overwrite;
- export round-trip and proposal fingerprint;
- proposed overlay determinism;
- failure cleanup;
- canonical COCO, dataset, Registry, fixed splits, and protected assets
  unchanged;
- existing Phase 04.5L review regressions;
- full repository suite at implementation closure.

## 15. Acceptance criteria

Phase 04.5M implementation may be declared complete only when:

- the source case set is exactly two;
- all source hashes and validation-only provenance pass;
- the Traditional Chinese app opens and resumes correctly;
- both cases can be reviewed with valid bbox identity and geometry;
- the completed export is blocked until `2/2`, pending `0`, adjudication `0`;
- completed artifacts and checksum evidence are produced without overwrite;
- no governed annotation or dataset artifact changes;
- focused, regression, and full tests pass;
- `git diff --check` passes;
- exact changed paths are committed and remotely reconciled.

## 16. Safety boundary

```text
TEST_SPLIT_READ=NO
MODEL_INFERENCE_EXECUTED=NO
CANONICAL_ANNOTATION_MODIFIED=NO
CANONICAL_COCO_MODIFIED=NO
DATASET_MODIFIED=NO
REGISTRY_MODIFIED=NO
FIXED_SPLITS_MODIFIED=NO
TRAINING_STARTED=NO
RETRAINING_STATUS=NOT_YET_APPROVED
DEPLOYMENT_ACCEPTANCE=NOT_YET_APPROVED
```

## 17. Authorization stop

This approved design authorizes only repository state synchronization, design
documentation, and the subsequent creation of a detailed implementation plan.

It does not authorize implementation, package execution, human review,
annotation correction promotion, dataset materialization, retraining, or
deployment acceptance.
