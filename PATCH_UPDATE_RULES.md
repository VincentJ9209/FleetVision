# FleetVision Patch Update Rules

本文件定義 FleetVision 後續檔案更新的固定規則。目標是避免使用完整專案壓縮包時，誤覆蓋本機已完成作業。

---

## 1. 基本規則

後續更新一律優先使用 **patch 壓縮包**。

Patch 壓縮包只應包含：

- 本階段新增的檔案
- 本階段需要替換的檔案
- 本階段同步更新的文件

Patch 壓縮包不應包含：

- 完整 `FleetVision/` 專案資料夾
- `dataset/01_raw/` 原始圖片
- 大量中間輸出
- YOLO dataset 產物
- 模型權重
- `.env`
- 與本階段無關的檔案

---

## 2. 套用前檢查

套用任何 patch 前，先回答：

```text
Patch 檢查

patch 檔案：<zip>
是否只含局部檔案：是 / 否
將新增：<files>
將替換：<files>
是否會覆蓋目前成果：是 / 否
是否已先 git status：是 / 否
是否需要先 commit：是 / 否
是否可以套用：是 / 否
```

---

## 3. 建議操作流程

1. 在 Cursor terminal 執行：

```bash
git status
```

2. 若有尚未提交的重要成果，先 commit 或備份。
3. 解壓 patch 到暫存資料夾。
4. 不要整包覆蓋 `FleetVision/`。
5. 逐一複製 patch 內檔案到 repo 對應位置。
6. 在 Cursor 查看 diff。
7. 執行驗收指令。
8. 通過後 commit / push。

---

## 4. PowerShell 套用範例

```powershell
Copy-Item "G:\Project\_patches\<patch_name>\PHASE_GATE_CHECKLIST.md" "G:\Project\FleetVision\PHASE_GATE_CHECKLIST.md" -Force
Copy-Item "G:\Project\_patches\<patch_name>\CODEX_WORKFLOW.md" "G:\Project\FleetVision\CODEX_WORKFLOW.md" -Force
```

只複製 patch 中明確要更新的檔案。

---

## 5. GitHub 上傳原則

套用 patch 後，只有在以下條件都成立時才 commit / push：

- `pytest` 通過
- 本階段指定驗收指令通過
- 文件已同步更新
- `git status` 未包含大型資料或私密檔案
- Cursor diff 已確認合理
