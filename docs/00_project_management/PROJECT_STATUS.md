# FleetVision Project Status

> 更新原則：每次正式 checkpoint 後更新。
> 基準日期：2026-07-11

## 1. 當前 Phase

- 主 Phase：Phase 04 — Pilot Human Review and Reviewed Dataset
- 子階段：Phase 04C — Portable Image Link Compatibility；Phase 04D — Human Review Execution

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

## 3. 目前進行中

### Human Review

- Vincent 已開始人工審核
- 存在部分已完成 `human_*` 結果
- 已完成內容必須保留
- Allison 初版 package 已交付

### Excel Image Link Compatibility

問題：Allison 的 Excel 將裸相對圖片 hyperlink 交由瀏覽器處理。

已完成程式修正：

- `open_image` 改用 Excel `HYPERLINK(...)` 公式
- `calcMode = auto`
- `fullCalcOnLoad = True`
- `forceFullCalc = True`
- `calcOnSave = True`

Codex 測試：Targeted 5 passed；Regression 6 passed；Full 111 passed, 1 skipped；`git diff --check` PASS。

尚未完成：

1. TEMP package 獨立本機驗收
2. Allison 實機前三筆連結驗證
3. commit／push hyperlink formula fix
4. 修補現有 Vincent Workbook 或安全搬移已完成人工資料
5. 重建／重新交付 Allison 正式 package
6. 確認兩人都使用可持續作業版本

## 4. 當前重要風險

- R-001：人工結果遺失
- R-002：舊 Package 連結不相容
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

Hyperlink formula fix 尚待新 checkpoint。

## 6. 下一個正式執行順序

### Immediate

1. TEMP 產生修正版 package
2. Allison 實機確認圖片由圖片檢視器開啟
3. 修補／遷移 Vincent 已填寫 Workbook
4. commit／push hyperlink formula fix
5. 重新交付 Allison 修正版 package
6. 兩人繼續人工審核

### After Review Completion

7. 回收兩份 Workbook
8. Merger 合併
9. Validator 驗證
10. 解決 `needs_followup`
11. 抽查 Reviewer 一致性
12. 建立正式 Reviewed Dataset
13. 產生分布與資料品質報告

### Parallel Governance Work

14. 建立 External Dataset Registry
15. 定義 Kaggle／Roboflow 搜尋與接受標準
16. 準備 external intake scripts／audit schema

## 7. 明確禁止事項

- 不重跑 Phase 03.5
- 不修改 `dataset/01_raw/`
- 不建立 YOLO labels
- 不建立 `dataset/05_yolo/`
- 不訓練模型
- 不下載未登錄或未確認 License 的外部資料
- 不將外部資料混入 internal test
- 不覆蓋已有人工審核結果
