# FleetVision Local Project Dashboard 操作指南

## 1. 定位

本工具是 FleetVision 的本機專案治理 Dashboard，集中呈現：

- Phase／Gate mapping；
- formal 與 candidate state；
- 整體與各 Phase 治理進度；
- 目前焦點、下一個允許動作與禁止動作；
- Git checkpoint 與 worktree；
- safety hard gates；
- tests、classification、Result ZIP metadata；
- append-only timeline 與來源警告。

它不是車損推論 UI，也不能核准或執行任何 Gate。

## 2. 執行前提

1. 在 FleetVision repository root。
2. Python 3 可由 `python` 或 `py -3` 啟動。
3. Dashboard 檔案已存在於 `docs/00_project_management/project_dashboard/`。
4. 不需網路、Node、CDN 或額外前端 build。

## 3. 資料驗證

先執行：

```powershell
python scripts\validate_project_dashboard_data.py `
  --dashboard-root docs\00_project_management\project_dashboard `
  --json
```

若結果為 `BLOCKED`，不要啟動並信任新的 snapshot。修正 JSON、schema 或 cross-reference 後重新驗證。

## 4. 啟動

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts\serve_project_dashboard.ps1
```

瀏覽器開啟：

```text
http://127.0.0.1:8765/
```

## 5. 畫面判讀

### Formal vs Candidate

- Formal：已寫入 Git 與治理文件的狀態。
- Candidate：獨立 worktree 中尚未正式 commit／push／remote verify 的工作。
- Candidate 不得覆蓋 formal state。

### Safety hard gate

只有安全值與 trust level 都達 verified clear，才會顯示 `HARD GATE CLEAR`。安全字串若僅為 operator reported，仍顯示 `HARD GATE NOT CLEAR`。

### Progress

進度表示治理 milestone completion，不表示時間或工期。

## 6. 搜尋與篩選

搜尋涵蓋：Phase、Gate、classification、commit SHA、evidence ID。狀態篩選只在瀏覽器記憶體執行，不會修改 JSON。

## 7. Auto-refresh

Dashboard 每 10 秒檢查 JSON fingerprint。載入失敗時：

- 保留最後有效 snapshot；
- 顯示 error banner；
- exponential backoff，最多 60 秒；
- 不顯示 partial data。

## 8. 更新 JSON

更新前先讀正式治理文件與 live Git facts。每個顯示項目必須有 `source_refs` 與 trust level。完成後：

1. 更新 `generated_at_utc`；
2. 使用 `compute_snapshot_id()` 重算 fingerprint；
3. 執行 validator；
4. review exact diff；
5. 只 stage allowlisted Dashboard paths。

不得把 chat summary 直接標為 `REPOSITORY_VERIFIED`。

## 9. N2 狀態更新條件

`04.5N-2` 不可只改狀態文字。只有在 `04.5N-1` 已是 `COMPLETED/PASS`，且 N2 的 `evidence_ids` 包含 `type=AUTHORIZATION`、verification status 為 repository 或 artifact verified 的正式授權證據時，validator 才允許 N2 從 `NOT_APPROVED` 前進。

## 10. 禁止事項

- Browser write-back；
- 自動 Git commit／push；
- Result ZIP 未審核 Apply；
- N1／N2 execution；
- canonical COCO、dataset、Registry、fixed splits mutation；
- test split access；
- inference、training、retraining 或 deployment acceptance。
