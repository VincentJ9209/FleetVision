# Phase 04.5N Controlled Annotation Correction Promotion Design

- Date: 2026-07-15
- Status: Proposed design for approval
- Selected approach: **A — two independent Gates**
- Predecessor classification: `PHASE_04_5M_ANNOTATION_CORRECTION_PROPOSALS_REVIEWED`
- Approved correction proposals: 2
- Canonical promotion authorization: **not granted by this design**
- Retraining authorization: **not granted**
- Deployment acceptance: **not granted**

## 1. Purpose

Phase 04.5N converts the two human-reviewed Phase 04.5M correction proposals into a controlled annotation change through two independent Gates:

1. **Phase 04.5N-1 — Staged Correction Build and Validation**
2. **Phase 04.5N-2 — Separately Authorized Atomic Promotion**

Phase 04.5N-1 must prove exactly what would change without modifying canonical annotations. Phase 04.5N-2 may promote the already validated staged artifact only after a separate explicit authorization and a fresh pre-promotion verification.

## 2. Authoritative predecessor evidence

The design is bound to the verified Phase 04.5M-2 export:

```text
OUTCOME=PASS
CLASSIFICATION=PHASE_04_5M_ANNOTATION_CORRECTION_PROPOSALS_REVIEWED
REVIEW_CASES=2
REVIEWED=2
PENDING=0
NEEDS_ADJUDICATION=0
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

Authoritative completed-review inputs:

- `exports/annotation_correction_proposals_reviewed.csv`
- `exports/annotation_correction_proposals_reviewed.json`
- `exports/correction_review_export_result.json`
- `exports/SHA256SUMS.csv`
- `source/source_contract.json`
- `source/source_manifest.csv`
- `source/correction_review_source.csv`

`exports/correction_review_export_result.json` is the completed Gate evidence. The design must not assume that `evidence/completed_gate_result.json` exists.

## 3. Fixed correction set

The proposal set is immutable and must contain exactly these two reviewed records in the original exported order.

### 3.1 Case `l_687b939a3a89bb8e`

```text
correction_case_id=m_57c102ad6b7c8376
image_id=147_jpg.rf.83b3e9e399d2f3546d5676a902148f0c.jpg
source_split=valid
operation=RESIZE_OR_REDRAW_BBOX
target_gt_bbox_ids=["gt_001"]
replacement_bbox={"x1":74.2,"y1":192.4,"x2":285.65,"y2":579.75}
proposal_fingerprint=C28DE952BFEB7B1C2C0F25BA348B8AF69E87032774714AC95D36B29A944A5FC4
```

### 3.2 Case `l_e5875a8f94620ff1`

```text
correction_case_id=m_ccb31aa1a564a66a
image_id=test_set_188_jpg.rf.ed3c01d255f1c18dd0c5dd2667c7a096.jpg
source_split=valid
operation=RESIZE_OR_REDRAW_BBOX
target_gt_bbox_ids=["gt_002"]
replacement_bbox={"x1":97.0,"y1":350.0,"x2":490.0,"y2":468.0}
proposal_fingerprint=EC8ABCDC49879C817480F1A09FD71E376C5CA47EDB730D5DA699B5298BA13095
```

The historical string `test_set` in the second filename must never be used to infer split identity. Split identity is authoritative only when the verified source record says `valid`.

## 4. Gate decomposition

## 4.1 Phase 04.5N-1 — Staged Correction Build and Validation

### Objective

Create a no-overwrite, timestamped workspace outside the repository containing:

- an immutable copy of the authoritative source COCO;
- a staged corrected COCO copy;
- exact before/after annotation records for the two target annotations;
- machine-readable semantic diff;
- human-readable diff report;
- before/after overlays;
- schema, referential-integrity, geometry, count, and checksum evidence.

### Expected classification

```text
PHASE_04_5N_STAGED_ANNOTATION_CORRECTIONS_VALIDATED
```

### Explicit non-effects

Phase 04.5N-1 must not:

- overwrite or rename canonical COCO;
- modify any canonical annotation file;
- modify images, dataset contents, Registry, or fixed splits;
- rerun model inference;
- read the test split;
- begin training, retraining, or fine-tuning;
- stage, commit, or push generated COCO or evidence artifacts.

## 4.2 Phase 04.5N-2 — Atomic Promotion

### Objective

After a separate explicit authorization, verify that the N1 staged package and the current canonical source are unchanged, then atomically promote the already validated staged COCO.

### Expected classification

```text
PHASE_04_5N_ANNOTATION_CORRECTIONS_PROMOTED
```

### Authorization boundary

N1 PASS does not authorize N2. N2 requires a new user instruction that explicitly authorizes canonical annotation promotion.

## 5. Canonical source discovery

The canonical validation COCO path must be resolved from repository-backed configuration or an existing authoritative phase contract. It must not be guessed from common filenames or hardcoded from conversation history.

N1 must record:

```text
canonical_source_relative_path
canonical_source_size_bytes
canonical_source_sha256
canonical_source_schema_summary
canonical_source_image_count
canonical_source_annotation_count
canonical_source_category_count
```

Execution blocks when:

- more than one candidate satisfies the contract;
- no candidate satisfies the contract;
- the resolved path is outside the approved project root;
- the source hash changes during the Gate;
- the source is not the validation annotation source;
- the source contract would require reading test annotations.

## 6. Annotation identity mapping

Case-local IDs such as `gt_001` and `gt_002` are not assumed to be native COCO annotation IDs.

N1 must deterministically map each reviewed target bbox to exactly one canonical annotation using all available immutable fields:

- `image_id` / source image identity;
- source split must equal `valid`;
- original bbox coordinates from `source_gt_bbox_records_json`;
- category identity;
- image width and height;
- source-case fingerprint and proposal fingerprint;
- any authoritative record keys preserved from Phase 04.5K.

Coordinate comparison may use only a small, explicitly configured floating-point tolerance sufficient for serialization noise. The mapping must block when zero or more than one canonical annotation matches.

The native COCO annotation ID, image ID, category ID, original bbox, area, and crowd flags must be written to the N1 mapping evidence.

## 7. Geometry transformation

Reviewed coordinates use absolute corner format:

```text
x1, y1, x2, y2
```

The staged COCO bbox uses standard COCO format:

```text
[x, y, width, height]
```

Transformation:

```text
x = x1
y = y1
width = x2 - x1
height = y2 - y1
area = width * height
```

Validation requirements:

- all coordinates are finite;
- `x1 < x2` and `y1 < y2`;
- width and height are positive;
- bbox remains within the authoritative image bounds;
- category, image identity, annotation ID, and non-geometry fields remain unchanged unless the existing repository contract explicitly requires area recalculation;
- `area` is recalculated consistently with the repository's COCO policy;
- segmentation is not fabricated or modified by this Gate;
- no model prediction geometry is silently substituted for the reviewed geometry.

## 8. Staged output workspace

```text
Phase04_5N/
└─ phase04_5n_staged_annotation_corrections_<timestamp>/
   ├─ source/
   │  ├─ annotation_correction_proposals_reviewed.csv
   │  ├─ annotation_correction_proposals_reviewed.json
   │  ├─ correction_review_export_result.json
   │  ├─ source_contract.json
   │  └─ source_manifest.csv
   ├─ canonical_snapshot/
   │  ├─ canonical_validation_coco.json
   │  └─ canonical_source_contract.json
   ├─ staged/
   │  └─ staged_corrected_validation_coco.json
   ├─ diff/
   │  ├─ annotation_correction_mapping.csv
   │  ├─ annotation_correction_diff.csv
   │  ├─ annotation_correction_diff.json
   │  └─ annotation_correction_diff.md
   ├─ overlays/
   │  ├─ before/
   │  ├─ after/
   │  └─ combined/
   └─ evidence/
      ├─ gate_result.json
      ├─ semantic_validation.json
      ├─ workspace_manifest.csv
      └─ SHA256SUMS.csv
```

Generated files remain outside Git. Existing final workspace paths block execution; overwrite is forbidden.

## 9. Required N1 semantic invariants

N1 PASS requires all of the following:

1. Exactly two reviewed proposals are loaded.
2. Proposal fingerprints match the Phase 04.5M export.
3. Both source rows have `source_split=valid`.
4. Exactly two native canonical annotations are mapped.
5. The two native annotation IDs are distinct.
6. Only bbox geometry and corresponding area change.
7. Image count is unchanged.
8. Annotation count is unchanged.
9. Category count and category definitions are unchanged.
10. Annotation ID set is unchanged.
11. Image ID set is unchanged.
12. Category ID set is unchanged.
13. All non-target annotations are byte-semantically unchanged after normalized JSON comparison.
14. Each target after-bbox exactly represents the reviewed replacement geometry.
15. No target bbox is out of bounds or has non-positive area.
16. Canonical source SHA256 is unchanged from N1 start to finish.
17. Canonical destination path is unchanged and unmodified.
18. Protected external assets are unchanged.
19. No test split artifact is read.
20. No inference, training, Registry update, split update, or dataset materialization occurs.

## 10. Diff contract

Each diff row must include:

```text
schema_version
phase04_5m_review_case_id
correction_case_id
proposal_fingerprint
source_split
image_id
native_coco_image_id
native_coco_annotation_id
native_category_id
before_bbox_xywh
before_bbox_xyxy
before_area
after_bbox_xywh
after_bbox_xyxy
after_area
changed_fields
source_coco_sha256
staged_coco_sha256
```

`changed_fields` must equal the exact approved field set. Unexpected changes block the Gate.

## 11. Overlay contract

N1 renders deterministic before, after, and combined overlays for both cases using the authoritative original images available in the local 04.5M workspace.

Overlay rendering is evidence only. It must not rewrite source images. Each overlay must identify:

- review case ID;
- native COCO annotation ID;
- before bbox;
- proposed after bbox;
- image dimensions.

The N1 package must still be semantically verifiable when overlays are unavailable, but missing locally contracted source images block the official PASS package because visual QA is part of this two-case promotion workflow.

## 12. Write and failure model

N1 uses staging directories and atomic final rename:

1. validate all source contracts;
2. create a unique staging workspace;
3. copy immutable source evidence;
4. snapshot canonical source;
5. build corrected COCO in memory;
6. write staged files;
7. run complete semantic validation;
8. generate overlays and checksums;
9. atomically rename staging workspace to final workspace.

On failure:

- canonical files remain untouched;
- the operation removes only its own incomplete staging workspace;
- a no-overwrite BLOCKED result is written outside the final workspace;
- prior successful N1 workspaces are never deleted or overwritten.

## 13. N2 atomic promotion design

N2 consumes one specific N1 PASS workspace. It must verify:

- N1 `gate_result.json` outcome and classification;
- all N1 manifest hashes;
- staged corrected COCO SHA256;
- current canonical source path and SHA256 equal the N1 recorded source;
- repository branch and approved checkpoint;
- production working tree contains only explicitly allowed pre-existing paths;
- no test, inference, training, Registry, or split mutation is involved.

Promotion sequence:

1. create a byte-for-byte backup of the current canonical COCO in a timestamped evidence directory;
2. verify backup SHA256 equals the current canonical source SHA256;
3. copy the validated staged COCO to a temporary file in the canonical destination directory;
4. fsync/close and verify the temporary file SHA256 equals the N1 staged SHA256;
5. atomically replace the canonical file;
6. verify promoted file SHA256 and complete semantic invariants;
7. record before/after hashes, backup path, N1 workspace identity, and safety declarations;
8. stop before any downstream dataset materialization or retraining.

If post-replace verification fails, the Gate must restore the verified backup atomically and record the recovery result. N2 must never continue to downstream work after a failed promotion verification.

## 14. N2 repository and data policy

Canonical annotation promotion is a governed data mutation, not ordinary source-code staging.

The implementation plan must resolve the existing repository policy for canonical COCO tracking before N2 is implemented. It must not assume that canonical data should be committed to Git. Generated evidence remains outside Git unless a controlling repository document explicitly requires a small source-code or governance-document update.

## 15. Test strategy

### N1 focused tests

- exact Phase 04.5M classification and count verification;
- exact two-proposal identity and order;
- proposal fingerprint verification;
- validation-only split enforcement;
- historical `test_set_` filename does not affect split identity;
- canonical path discovery: zero, one, and multiple candidates;
- canonical source hash drift detection;
- case-local-to-native annotation mapping: exact, missing, and ambiguous;
- floating-point serialization tolerance boundaries;
- xyxy-to-xywh conversion and area calculation;
- image-bound validation;
- preservation of image/category/annotation ID sets;
- exact changed-field allowlist;
- normalized semantic equality of all non-target records;
- deterministic JSON serialization and SHA256;
- deterministic overlay rendering;
- source image missing and manifest mismatch blocking;
- no-overwrite and staging cleanup;
- canonical source remains byte-identical;
- protected assets remain unchanged;
- test split, inference, training, Registry, and fixed-split safety flags.

### N2 focused tests

- explicit authorization required;
- N1 PASS workspace and manifests required;
- current canonical source must match N1 source SHA256;
- staged SHA256 must match N1 evidence;
- backup verification;
- atomic replace success;
- post-promotion semantic verification;
- simulated post-replace failure restores backup;
- repeat promotion and overwrite blocked;
- downstream training and dataset materialization not triggered.

### Regression and closure tests

- Phase 04.5M package, state, app, and export regressions;
- existing COCO validators and annotation utilities;
- full repository test suite;
- Python compile checks;
- PowerShell 5.1 parser checks for thin wrappers only;
- `git diff --check` for repository code/document changes.

Operational verification must use structured JSON or JUnit XML. It must not parse human-formatted pytest summary text.

## 16. Acceptance criteria

### N1 completion

Phase 04.5N-1 may be declared PASS only when:

```text
OUTCOME=PASS
CLASSIFICATION=PHASE_04_5N_STAGED_ANNOTATION_CORRECTIONS_VALIDATED
PROPOSAL_COUNT=2
MAPPED_ANNOTATION_COUNT=2
CHANGED_ANNOTATION_COUNT=2
IMAGE_COUNT_DELTA=0
ANNOTATION_COUNT_DELTA=0
CATEGORY_COUNT_DELTA=0
CANONICAL_SOURCE_MODIFIED=NO
TEST_SPLIT_READ=NO
MODEL_INFERENCE_EXECUTED=NO
DATASET_MODIFIED=NO
REGISTRY_MODIFIED=NO
FIXED_SPLITS_MODIFIED=NO
TRAINING_STARTED=NO
RETRAINING_STATUS=NOT_YET_APPROVED
DEPLOYMENT_ACCEPTANCE=NOT_YET_APPROVED
```

### N2 completion

Phase 04.5N-2 may be declared PASS only when:

```text
OUTCOME=PASS
CLASSIFICATION=PHASE_04_5N_ANNOTATION_CORRECTIONS_PROMOTED
PROMOTED_ANNOTATION_COUNT=2
BACKUP_VERIFIED=YES
ATOMIC_PROMOTION_VERIFIED=YES
POST_PROMOTION_SEMANTIC_VALIDATION=PASS
TEST_SPLIT_READ=NO
MODEL_INFERENCE_EXECUTED=NO
DATASET_MATERIALIZATION_EXECUTED=NO
REGISTRY_MODIFIED=NO
FIXED_SPLITS_MODIFIED=NO
TRAINING_STARTED=NO
RETRAINING_STATUS=NOT_YET_APPROVED
DEPLOYMENT_ACCEPTANCE=NOT_YET_APPROVED
```

## 17. Safety boundary

```text
TEST_SPLIT_READ=NO
MODEL_INFERENCE_EXECUTED=NO
DATASET_MODIFIED=NO               # N1
CANONICAL_ANNOTATION_MODIFIED=NO  # N1
CANONICAL_COCO_MODIFIED=NO        # N1
REGISTRY_MODIFIED=NO
FIXED_SPLITS_MODIFIED=NO
TRAINING_STARTED=NO
RETRAINING_STATUS=NOT_YET_APPROVED
DEPLOYMENT_ACCEPTANCE=NOT_YET_APPROVED
```

For N2, canonical annotation modification is permitted only after separate explicit authorization and only for the two validated target annotations. All other safety boundaries remain in force.

## 18. Authorization stop

Approval of this design authorizes only creation of a detailed implementation plan for Phase 04.5N-1 and Phase 04.5N-2.

It does not authorize implementation, execution of N1, canonical promotion, downstream dataset materialization, retraining, fine-tuning, evaluation, or deployment acceptance.
