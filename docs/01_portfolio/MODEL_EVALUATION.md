# Model Evaluation

## Detection Contract

The first model contract is YOLOv8 Detect with one bounding-box class: `damage`. `minor_damage` and `claimable_damage` are not YOLO classes. The current evaluation surface does not make severity, claimability, liability, pricing, or legal decisions.

## IoU-Based Matching

Evaluation uses Intersection over Union (IoU) to relate predicted and reference boxes. [`baseline_error_analysis.py`](../../src/fleetvision/evaluation/baseline_error_analysis.py) provides one-to-one matching so that a prediction or ground-truth box is not credited multiple times. A focused IoU utility also exists in [`compare_damage.py`](../../src/fleetvision/vision/compare_damage.py); that utility does not constitute a completed before/after comparison system.

## Validation-Only Threshold Analysis

Confidence and IoU operating-point analysis is restricted to validation evidence. Sweeps are used to understand trade-offs and produce an explicit recommendation record—not to tune against Frozen Test or combine incompatible experiments into an apparent final result.

## FP/FN Taxonomy

The analysis converts model outcomes into reviewable categories, including false positives, false negatives, localization/matching evidence, photo and quality context, and prioritized error groups. These records support diagnosis and worklist creation rather than an unsupported deployment claim.

## Human-Review Feedback Loop

Error-analysis outputs feed Streamlit/SQLite review workflows where a human can confirm context, severity/scope metadata, or annotation-correction proposals. Transactional state, audit events, backups, validation, and controlled export preserve the relationship between model evidence and reviewer decisions.

## Test-Use Boundary

- Frozen Test access is not authorized during portfolio maintenance.
- Historical test results are one-time historical evidence and are not available for threshold tuning.
- Software tests verify code contracts, not model accuracy.
- No weight is accepted as `FINAL` or `PRODUCTION` based on a filename or `final_selected` folder.
- Model, dataset, and metric identities will be reconciled in later approved maintenance tasks before quantitative portfolio claims are finalized.

Current results and boundaries are summarized in [Results and Limitations](RESULTS_AND_LIMITATIONS.md).
