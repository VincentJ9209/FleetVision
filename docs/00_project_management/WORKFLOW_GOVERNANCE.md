# FleetVision Workflow Governance

## 1. 核心原則

FleetVision 不依賴聊天記憶推進。

正式真相來源：Git Repository、Project Context、Project Status、Master Phase Map、Decision Log、Data Registry、測試與輸出稽核。

任何只存在對話、未寫入文件與 Git 的重大決策，視為尚未正式生效。

## 2. 每個任務的標準循環

1. Context Check
2. Goal Check
3. Dependency Check
4. Safe Implementation
5. Test
6. Output Audit
7. Documentation Update
8. Git Checkpoint
9. Next-phase Gate

### Context Check 必查

- Project root
- branch
- worktree
- current Phase／subphase
- latest checkpoint
- immutable architecture
- protected formal outputs

### Safe Implementation 原則

- 原始資料唯讀
- 正式輸出預設不覆寫
- 先 TEMP smoke test，再正式產出
- 多人結果以 identity key 合併
- 所有人工結果先備份

### Test 至少依任務執行

- Targeted tests
- Regression tests
- Full tests
- `git diff --check`
- data count／schema／file existence audit
- formula／link audit
- failure no-overwrite audit

### Documentation Update

判斷是否更新：Project Status、Master Phase Map、Decision Log、Phase guide、external registry、model card／experiment record。

## 3. Codex 任務模式

每個 Codex prompt 必須包含：

```text
Context Lock
- Project:
- Project root:
- Current Phase:
- Current status:
- Immutable architecture:
- Data imbalance strategy:
- External data status:
- In scope:
- Out of scope:
- Files allowed:
- Formal outputs protected:
- Acceptance criteria:
- Required tests:
- Required document updates:
- Commit/push permission:
```

模式：小型明確修改直接送出；多檔且驗收明確用 Goal；架構不明用 Plan。資料切分、合併、去重、實驗設計使用 High。

## 4. Colab／Notebook 規範

每個儲存格開頭標註：儲存格編號、操作類型、插入或覆蓋位置、主要目的、執行前提、重點、驗收標準。

每次只進行一個清楚步驟，不假設使用者知道執行順序。

## 5. 資料治理規範

- `dataset/01_raw/` 唯讀
- 衍生資料可追蹤 source、builder、config、generation date、schema version
- 外部資料先進 Registry 再下載
- 優先 group split
- internal test frozen
- external data 不進 internal test
- 重複與近似圖不得跨 split
- 每次 split 需有 manifest

## 6. 人工審核規範

- 只修改人工欄位
- 不修改 review identity、image identity、original path、source bucket、assignment、suggestions、canonical order
- 每完成 50 筆建立備份
- Workbook 修改前建立 pre-change backup
- 合併前保留原始兩份 reviewer workbook
- Merger 不直接覆寫唯一成功輸出

## 7. 實驗治理規範

每次訓練記錄：experiment_id、git commit、dataset version、manifest、model、weights、seed、imgsz、batch、epochs、patience、augmentations、environment、metrics、artifact paths、notes。

External data 是否有效，只能以 internal validation／test 表現判斷。

## 8. 必須新增 ADR 的變更

- YOLO class 改變
- Detect 改為 Segmentation
- 重新執行 Phase 03.5
- 調整 internal test
- 更換標註定義
- 改變外部資料接受規則
- 改變 group split key
- 改變專案根目錄
- 將理賠判定納入模型輸出
- 擴張到正式生產部署

## 9. 完成聲明

只有在具備 tests output、audit output、expected counts、Git status、local／remote sync 與 updated documentation 時才可宣告完成。

原則：Evidence before assertion。
