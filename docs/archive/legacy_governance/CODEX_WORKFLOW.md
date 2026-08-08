# FleetVision Codex 工作流

本專案以 Codex 作為主要工程實作助手，Cursor 作為主要 IDE / 本機操作介面。ChatGPT 負責階段規劃、錯誤解釋、Codex prompt 產生與流程判斷。

---

## 1. 使用方式

1. 用 Cursor 開啟 FleetVision repo。
2. 確認根目錄存在：

```text
AGENTS.md
CODEX_WORKFLOW.md
PROJECT_CONTEXT_BRIEF.md
PHASE_GATE_CHECKLIST.md
README.md
```

3. 每次開始新階段前，先執行 `PHASE_GATE_CHECKLIST.md` 的 Phase Gate 檢查。
4. 每次只請 Codex 完成一個階段中的一個明確任務。
5. Codex 完成後，使用 Cursor 查看 diff。
6. 在 Cursor terminal 執行測試與驗收指令。
7. 通過後再 commit。
8. 確認沒有大型資料或私密檔案後，再 push 到 GitHub。

---

## 2. ChatGPT 對話與 Codex 轉移原則

不要只對 Codex 說：

```text
接續我們剛剛在 ChatGPT 的對話。
```

應該改成：

```text
請先閱讀 AGENTS.md、CODEX_WORKFLOW.md、PROJECT_CONTEXT_BRIEF.md、PHASE_GATE_CHECKLIST.md，
並依照這些規則執行 Phase XX。
```

---

## 3. 工具分工

| 工具 | 主要用途 | 不建議用途 |
|---|---|---|
| ChatGPT | Phase 規劃、Prompt、錯誤說明、架構判斷 | 直接長期持有 repo 狀態 |
| Codex | 程式實作、測試、重構、文件同步 | 一次完成整個專案 |
| Cursor | 開 repo、看 diff、跑指令、手動微調、Git 操作 | 取代 Codex 做大量自動生成 |
| Colab | YOLOv8 GPU 訓練與 notebook 執行 | 一般程式碼維護 |
| GitHub | 版本控管、備份、PR review | 儲存大型圖片、模型權重、`.env` |

---

## 4. GitHub 上傳判斷

建議先 commit / push 的情況：

- 前一階段程式碼已完成。
- 測試已通過。
- 文件已同步更新。
- `git status` 沒有大型資料、模型權重、`.env`。
- 即將進入下一個 Phase，且需要穩定 checkpoint。

不建議 commit / push 的情況：

- 測試尚未跑過。
- Codex 剛修改大量檔案但尚未看 diff。
- `dataset/01_raw/`、`outputs/`、`models/` 有大型檔案被 staged。
- `.env` 或私密資訊被 staged。

建議檢查：

```bash
git status
pytest
```

---

## 5. Patch-only 交付與套用規則

後續 ChatGPT / Codex 產出的 FleetVision 檔案更新，應優先採用 **patch-only** 方式交付。

### 原則

- 不交付完整 `FleetVision/` 專案資料夾作為主要更新方式。
- 每次只提供本階段需要新增或替換的檔案。
- Patch zip 內的相對路徑必須對應 repo 根目錄。
- 套用 patch 前，先用 Cursor 檢查檔案清單與 diff。
- 套用 patch 後，必須執行本階段驗收指令。
- 驗收通過後，再由 Cursor / Git terminal 進行 commit / push。

### Codex 任務要求

交給 Codex 的 prompt 應明確要求：

```text
請只新增或修改本階段列出的檔案，不要重建整個專案資料夾，不要移動 dataset，不要覆蓋與本任務無關的檔案。
```

### Cursor 套用 patch 的角色

Cursor 不只是編輯器，也負責保護本機成果：

1. 查看 patch 內容。
2. 確認只包含本階段檔案。
3. 套用後查看 diff。
4. 執行測試。
5. 確認沒有大型檔案被 staged。
6. 再進行 GitHub 上傳。
