# FleetVision Phase 04.5L Completed Review Findings Analysis

## 目的

本流程只處理已凍結的 130 筆 validation-error 人工複核結果，分成兩個操作 Gate：

- **F1**：驗證 Completed Workbook、既有 canonical export／validator／summarizer，建立 severity-scope 人工複核 Workbook。
- **F2**：在 130／130 scope review 完成後，驗證來源欄位與順序、匯出 scope CSV、建立 findings／recommendation／evidence。

F1／F2 都不得讀取 test split、重新推論、修改 annotation／GT／dataset／Registry／fixed splits，也不得開始 training／fine-tuning。

## 權威輸入

| Artifact | Path | Expected SHA256 |
|---|---|---|
| Completed Workbook | `G:\Project\FleetVision_Review_Packages\Phase04_5L\phase04_5l_20260714_v1_review_workspace\exports\validation_error_human_review_completed.xlsx` | `C9DF0A38B115406791DF03BFDC714901A66A47BE95CE0E2047E573FCC8D6FB6C` |
| Source Workbook | `G:\Project\FleetVision_Review_Packages\Phase04_5L\phase04_5l_20260714_v1\workbook\validation_error_human_review.xlsx` | `5DC9C1FDA69865D36C60EACB90A0AEA0FC9F4B263F30281723BB0E1172549DE5` |
| Frozen package | `G:\Project\FleetVision_Review_Packages\Phase04_5L\phase04_5l_20260714_v1_PACKAGE.zip` | `6D6243FE8F3E12910C03A5EDCFF178CE20B180473EED43DED2B36301A877B42A` |

Completed Workbook expected size：`31871231` bytes。Logical fingerprint：
`F87882E8F6DBF20B6603FC5106BE5A78BD61E4A22A6500E9586E51498B4AAC35`。

執行前需確認 Source Workbook 的實際 authoritative path。只能在 SHA256 維持上述值時修正 config 路徑；不可開啟後儲存 Workbook。

## Implementation closure prerequisite

1. `main`、local HEAD、`origin/main`、GitHub remote HEAD 必須一致。
2. worktree 只能是 clean，或僅有 `?? outputs/metadata/external_assets/...`。
3. `outputs/metadata/external_assets/` 不得 stage、commit、delete、clean、move 或 rewrite。
4. 使用已完成 implementation closure 的 40 字元 SHA 作為 `-ExpectedHead`。
5. 不得直接把 design checkpoint `420b6a3...` 當作 implementation closure SHA。

## F1 執行

```powershell
Set-Location -LiteralPath 'G:\Project\FleetVision'

.\scripts\phase04_5_run_completed_review_findings_f1.ps1 `
  -ExpectedHead <IMPLEMENTATION_CLOSURE_SHA>
```

預期 PASS classification：

```text
PHASE_04_5L_COMPLETED_REVIEW_VALIDATED_AND_SCOPE_REVIEW_PACKAGE_CREATED
```

F1 會建立 timestamped no-overwrite workspace，位於：

```text
G:\Project\FleetVision_Review_Packages\Phase04_5L\
phase04_5l_20260714_v1_review_workspace\analysis\
phase04_5l_completed_review_findings_<timestamp>\
```

F1 必須產出：

- `canonical/validation_error_human_review.csv`
- `canonical/annotation_correction_proposals.csv`
- `reports/validation_report.json`
- `reports/validation_errors.csv`
- `reports/review_summary.json`
- `reports/review_summary.md`
- `reports/data_improvement_action_queue.csv`
- `reports/data_improvement_action_summary.csv`
- `scope_review/severity_scope_review.xlsx`
- `scope_review/severity_scope_review_source.csv`
- `scope_review/scope_asset_manifest.csv`
- `evidence/source_hashes.csv`
- `evidence/f1_gate_result.json`
- `evidence/F1_SHA256SUMS.csv`

## 人工 scope review hard stop

F1 PASS 後停止自動流程。`severity_scope_review.xlsx` 是唯讀 template／稽核 artifact，**不得直接作為 live 人工審核檔**。正式人工審核固定使用本機繁體中文 Streamlit app、SQLite state、JSONL audit events 與定期 backup。

啟動：

```powershell
.\scripts\phase04_5_launch_severity_scope_review_app.ps1
```

完成條件：

```text
rows = 130
scope reviewed = 130
pending = 0
needs adjudication = 0
```

完成後匯出：

```powershell
.\scripts\phase04_5_export_severity_scope_review_app_workbook.ps1
```

F2 只接受：

```text
<F1_WORKSPACE_ROOT>\scope_review_app\exports\
severity_scope_review_completed.xlsx
```

以及同目錄的 `scope_review_export_result.json`。詳細操作與 controlled values 見 `docs/01_phase_guides/phase_04_5_severity_scope_review_app.md`。

### Conditional rules

- reviewer 與 timezone-aware timestamp 由 Streamlit app 自動填入。
- low confidence、`other`、`insufficient_visual_evidence` 必須填 notes。
- catastrophic group 必須使用 approved catastrophic reason。
- catastrophic + likely drivable 必須填 notes。
- `IN_SCOPE_LIGHT_MODERATE` 不可使用 `catastrophic_collision` 或 `vehicle_integrity_compromised`。
- `insufficient_visual_evidence` 必須是 low confidence 且有 notes。
- F1 source／template／asset manifest 不可修改；completed output 預設 no-overwrite。

## F2 執行

只在 Streamlit scope review 130／130 完成、completed scope Workbook 已由受控 exporter 產生後：

```powershell
.\scripts\phase04_5_run_completed_review_findings_f2.ps1 `
  -ExpectedHead <IMPLEMENTATION_CLOSURE_SHA> `
  -WorkspaceRoot '<F1_WORKSPACE_ROOT>'
```

F2 會驗證 completed scope Workbook、export evidence、F1 immutable checksum 與 source hash contract；直接修改 F1 template Workbook 會 fail closed。

預期 PASS classification：

```text
PHASE_04_5L_COMPLETED_REVIEW_VALIDATION_AND_FINDINGS_ANALYSIS_COMPLETED
```

F2 必須產出：

- `final_findings/severity_scope_classification.csv`
- `final_findings/severity_scope_summary.json`
- `final_findings/severity_scope_summary.md`
- `final_findings/phase04_5l_findings_report.json`
- `final_findings/phase04_5l_findings_report.md`
- `final_findings/retraining_recommendation.json`
- `evidence/workspace_after.csv`
- `evidence/gate_result.json`
- `evidence/SHA256SUMS.csv`

## Recovery 與 no-overwrite

- 任何既有 workspace 或 output filename 會 fail closed。
- ZIP extraction 會拒絕 absolute path、`..` 與 symlink。
- F1/F2 failure 只保留 blocked evidence，清除自身 `.staging-*`；不刪除 frozen inputs。
- 不得為了重跑而刪除既有 PASS workspace。需建立新的治理決策與 timestamped workspace。

## 強制安全聲明

```text
TEST_SPLIT_READ=NO
MODEL_INFERENCE_EXECUTED=NO
ANNOTATION_MODIFIED=NO
TRAINING_STARTED=NO
RETRAINING_STATUS=NOT_YET_APPROVED
DEPLOYMENT_ACCEPTANCE=NOT_YET_APPROVED
```

Threshold `0.20` 永遠只是 `BALANCED_VALIDATION_THRESHOLD_CANDIDATE`，不是 deployment threshold。
F2 PASS 只形成 advisory recommendation，不核准 retraining 或 deployment。

<!-- FLEETVISION-MANAGED:PHASE_04_5L_F2_COMPLETION_HANDOFF:BEGIN -->
## F2 completion record and Phase 04.5M handoff

Phase 04.5L F2 completed successfully:

```text
CLASSIFICATION=PHASE_04_5L_COMPLETED_REVIEW_VALIDATION_AND_FINDINGS_ANALYSIS_COMPLETED
PRIMARY_RECOMMENDATION=DATA_CORRECTION_REQUIRED_BEFORE_RETRAINING
REVIEW_CASES=130
SCOPE_REVIEWED=130
PENDING=0
NEEDS_ADJUDICATION=0
ANNOTATION_CORRECTION_PROPOSAL_COUNT=2
COMPLETED_SCOPE_WORKBOOK_SHA256=AC0EE5882E8E6C7A3E9300BF6AD1589EC18C169681AA6720F0C36132A42B3946
```

The two correction proposals are:

1. `l_687b939a3a89bb8e` — `wrong_damage_scope`
2. `l_e5875a8f94620ff1` — `extra_bbox`

The F2 recommendation is advisory. It does not authorize annotation changes or
retraining. The next controlled work is Phase 04.5M design review and a detailed
implementation plan for a dedicated two-case Streamlit/SQLite correction-review
workflow.

Controlling design:

`docs/superpowers/specs/2026-07-14-phase04-5m-data-correction-proposal-review-design.md`
<!-- FLEETVISION-MANAGED:PHASE_04_5L_F2_COMPLETION_HANDOFF:END -->
