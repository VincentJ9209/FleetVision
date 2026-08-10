# FleetVision Notebooks

This directory contains small, tracked notebook evidence. Notebooks are not primary production logic and are not authorization to execute historical training or inference workflows.

## Current Operating Boundary

- Technical phase: `Phase 05S-A2`
- Technical development: `PAUSED`
- Current activity: `PORTFOLIO_MAINTENANCE`
- Phase 03.5 inference: `FROZEN`
- Training/fine-tuning authorized: `false`
- Model inference authorized: `false`
- Frozen Test access authorized: `false`

Historical notebooks may document prior work, but they must not be rerun merely because the file remains available. Any future execution requires the applicable Gate, current configuration and data identity, protected-asset reconciliation, and a new verification plan.

## Active Tracked Evidence

| Notebook | Purpose | Evidence Status | Dataset Dependency | GPU | Safe to Run in Phase 05S-A2 | Large Outputs |
|---|---|---|---|---|---|---|
| [`FleetVision_04_5K_Validation_Error_Analysis_8_4_93.ipynb`](FleetVision_04_5K_Validation_Error_Analysis_8_4_93.ipynb) | Historical validation-only IoU matching, threshold analysis, FP/FN taxonomy, and improvement prioritization. | `HISTORICAL_EVIDENCE`; output-stripped tracked contract, not a current metric source. | Historical Phase 04.5J validation prediction/ground-truth artifacts and tracked [`baseline_error_analysis_config.yaml`](../configs/modeling/baseline_error_analysis_config.yaml). Private artifacts are not in Git. | No GPU required for the analysis logic. | **No.** Inputs and provenance must be reconciled first; Frozen Test remains unavailable. | Direct historical notebook evidence is archived in Drive under `FleetVision/99_ARCHIVE/04_old_experiments/`; mixed runs remain `NOT_MOVED`. |
| [`phase03_5_auto_review_prelabeller.ipynb`](phase03_5_auto_review_prelabeller.ipynb) | Historical CLIP-assisted `photo_type` suggestion workflow. | `HISTORICAL_EVIDENCE_FROZEN`; output-stripped and never an automated damage/severity decision. | Historical reviewed metadata/image inputs plus the approved Phase 03.5 model/configuration contract. Private images and model artifacts are not in Git. | GPU was useful for the historical workflow but does not authorize execution. | **No.** Phase 03.5 inference is frozen and may not be rerun without a formal decision and complete rerun plan. | Historical Phase 03.5 outputs remain inside the old Drive `outputs/` tree, `NOT_MOVED/RECONCILE_REQUIRED`. |

Both tracked notebooks were statically verified as notebook JSON with `0` embedded outputs, `0` executed cells, `0` secret-literal matches, and `0` credential-file/private-key references. This is a structural safety check, not proof that historical data or model dependencies are currently executable.

## Drive Notebook Classification

The Task 7 inventory is authoritative in [`DRIVE_MIGRATION_MANIFEST.md`](../docs/02_workflow/DRIVE_MIGRATION_MANIFEST.md). Summary:

- Active Drive-hosted notebooks selected: `0`.
- Deprecated/recovery notebooks archived under `FleetVision/99_ARCHIVE/01_deprecated_notebooks/`: `8` identities.
- Historical training/evaluation notebooks moved individually from `04_5J/` to `FleetVision/99_ARCHIVE/04_old_experiments/`: `2` identities; the mixed parent container remains `NOT_MOVED`.
- Unresolved same-title rapid-training notebook moved to `FleetVision/99_ARCHIVE/06_duplicate_candidates/`: `1` identity; no duplicate or deletion conclusion was made.
- Output-rich or size-bounded Drive variants were not promoted to active evidence.

No notebook was executed, trained, fine-tuned, or used for inference during classification. No Drive file was renamed, copied, uploaded, shared, replaced, trashed, or deleted.

## Resume Rules

1. Read [`START_HERE.md`](../START_HERE.md) and the current workflow state before any notebook work.
2. Treat Drive notebooks as historical evidence unless a later registry explicitly changes their status.
3. Do not use historical notebook outputs as current model, dataset, or metric provenance.
4. Do not access Frozen Test data or results for tuning.
5. Keep large outputs in governed Drive locations and durable identities in the migration manifest.
