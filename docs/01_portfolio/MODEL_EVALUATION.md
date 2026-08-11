# Model Evaluation

## Detection Contract

The first model contract is YOLOv8 Detect with one bounding-box class: `damage`. `minor_damage` and `claimable_damage` are not YOLO classes. The evaluation surface does not make severity, claimability, liability, pricing, or legal decisions.

## Registry and Model Status

The [Model Registry](../02_workflow/MODEL_REGISTRY.md) classifies `MDL-045J-Y8S-BASELINE` as `VERIFIED_HISTORICAL_BASELINE`, not as a current or final model. `MDL-05R-C01-POC`, including the artifact stored under a folder named `final_selected`, is only `BEST_AVAILABLE_POC_ONLY`; its own selection record says `quality_gate_pass=false`. `CURRENT_REFERENCE_MODEL = NONE`.

All quantitative model claims in this portfolio come only from the [Results Registry](../02_workflow/RESULTS_REGISTRY.md). That registry identifies the metric dataset as the Phase 04.5J controlled dataset; the portfolio does not rename it to `DS-INT-V1` or infer dataset identity from a later folder name.

## Historical Controlled Baseline

### Training-Selected Validation Metrics

These values are the historical validation summary at the training-selected best epoch. They are not validation operating-point candidates and are not deployment results.

| Result ID | Metric | Value |
|---|---|---:|
| `RES-045J-VAL-P` | Precision | `0.4868` |
| `RES-045J-VAL-R` | Recall | `0.3508` |
| `RES-045J-VAL-MAP50` | mAP50 | `0.3516` |
| `RES-045J-VAL-MAP5095` | mAP50-95 | `0.1620` |

### Historical One-Time Test

These values come from one governed historical test evaluation. They are reporting evidence only and are unavailable for threshold tuning, candidate selection, error prioritization, or data-improvement decisions.

| Result ID | Metric | Value |
|---|---|---:|
| `RES-045J-TEST-P` | Precision | `0.5423` |
| `RES-045J-TEST-R` | Recall | `0.3883` |
| `RES-045J-TEST-MAP50` | mAP50 | `0.3804` |
| `RES-045J-TEST-MAP5095` | mAP50-95 | `0.1756` |

The validation and historical test rows describe separate splits of the same historical controlled baseline. They must not be merged into a synthetic `final score`.

## Validation Operating-Point Analysis

Operating-point analysis is a separate validation-only artifact. The registered candidates use IoU `0.5` and are not training metrics or approved deployment thresholds.

| Result ID | Analysis profile | Confidence candidate | Boundary |
|---|---|---:|---|
| `RES-045K-OP-HIGH-RECALL` | High recall | `0.05` | Validation analysis only |
| `RES-045K-OP-BALANCED` | Balanced | `0.20` | Validation analysis only |
| `RES-045K-OP-HIGH-PRECISION` | High precision | `0.80` | Validation analysis only |

## IoU-Based Matching

Evaluation uses Intersection over Union (IoU) to relate predicted and reference boxes. [`baseline_error_analysis.py`](../../src/fleetvision/evaluation/baseline_error_analysis.py) provides one-to-one matching so that a prediction or ground-truth box is not credited multiple times. A focused IoU utility also exists in [`compare_damage.py`](../../src/fleetvision/vision/compare_damage.py); that utility does not constitute a completed before/after comparison system.

## FP/FN Taxonomy

The analysis converts model outcomes into reviewable categories, including false positives, false negatives, localization/matching evidence, photo and quality context, and prioritized error groups. These records support diagnosis and worklist creation rather than an unsupported deployment claim.

## Human-Review Feedback Loop

Error-analysis outputs feed Streamlit/SQLite review workflows where a human can confirm context, severity/scope metadata, or annotation-correction proposals. Transactional state, audit events, backups, validation, and controlled export preserve the relationship between model evidence and reviewer decisions.

## Test-Use Boundary

- Frozen Test access is not authorized during portfolio maintenance.
- Historical test results are one-time reporting evidence and are not available for tuning.
- Software tests verify code contracts, not model accuracy.
- No weight is accepted as `FINAL` or `PRODUCTION` based on a filename or folder name.
- No result supports production SaaS readiness, automated insurance adjudication, reliable true-new-damage detection, or a completed before/after workflow.

Current claims and their evidence mapping are summarized in [Results and Limitations](RESULTS_AND_LIMITATIONS.md).
