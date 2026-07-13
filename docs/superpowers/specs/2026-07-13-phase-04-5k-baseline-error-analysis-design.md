# Phase 04.5K Baseline Error Analysis Design

## Purpose

Build a deterministic validation-only analysis workflow that converts the Phase 04.5J baseline into traceable threshold candidates, object-level error records, a human-review queue, and an evidence-based data-improvement order.

## Architecture

The workflow has two layers:

1. A pure Python evaluation core under `src/fleetvision/evaluation/` for IoU, deterministic one-to-one matching, threshold metrics, candidate selection, bbox-size grouping, and improvement prioritization.
2. A controlled Colab Notebook that validates the 04.5J evidence, extracts only validation data, performs one low-confidence inference pass, invokes the pure core offline, creates visual review artifacts, and packages a ZIP Log.

The local CLI replays analysis from exported prediction and GT CSV files without GPU inference.

## Safety decisions

- Validation is the only allowed split.
- Test data is not extracted or read.
- Test metrics are not used for tuning.
- Inference uses a fixed confidence floor and fixed NMS; all confidence candidates are evaluated offline from one prediction inventory.
- Detailed error analysis is generated at the balanced validation candidate.
- Candidate thresholds never imply deployment approval.
- Outputs are staged and promoted atomically by the CLI.

## Matching rules

- Predictions are sorted by confidence descending, then deterministic ID.
- A prediction can match one currently-unmatched GT box of the same class.
- TP requires IoU at or above 0.50.
- A second prediction overlapping an already matched GT at or above 0.50 is `duplicate_prediction`.
- An unmatched prediction with IoU from 0.10 to below 0.50 is `localization_error`.
- Remaining unmatched predictions are `background_false_positive`.
- Unmatched GT with a raw prediction at IoU 0.50 or above but below the active confidence threshold is `low_confidence_miss`.
- Other partial overlaps are `localization_miss`; otherwise `no_detection`.

## Operating points

- High recall: best precision among thresholds retaining at least 95% of maximum observed recall.
- Balanced: maximum F1, then precision, recall, and threshold as deterministic tie-breakers.
- High precision: best recall among thresholds retaining at least 95% of maximum observed precision.

All three rows carry status `VALIDATION_THRESHOLD_CANDIDATE`.

## Verification

Synthetic tests cover IoU, one-to-one matching, duplicate handling, localization errors, low-confidence misses, operating-point selection, bbox grouping, configuration fail-closed behavior, CLI output promotion, count mismatch rejection, notebook safety strings, and Python syntax for every Notebook code cell.
