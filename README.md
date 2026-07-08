# FleetVision

FleetVision 是一個針對共享車輛借還車情境設計的車輛外觀車損辨識專案。第一版目標是建立可見車損偵測流程：從圖片資料盤點、外觀照片篩選、YOLOv8 Detect 訓練、模型推論、PostgreSQL 儲存，到 Streamlit Dashboard 展示。

> 本專案以 **Codex 付費版為主要工程助手**，**Cursor 免費版作為主要 IDE / 編輯介面**，**VS Code 作為備援**，**Colab 作為 YOLOv8 GPU 訓練環境**。

---

## 專案定位

FleetVision 的目標不是一開始直接做「索賠判斷模型」，而是先完成較穩定、可解釋的基礎能力：

1. 建立圖片 metadata 與資料品質檢查流程。
2. 從混合車況照片中篩選外觀照片。
3. 標註可見車損 bounding box。
4. 使用 YOLOv8 Detect 訓練單類別 `damage` 模型。
5. 輸出車損位置、信心分數、模型版本。
6. 將結果寫入 PostgreSQL。
7. 以 Dashboard 展示模型偵測結果與人工覆核案例。
8. 預留未來借車 / 還車同角度照片的新增車損比對模組。

---

## 目前資料來源規劃

原始素材請放在：

```text
FleetVision/dataset/01_raw/
├── 01_general_fleet/images/          # 一般車況照片，可能包含車內、車外、正常、未知
├── 02_claimable_damage/images/       # 較嚴重、可能列入索賠的車損照片
└── 03_minor_damage/images/           # 輕微、不列入索賠的車損照片
```

原本對應的 Excel 檔請放在：

```text
FleetVision/dataset/00_catalog/raw_excels/
```

例如：

```text
FleetVision/dataset/00_catalog/raw_excels/01_general_fleet.xlsx
FleetVision/dataset/00_catalog/raw_excels/02_claimable_damage.xlsx
FleetVision/dataset/00_catalog/raw_excels/03_minor_damage.xlsx
```

---

## 專案結構

```text
FleetVision/
├── README.md
├── AGENTS.md
├── .gitignore
├── .env.example
├── requirements.txt
├── docker-compose.yml
├── docs/
├── .agents/
├── dataset/
├── notebooks/
├── src/
├── configs/
├── sql/
├── scripts/
├── tests/
├── outputs/
├── models/
└── demo/
```

詳細資料夾用途請見：

```text
docs/03_data_guidelines/dataset_structure.md
```

---

## 第一版建模策略

第一版不要訓練：

```text
normal / minor_damage / claimable_damage
```

第一版只訓練：

```text
class 0: damage
```

原因：

- 目前 claimable damage 數量偏少，不適合直接訓練索賠分類。
- 「是否索賠」是業務規則，不完全等於視覺損傷類型。
- 先讓模型穩定偵測可見車損位置，後續再做嚴重度、人工覆核與索賠候選規則。

---

## 工具分工

| 工具 | 角色 |
|---|---|
| Codex 付費版 | 主要工程助手：產生程式、修錯、重構、文件 |
| Cursor 免費版 | 主要 IDE：開啟 repo、查看 diff、手動編輯 |
| VS Code | 備援 IDE、標準工程工具 |
| GitHub | 程式碼與文件版本控管 |
| Google Drive | 原始圖片、YOLO dataset、模型、Colab 結果同步 |
| 外接硬碟 | 全量資料備份 |
| Colab | YOLOv8 GPU 訓練 |
| Docker Compose | 啟動 PostgreSQL、MLflow、Streamlit |
| PostgreSQL | 儲存 metadata、prediction、comparison result |
| Streamlit | Dashboard 與 demo 展示 |
| MLflow | 實驗追蹤與模型版本紀錄 |

---

## 建議實作順序

1. 建立專案骨架。
2. 放置原始資料與 Excel。
3. 建立 metadata 掃描腳本。
4. 篩選外觀 / 車內 / 低品質 / 無關照片。
5. 建立標註規則。
6. 標註第一版 `damage` bbox。
7. 建立 YOLOv8 dataset。
8. 在 Colab 訓練 YOLOv8 Detect baseline。
9. 做模型評估與錯誤分析。
10. 用 Docker Compose 啟動 PostgreSQL。
11. 批次推論並寫入 PostgreSQL。
12. 建立 Dashboard。
13. 製作 demo package 與發表備援資料。

---

## 重要原則

- 原始圖片只放在 `dataset/01_raw/`，不要直接修改。
- 中間產物放 `dataset/02_interim/`。
- 人工分類後資料放 `dataset/03_reviewed/`。
- 標註資料放 `dataset/04_annotations/`。
- YOLO 訓練資料放 `dataset/05_yolo/`。
- 展示用小樣本放 `dataset/06_demo_samples/`。
- 大型圖片、模型權重、預測圖片不要放 GitHub。
- 程式碼、設定檔、文件、schema、少量 sample 可以放 GitHub。
