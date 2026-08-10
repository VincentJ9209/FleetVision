# Data Pipeline

## 1. Metadata Inventory

[`build_metadata.py`](../../src/fleetvision/data/build_metadata.py) consumes tracked configuration, scans approved image inputs, and produces deterministic metadata records including stable identifiers, dimensions, and quality fields. The CLI entry point is [`phase01_build_metadata.py`](../../scripts/phase01_build_metadata.py).

## 2. Review Queue

[`build_review_queue.py`](../../src/fleetvision/data/build_review_queue.py) converts metadata into deterministic review work. Tracked schemas constrain values such as photo type, angle, and severity metadata; severity remains a review concept, not the YOLO class.

## 3. Human Review

The repository contains worklist, package, validation, merge, and export flows. Current multi-case interfaces use local Traditional Chinese Streamlit apps and SQLite state stores. The state implementations provide transactions, resumable progress, audit synchronization, integrity checks, and backups; examples include [`validation_error_review_state.py`](../../src/fleetvision/review/validation_error_review_state.py) and [`annotation_correction_review_state.py`](../../src/fleetvision/review/annotation_correction_review_state.py).

## 4. Reviewed Dataset Boundary

[`build_reviewed_dataset.py`](../../src/fleetvision/data/build_reviewed_dataset.py) represents the controlled transition from reviewed records toward dataset artifacts. A reviewed output is not automatically a training-ready canonical dataset; applicable phase, approval, and acceptance gates still govern promotion.

## 5. External Intake and Registry

[`intake_external_dataset.py`](../../src/fleetvision/data/intake_external_dataset.py) implements controlled external COCO intake. The workflow records source/registry evidence, verifies archive identity and copy integrity, validates safe extraction and referenced images, stages outputs, and avoids partial canonical promotion.

License and lineage evidence are prerequisites for training use. External sources remain separate from the frozen internal holdout.

## 6. Bounding Boxes and Canonicalization

- [`repair_external_coco_bbox.py`](../../src/fleetvision/data/repair_external_coco_bbox.py) handles controlled bounding-box repair.
- [`normalize_external_coco_categories.py`](../../src/fleetvision/data/normalize_external_coco_categories.py) maps approved aliases to the single canonical class `damage` while preserving geometry and provenance contracts.
- [`validate_external_annotation_split_balance.py`](../../src/fleetvision/data/validate_external_annotation_split_balance.py) checks mapping, annotation structure, group leakage, and split balance.

## 7. Deduplication

[`audit_external_dataset_deduplication.py`](../../src/fleetvision/data/audit_external_dataset_deduplication.py) combines exact SHA-256 identities with bounded perceptual-hash candidate generation. Perceptual matches are review candidates rather than automatic deletion decisions. Cross-source controls, deterministic ordering, staging, and atomic promotion protect repeatability.

## 8. Group-Safe Split and QA

Vehicle, rental, burst, and near-duplicate relationships must not leak across evaluation boundaries. Split QA therefore treats grouping evidence and internal/external separation as first-class constraints. A working copy or folder name is never enough to establish canonical status.

## Data Safety

- `dataset/01_raw/` is immutable.
- Frozen Test listing, reading, hashing, tuning, or reuse requires a separate explicit Gate and is not authorized now.
- Internal holdout definitions remain fixed and separate from external data.
- Canonical CSV/COCO/dataset manifests, Registry assets, source archives, and completed human-review outputs are protected.
- Failed operations must not overwrite canonical outputs or leave a partial promotion.
- Private images, datasets, source archives, weights, and generated review packages stay outside Git.

The current rules are authoritative in [`PROTECTED_ASSETS.md`](../02_workflow/PROTECTED_ASSETS.md).
