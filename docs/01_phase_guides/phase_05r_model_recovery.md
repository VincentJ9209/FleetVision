# FleetVision Phase 05R — Model Recovery Guide

<!-- FLEETVISION-MANAGED:PHASE05R-GUIDE:BEGIN -->
## Purpose

Recover model quality by diagnosing dataset and annotation weaknesses before
additional training. Preserve prior FleetVision governance and treat the
three-day model as a baseline PoC, not a production-quality final model.

## Entry contract

Read in order:

1. `docs/00_project_management/START_HERE.md`
2. `docs/00_project_management/PROJECT_STATUS.md`
3. `docs/00_project_management/HANDOFF_CURRENT.md`
4. `docs/00_project_management/PHASE05R_SCOPE_CONTRACT.md`
5. this guide;
6. `docs/02_prompts/PHASE_05R_NOTEBOOK_RULES.md`;
7. `docs/00_project_management/phase_logs/PHASE_05R_LOG.md`.

No Colab Cell may execute until the governance activation commit is pushed and
remote verified.

## Baseline facts

- Dataset v1：195 images；137／29／29；100 positive；95 null；159 boxes；57 groups.
- Dataset ZIP SHA256：`B72812D97E08B312EBC239ADB43C7DE7DED29FB1B3098CD3BEA17C880813C58A`.
- Baseline model SHA256：`605FFAC6B1AA39A2E9F13BA09456943529B2788B7FCBEEACE43A3616D1C41C89`.
- Frozen Test baseline：
  Precision 0.015667；Recall 0.083333；F1 0.026375；
  mAP50 0.001638；mAP50-95 0.000166.
- Baseline classification：`BEST_AVAILABLE_POC_ONLY`.
- CLI／API：technical demo shell; model quality not accepted.

## Gate table

| Gate | Purpose | Mutation／training boundary | Required exit |
|---|---|---|---|
| 05R-00 | Git／Drive／Notebook／Dataset／model reconciliation | read-only | `PHASE_05R_00_RECONCILIATION_VERIFIED` |
| 05R-00A | approve governance alignment | external decision only | governance proposal authorized |
| 05R-00B | prepare exact repository proposal | read-only repository snapshot | proposal package verified |
| 05R-00C | apply and verify governance files locally | governance Markdown only; no stage／commit | exact diff verified |
| 05R-00D | exact commit, push and remote verification | explicit authorization required | heads aligned |
| 05R-01 | dataset and label quality audit | train／valid read-only; no Test | diagnosis verified |
| 05R-02 | baseline FP／FN error analysis | validation only; inference cache allowed | worklist verified |
| 05R-03 | hard-negative and correction review | proposals first; no direct canonical edit | reviewed corrections approved |
| 05R-04 | build versioned Dataset v2 | raw and Frozen Test immutable | lineage and splits accepted |
| 05R-05 | Candidate C03–C05 training | one candidate per Cell; max three | experiment manifests complete |
| 05R-06 | validation quality Gate | validation only | one candidate selected or recovery loop |
| 05R-07 | single-model Frozen Test | one governed evaluation only | immutable test summary |
| 05R-08 | CLI／API replacement | only after model acceptance | reintegration verified |

## Notebook Cell groups

- `R0`：environment, paths and active governance contract.
- `R1`：dataset／label audit; Test not mounted or read.
- `R2`：baseline validation FP／FN and hard-negative diagnosis.
- `R3`：reviewed corrections, promotion evidence and Dataset v2.
- `R4`：Candidate C03–C05 training.
- `R5`：validation quality Gate and selected-candidate manifest.
- `R6`：single-model Frozen Test.
- `R7`：CLI／API reintegration verification.

Every response supplies one complete Cell only. Use fixed Cell IDs and exact
insertion or full-replacement instructions.

## Dataset audit requirements

05R-01 must produce evidence for:

- image and label readability;
- YOLO schema and class ID validity;
- normalized bbox width, height, area and edge distributions;
- empty labels, missing pairs and orphan files;
- source, angle, positive／negative and vehicle-group distribution;
- exact and perceptual duplicate risks;
- split and group leakage;
- train／validation only visual audit sample;
- issues classified by severity and recommended next Gate.

The Frozen Test directory must not be traversed, inventoried for improvement
decisions, visualized or used in any audit summary.

## Baseline error-analysis requirements

05R-02 uses validation material only and must record:

- model SHA256 and inference configuration;
- matching rule and IoU threshold;
- image-level hit／miss and box-level FP／FN;
- negative-image false positives;
- localization, scale, glare, occlusion and background patterns;
- evidence-backed hard-negative and correction worklists;
- immutable output manifest and SHA256.

## Dataset v2 requirements

`fleetvision_damage_v2` must:

- leave raw sources unchanged;
- exclude Frozen Test feedback;
- preserve vehicle-group split isolation;
- record every included image and label lineage;
- record each correction decision and reviewer evidence;
- contain deterministic manifests and checksums;
- pass an independent pre-training validator.

## Candidate controls

First round:

- C03：Dataset v2 baseline.
- C04：Dataset v2 plus approved hard negatives.
- C05：Dataset v2 plus one predeclared resolution or tiling change.

Each candidate must isolate outputs and record model, dataset version, image
size, epochs, seed, augmentation, software versions and weights SHA256.
Do not change multiple uncontrolled variables in the same comparison.

## Validation quality Gate

Initial development thresholds:

- Precision ≥ 0.60
- Recall ≥ 0.50
- mAP50 ≥ 0.50
- Negative-image FP < 0.5 box／image
- Positive-image hit rate ≥ 0.70
- Negative-image correct rate ≥ 0.80

05R-01／02 may refine metric definitions before training, but must not loosen
thresholds based on Frozen Test results. Thresholds become locked before
Candidate selection.

## Frozen Test contract

- Access only after one candidate passes 05R-06.
- Evaluate one selected candidate once.
- Do not use results to retune threshold, select another candidate or reprioritize data.
- Preserve summary, configuration, selected-model SHA256 and access evidence.
- A failed Frozen Test blocks model replacement and returns work to a new
  separately approved recovery iteration.

## Completion boundary

Passing structural CLI／API tests does not imply model quality acceptance.
Production or no-human-review claims remain prohibited.
<!-- FLEETVISION-MANAGED:PHASE05R-GUIDE:END -->
