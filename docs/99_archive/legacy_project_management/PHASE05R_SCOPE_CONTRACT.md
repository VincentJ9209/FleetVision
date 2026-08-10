# FleetVision Phase 05R Scope Contract

<!-- FLEETVISION-MANAGED:PHASE05R-SCOPE-CONTRACT:BEGIN -->
- Contract ID：`PHASE05R_SCOPE_CONTRACT`
- Decision date：`2026-07-18`
- Approval basis：`PHASE_05R_00A_GOVERNANCE_ALIGNMENT_DECISION`
- Effective condition：the commit containing this contract is pushed and
  local HEAD = `origin/main` = GitHub remote `main`
- Repository mutation represented by this document：governance Markdown only
- Commit／push authorization：separate explicit authorization required

## 1. Unique outcome

Phase 05R must produce one YOLO Detect, single-class `damage` model that:

1. passes a validation quality Gate fixed before Frozen Test access;
2. receives one honest Frozen Test evaluation;
3. replaces the existing CLI／API model reference only if all recovery Gates pass.

Passing Phase 05R does not authorize automated liability, insurance-claim or
payment decisions.

## 2. Controlled recovery sequence

1. `PHASE_05R_00_STARTUP_RECONCILIATION`
2. `PHASE_05R_00A_GOVERNANCE_ALIGNMENT_DECISION`
3. `PHASE_05R_00B_REPOSITORY_GOVERNANCE_PROPOSAL_PREPARATION`
4. `PHASE_05R_00C_LOCAL_GOVERNANCE_APPLICATION_AND_VERIFICATION`
5. `PHASE_05R_00D_GOVERNANCE_COMMIT_PUSH_REMOTE_VERIFICATION`
6. `PHASE_05R_01_DATASET_LABEL_QUALITY_AUDIT`
7. `PHASE_05R_02_BASELINE_FP_FN_ERROR_ANALYSIS`
8. `PHASE_05R_03_HARD_NEGATIVE_AND_ANNOTATION_CORRECTION_REVIEW`
9. `PHASE_05R_04_VERSIONED_DATASET_V2`
10. `PHASE_05R_05_CANDIDATE_03_TO_05_TRAINING`
11. `PHASE_05R_06_VALIDATION_QUALITY_GATE`
12. `PHASE_05R_07_SINGLE_MODEL_FROZEN_TEST`
13. `PHASE_05R_08_CLI_API_MODEL_REPLACEMENT_IF_PASSED`

`00C` is intentionally separated from `00D`: local file application is not
repository-canonical until commit, push and remote verification complete.

## 3. Controlled identities

### Internal grouped dataset v1

- Total images：195
- Train／Valid／Test：137／29／29
- Positive／Null：100／95
- Bounding boxes：159
- Vehicle groups：57
- Cross-split groups：0
- External frozen overlap：0
- ZIP SHA256：`B72812D97E08B312EBC239ADB43C7DE7DED29FB1B3098CD3BEA17C880813C58A`

### Recovery baseline

- Canonical recovery name：`baseline_candidate_01`
- Historical Drive path：
  `/content/drive/MyDrive/AI_Class/00.Project/FleetVision/models/final_selected/weights/best.pt`
- SHA256：`605FFAC6B1AA39A2E9F13BA09456943529B2788B7FCBEEACE43A3616D1C41C89`
- Classification：`BEST_AVAILABLE_POC_ONLY`
- Production quality Gate：`FAILED`

### Recovery Notebook

- Drive path：
  `/content/drive/MyDrive/AI_Class/00.Project/FleetVision/notebooks/FleetVision_Phase05_Model_Recovery.ipynb`
- Reconciled empty Notebook SHA256：`2086D3EA155748EF61E0751CAC796739CD9E5F4624744D2C0DCA726D67146CCF`
- First execution Cell：prohibited before `PHASE_05R_00D` passes

## 4. Allowed scope

- Read-only dataset, label, split, group, duplicate and leakage diagnostics.
- Train／validation-only baseline FP／FN analysis.
- Evidence-backed hard-negative and annotation-correction review packages.
- Reviewed correction proposals before any canonical mutation.
- Controlled promotion outside immutable raw sources.
- One lineage-complete Dataset v2.
- First-round Candidate 03, 04 and 05 only.
- Validation-only candidate selection and threshold determination.
- One Frozen Test run for one validation-approved candidate.
- Existing CLI／API model-reference replacement only after all model Gates pass.

## 5. Prohibited scope

- Modification of `dataset/01_raw/`.
- Delete, modify, move, stage, commit or clean
  `outputs/metadata/external_assets/`.
- Modification of the External Frozen Split.
- Frozen Test use for tuning, model selection, data prioritization or threshold adjustment.
- Segmentation or multi-class expansion without a separately approved ADR.
- Unlimited relabeling, candidate training or hyperparameter search.
- New dashboard, database, MLOps platform or large frontend work.
- Formal paired before／after change detection during this recovery round.
- Liability, responsibility or insurance-claim decisions.
- Automatic commit／push.
- Unreviewed Codex execution.

## 6. First-round limits

- Dataset version：one `fleetvision_damage_v2`.
- Candidate count：maximum three, C03–C05.
- Corrections：only cases supported by audit or human-review evidence.
- Frozen Test：one selected model, one governed evaluation.
- Validation threshold changes after Frozen Test access：prohibited.

## 7. Stop conditions

Stop and classify the Gate as blocked when any of the following occurs:

- dataset lineage cannot be verified;
- split or vehicle-group leakage is detected and unresolved;
- Frozen Test is accessed before its Gate;
- a protected or immutable asset changes without authorization;
- worktree contains unexplained changes;
- Notebook, configuration, dataset and reported evidence disagree;
- candidate variables are not controlled;
- evaluation cannot be reproduced;
- progress requires exceeding this contract.

## 8. Tool assignment

- ChatGPT：governance, Gate design, Notebook Cell design and result interpretation.
- Colab：dataset audit, FP／FN analysis, training, validation and Frozen Test.
- Codex：`CONDITIONALLY_PAUSED`; only separately authorized, small,
  repository-scoped tasks after current Gate and file allowlists are explicit.
- GitHub：long-term source of truth.

## 9. Existing Phase 04.5 relationship

`PHASE_04_5M_1_CORRECTION_REVIEW_PACKAGE_PREPARATION` is retained as an
incomplete historical Gate and deferred by the approved recovery track. It is
not retroactively marked complete or deleted. Resumption requires a separate
governance decision.
<!-- FLEETVISION-MANAGED:PHASE05R-SCOPE-CONTRACT:END -->
