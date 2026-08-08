# iRent 借還車新增車損車況辨識專案

> 最終執行版本：以 **Cursor 為主、VS Code 為輔、Colab 訓練、PostgreSQL + Docker Compose 管理資料、YOLOv8 Detect 建立車損偵測 baseline、Streamlit 展示結果**。

---

## 1. 專案目標

本專案目標是建立一套 iRent 借還車外觀車況辨識流程，透過 App 拍照、AI 車損辨識與前後差異比對，協助判斷還車時是否出現疑似新增車損。

整體專案分為三階段：

| 階段 | 任務 | 負責重點 |
|---|---|---|
| Phase A | App 拍照品質與角度控管 | 確認左前、左後、右前、右後，且照片需包含車牌與車輪 |
| Phase B | 車輛外觀車損辨識 | 使用 YOLOv8 Detect 偵測可見車損位置，這是本專案主要負責範圍 |
| Phase C | 結果呈現與通知 | Dashboard、資料庫、App / Email 通知 |

目前本專案以 **Phase B 車損偵測模型** 作為核心。

---

## 2. 目前資料狀況

| 資料來源 | 數量 | 狀況 | 使用策略 |
|---|---:|---|---|
| 各角度車況照片 | 約 27,367 張 | 包含車內、車外、不同角度、不同光線與品質 | 先分類篩選，只保留外觀相關照片 |
| 輕微不索賠車損照片 | 約 240 張 | 有車損但未必構成索賠 | 標註為 `damage`，severity 只存在 metadata |
| 嚴重索賠車損照片 | 約 53 張 | 數量太少，不適合直接訓練索賠模型 | 標註為 `damage`，claim 只存在 metadata |
| 同車借還車成對照片 | 暫無 | 無法完整訓練新增車損模型 | 先建立單張車損偵測模型與比對規則 |

---

## 3. 重要決策

### 3.1 第一版不做索賠分類

目前不直接訓練：

```text
normal / minor_damage / claim_damage
```

原因：

- claim-level 圖片只有約 53 張，樣本過少。
- 索賠與否是業務判斷，不完全等同視覺特徵。
- 直接訓練索賠分類容易 overfit。

第一版只訓練：

```yaml
names:
  0: damage
```

### 3.2 第一版採用 YOLOv8 Detect

原因：

- 標註成本較低。
- 適合 MVP 與課程專題。
- 可輸出 bbox、confidence、class，方便 dashboard 顯示。
- 未來可升級 YOLOv8 Segmentation，但第一版不必一開始承擔 polygon 標註成本。

### 3.3 新增車損判斷先做規則模組

目前沒有借還車成對資料，因此現階段不訓練「新增車損模型」。

現階段先建立：

```text
單張車損偵測模型
    ↓
pickup / return 同角度結果比對模組
    ↓
IoU + confidence threshold + review_required rule
```

等未來取得成對照片後，再進行 paired validation。

---

## 4. 最終技術架構

```text
Cursor / VS Code
    ↓
Python 專案開發
    ↓
圖片 metadata 建立與資料清理
    ↓
CVAT / Label Studio 標註 YOLO bbox
    ↓
Colab 訓練 YOLOv8 Detect
    ↓
批次推論輸出 CSV / annotated images
    ↓
PostgreSQL 儲存 metadata / predictions / comparison results
    ↓
Streamlit Dashboard 顯示案件與模型結果
    ↓
MLflow 記錄模型實驗與版本
```

---

## 5. 主要工具與用途

| 工具 | 用途 | 何時使用 |
|---|---|---|
| Cursor | 主力 AI IDE，產生與修改程式碼 | 全階段 |
| VS Code | 備用 IDE，穩定 debug 與標準開發 | 全階段 |
| Colab | GPU 訓練 YOLOv8 | 模型訓練階段 |
| Git / GitHub | 版本控管 | 每完成一階段就 commit |
| Python | 資料處理、模型推論、Dashboard | 全階段 |
| OpenCV | 圖片讀取、模糊、亮度、品質檢查 | 資料前處理 |
| pandas / numpy | metadata、prediction table、EDA | 資料分析 |
| Ultralytics YOLOv8 | 車損偵測模型 | 模型訓練 / 推論 |
| CVAT / Label Studio | 車損 bbox 標註 | 標註階段 |
| Docker Compose | 啟動 PostgreSQL、MLflow、Streamlit | 工程整合 |
| PostgreSQL | 儲存 metadata、預測結果與比對結果 | 資料庫階段 |
| DBeaver / pgAdmin | 查看 PostgreSQL 資料表 | DB 檢查 |
| Streamlit | Dashboard 與人工覆核介面 | 展示階段 |
| MLflow | 紀錄訓練參數、metrics、模型版本 | 模型迭代 |

---

## 6. 專案資料夾結構

```text
irent-damage-detection/
│
├── README.md
├── AGENTS.md
├── CODEX_WORKFLOW.md
├── PHASE_GUIDE.md
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── .env.example
│
├── .agents/
│   └── skills/
│       ├── project-orchestrator/
│       ├── dataset-auditor/
│       ├── image-review-builder/
│       ├── yolo-dataset-builder/
│       ├── yolo-trainer/
│       ├── postgres-docker-engineer/
│       ├── prediction-pipeline/
│       ├── damage-comparison-engineer/
│       ├── streamlit-dashboard-builder/
│       └── mlflow-tracker/
│
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── metadata/
│
├── notebooks/
│   ├── 01_data_inventory.ipynb
│   ├── 02_image_quality_check.ipynb
│   ├── 03_annotation_eda.ipynb
│   ├── 04_train_yolov8_detect_colab.ipynb
│   ├── 05_evaluate_model.ipynb
│   └── 06_before_after_comparison.ipynb
│
├── src/
│   ├── data/
│   │   ├── build_metadata.py
│   │   ├── filter_exterior.py
│   │   ├── split_dataset.py
│   │   └── export_yolo_dataset.py
│   │
│   ├── vision/
│   │   ├── quality_check.py
│   │   ├── validate_yolo_dataset.py
│   │   ├── train_yolo.py
│   │   ├── predict_damage.py
│   │   └── compare_damage.py
│   │
│   ├── db/
│   │   ├── schema.sql
│   │   ├── init_db.py
│   │   ├── insert_metadata.py
│   │   └── insert_predictions.py
│   │
│   └── app/
│       ├── image_review_app.py
│       └── streamlit_dashboard.py
│
├── configs/
│   ├── data.yaml
│   ├── train_yolov8s.yaml
│   └── thresholds.yaml
│
├── models/
├── outputs/
│   ├── predictions/
│   ├── reports/
│   ├── metrics/
│   └── figures/
└── tests/
```

---

## 7. 快速開始

### 7.1 建立環境

```bash
python -m venv .venv
source .venv/bin/activate  # macOS / Linux
# Windows PowerShell:
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 7.2 啟動 PostgreSQL 與相關服務

```bash
docker compose up -d
```

### 7.3 建立 metadata

```bash
python src/data/build_metadata.py \
  --input_dir data/raw \
  --output_csv data/metadata/image_metadata.csv
```

### 7.4 啟動人工圖片審查 App

```bash
streamlit run src/app/image_review_app.py
```

### 7.5 檢查 YOLO dataset

```bash
python src/vision/validate_yolo_dataset.py \
  --dataset_root data/processed \
  --data_yaml configs/data.yaml \
  --output_csv outputs/reports/yolo_dataset_validation.csv
```

### 7.6 在 Colab 訓練 YOLOv8

建議在 Colab 執行 notebook：

```text
notebooks/04_train_yolov8_detect_colab.ipynb
```

或使用：

```bash
python src/vision/train_yolo.py \
  --data_yaml configs/data.yaml \
  --model yolov8s.pt \
  --epochs 100 \
  --imgsz 640 \
  --batch 16 \
  --project outputs/runs \
  --name irent_damage_yolov8s_v1
```

### 7.7 執行批次推論

```bash
python src/vision/predict_damage.py \
  --model models/yolov8_damage_v1.pt \
  --source data/processed/images/test \
  --conf 0.25 \
  --output_csv outputs/predictions/damage_predictions.csv
```

### 7.8 啟動 Dashboard

```bash
streamlit run src/app/streamlit_dashboard.py
```

---

## 8. 第一版 MVP 驗收標準

第一版完成時，至少要有：

- [ ] 可掃描圖片並建立 `image_metadata.csv`
- [ ] 可人工分類車外 / 車內 / 低品質圖片
- [ ] 有 YOLO 格式資料集與 `configs/data.yaml`
- [ ] 可訓練 YOLOv8 Detect 單一類別 `damage`
- [ ] 可輸出預測 bbox、confidence、class_name、model_version
- [ ] 可將 metadata 與 prediction 寫入 PostgreSQL
- [ ] 可用 Streamlit dashboard 顯示圖片與車損框
- [ ] 可展示 before-after comparison 規則函數，即使目前僅用模擬或人工配對資料
- [ ] README 能讓他人重現基本流程

---

## 9. 目前不做與未來再做

### 目前不做

- 不訓練索賠 / 不索賠二分類模型。
- 不訓練新增車損模型。
- 不直接使用車內照片做外觀車損模型。
- 不手動把原圖硬拉成 640x640。

### 未來再做

- 補 100 組以上同車、同角度、借還車 paired validation cases。
- 升級 YOLOv8 Segmentation。
- 建立人工覆核回饋機制。
- 將人工覆核結果回流成下一版訓練資料。
- 導入 API，例如 FastAPI。
- 導入正式 object storage，例如 S3 / GCS / MinIO。

