# FleetVision 新對話上下文摘要

如果後續要重開新對話，請將以下內容貼給 ChatGPT / Codex 作為上下文。

---

我正在做一個數據分析與機器學習專案，專案名稱是 **FleetVision**。

專案主題是共享車輛借還車場景中的車輛外觀車損辨識。第一階段會要求使用者在 App 拍攝標準角度照片；第二階段是我主要負責的模型訓練與車損辨識；第三階段是 Dashboard 與通知展示。

目前我負責第二階段，目標是先建立單張外觀照片的可見車損偵測模型。第一版不直接做索賠分類，也不直接做完整新增車損判斷，因為目前尚未取得大量真實借還車成對照片。

目前資料包含：

1. `01_general_fleet`：約 27,367 張一般車況照片，包含車內、車外、不同角度、不同品質。
2. `02_claimable_damage`：約 53 張較嚴重、可能索賠車損照片。
3. `03_minor_damage`：約 240 張輕微、不列入索賠車損照片。

第一版模型策略：

- 使用 YOLOv8 Detect。
- 第一版只訓練單一類別：`damage`。
- 標註方式使用 bounding box。
- 不把 `minor_damage` / `claimable_damage` 當成 YOLO 第一版類別。
- 索賠與否後續用規則、嚴重度、人工覆核與業務流程處理。

主要工具策略：

- Codex 付費版：主要工程助手。
- Cursor 免費版：主要 IDE / 編輯介面。
- VS Code：備援。
- Colab：YOLOv8 GPU 訓練。
- GitHub：程式碼與文件版本控管。
- Google Drive：大型資料、Colab 訓練結果、模型權重。
- 外接硬碟：完整備份。
- Docker Compose：本機 PostgreSQL、MLflow、Streamlit。
- PostgreSQL：儲存 metadata、prediction、comparison result。
- Streamlit：Dashboard。

FleetVision 資料夾結構已決定：

```text
FleetVision/
├── docs/
├── .agents/skills/
├── dataset/
│   ├── 00_catalog/
│   ├── 01_raw/
│   ├── 02_interim/
│   ├── 03_reviewed/
│   ├── 04_annotations/
│   ├── 05_yolo/
│   └── 06_demo_samples/
├── notebooks/
├── src/fleetvision/
├── configs/
├── sql/
├── scripts/
├── tests/
├── outputs/
├── models/
└── demo/
```

原始資料放置：

```text
dataset/01_raw/01_general_fleet/images/
dataset/01_raw/02_claimable_damage/images/
dataset/01_raw/03_minor_damage/images/
```

Excel 檔放置：

```text
dataset/00_catalog/raw_excels/
```

請後續回答都以 FleetVision 新版架構為準，不要沿用舊的 irent-damage-detection 架構。
