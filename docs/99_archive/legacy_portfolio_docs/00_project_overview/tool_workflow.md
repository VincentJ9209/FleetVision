# 工具使用與協作流程

## 工具角色

| 工具 | 角色 |
|---|---|
| Codex 付費版 | 主要工程助手，負責產生、修改、重構、測試程式與文件 |
| Cursor 免費版 | 主要 IDE，負責開啟 repo、查看檔案、審查 diff、手動修改 |
| VS Code | 備援 IDE 與穩定工程環境 |
| GitHub | 程式碼與文件版本控管 |
| Google Drive | 大型圖片、YOLO dataset、Colab 訓練結果、模型權重 |
| 外接硬碟 | 原始資料與成果完整備份 |
| Colab | YOLOv8 GPU 訓練 |
| Docker Compose | PostgreSQL、MLflow、Streamlit 服務管理 |
| PostgreSQL | 儲存 metadata、prediction、comparison result |
| Streamlit | Dashboard 與成果展示 |
| MLflow | 模型實驗追蹤 |

## 主要工作流

```text
GitHub 建立 FleetVision repo
    ↓
桌機 clone repo
    ↓
Cursor 開啟 repo
    ↓
Codex 在 repo 中產生 / 修改程式
    ↓
本機執行與測試
    ↓
git commit / push
    ↓
大型資料放 Google Drive / 外接硬碟
    ↓
Colab 掛載 Google Drive 訓練 YOLOv8
    ↓
模型結果回存 Google Drive
    ↓
桌機下載模型並執行推論 / 入庫
    ↓
Docker Compose 啟動 PostgreSQL / Dashboard
    ↓
Streamlit 展示結果
    ↓
Demo package 備份到 Google Drive / USB
```

## 工作原則

- 每次只請 Codex 完成一個明確任務。
- Codex 完成後必須檢查 diff。
- 可以執行的程式一定要執行驗證。
- 有價值的修改才 commit。
- 大型資料不進 GitHub。
- 成果發表需要準備 demo video 與 CSV fallback。
