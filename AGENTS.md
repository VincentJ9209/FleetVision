# AGENTS.md

## 專案名稱

FleetVision

## 專案背景

FleetVision 是共享車輛借還車情境下的車輛外觀車損辨識專案。第一版目標是完成單張外觀照片的可見車損偵測，並建立可擴充到借還車前後差異比對的工程架構。

## 主要工程助手

本專案以 Codex 付費版作為主要工程助手。Cursor 免費版作為主要 IDE / 編輯器，VS Code 作為備援。

## 當前建模策略

第一版模型採用：

- YOLOv8 Detect
- 單一類別：`damage`
- 標註方式：bounding box
- 任務：偵測可見車損位置與信心分數

請不要在第一版直接訓練以下分類：

- `minor_damage`
- `claimable_damage`
- `normal`
- `new_damage`

原因：目前 claimable damage 樣本數偏少，且索賠與否是業務規則，不應直接等同於模型類別。

## 目前資料來源

資料來源分為三類：

```text
dataset/01_raw/01_general_fleet/images/
dataset/01_raw/02_claimable_damage/images/
dataset/01_raw/03_minor_damage/images/
```

Excel / catalog 類資料放在：

```text
dataset/00_catalog/raw_excels/
```

## 資料處理原則

1. 不修改 `dataset/01_raw/` 原始圖片。
2. 任何中間處理結果放入 `dataset/02_interim/`。
3. 人工分類後結果放入 `dataset/03_reviewed/`。
4. 標註結果放入 `dataset/04_annotations/`。
5. YOLO 訓練資料放入 `dataset/05_yolo/`。
6. demo 小樣本放入 `dataset/06_demo_samples/`。
7. 大型圖片與模型檔不要放 GitHub。

## 程式碼規則

1. 正式 Python 程式放在 `src/fleetvision/`。
2. Notebook 只作為探索與 Colab 訓練用途，不放主要商業邏輯。
3. 函數、類別、檔名、欄位名稱使用英文。
4. 文件、註解、README 可使用繁體中文。
5. 不要硬編碼個人電腦的絕對路徑。
6. 請使用 config 或 CLI arguments 管理路徑。
7. 每個主要腳本都要能從專案根目錄執行。
8. 每個資料處理腳本都應輸出 summary。
9. 重要函數應有 type hints 與 docstring。
10. 重要邏輯，例如 IoU，比對規則、label validation，必須有測試。

## Git 與版本控管規則

請使用清楚的 commit message，例如：

```text
feat: add image metadata builder
fix: handle corrupted images
chore: initialize project structure
docs: update dataset structure guide
test: add iou unit tests
```

## Docker / PostgreSQL 原則

1. Docker Compose 用於本機服務，例如 PostgreSQL、MLflow、Streamlit。
2. PostgreSQL schema 放在 `sql/schema.sql`。
3. `.env` 不得進 GitHub。
4. `.env.example` 可以放 GitHub。
5. 資料庫 dump 不進 GitHub，放 Google Drive 或外接硬碟備份。

## Colab 訓練原則

1. Colab 用於 YOLOv8 GPU 訓練。
2. 訓練資料從 Google Drive 掛載。
3. 模型權重輸出回 Google Drive。
4. Notebook 範本可以放 GitHub，但大量訓練輸出不放。

## 回答與協作要求

當協助產生或修改程式時，請提供：

1. 修改了哪些檔案。
2. 如何執行。
3. 會產生哪些輸出。
4. 驗收標準。
5. 新手應理解的關鍵概念。
6. 可能風險與下一步。

## 不要做的事

- 不要把大型圖片放入 Git。
- 不要把 `.env` 放入 Git。
- 不要直接覆蓋 raw data。
- 不要一次生成整個專案所有功能。
- 不要把 claimable / minor 當成第一版 YOLO 類別。
- 不要宣稱目前已能完整判斷真實新增車損，因為尚未有大量真實借還車成對資料。
