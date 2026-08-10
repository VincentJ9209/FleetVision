# Interview Guide

## 30-Second Summary

FleetVision is my Phase 2 computer-vision engineering contribution to a broader vehicle-condition workflow. I built the governed path from imperfect image collections to reviewable damage-analysis evidence: metadata and review queues, external-data intake and deduplication, annotation QA, Streamlit/SQLite human review, and validation-only error analysis. The project deliberately separates implemented evidence from planned before/after comparison and avoids insurance or production claims it cannot support.

## 2-Minute Technical Walkthrough

1. Start with the [architecture boundary](ARCHITECTURE.md): Phase 1 capture and Phase 3 dashboard are team context; Phase 2 is the primary contribution.
2. Follow the [data pipeline](DATA_PIPELINE.md) from metadata through human review, external intake, deduplication, canonicalization, and group-safe QA.
3. Explain why the model contract is YOLOv8 Detect with one `damage` class and why severity/claimability stay outside it.
4. Show the [evaluation methodology](MODEL_EVALUATION.md): one-to-one IoU matching, validation-only threshold analysis, FP/FN taxonomy, and human-review feedback.
5. Close with [results and limitations](RESULTS_AND_LIMITATIONS.md), distinguishing implemented workflow evidence from incomplete model provenance and before/after comparison.

## Five Evidence Cases

### 1. Data Governance

**Problem:** generated files and human decisions can become untraceable or overwrite protected evidence.

**Evidence:** deterministic builders, tracked schemas, explicit promotion boundaries, no-overwrite tests, and the current [protected-asset contract](../02_workflow/PROTECTED_ASSETS.md).

**Point:** I designed data state and failure behavior as part of the product, not as cleanup after modelling.

### 2. External Dataset Intake

**Problem:** an external COCO archive can have unclear licensing, unsafe paths, missing image references, inconsistent classes, or duplicates.

**Evidence:** [`intake_external_dataset.py`](../../src/fleetvision/data/intake_external_dataset.py), [`audit_external_dataset_deduplication.py`](../../src/fleetvision/data/audit_external_dataset_deduplication.py), category normalization, bounding-box repair, and split QA.

**Point:** ingestion is fail-closed and provenance-first; naming alone cannot promote an asset.

### 3. Human-in-the-Loop Review

**Problem:** spreadsheet-only live review is fragile for resumability, concurrency, timestamps, and audit history.

**Evidence:** Traditional Chinese Streamlit interfaces and SQLite state stores under [`src/fleetvision/review/`](../../src/fleetvision/review/), with transactions, audit events, backups, validation, and controlled exports.

**Point:** human judgment remains explicit and operationally recoverable.

### 4. Model Evaluation and Error Analysis

**Problem:** a single aggregate score hides threshold trade-offs and recurring FP/FN failure modes.

**Evidence:** [`baseline_error_analysis.py`](../../src/fleetvision/evaluation/baseline_error_analysis.py) and its tests implement one-to-one IoU matching, validation-only sweeps, error taxonomy, and prioritized worklists.

**Point:** evaluation produces actionable data/review work without tuning on Frozen Test.

### 5. Before/After Architecture Boundary

**Problem:** true new-damage detection requires same-vehicle, same-view pairing and sufficient paired validation, not just independent visible-damage boxes.

**Evidence:** the architecture marks pairing/comparison as `PLANNED`; [`compare_damage.py`](../../src/fleetvision/vision/compare_damage.py) is only a focused IoU utility.

**Point:** I can explain the intended boundary without claiming the workflow is implemented.

## Questions I Expect

**Why one class?** The first detector isolates visible `damage`; severity and claimability require different evidence and human/business rules.

**How do you prevent leakage?** Preserve vehicle/rental/burst/near-duplicate grouping, separate internal holdout from external data, and validate split relationships.

**Why Streamlit and SQLite?** They provide a local, operator-focused review interface plus transactional, resumable, auditable state. Excel remains an export/exchange/archive format.

**What happens when intake fails?** Validation stops before promotion; staged outputs and no-overwrite behavior prevent partial canonical replacement.

**What would you do next?** Resume only after the Phase 05S-A3 authorization Gate, then implement approved pairing work under fresh governance and protected-asset reconciliation.

## Claims I Must Not Overstate

- FleetVision is not production SaaS or a complete deployed application.
- It does not make insurance, claimability, liability, pricing, or legal decisions.
- Before/after true new-damage comparison is not complete.
- Phase 1 capture and Phase 3 dashboard are team/system context, not my individually completed products.
- No model is `FINAL` or `PRODUCTION` because of a folder name.
- Historical model metrics are not current final performance until provenance reconciliation is complete.
- Test-suite success is not model-accuracy evidence.

## Demo / Presentation Assets

Git contains the [demo-package guide](../../demo/README_demo.md), source code, tests, and technical documentation. Large videos, screenshots, decks, private data, model weights, and generated outputs live in managed Drive storage and will be linked here only after selection, identity verification, and sharing review in later reset tasks.
