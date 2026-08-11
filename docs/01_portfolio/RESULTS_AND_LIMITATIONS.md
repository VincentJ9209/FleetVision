# Results and Limitations

## Claim-to-Evidence Reconciliation

| Claim area | Evidence source | Reconciled claim | Boundary |
|---|---|---|---|
| Phase 2 software and workflow | [`src/fleetvision/`](../../src/fleetvision/), [`scripts/`](../../scripts/), [`configs/`](../../configs/), and [`tests/`](../../tests/) | Data governance, human-review support, and validation error-analysis contracts are repository-backed. | Software behavior is not model accuracy or deployment evidence. |
| Primary contribution | [Project Overview](PROJECT_OVERVIEW.md) and Task 6 classifications in the [Drive Migration Manifest](../02_workflow/DRIVE_MIGRATION_MANIFEST.md) | Phase 2 data governance and model evaluation are the primary individual contribution. | Phase 1 capture and Phase 3 dashboard/review remain team/system context, except for repository-backed Phase 2 review components. |
| Quantitative model results | [`RESULTS_REGISTRY.md`](../02_workflow/RESULTS_REGISTRY.md) | Only the registered Phase 04.5J historical controlled-baseline rows are published. | No cross-experiment metric stitching and no synthetic `final score`. |
| Model status | [`MODEL_REGISTRY.md`](../02_workflow/MODEL_REGISTRY.md) | `CURRENT_REFERENCE_MODEL = NONE`; the strongest verified model is historical, and the folder-named selection is PoC-only. | No current, final, production, or deployment-ready model claim. |
| Dataset identity | [`DATASET_REGISTRY.md`](../02_workflow/DATASET_REGISTRY.md) | `DS-INT-V1` is a protected historical baseline; `DS-RELABEL-V3-WORKING` is `NOT_CANONICAL`. | Folder names and unresolved exports are not provenance. |
| Technical status | [`PROJECT_STATUS.md`](../02_workflow/PROJECT_STATUS.md) and [`HANDOFF_CURRENT.md`](../02_workflow/HANDOFF_CURRENT.md) | Technical phase is `Phase 05S-A2`; development is `PAUSED`; A3 and Frozen Test access are unauthorized. | Portfolio maintenance does not advance a technical Gate. |
| Demo and presentation assets | Task 6 in the [Drive Migration Manifest](../02_workflow/DRIVE_MIGRATION_MANIFEST.md) | No evidence-safe active deck, overview, or demo is selected for public use. | Archived/team assets are not upgraded into individual claims. |

## Repository-Backed Software Results

| Evidence | Supported claim |
|---|---|
| [`build_metadata.py`](../../src/fleetvision/data/build_metadata.py) and [`build_review_queue.py`](../../src/fleetvision/data/build_review_queue.py) | Deterministic metadata and review-work generation are implemented and tested. |
| [`intake_external_dataset.py`](../../src/fleetvision/data/intake_external_dataset.py) | Archive identity, safe extraction, COCO validation, staged promotion, and failure controls are implemented. |
| [`audit_external_dataset_deduplication.py`](../../src/fleetvision/data/audit_external_dataset_deduplication.py) plus canonicalization/QA modules under [`src/fleetvision/data/`](../../src/fleetvision/data/) | Exact/perceptual duplicate auditing, category normalization, bounding-box repair, and split QA are implemented. |
| Review modules under [`src/fleetvision/review/`](../../src/fleetvision/review/) | Resumable transactional review state, audit events, backups, validation, and controlled exports are implemented. |
| [`baseline_error_analysis.py`](../../src/fleetvision/evaluation/baseline_error_analysis.py) | One-to-one IoU matching, validation-only analysis, FP/FN taxonomy, and improvement worklists are implemented. |

These are software and workflow results. They do not establish production readiness, reliable true-new-damage detection, or performance on newly accessed Frozen Test data.

## Historical Controlled-Baseline Metrics

All model numbers in this section map directly to rows in [`RESULTS_REGISTRY.md`](../02_workflow/RESULTS_REGISTRY.md) for `MDL-045J-Y8S-BASELINE`.

### Training-Selected Validation Summary

| Result ID | Metric | Value |
|---|---|---:|
| `RES-045J-VAL-P` | Precision | `0.4868` |
| `RES-045J-VAL-R` | Recall | `0.3508` |
| `RES-045J-VAL-MAP50` | mAP50 | `0.3516` |
| `RES-045J-VAL-MAP5095` | mAP50-95 | `0.1620` |

### Historical One-Time Test

| Result ID | Metric | Value |
|---|---|---:|
| `RES-045J-TEST-P` | Precision | `0.5423` |
| `RES-045J-TEST-R` | Recall | `0.3883` |
| `RES-045J-TEST-MAP50` | mAP50 | `0.3804` |
| `RES-045J-TEST-MAP5095` | mAP50-95 | `0.1756` |

The historical test row is reporting evidence only and is unavailable for tuning, model selection, error prioritization, or data-improvement decisions. It is not combined with the validation summary into a final score.

### Separate Validation Operating-Point Candidates

| Result ID | Profile | Confidence candidate | IoU | Interpretation |
|---|---|---:|---:|---|
| `RES-045K-OP-HIGH-RECALL` | High recall | `0.05` | `0.5` | Validation analysis candidate only |
| `RES-045K-OP-BALANCED` | Balanced | `0.20` | `0.5` | Validation analysis candidate only |
| `RES-045K-OP-HIGH-PRECISION` | High precision | `0.80` | `0.5` | Validation analysis candidate only |

These operating points are not training metrics and are not approved deployment thresholds.

## Model and Dataset Disposition

- `MDL-045J-Y8S-BASELINE` is a `VERIFIED_HISTORICAL_BASELINE`, not a current reference.
- `MDL-05R-C01-POC` is `BEST_AVAILABLE_POC_ONLY`; `quality_gate_pass=false`. The name `final_selected` does not make it final.
- `CURRENT_REFERENCE_MODEL = NONE`; no production-ready final model has been accepted.
- `DS-INT-V1` is a protected historical baseline, not a newly promoted current canonical dataset.
- `DS-RELABEL-V3-WORKING` is a `WORKING_COPY` with `NOT_CANONICAL` status and must not be called canonical Dataset v3.
- `DS-GROUPED-LEGACY` and `DS-YOLO-LABELS-ZIP` remain unresolved and are not active training/evaluation datasets.

## Limitations

- **No production deployment:** FleetVision is a governed engineering and research portfolio, not a deployed SaaS product.
- **No automated adjudication:** visible damage evidence does not determine insurance claimability, liability, price, legal outcome, or final business action.
- **No reliable true-new-damage claim:** sufficient paired validation does not exist to support that claim.
- **Incomplete before/after comparison:** same-vehicle, same-view pairing and comparison are not complete.
- **No production-ready final model:** the current-reference area is intentionally empty; historical and PoC artifacts retain their registry labels.
- **Private artifacts remain external:** private datasets, model weights, source archives, videos, presentations, and generated packages are not distributed in Git.
- **Training and inference are not complete products:** tracked builders, configurations, and historical evidence do not equal a current production service.
- **Frozen Test is protected:** access is `false`; it is unavailable for tuning or further use without a separate explicit Gate.
- **Phase 1/3 ownership is bounded:** capture and dashboard/review are team/system context; the primary individual contribution is the repository-backed Phase 2 workflow.
- **Phase 05S-A3 is unauthorized:** portfolio maintenance does not authorize or complete A3 implementation.

## Current Interpretation

The strongest portfolio evidence is the safety-oriented Phase 2 pipeline: traceable inputs, auditable human decisions, deterministic processing, protected evaluation boundaries, and tests for failure behavior. Published quantitative claims are limited to the separately labelled historical registry rows above. Current technical state remains `Phase 05S-A2`, technical development remains `PAUSED`, `A3 authorized = false`, and `Frozen Test access = false`.
