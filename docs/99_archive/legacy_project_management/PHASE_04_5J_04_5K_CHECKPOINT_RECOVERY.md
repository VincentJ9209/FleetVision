# Phase 04.5J–04.5K Checkpoint Recovery

## Reason

At repository checkpoint `0fa698a21be5fcc737fe4b000364cdccd743ec5f`, tracked governance documents still describe an earlier Phase 04.5F state. Later controlled Gates were executed without a corresponding Git documentation checkpoint. This note records the evidence-based recovery boundary before Phase 04.5K repository integration.

## Recovered Phase 04.5J checkpoint

- Gate: `04.5J`
- Outcome: `PASS`
- Classification: `CONTROLLED_COLAB_BASELINE_TRAINING_COMPLETED`
- Final ZIP: `04_5J_20260713_082857_6c719a70_ZIP_LOG.zip`
- ZIP SHA256: `98F0A04301FD08862941CB9033E23A932929F646494EE5917CD043DE3A815CEB`
- Model: YOLOv8s Detect, single class `damage`
- Training: 33 epochs, best epoch 13, early stopping
- Validation best: P 0.4868 / R 0.3508 / mAP50 0.3516 / mAP50-95 0.1620
- Test: P 0.5423 / R 0.3883 / mAP50 0.3804 / mAP50-95 0.1756
- `best.pt` SHA256: `90A880513A42EF2DB1373902D98FF09D1756AB7A8A4EEA6A7AA231D4020B77BF`
- `last.pt` SHA256: `9D97A7053CA4400F45E9365C3FB9BFBE3EFFF20E6F3D37A403EC505186B386AC`
- Deployment acceptance: `NOT_YET_APPROVED`

## Evaluation policy

The test set was evaluated once during Phase 04.5J. It is now excluded from threshold tuning, error prioritization, candidate selection, and data-improvement decisions. Phase 04.5K uses the validation split only.

## Phase 04.5K authorization

Approved approach: automatic quantitative analysis plus a human-review worklist. No retraining, annotation modification, canonical data modification, Registry modification, or deployment approval is included.

Target classification:

`VALIDATION_ERROR_ANALYSIS_AND_THRESHOLD_CANDIDATES_COMPLETED`

## Git boundary

This recovery note and the Phase 04.5K implementation may be added to the repository, but commit and push require a separate explicit authorization and fresh verification evidence.
