# FleetVision Phase Gate Checklist

本文件定義 FleetVision 每個階段開始前與結束前的固定檢查流程。目的不是增加流程負擔，而是避免上下文混亂、工具分工不明、GitHub 上傳時機錯誤，以及大型資料誤入版本控管。

---

## 1. Phase 開始前固定檢查

每個 Phase 開始前，先回答以下事項：

```text
Phase Gate 檢查

目前階段：Phase XX - <名稱>
上下文狀態：清楚 / 建議重開
主要工具：Codex / Cursor / Colab / ChatGPT
Cursor 角色：開 repo、看 diff、跑指令、手動修正
Codex 角色：主要工程實作
是否先 GitHub 上傳：是 / 否，理由：<理由>
本階段最小成果：<成果>
本階段不做：<排除範圍>
預計驗收指令：<commands>
```

---

## 2. 工具分工

| 工具 | 使用時機 |
|---|---|
| ChatGPT | Phase 規劃、錯誤解釋、Codex prompt、流程判斷 |
| Codex | 程式實作、重構、修 bug、建立測試、更新文件 |
| Cursor | 開啟 repo、查看 diff、執行本機指令、Git 操作、手動微調 |
| Colab | YOLOv8 GPU 訓練與 notebook 執行 |
| GitHub | 保存通過驗收的程式碼與文件版本 |

原則：主要工程實作交給 Codex；Cursor 是本機 IDE 與檢查環境；ChatGPT 負責規劃與判斷。

---

## 3. GitHub 上傳判斷

### Phase 開始前

| 狀態 | 建議 |
|---|---|
| 前一階段已通過測試與驗收 | 可以 commit / push 前一階段成果 |
| 前一階段還沒跑測試 | 先不要 push，先驗收 |
| 只放入 raw images / Excel / model weights | 不要 commit 這些大型資料 |
| 文件與程式碼已穩定 | 可以 commit |

### 可以上傳 GitHub 的內容

- `src/`
- `scripts/`
- `tests/`
- `configs/`
- `docs/`
- `sql/`
- `notebooks/` 範本
- `README.md`
- `AGENTS.md`
- `CODEX_WORKFLOW.md`
- `PHASE_GATE_CHECKLIST.md`

### 不要上傳 GitHub 的內容

- `dataset/01_raw/` 原始圖片
- `dataset/02_interim/` 大量中間圖片
- `dataset/05_yolo/` 大量訓練圖片與 label 產物
- `outputs/` 大量輸出檔
- `models/` 權重檔，例如 `.pt`, `.pth`, `.onnx`, `.engine`
- `.env`
- 資料庫 dump

---

## 4. 基本驗收指令

每個 Phase 開始前至少執行：

```bash
python scripts/phase00_init_project.py --validate
pytest
```

Phase 01 之後若 metadata 已建立，可加：

```bash
python scripts/phase01_build_metadata.py --max-images-per-source 20
```

---

## 5. Phase 結束前固定檢查

每個 Phase 結束前確認：

1. 修改了哪些檔案。
2. 如何執行。
3. 會產生哪些輸出。
4. 測試是否通過。
5. 是否需要更新文件。
6. 是否可以 commit。
7. 是否可以 push 到 GitHub。
8. 是否需要進入下一個 Phase。

---

## 6. Patch-only 更新規則

為避免覆蓋本機已完成作業，FleetVision 後續交付一律優先採用 **patch 壓縮包**，不再以完整專案資料夾作為主要交付方式。

### 核心原則

- Patch 壓縮包只包含本階段需要「新增」或「替換」的檔案。
- 不要直接把完整壓縮包解壓覆蓋整個 `FleetVision/` 根目錄。
- 使用 patch 前，必須先檢查壓縮包內檔案清單。
- 只複製 patch 中明確列出的檔案到 repo 對應位置。
- 若 patch 中的檔案會替換現有檔案，先用 Cursor 查看 diff，再決定是否接受。
- 若本機檔案已有手動修改，先備份或建立 Git commit，再套用 patch。
- Patch 不應包含 `dataset/01_raw/`、大型輸出、模型權重或 `.env`。

### Patch 套用前固定檢查

```text
Patch 套用檢查

patch 檔名：<zip name>
是否為完整專案包：否，應為局部 patch
將新增檔案：<list>
將替換檔案：<list>
是否可能覆蓋本機已完成作業：是 / 否
是否已查看 diff：是 / 否
是否需要先 commit 目前狀態：是 / 否
是否允許套用：是 / 否
```

### 建議套用流程

1. 先在 Cursor terminal 執行：

```bash
git status
```

2. 若目前有重要修改，先 commit 或至少備份。
3. 解壓 patch 到暫存資料夾，不要直接覆蓋 `FleetVision/`。
4. 逐一複製 patch 內檔案到對應路徑。
5. 用 Cursor 查看 diff。
6. 執行本階段驗收指令。
7. 通過後再 commit / push。

### Windows PowerShell 範例

假設 patch 解壓到：

```text
G:\Project\_patches\FleetVision_phase_gate_patch\
```

專案根目錄是：

```text
G:\Project\FleetVision\
```

則只複製 patch 內指定檔案，例如：

```powershell
Copy-Item "G:\Project\_patches\FleetVision_phase_gate_patch\PHASE_GATE_CHECKLIST.md" "G:\Project\FleetVision\PHASE_GATE_CHECKLIST.md" -Force
Copy-Item "G:\Project\_patches\FleetVision_phase_gate_patch\CODEX_WORKFLOW.md" "G:\Project\FleetVision\CODEX_WORKFLOW.md" -Force
Copy-Item "G:\Project\_patches\FleetVision_phase_gate_patch\CODEX_PHASE02_PROMPT.md" "G:\Project\FleetVision\CODEX_PHASE02_PROMPT.md" -Force
```

禁止使用會把整包內容直接覆蓋到根目錄的做法，除非已確認該 patch 只含安全的局部檔案，且已完成 diff 檢查。
