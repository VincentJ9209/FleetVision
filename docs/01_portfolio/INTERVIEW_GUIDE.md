# Interview Guide

## 30-Second Summary

FleetVision is my Phase 2 computer-vision engineering contribution to a broader vehicle-condition workflow. I built the governed path from imperfect image collections to reviewable damage-analysis evidence: metadata and review queues, external-data intake and deduplication, annotation QA, Streamlit/SQLite human review, and validation-only error analysis. The project deliberately separates implemented evidence from planned before/after comparison and avoids insurance, production, or final-model claims it cannot support.

## 2-Minute Technical Walkthrough

1. Start with the [architecture boundary](ARCHITECTURE.md): Phase 1 capture and Phase 3 dashboard/review are team context; repository-backed Phase 2 work is the primary contribution.
2. Follow the [data pipeline](DATA_PIPELINE.md) from metadata through human review, external intake, deduplication, canonicalization, and group-safe QA.
3. Explain why the model contract is YOLOv8 Detect with one `damage` class and why severity/claimability stay outside it.
4. Show the [evaluation methodology](MODEL_EVALUATION.md): one-to-one IoU matching, training-selected historical validation metrics, separate validation operating-point analysis, FP/FN taxonomy, and the Frozen Test boundary.
5. Close with [results and limitations](RESULTS_AND_LIMITATIONS.md): the only quantitative claim is a historical controlled baseline, the current reference model is `NONE`, dataset identities follow the registry, and before/after comparison remains incomplete.

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

**Problem:** a single aggregate score hides split boundaries, threshold trade-offs, and recurring FP/FN failure modes.

**Evidence:** [`baseline_error_analysis.py`](../../src/fleetvision/evaluation/baseline_error_analysis.py) and its tests implement one-to-one IoU matching, validation-only operating-point analysis, error taxonomy, and prioritized worklists. Quantitative claims map only to [`RESULTS_REGISTRY.md`](../02_workflow/RESULTS_REGISTRY.md).

**Point:** the historical controlled-baseline metrics, validation operating-point candidates, and one-time historical test are three separate evidence layers. None is a current final score or a Frozen Test tuning signal.

### 5. Before/After Architecture Boundary

**Problem:** true new-damage detection requires same-vehicle, same-view pairing and sufficient paired validation, not just independent visible-damage boxes.

**Evidence:** the architecture marks pairing/comparison as `PLANNED`; [`compare_damage.py`](../../src/fleetvision/vision/compare_damage.py) is only a focused IoU utility.

**Point:** I can explain the intended boundary without claiming the workflow is implemented or reliable.

## Questions I Expect

**Why one class?** The first detector isolates visible `damage`; severity and claimability require different evidence and human/business rules.

**What model result can you claim?** Only the `MDL-045J-Y8S-BASELINE` historical controlled baseline. Its training-selected validation summary is Precision `0.4868`, Recall `0.3508`, mAP50 `0.3516`, and mAP50-95 `0.1620`; its one-time historical test is Precision `0.5423`, Recall `0.3883`, mAP50 `0.3804`, and mAP50-95 `0.1756`. Every value maps to one of the eight exact Result IDs listed in the Results Registry and [Results and Limitations](RESULTS_AND_LIMITATIONS.md). The test row is reporting only and was not used for tuning.

**Are the confidence values deployment thresholds?** No. Confidence `0.05` (`RES-045K-OP-HIGH-RECALL`), `0.20` (`RES-045K-OP-BALANCED`), and `0.80` (`RES-045K-OP-HIGH-PRECISION`) at IoU `0.5` are separate validation operating-point candidates, not training metrics or production thresholds.

**What is the current model?** There is no accepted current reference model. The verified Phase 04.5J model is historical; the artifact under `final_selected` is `BEST_AVAILABLE_POC_ONLY` and has `quality_gate_pass=false`.

**Which dataset is canonical?** The registry treats `DS-INT-V1` as a protected historical baseline. `DS-RELABEL-V3-WORKING` is a `NOT_CANONICAL` working copy; neither that folder name nor an unresolved export establishes canonical Dataset v3.

**How do you prevent leakage?** Preserve vehicle/rental/burst/near-duplicate grouping, separate internal holdout from external data, and validate split relationships.

**Why Streamlit and SQLite?** They provide a local, operator-focused review interface plus transactional, resumable, auditable state. Excel remains an export/exchange/archive format.

**What happens when intake fails?** Validation stops before promotion; staged outputs and no-overwrite behavior prevent partial canonical replacement.

**What would you do next?** Resume only after a separate Phase 05S-A3 authorization Gate, then execute only its explicitly authorized scope after fresh governance, Git, and protected-asset reconciliation.

## Claims I Must Not Overstate

- FleetVision is not production SaaS or a complete deployed application.
- It does not make automated insurance, claimability, liability, pricing, or legal decisions.
- Reliable true-new-damage detection has not been established.
- Before/after same-vehicle, same-view comparison is not complete.
- Phase 1 capture and Phase 3 dashboard/review are team/system context, not my individually completed products.
- No model is current, `FINAL`, `PRODUCTION`, or production-ready because of a folder name.
- Historical validation and one-time test metrics are not a current final score and must not be mixed with operating-point candidates.
- The relabel working copy is not canonical Dataset v3; folder names are not provenance.
- Test-suite success is not model-accuracy evidence.
- Phase 05S-A3 is not authorized or complete.

## Demo / Presentation Assets

Git contains the [demo-package guide](../../demo/README_demo.md), source code, tests, and technical documentation. The Drive audit selected no evidence-safe active deck, overview, or demo for public use. Large videos, screenshots, decks, private data, model weights, and generated outputs remain in managed Drive storage with their identity and disposition recorded in the [Drive Migration Manifest](../02_workflow/DRIVE_MIGRATION_MANIFEST.md); archived or team-context assets are not promoted into individual claims.

## Current Technical Boundary

- Technical phase: `Phase 05S-A2`
- Technical development: `PAUSED`
- A3 authorized: `false`
- Frozen Test access: `false`
