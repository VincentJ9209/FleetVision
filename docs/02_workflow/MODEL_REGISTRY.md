# FleetVision Model Registry

## Registry Boundary

- Registry checkpoint: Task 8 `PORTFOLIO_MAINTENANCE`; technical development remains `PAUSED` at Phase 05S-A2.
- Allowed quality labels: `VERIFIED_HISTORICAL_BASELINE`, `BEST_AVAILABLE_POC_ONLY`, `EXPERIMENTAL`, `UNRESOLVED_IDENTITY`.
- `FINAL` and `PRODUCTION` are prohibited. A Drive folder name is not acceptance evidence.
- Model and weight bytes were not downloaded, opened, executed, or hashed. SHA256 values below come only from repository evidence or bounded non-sensitive Drive selection manifests.
- Provider checksum metadata was requested for every weight, but the connector exposed no checksum field. `UNKNOWN/UNRESOLVED` therefore means no independently usable checksum was available without reading model bytes.
- `FleetVision/02_MODELS/01_current/` (Drive ID `18aS9iKTDBUlV3ivsWlzw15nU4SKSK7LV`) remains empty because no artifact meets a current-reference or production acceptance standard.
- `outputs/day1_test_evaluation/` (Drive ID `1FkqqIsz-wGs2iol0EG2mI7rtIByrYh--`) was not listed, fetched, read, or hashed. Historical test statements below come only from already-tracked repository governance.

## Registered Models

| Model ID | Artifact | SHA256 / Identity | Training Dataset | Experiment | Validation Evidence | Test Evidence | Quality Status | Allowed Portfolio Claim |
|---|---|---|---|---|---|---|---|---|
| `MDL-045J-Y8S-BASELINE` | Drive `04_5J/runs/FleetVision_04_5J_20260713_135656_d656e8c2/.../training/baseline/weights/best.pt` (ID `1mr2DwMMH9jP96uq2OAHM17ukflWCU-ty`) | Repository-recorded SHA256 `90A880513A42EF2DB1373902D98FF09D1756AB7A8A4EEA6A7AA231D4020B77BF` | Phase 04.5J controlled dataset; an exact Task 8 dataset-registry ID is not yet available | YOLOv8s Detect, single class `damage`; 33 epochs, best epoch 13, early stopping | [Phase 04.5J–04.5K checkpoint recovery](../99_archive/legacy_project_management/PHASE_04_5J_04_5K_CHECKPOINT_RECOVERY.md#recovered-phase-045j-checkpoint) | One-time historical Phase 04.5J test evaluation; prohibited for threshold tuning or model selection | `VERIFIED_HISTORICAL_BASELINE` | Historical controlled baseline only; not deployment-approved and not a current/final model |
| `MDL-05R-C01-POC` | Drive `models/candidate_01/` (ID `1UAO0tZyrC2v49cvSfw2aZw0Svve1DRT_`) and separately copied `models/final_selected/weights/best.pt` (ID `1OQRoHAE2oa2-AMns4BM398WD2bzT9zwn`) | Bounded selection record SHA256 `605FFAC6B1AA39A2E9F13BA09456943529B2788B7FCBEEACE43A3616D1C41C89`; Drive bytes not re-hashed | Internal grouped dataset v1, repository-governed identity in [Phase 05R scope contract](../99_archive/legacy_project_management/PHASE05R_SCOPE_CONTRACT.md#internal-grouped-dataset-v1) | `candidate_01`; selected at confidence `0.1`, IoU `0.5`, image size `1024`; `quality_gate_pass=false` | Bounded Drive records `final_model_selection.json` (ID `1KqY0-c7ubeI4g3CR9MruusPl3Y0fNprT`) and `validation_threshold_comparison.csv` (ID `17dHFjLM2P6-vJiWXBAQalB5crmI7AXgz`) | Task 8 did not access Frozen Test content; selection record states `test_split_used=false` | `BEST_AVAILABLE_POC_ONLY` | Historical PoC selected from two weak candidates; explicitly not production, final, or current |
| `MDL-05R-C02` | Drive `models/candidate_02/` (ID `1C1jCTh4putMmObQ1pZ5rKpiD8o6pyf2Z`) | Weight SHA256 `UNKNOWN/UNRESOLVED`; best/last metadata IDs recorded below | Historical Day-1 candidate dataset; exact lineage remains unresolved pending Task 9 | `candidate_02`; comparison record shows it was not selected | Bounded Drive `validation_threshold_comparison.csv` (ID `17dHFjLM2P6-vJiWXBAQalB5crmI7AXgz`) | No Task 8 test evidence; Frozen Test content was not accessed | `EXPERIMENTAL` | Historical experimental candidate only |
| `MDL-RDR-C01` | Drive `outputs/rapid_detection_recovery_colab/` (ID `13E6gYGUuxpbtmsg38Ipzgs61r31YAKYz`) and exported `recovery_candidate_01_colab_best.pt` (ID `1yfWqV6doTvxzwFThltYrSiZjlLV15rDZ`) | Bounded manifest selected-checkpoint SHA256 `371214ED6D28B7FF6AEB42DA8160153F39588C9BEBC77BB229A917F8649B4D1F`; Drive bytes not re-hashed | `internal_grouped_dataset_v1_20260717_212356`; manifest declares train+validation only | Rapid detection recovery, smoke → head warm-up → full fine-tune → validation; `production_approved=false` | Bounded `recovery_candidate_01_colab_manifest.json` (ID `1fSztdS-8FRNfZXRLV3D2WgdWXwkf_Bek`) and `05_validation_metrics.json` (ID `1UBVIcARJIUzCeFIJq6eSTn33w9PiSO63`) | Manifest states `frozen_test_access=false` and `test_split_evaluation=false` | `EXPERIMENTAL` | Historical train/validation recovery experiment only; not accepted for deployment |
| `MDL-LEGACY-YOLOV5-CLOUD` | Drive `00.彙總發表/Cloud Function - Colab/YOLO_car_damage_detection_V5.pt` (ID `1qrMR1absDvDKWEbhGE6pV5Q3K7_f3HzB`) | SHA256 and experiment linkage `UNKNOWN/UNRESOLVED`; metadata size `19,208,858` bytes | `UNKNOWN/UNRESOLVED` | Legacy demo/model artifact retained by Task 6 | No reconciled validation evidence | No reconciled test evidence; no protected content accessed | `UNRESOLVED_IDENTITY` | Legacy artifact exists; no performance or deployment claim allowed |
| `MDL-LEGACY-CARDENT` | Drive `00.彙總發表/Cloud Function - Colab/reference/CarDentScratch.pt` (ID `137GYrPXSf38V1qmkm3BWYwSMvXVYd93V`) | SHA256 and source/license lineage `UNKNOWN/UNRESOLVED`; metadata size `23,381,341` bytes | `UNKNOWN/UNRESOLVED` | Legacy reference artifact retained by Task 6 | No reconciled validation evidence | No reconciled test evidence | `UNRESOLVED_IDENTITY` | Historical reference presence only; no FleetVision model-performance claim allowed |
| `MDL-LEGACY-YOLOV5-AUTOLABEL` | Drive `02.Auto Labeling/YOLO_car_damage_detection_V5.pt` (ID `1UrR_rtfSOAKPjOgIpSd8dIDp7BJsiErF`) | SHA256 and relationship to `MDL-LEGACY-YOLOV5-CLOUD` `UNKNOWN/UNRESOLVED`; same name/size is not identity | `UNKNOWN/UNRESOLVED` | Legacy auto-label model artifact retained by Task 6 | No reconciled validation evidence | No reconciled test evidence | `UNRESOLVED_IDENTITY` | Legacy artifact exists; duplicate or quality claims are prohibited |

## Complete Weight Artifact Inventory

`Available Checksum` records only checksums made available without reading model bytes. All timestamps are UTC.

| # | Model ID | Drive Path / Artifact | Drive ID | Size Bytes | Modified UTC | Parent ID | Available Checksum | Identity / Disposition |
|---:|---|---|---|---:|---|---|---|---|
| 1 | `MDL-045J-Y8S-BASELINE` | `04_5J/.../training/baseline/weights/best.pt` | `1mr2DwMMH9jP96uq2OAHM17ukflWCU-ty` | 22,518,186 | `2026-07-13T08:20:27.438Z` | `1jZciYdSCUgnIbjBmMrsIOv2xfePVb4U5` | Not exposed | Repository SHA verified; retained with historical run |
| 2 | `MDL-045J-Y8S-BASELINE` | `04_5J/.../training/baseline/weights/last.pt` | `178jP8FjjB5dTqXJSLJs94u_9DgZ2tSAX` | 22,518,186 | `2026-07-13T08:20:26.403Z` | `1jZciYdSCUgnIbjBmMrsIOv2xfePVb4U5` | Not exposed | Repository last-weight SHA `9D97A7053CA4400F45E9365C3FB9BFBE3EFFF20E6F3D37A403EC505186B386AC`; retained with historical run |
| 3 | `MDL-05R-C01-POC` | `models/candidate_01/weights/best.pt` | `1UkqqW3z_KWtkIgoCOtPMoHJApZ3UDPLL` | 22,490,474 | `2026-07-17T15:16:24.000Z` | `1jyRKOjtTuVLkfTknba-JKRqFJXv4njHG` | Not exposed | Candidate 01 evidence |
| 4 | `MDL-05R-C01-POC` | `models/candidate_01/weights/last.pt` | `1Oyev1CsBeBApiI_pmmOpGKfp4AxvPayM` | 22,490,474 | `2026-07-17T15:16:24.000Z` | `1jyRKOjtTuVLkfTknba-JKRqFJXv4njHG` | Not exposed | Candidate 01 training endpoint |
| 5 | `MDL-05R-C01-POC` | `models/final_selected/weights/best.pt` | `1OQRoHAE2oa2-AMns4BM398WD2bzT9zwn` | 22,490,474 | `2026-07-17T15:16:24.000Z` | `1KOKjqdfzisWAlfzEdvt8NHvTv396Z9NV` | Not exposed | Selection record maps to Candidate 01; `BEST_AVAILABLE_POC_ONLY` |
| 6 | `MDL-05R-C02` | `models/candidate_02/weights/best.pt` | `1vdEmSRNP9GeDwidPX1ueSQYBvopYc4uO` | 22,538,986 | `2026-07-17T15:34:02.000Z` | `1d1TtsiyGa0YoI4ul3eBLhil9_bUTi5Rk` | Not exposed | Experimental Candidate 02 |
| 7 | `MDL-05R-C02` | `models/candidate_02/weights/last.pt` | `1Ao70EWZBTB0ymKjYRSHPa-OnZDCEB_fD` | 22,538,986 | `2026-07-17T15:34:01.000Z` | `1d1TtsiyGa0YoI4ul3eBLhil9_bUTi5Rk` | Not exposed | Experimental Candidate 02 training endpoint |
| 8 | `MDL-RDR-C01` | `outputs/rapid_detection_recovery_colab/.../00_smoke/.../weights/best.pt` | `1Oy4Q4PPG8tcf39MhMO-F9sL66IDX4MUf` | 22,499,498 | `2026-07-19T17:28:02.000Z` | `1919-z6q6VWtmcmks9EVY_K44oPMU7zRh` | Not exposed | Smoke-run intermediate |
| 9 | `MDL-RDR-C01` | `.../00_smoke/.../weights/last.pt` | `1xOiF0_b6yDaI3lhSnHZpmv5SvVrhYDNc` | 22,499,498 | `2026-07-19T17:28:00.000Z` | `1919-z6q6VWtmcmks9EVY_K44oPMU7zRh` | Not exposed | Smoke-run endpoint |
| 10 | `MDL-RDR-C01` | `.../00_smoke/.../weights/epoch0.pt` | `1Qxrv1ZIqaLXHh6jZuNpfNF1LMhy1MLRL` | 22,523,953 | `2026-07-19T17:27:56.000Z` | `1919-z6q6VWtmcmks9EVY_K44oPMU7zRh` | Not exposed | Smoke checkpoint |
| 11 | `MDL-RDR-C01` | `.../00_smoke/.../weights/epoch1.pt` | `1et5sUVd3KWqU42Wljv9N4h7-UDSZ1dgJ` | 22,524,081 | `2026-07-19T17:27:58.000Z` | `1919-z6q6VWtmcmks9EVY_K44oPMU7zRh` | Not exposed | Smoke checkpoint |
| 12 | `MDL-RDR-C01` | `.../00_smoke/.../weights/epoch2.pt` | `11_eVftzkXDtnDFjzDXeBvMggsYEZLSA7` | 22,524,209 | `2026-07-19T17:28:00.000Z` | `1919-z6q6VWtmcmks9EVY_K44oPMU7zRh` | Not exposed | Smoke checkpoint |
| 13 | `MDL-RDR-C01` | `.../01_stage1/.../weights/best.pt` | `1enGkV3oLc2Ou94K8p0Vjd0NATk_kS6PB` | 22,489,258 | `2026-07-21T05:14:00.331Z` | `1BtapdVlti3nXecyhOCnEhkwu4wSsvrwB` | Not exposed | Stage 1 best |
| 14 | `MDL-RDR-C01` | `.../01_stage1/.../weights/last.pt` | `1Lmjb0XCnclsRcMt2n1otaLzvOZgJ-szc` | 22,489,258 | `2026-07-19T17:31:26.000Z` | `1BtapdVlti3nXecyhOCnEhkwu4wSsvrwB` | Not exposed | Stage 1 endpoint |
| 15 | `MDL-RDR-C01` | `.../01_stage1/.../weights/epoch0.pt` | `1n6e1YGbd-kNnMQd0gcjkeIBN0neLHEhy` | 22,513,329 | `2026-07-21T05:14:04.878Z` | `1BtapdVlti3nXecyhOCnEhkwu4wSsvrwB` | Not exposed | Stage 1 checkpoint |
| 16 | `MDL-RDR-C01` | `.../01_stage1/.../weights/epoch1.pt` | `11g3O4BH9ki1WP3OaNjTxVLTx71n1lH3K` | 58,937,485 | `2026-07-21T05:13:55.414Z` | `1BtapdVlti3nXecyhOCnEhkwu4wSsvrwB` | Not exposed | Stage 1 checkpoint |
| 17 | `MDL-RDR-C01` | `.../01_stage1/.../weights/epoch2.pt` | `1bMektMVbYeiXnhNzgXFchc60lgFfhb_H` | 58,937,613 | `2026-07-19T17:31:16.000Z` | `1BtapdVlti3nXecyhOCnEhkwu4wSsvrwB` | Not exposed | Stage 1 checkpoint |
| 18 | `MDL-RDR-C01` | `.../01_stage1/.../weights/epoch3.pt` | `1GRriXd9ux58WGYsig8fNKa32d-9qo-SU` | 58,937,741 | `2026-07-19T17:31:24.000Z` | `1BtapdVlti3nXecyhOCnEhkwu4wSsvrwB` | Not exposed | Stage 1 checkpoint |
| 19 | `MDL-RDR-C01` | `.../01_stage1/.../weights/epoch4.pt` | `1bgDbgcKv-oZD_qYct1JnmAcJR2yuuw0T` | 58,937,869 | `2026-07-19T17:31:26.000Z` | `1BtapdVlti3nXecyhOCnEhkwu4wSsvrwB` | Not exposed | Stage 1 checkpoint |
| 20 | `MDL-RDR-C01` | `.../02_stage2/.../weights/best.pt` | `1ksyCUVN2_864600XPBaVgicG6vt-XD_l` | 22,490,794 | `2026-07-19T17:33:08.000Z` | `1aDe1iJqKg2fEyCK4NMOnMICeWoV7qnRi` | Not exposed | Stage 2 selected checkpoint per manifest |
| 21 | `MDL-RDR-C01` | `.../02_stage2/.../weights/last.pt` | `1zSiRWtPMGii-fU2sm7MK89K0e0uvQjPl` | 22,490,794 | `2026-07-19T17:32:58.000Z` | `1aDe1iJqKg2fEyCK4NMOnMICeWoV7qnRi` | Not exposed | Stage 2 endpoint |
| 22 | `MDL-RDR-C01` | `.../02_stage2/.../weights/epoch0.pt` | `1B4KnaDcp7rLwjJdJKvG58z-vkTjHGHLx` | 89,484,327 | `2026-07-19T17:31:58.000Z` | `1aDe1iJqKg2fEyCK4NMOnMICeWoV7qnRi` | Not exposed | Stage 2 checkpoint |
| 23 | `MDL-RDR-C01` | `.../02_stage2/.../weights/epoch5.pt` | `1EV_DDeu3uGO6uvDkVS8_tY0Dueu8_RzR` | 89,485,031 | `2026-07-19T17:32:18.000Z` | `1aDe1iJqKg2fEyCK4NMOnMICeWoV7qnRi` | Not exposed | Stage 2 checkpoint |
| 24 | `MDL-RDR-C01` | `.../02_stage2/.../weights/epoch10.pt` | `1E2pVWBkpB1dRxl53nW8W2AHlkq3joB9P` | 89,485,671 | `2026-07-19T17:32:40.000Z` | `1aDe1iJqKg2fEyCK4NMOnMICeWoV7qnRi` | Not exposed | Stage 2 checkpoint |
| 25 | `MDL-RDR-C01` | `.../02_stage2/.../weights/epoch15.pt` | `1i6k7FA9_8lJ7vKWPh1bVE3k2M4jzURyu` | 89,486,311 | `2026-07-19T17:32:58.000Z` | `1aDe1iJqKg2fEyCK4NMOnMICeWoV7qnRi` | Not exposed | Stage 2 checkpoint |
| 26 | `MDL-RDR-C01` | `outputs/rapid_detection_recovery_colab/recovery_candidate_01_colab_best.pt` | `1yfWqV6doTvxzwFThltYrSiZjlLV15rDZ` | 22,490,794 | `2026-07-21T05:10:26.996Z` | `13E6gYGUuxpbtmsg38Ipzgs61r31YAKYz` | Not exposed | Exported selected checkpoint; manifest SHA only |
| 27 | `MDL-LEGACY-YOLOV5-CLOUD` | `.../Cloud Function - Colab/YOLO_car_damage_detection_V5.pt` | `1qrMR1absDvDKWEbhGE6pV5Q3K7_f3HzB` | 19,208,858 | `2026-07-22T06:58:31.000Z` | `1XrK-FGC8hEccUX56ZywNnnCQ1mYe22WP` | Not exposed | Move to unresolved old-model archive |
| 28 | `MDL-LEGACY-CARDENT` | `.../Cloud Function - Colab/reference/CarDentScratch.pt` | `137GYrPXSf38V1qmkm3BWYwSMvXVYd93V` | 23,381,341 | `2026-07-22T06:58:31.000Z` | `1ledzNwpk3FUBnFeY8myLyZ_279cshCZe` | Not exposed | Move to unresolved old-model archive |
| 29 | `MDL-LEGACY-YOLOV5-AUTOLABEL` | `02.Auto Labeling/YOLO_car_damage_detection_V5.pt` | `1UrR_rtfSOAKPjOgIpSd8dIDp7BJsiErF` | 19,208,858 | `2026-07-22T07:57:25.796Z` | `1L8pV9VGLtRs89eknQbo12E8DlNDXOR1e` | Not exposed | Move to unresolved old-model archive; same size is not duplicate proof |

## Selection and Summary Record Inventory

| Record | Drive ID | Size Bytes | Modified UTC | Bounded Read | Registry Use |
|---|---|---:|---|---|---|
| `models/model_selection/final_model_selection.json` | `1KqY0-c7ubeI4g3CR9MruusPl3Y0fNprT` | 671 | `2026-07-17T15:38:13.833Z` | Yes; non-sensitive JSON only | Candidate 01 mapping, SHA, `quality_gate_pass=false`, `BEST_AVAILABLE_POC_ONLY`, test unused |
| `models/model_selection/validation_threshold_comparison.csv` | `17dHFjLM2P6-vJiWXBAQalB5crmI7AXgz` | 1,560 | `2026-07-17T15:38:13.628Z` | Yes; non-sensitive CSV only | Candidate 01/02 validation comparison; not used as repository-backed portfolio metrics |
| `outputs/rapid_detection_recovery_colab/recovery_candidate_01_colab_manifest.json` | `1fSztdS-8FRNfZXRLV3D2WgdWXwkf_Bek` | 2,676 | `2026-07-21T05:10:24.261Z` | Yes; non-sensitive JSON only | Selected checkpoint SHA, dataset/run linkage, validation-only and production false |
| `.../04_training_design.json` | `106d2KFgjF9o1ND7mId8e7ajEZo6E8bLy` | 641 | `2026-07-21T05:10:27.532Z` | Yes; non-sensitive JSON only | Training design and explicit Frozen/Test false |
| `.../05_validation_metrics.json` | `1UBVIcARJIUzCeFIJq6eSTn33w9PiSO63` | 676 | `2026-07-21T05:10:27.466Z` | Yes; non-sensitive JSON only | Validation-only status; not promoted to portfolio metric registry |
| `04_5J/.../04_5J_gate_result.json` | `1GQvKi3Q9_fLHFBZ6Iyaf7nLRTLn2e7hD` | 1,299 | `2026-07-13T08:28:57.002Z` | No; repository evidence was authoritative and sufficient | Drive provenance record retained with historical run |
| `04_5J/.../training_artifact_manifest.csv` | `1aWBYmwFpfNSoNXbWPMDFIyR8ZULadPrq` | 4,527 | `2026-07-13T08:28:56.823Z` | No; repository evidence was authoritative and sufficient | Drive provenance record retained with historical run |
| `04_5J/.../training_completion.json` | `1rXXQc1eloxyhD__RdUdO6Rhdgdn6PrhM` | 778 | `2026-07-13T08:20:30.983Z` | No; repository evidence was authoritative and sufficient | Drive provenance record retained with historical run |

## Current Reference Decision

```text
CURRENT_REFERENCE_MODEL = NONE
02_MODELS/01_current direct children = 0
Reason = no artifact has both reconciled provenance and a passed current quality/deployment gate
```

The Phase 04.5J artifact is the strongest repository-verified historical baseline. It is not a current reference. The folder-named `final_selected` artifact is separately classified `BEST_AVAILABLE_POC_ONLY` because its own selection record says `quality_gate_pass=false`.
