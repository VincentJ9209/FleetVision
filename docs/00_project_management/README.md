# FleetVision Project Management Index

本資料夾是 FleetVision 的專案治理中心。

## 必讀順序

1. `PROJECT_CONTEXT_BRIEF.md`
2. `docs/00_project_management/PROJECT_STATUS.md`
3. `docs/00_project_management/MASTER_PHASE_MAP.md`
4. `docs/00_project_management/WORKFLOW_GOVERNANCE.md`
5. `docs/00_project_management/DECISION_LOG.md`
6. `dataset/00_catalog/external_dataset_registry.csv`

## 文件職責

| 文件 | 用途 | 更新時機 |
|---|---|---|
| `PROJECT_CONTEXT_BRIEF.md` | 不可變核心架構與長期規則 | 重大架構 ADR 通過後 |
| `PROJECT_STATUS.md` | 當前 Phase、完成項目、阻塞與下一步 | 每次 checkpoint |
| `MASTER_PHASE_MAP.md` | 完整路線、前置條件與驗收 Gate | Phase 設計改變時 |
| `WORKFLOW_GOVERNANCE.md` | 任務、測試、文件與 Git 作業規範 | 流程規則改變時 |
| `DECISION_LOG.md` | 重大決策、原因與取代關係 | 每次重大決策 |
| `external_dataset_registry.csv` | Kaggle／Roboflow 候選、授權與採用狀態 | 每個外部資料集事件 |

## 單一真實來源原則

- Git Repository：正式真相來源
- ChatGPT Memory：輔助
- 對話：臨時工作區
- 未寫入文件並提交 Git 的重大決策，視為尚未正式納入專案
