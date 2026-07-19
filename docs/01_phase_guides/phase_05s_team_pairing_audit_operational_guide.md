# Phase 05S Team Pairing Audit 操作指南

## 目的

本流程將 `dataset/01_raw/04_team` 的團隊借還車照片建立為可追溯的候選批次、人工角度與前後配對審核工作區。

固定原則：

- `dataset/01_raw/04_team` 全程唯讀。
- SQLite 是 live review state 的唯一來源。
- XLSX 只在完成審核後輸出，不作 live input。
- Streamlit 只綁定 `127.0.0.1`。
- 不讀取 Frozen Test、不執行 OCR、模型 inference 或 training。
- 所有 wrapper 都不執行 Git add、commit、push。

## 三步操作

### 1. Prepare

建立 inventory、source snapshots、capture batches、contact sheets、candidate manifest 與 SQLite workspace。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\phase05s_prepare_team_pairing_audit.ps1 `
  -WorkspaceRoot "G:\Project\FleetVision\outputs\phase05s\team_pairing_audit\team_pairing_audit_<RUN_ID>"
```

成功證據：

```text
OUTCOME=PASS
OPERATION=PREPARE_TEAM_PAIRING_AUDIT
WRAPPER_OUTCOME=PASS
NEXT_ACTION=RUN_REVIEW_WRAPPER
```

Prepare 為 no-overwrite。若 workspace 已存在，必須使用新 run ID，不得覆蓋或刪除既有工作區。

### 2. Review

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\phase05s_launch_team_pairing_review_app.ps1 `
  -WorkspaceRoot "<PREPARED_WORKSPACE>"
```

操作順序：

1. 批次審核：確認 vehicle ID、before/after 與 batch status。
2. 角度標記：只標 confirmed batches 的 representative images。
3. 前後配對：確認 pair status、既有損傷、新增損傷、demo role。
4. 完成狀態：確認 blocking count 為 0、confirmed pairs 至少 3、primary 恰好 1。

### 3. Export

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\phase05s_export_team_pairing_review.ps1 `
  -WorkspaceRoot "<REVIEWED_WORKSPACE>"
```

Exporter 只有在 completion gate 全部通過時才會建立 completed export；不完整時輸出 `WRAPPER_OUTCOME=BLOCKED`，不留下半成品。

## 故障處理

- `WRAPPER_OUTCOME=BLOCKED`：先讀取 `BLOCKING_REASON`，不要手動修改 SQLite 或 candidate artifacts。
- source snapshot mismatch：停止 export，確認原始照片是否被移動、覆蓋或重新編碼。
- workspace identity mismatch：不可沿用其他 run 的 SQLite；建立新 workspace。
- Streamlit 無法啟動：確認共用 Python 為 `G:\Project\FleetVision\.venv\Scripts\python.exe`。

## A3 與下一階段邊界

A3 只建立與驗證工具，不執行正式 `04_team` 掃描。正式 prepare/review/export 屬於 A4 run。A3 完成後應停止新增治理功能，轉入 pair comparison MVP：影像對位、差異區域與既有 ResNet18 證據整合。
