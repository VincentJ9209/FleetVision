# Phase 04.5K — Baseline Error Analysis

## 1. Gate objective

Phase 04.5K performs validation-only error analysis for the approved YOLOv8s single-class `damage` baseline. It does not retrain the model and does not use the test set for threshold selection.

Target classification:

`VALIDATION_ERROR_ANALYSIS_AND_THRESHOLD_CANDIDATES_COMPLETED`

## 2. Fixed inputs

- Model: YOLOv8s Detect
- Class: `damage`
- Weight: Phase 04.5J `best.pt`
- Expected weight SHA256: `90A880513A42EF2DB1373902D98FF09D1756AB7A8A4EEA6A7AA231D4020B77BF`
- Allowed split: `valid`
- Expected validation images: 168
- Expected validation annotations: 325
- Ultralytics: 8.4.93

## 3. Safety boundary

- Do not call training or fine-tuning APIs.
- Do not extract, read, or tune against test images or labels.
- Do not change canonical COCO, `dataset/01_raw`, Registry, the formal YOLO dataset, or annotations.
- Do not approve deployment.
- Treat all selected thresholds as `VALIDATION_THRESHOLD_CANDIDATE` only.

## 4. Analysis method

1. Verify the Phase 04.5J gate result and `best.pt` SHA256.
2. Verify the original 04.5J dataset TAR and manifest.
3. Extract only `dataset/05_yolo/images/valid/` and `dataset/05_yolo/labels/valid/`.
4. Run one validation inference pass at confidence floor 0.001 with fixed NMS IoU 0.70.
5. Perform the configured confidence sweep offline.
6. Match predictions to GT one-to-one at IoU 0.50.
7. Classify duplicate predictions, localization errors, background false positives, low-confidence misses, localization misses, and no-detection misses.
8. Select high-recall, balanced, and high-precision validation candidates.
9. Produce a human-review worklist, representative overlays, and data-improvement priorities.

## 5. Outputs

The Colab run writes an isolated session under the sibling Google Drive folder `04_5K/runs/`:

- `metrics/validation_threshold_sweep.csv`
- `metrics/validation_operating_points.csv`
- `metrics/validation_error_summary.csv`
- `metrics/validation_error_by_bbox_size.csv`
- `metrics/validation_threshold_sweep.png`
- `records/validation_predictions.csv`
- `records/validation_ground_truth.csv`
- `records/validation_matches.csv`
- `records/validation_error_cases.csv`
- `review/validation_error_review_worklist.csv`
- `review/overlays/`
- `reports/baseline_error_analysis.md`
- `reports/data_improvement_priorities.csv`
- `manifest/phase_04_5k_artifact_manifest.csv`
- `manifest/phase_04_5k_checksums.sha256`
- `04_5K_gate_result.json`
- `04_5K_*_ZIP_LOG.zip`

## 6. Execution

Open `notebooks/FleetVision_04_5K_Validation_Error_Analysis_8_4_93.ipynb` in Colab and execute Cell 1 through Cell 8 in order. Each cell must print its own `PASS` marker before the next cell is executed.

Return only the final 04.5K ZIP Log for external Gate review. Model weights remain in Google Drive and are never included in the ZIP.
