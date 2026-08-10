# FleetVision Local Project Dashboard

FleetVision Local Project Dashboard 是 repository-tracked、唯讀、離線的專案治理與證據檢視。它不是 Phase 10 推論產品 Dashboard，也不會執行 Git、N1、N2、推論、訓練或資料修改。

## 啟動方式

請從 repository root 執行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\serve_project_dashboard.ps1
```

指定 port：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\serve_project_dashboard.ps1 `
  -Port 8876
```

Server 只綁定：

```text
127.0.0.1
```

請勿直接雙擊 `index.html` 使用 `file://`。瀏覽器通常會阻擋本機 JSON `fetch()`；正式支援模式是 loopback localhost HTTP。

## 驗證資料

```powershell
python .\scripts\validate_project_dashboard_data.py `
  --dashboard-root .\docs\00_project_management\project_dashboard `
  --json
```

成功結果包含：

```text
"status": "PASS"
```

Validator 檢查：

- JSON Schema Draft 2020-12；
- snapshot fingerprint；
- Phase／Gate／evidence／event ID 唯一性；
- Phase、Gate、evidence cross-reference；
- progress 與 weighted progress；
- 必要安全硬閘；
- N1／N2 授權分離；N2 狀態只有在 N1 PASS 且存在 verified `AUTHORIZATION` evidence 時才可前進；
- Result ZIP `DO_NOT_COMMIT` policy；
- append-only history ordering。

## 來源與信任模型

Dashboard 將 formal repository state 與 operational candidate state 分開顯示。信任等級：

```text
REPOSITORY_VERIFIED
ARTIFACT_VERIFIED
WORKTREE_VERIFIED
OPERATOR_REPORTED
STALE_OR_CONFLICTING
UNVERIFIED
```

Dashboard JSON 是衍生檢視，不取代：

- `PROJECT_STATUS.md`
- `HANDOFF_CURRENT.md`
- `MASTER_PHASE_MAP.md`
- Phase logs
- Decision Log
- Git facts
- artifact SHA256

## 更新流程

初始版本只允許受控人工更新：

```text
Edit JSON
→ recompute snapshot_id
→ run validator
→ review exact diff
→ commit exact paths
```

Browser 不會 write back。Result ZIP 自動更新器不在初始 implementation scope。

## 安全邊界

Dashboard 必須維持：

```text
N1_EXECUTED=NO
N2_EXECUTED=NO
CANONICAL_COCO_MODIFIED=NO
DATASET_MODIFIED=NO
REGISTRY_MODIFIED=NO
FIXED_SPLITS_MODIFIED=NO
TRAINING_STARTED=NO
RETRAINING_STATUS=NOT_YET_APPROVED
DEPLOYMENT_ACCEPTANCE=NOT_YET_APPROVED
```

大型 Result ZIP、圖片、模型、database、review package 與 extracted evidence 不進 Git。

## 停止 Server

在執行 PowerShell 視窗按：

```text
Ctrl+C
```
