# FleetVision Project Status

> 更新原則：每次正式 checkpoint 後更新。
> 基準日期：2026-07-12

## 1. 當前 Phase

- 主 Phase：Phase 04 — Pilot Human Review and Reviewed Dataset（尚未完全關閉）
- 已完成 Gate：Phase 04C — Portable Image Link Compatibility；Phase 04D — Human Review Execution；Phase 04E — Verified Freeze；Phase 04E — Formal Merge
- 下一 Gate：Phase 04E — Reviewed Dataset Schema Promotion and Dataset Build

## 2. 已完成項目

- Phase 01 Metadata catalog
- Phase 02 Review queue
- Phase 03 Human review schema／Validator
- Phase 03.5 Auto prelabel pilot（已封存）
- Pilot worklist builder
- Human review validator
- Excel review interface／exporter
- Human review guide PDF
- Multi-reviewer package builder／merger
- Vincent／Allison 250／250 deterministic assignment
- Collaboration artifacts `.gitignore`
- Phase 04C portable image link 與 dropdown compatibility 驗證
- Phase 04D Vincent 250／250、Allison 250／250，共 500／500 人工審核
- 兩份完成版 canonical Workbook 凍結快照與 SHA256 manifest
- Phase 04E Verified Freeze（`NEW_FREEZE_VERIFIED`）
- Phase 04E Formal Merge Preflight（`FORMAL_MERGE_PREFLIGHT_PASS`）
- Phase 04E Formal Merge（`FORMAL_MERGE_VERIFIED`）

## 3. Phase 04C／04D 完成狀態

### Excel Workbook Compatibility

已完成並驗證：

- `open_image` 改用 Excel `HYPERLINK(...)` 公式
- 六組 Excel list Data Validation 改用 workbook-scoped named ranges，指向隱藏的 `選項清單`
- `calcMode = auto`
- `fullCalcOnLoad = True`
- `forceFullCalc = True`
- `calcOnSave = True`
- TEMP Vincent／Allison Package build PASS
- Excel COM 驗收 PASS
- Allison 實際 Excel 工作流程完成

驗證結果：Targeted 6 passed；Merger regression 6 passed；Exporter regression 10 passed；Full 112 passed, 1 skipped。

### Human Review Completion and Freeze

- Vincent：250／250 完成
- Allison：250／250 完成
- 合計：500／500 完成
- 兩份完成版 canonical Workbook 均已建立凍結快照與 SHA256 manifest
- 正式人工成果未被 Builder 修正流程覆蓋

### Phase 04E Verified Freeze and Formal Merge

- Gate：`NEW_FREEZE_VERIFIED`、`FORMAL_MERGE_PREFLIGHT_PASS`、`FORMAL_MERGE_VERIFIED`
- 合併列數：500 rows、500 unique review IDs
- reviewed：500；pending：0；validation errors：0
- Vincent／Allison overlap：0
- Frozen snapshot：`G:\Project\FleetVision_Backups\Phase04_Completed_Reviews\Frozen_500\20260711_235712`
- Formal merge provenance：`G:\Project\FleetVision_Backups\Phase04_Completed_Reviews\Formal_Merge_500\20260712_001744`
- Formal merged CSV：`outputs/manual_review/collaboration/pilot500_human_review_results_collaboration.csv`
- Logical fingerprint：`1FF38FF9E9B04481A0C0BAD724E3D9B9ADFCA4E2C92441D8A2DC7DC3D30113FD`

## 4. 當前重要風險

- R-001：人工結果遺失（已以凍結快照、formal merge provenance 與 SHA256 manifest 控制；後續步驟仍須維持唯讀）
- R-002：舊 Package 連結不相容（Phase 04C 已完成驗證）
- R-003：資料不平衡
- R-004：外部資料尚未建立正式接收流程
- R-005：Internal holdout 尚未凍結

## 5. 最近 Git Checkpoints

- `feat: complete phase03.5 auto prelabel pilot`
- `06efb67 feat: add phase04 pilot human review worklist`
- `bb0be16 feat: add phase04 pilot human review validator`
- `ea20ad3 feat: add phase04 Excel human review interface`
- `fix: resolve phase04 Excel image hyperlinks`
- `feat: add phase04 Excel review exporter`
- `docs: add phase04 human review guide`
- `feat: add phase04 multi-reviewer collaboration workflow`
- `chore: ignore phase04 collaboration artifacts`

- `docs: record phase04c workbook integrity fix`
- `docs: record phase04e verified freeze and formal merge`

## 6. 下一個正式執行順序

### Phase 04E — Reviewed Dataset Schema Promotion and Dataset Build

目前正式 merged CSV 使用 `human_*` 欄位，而既有 Reviewed Dataset Builder 預期 canonical review 欄位：

- `photo_type_review`
- `angle_review`
- `is_exterior_review`
- `has_visible_damage_review`
- `severity_review`
- `review_status`
- `reviewer`
- `review_notes`

在建立 Reviewed Dataset 前，必須先完成受驗證的 schema promotion／adapter，不得直接執行舊 builder。

1. 建立並驗證 `human_*` → canonical review schema promotion／adapter
2. 執行 Reviewed Dataset build
3. 產生 annotation candidates list
4. 產生分布與資料品質報告
5. 解決 `needs_followup`（若 promotion 後仍待處理）
6. Phase 04 final closeout

### Parallel Governance Work

8. 建立 External Dataset Registry
9. 定義 Kaggle／Roboflow 搜尋與接受標準
10. 準備 external intake scripts／audit schema

## 7. 明確禁止事項

- 不重跑 Phase 03.5
- 不修改 `dataset/01_raw/`
- 不建立 YOLO labels
- 不建立 `dataset/05_yolo/`
- 不訓練模型
- 不下載未登錄或未確認 License 的外部資料
- 不將外部資料混入 internal test
- 不覆蓋已有人工審核結果
