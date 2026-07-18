# FleetVision Phase 05S-A1 — Team Pairing Audit Design

- **Date:** 2026-07-19
- **Status:** Approved for design documentation
- **Scope owner:** FleetVision 第二階段
- **Source dataset:** `G:\Project\FleetVision\dataset\01_raw\04_team`
- **Estimated source size:** 319 images
- **Known business outcome:** 借車前後無新增車損；部分案例可能存在借車前既有輕微傷痕
- **Frozen Test:** Locked; must not be accessed, searched, listed, hashed, or modified

## 1. Objective

Build a read-only, semi-automated audit workflow that converts 319 unorganized team-captured images into reviewable capture-batch and before/after pairing candidates.

The workflow must reduce manual work while preserving human confirmation for:

- vehicle identity;
- capture batch membership;
- view angle;
- before/after stage;
- rental pairing;
- existing damage;
- confirmation that no new damage occurred.

This phase does not train a model and does not implement the first-stage capture application or Dashboard.

## 2. Responsibility Boundary

### In scope

- Scan `dataset/01_raw/04_team` without modifying source files.
- Extract image and timestamp metadata.
- Detect unreadable files, exact duplicates, and near-duplicate candidates.
- Generate candidate capture batches from time proximity.
- Generate batch contact sheets.
- Generate candidate before/after pairings.
- Produce a local Traditional Chinese review interface with SQLite live state,
  append-only audit events, backups, and machine-readable CSV/JSON/XLSX exports.
- Select reliable `NO_NEW_DAMAGE` and `EXISTING_DAMAGE_UNCHANGED` demonstration pairs after human confirmation.

### Out of scope

- First-stage mobile capture application.
- Real-time angle or photo-quality gate.
- Dashboard and review UI.
- Damage-model training.
- Automatic license-plate OCR as a hard dependency.
- Automatic final before/after confirmation.
- Responsibility or insurance settlement determination.
- Any Frozen Test access.

## 3. Source Protection Rules

The implementation must never:

- move, rename, delete, overwrite, or re-encode source images;
- modify EXIF;
- write output under `dataset/01_raw`;
- infer a confirmed pair without human review;
- inspect or enumerate Frozen Test paths.

All outputs must be created under:

`G:\Project\FleetVision\outputs\phase05s\team_pairing_audit`

CSV, Excel, JSON, images, and generated contact sheets remain untracked by Git unless explicitly approved. Source code, configuration, tests, and documentation may be committed.

## 4. High-Level Workflow

```text
04_team source images
        ↓
read-only inventory scan
        ↓
EXIF / filesystem time / dimensions / SHA256 / perceptual hash
        ↓
unreadable and duplicate audit
        ↓
timestamp confidence selection
        ↓
capture-batch candidate generation
        ↓
batch contact-sheet generation
        ↓
human vehicle / angle / stage review
        ↓
before-after pair candidate generation
        ↓
human pair confirmation
        ↓
confirmed NO_NEW_DAMAGE / EXISTING_DAMAGE_UNCHANGED cases
```

## 5. Timestamp Strategy

Each image receives:

- `exif_datetime_original`
- `exif_datetime_digitized`
- `filesystem_created_at`
- `filesystem_modified_at`
- `selected_capture_time`
- `selected_time_source`
- `time_confidence`

Selection priority:

1. valid `DateTimeOriginal`;
2. valid `DateTimeDigitized`;
3. other valid EXIF datetime;
4. filesystem creation time when meaningful;
5. filesystem modification time as fallback;
6. missing/invalid timestamp → manual review.

No timestamp source is treated as authoritative without recording its origin.

## 6. Inventory Output

### `team_image_inventory.csv`

One row per discovered image.

Required columns:

- `image_id`
- `filename`
- `relative_path`
- `original_path`
- `extension`
- `file_size_bytes`
- `width`
- `height`
- `aspect_ratio`
- `is_readable`
- `read_error`
- `sha256`
- `perceptual_hash`
- `exif_datetime_original`
- `exif_datetime_digitized`
- `filesystem_created_at`
- `filesystem_modified_at`
- `selected_capture_time`
- `selected_time_source`
- `time_confidence`
- `exact_duplicate_group`
- `near_duplicate_group_candidate`
- `inventory_notes`

`image_id` must be deterministic and derived from stable source identity, not row number.

## 7. Duplicate Audit

### Exact duplicates

Images with identical SHA256 belong to the same `exact_duplicate_group`.

Exact duplicates remain in the inventory but only one representative is used by default in batch/contact-sheet generation. Excluded duplicates must remain traceable.

### Near-duplicate candidates

Use a perceptual hash such as pHash. Near-duplicate grouping is advisory only.

The configuration must expose a conservative Hamming-distance threshold. No source image is deleted, and no near-duplicate is automatically removed from a confirmed case.

## 8. Capture-Batch Candidate Generation

A capture batch represents one continuous walk-around session for one vehicle.

Initial candidate rule:

- sort by `selected_capture_time`;
- start a new candidate batch when the adjacent-image gap exceeds 10 minutes;
- isolate images with missing/low-confidence time;
- do not automatically merge across calendar dates;
- retain configuration for the gap threshold.

The 10-minute rule creates candidates only; it does not establish vehicle identity or before/after status.

### `team_capture_batch_candidates.csv`

Required columns:

- `batch_id`
- `batch_sequence`
- `start_time`
- `end_time`
- `duration_seconds`
- `image_count`
- `timestamp_source_summary`
- `time_confidence_min`
- `suspected_four_angle_complete`
- `batch_confidence`
- `manual_vehicle_id`
- `manual_stage`
- `manual_batch_status`
- `manual_notes`

Expected manual values:

- `manual_stage`: `before`, `after`, `unknown`
- `manual_batch_status`: `confirmed`, `split_required`, `merge_required`, `exclude`, `uncertain`

## 9. Contact Sheets

Create one contact sheet per candidate batch.

Each image tile must show:

- sequence number;
- filename;
- selected timestamp;
- timestamp source;
- image dimensions.

The contact sheet must not modify source images.

Preferred layout:

- 4 columns;
- readable thumbnail size;
- output filename based on `batch_id`;
- deterministic ordering by selected time then filename.

Contact sheets are intended to support manual confirmation of:

- same vehicle;
- four-angle coverage;
- view-angle labels;
- batch boundaries;
- before/after stage.

## 10. View-Angle Review

The system does not need to automate angle classification in Phase 05S-A1.

The Excel review workbook must permit:

- `front_left`
- `front_right`
- `rear_left`
- `rear_right`
- `front`
- `rear`
- `left_side`
- `right_side`
- `closeup`
- `interior`
- `other`
- `unknown`

Human angle labels are authoritative for confirmed demo pairs.

## 11. Before/After Pair Candidate Generation

Pairing runs only after batch-level human fields are available.

Candidate rules:

- same confirmed `manual_vehicle_id`;
- same calendar day by default;
- one batch marked `before`, another marked `after`;
- `after.start_time` later than `before.end_time`;
- elapsed time within configurable upper bound, initially 12 hours;
- no automatic confirmation;
- prefer pairs with four-angle completeness.

### `team_before_after_pair_candidates.csv`

Required columns:

- `pair_candidate_id`
- `manual_vehicle_id`
- `before_batch_id`
- `after_batch_id`
- `elapsed_minutes`
- `before_image_count`
- `after_image_count`
- `four_angle_overlap_count`
- `pair_confidence`
- `pair_reason`
- `manual_pair_status`
- `manual_existing_damage_visible`
- `manual_new_damage_status`
- `manual_notes`

Allowed review values:

- `manual_pair_status`: `confirmed`, `rejected`, `uncertain`
- `manual_existing_damage_visible`: `yes`, `no`, `uncertain`
- `manual_new_damage_status`: `none`, `suspected`, `uncertain`

Confirmed team cases are expected to use `manual_new_damage_status = none`.

## 12. Human Review Interface and Export Workbook

Phase 05S-A1 follows `docs/00_project_management/HUMAN_REVIEW_INTERFACE_STANDARD.md`.
The live human confirmation workflow must use a local Traditional Chinese
Python interface, preferably Streamlit, with SQLite live state.

### Live review state

Required live-state components:

- SQLite database under the output root;
- append-only JSONL audit events;
- automatic backups after successful saves;
- reviewer identity and timezone-aware timestamps populated by the system;
- resumable progress for batch, angle, and pair review;
- no direct source-image mutation;
- no direct Excel editing as the default live state.

The interface must support:

- batch confirmation;
- vehicle identity review;
- before/after stage review;
- image angle review;
- before/after pair confirmation;
- existing-damage and new-damage status review;
- contact-sheet links or previews;
- progress, filters, and pending counts.

### Completed exports

Completed exports may include:

- `team_image_inventory.csv`
- `team_capture_batch_candidates.csv`
- `team_before_after_pair_candidates.csv`
- `team_pair_review_completed.xlsx`
- `team_pairing_summary.json`
- SHA256 manifest

Excel is allowed only as completed export, exchange, or archive format. It is
not the live review state unless a later Gate explicitly approves a controlled
offline-collaboration exception.

## 13. Configuration

Create:

`configs/data/team_pairing_audit_config.yaml`

Minimum configuration:

```yaml
source_relative_path: dataset/01_raw/04_team
output_relative_path: outputs/phase05s/team_pairing_audit
supported_extensions:
  - .jpg
  - .jpeg
  - .png
  - .webp
  - .jfif
batch_gap_minutes: 10
pair_max_elapsed_hours: 12
phash_distance_threshold: 6
contact_sheet_columns: 4
contact_sheet_thumbnail_size: 320
timezone: Asia/Taipei
frozen_test_access: false
```

The implementation must resolve paths from project root and reject output paths under `dataset/01_raw`.

## 14. Proposed Code Boundary

Recommended files:

- `src/fleetvision/data/team_pairing_audit.py`
- `src/fleetvision/review/team_pairing_review_app.py`
- `scripts/phase05s_build_team_pairing_audit.py`
- `scripts/phase05s_launch_team_pairing_review.ps1`
- `scripts/phase05s_export_team_pairing_review.ps1`
- `configs/data/team_pairing_audit_config.yaml`
- `tests/test_team_pairing_audit.py`
- `tests/test_team_pairing_review_app.py`
- `docs/01_phase_guides/phase_05s_a1_team_pairing_audit_design.md`
- `docs/01_phase_guides/phase_05s_a1_team_pairing_audit.md`

Responsibilities:

### Library module

Pure/testable functions for:

- image discovery;
- metadata extraction;
- deterministic IDs;
- hashing;
- batch generation;
- pair candidate generation;
- contact-sheet creation;
- workbook generation;
- summary generation.

### CLI script

- project-root/config argument parsing;
- orchestration;
- logging;
- safety validation;
- final summary and exit codes.

### Review application

- Traditional Chinese operator-facing text;
- SQLite initialize/save/resume;
- append-only audit events;
- automatic backups with retention;
- completed export generation;
- no-overwrite behavior;
- source and Frozen Test path safety checks.

## 15. Error Handling

Fatal errors:

- source root missing;
- source root resolves outside project root;
- output resolves under `dataset/01_raw`;
- invalid configuration;
- zero supported images;
- output file cannot be written.

Non-fatal per-image errors:

- unreadable/corrupt image;
- malformed EXIF;
- missing EXIF;
- unsupported metadata encoding;
- pHash failure.

Non-fatal errors must be recorded in inventory and summary without stopping the whole 319-image scan unless a configurable error-rate threshold is exceeded.

## 16. Summary Output

### `team_pairing_summary.json`

Minimum fields:

- run timestamp;
- config path and SHA256;
- source root;
- output root;
- discovered file count;
- supported image count;
- readable/unreadable count;
- EXIF availability count;
- timestamp-source distribution;
- exact duplicate groups and image count;
- near-duplicate candidate groups;
- candidate batch count;
- batch-size distribution;
- four-angle candidate count;
- pair candidate count;
- warnings;
- Frozen Test declaration.

## 17. Testing Strategy

Tests must use temporary synthetic images only.

Required cases:

1. deterministic image IDs;
2. supported-extension filtering;
3. EXIF timestamp priority;
4. filesystem-time fallback;
5. exact duplicate grouping;
6. conservative near-duplicate behavior;
7. 10-minute batch boundary;
8. missing timestamp isolation;
9. pair generation requires same vehicle and before/after labels;
10. pair elapsed-time limit;
11. output path protection;
12. contact-sheet creation;
13. SQLite live-state save/resume and completed export generation;
14. unreadable image recorded without source modification;
15. Frozen Test path is never accepted or traversed.
16. Excel export is generated only from completed review state.

Tests must not read `dataset/01_raw/04_team` or Frozen Test.

## 18. Validation Commands

Expected commands after implementation:

```powershell
python scripts/phase05s_build_team_pairing_audit.py --help

python -m pytest tests/test_team_pairing_audit.py -q

python -m pytest tests/test_team_pairing_review_app.py -q

python scripts/phase00_init_project.py --validate

python scripts/phase05s_build_team_pairing_audit.py `
  --project-root "G:\Project\FleetVision" `
  --config "configs\data\team_pairing_audit_config.yaml"
```

## 19. Acceptance Criteria

Phase 05S-A1 is accepted when:

- all supported images under `04_team` are inventoried;
- the source directory remains byte-identical before and after the run;
- no file is written under `dataset/01_raw`;
- metadata and duplicate audit outputs exist;
- candidate batches and contact sheets exist;
- the local review state records manual confirmations transactionally;
- completed exports include CSV/JSON/XLSX and SHA256 evidence;
- the summary reports all warnings and counts;
- tests pass;
- project validation passes;
- working tree includes only approved code/config/test/docs changes;
- generated CSV/XLSX/JSON/contact sheets are not committed by default;
- at least 3–5 reliable before/after pairs can be confirmed manually;
- at least one pair is suitable for the `NO_NEW_DAMAGE` final demonstration;
- Frozen Test remains locked and untouched.

## 20. Deferred Work

Explicitly deferred:

- automatic plate OCR;
- learned vehicle re-identification;
- automatic view-angle classifier;
- pair confirmation without human review;
- damage detection or comparison;
- Dashboard integration;
- preservation merge for previously reviewed Excel workbooks if not needed for the first run.

## 21. Design Decision

Phase 05S-A1 uses:

> **Semi-automated candidate pairing plus human confirmation.**

The automated workflow reduces the 319-image review burden by organizing metadata, batches, duplicates, contact sheets, and pair candidates. Human review remains authoritative for vehicle identity, stage, angle, and final pairing.

This design is intentionally narrow so the project can quickly obtain dependable no-new-damage demonstration cases without delaying the core damage-detector and before/after comparison work.
