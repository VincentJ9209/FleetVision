# PHASE_GUIDE.md

# iRent 車損辨識專案分階段實作手冊

> 使用方式：每次只做一個階段。完成後測試、檢查輸出、commit，再進下一階段。

---

## Phase 0：開發環境與專案骨架

### 目標

建立可維護的專案結構，讓 Cursor、VS Code、Colab、Docker、PostgreSQL 都能順利協作。

### 你要做什麼

1. 建立 GitHub repo。
2. 用 Cursor 開啟專案資料夾。
3. 放入 `README.md`、`AGENTS.md`、`CODEX_WORKFLOW.md`、`.agents/skills/`。
4. 建立 Python venv。
5. 建立 `requirements.txt`。
6. 建立基本資料夾。
7. 第一次 commit。

### 產出檔案

```text
README.md
AGENTS.md
CODEX_WORKFLOW.md
requirements.txt
.env.example
Dockerfile
docker-compose.yml
data/
notebooks/
src/
configs/
models/
outputs/
tests/
```

### 驗收標準

- [ ] 專案可以用 Cursor 開啟。
- [ ] `python --version` 正常。
- [ ] `pip install -r requirements.txt` 正常。
- [ ] GitHub repo 已建立。
- [ ] 第一個 commit 完成。

---

## Phase 1：建立圖片 metadata

### 目標

把混亂的圖片資料轉成可分析、可篩選、可追蹤的表格。

### 為什麼重要

你目前有 27,367 張照片，但裡面混有車內、車外、模糊、夜間、角度不一等情況。如果沒有 metadata，後面訓練會失控。

### 你要做什麼

建立：

```text
src/data/build_metadata.py
```

掃描 `data/raw/`，輸出：

```text
data/metadata/image_metadata.csv
```

### metadata 欄位

| 欄位 | 說明 |
|---|---|
| image_id | 圖片唯一 ID |
| file_path | 圖片路徑 |
| filename | 檔名 |
| file_extension | 副檔名 |
| file_size_bytes | 檔案大小 |
| image_width | 圖片寬 |
| image_height | 圖片高 |
| aspect_ratio | 長寬比 |
| is_readable | 是否可讀 |
| blur_score | 模糊分數 |
| brightness | 平均亮度 |
| photo_type | exterior / interior / irrelevant / low_quality / unknown |
| angle | front / rear / left / right / front_left / front_right / rear_left / rear_right / unknown |
| has_visible_damage | 0 / 1 / unknown |
| severity_label | minor_non_claim / claim / unknown |
| source_group | A / B / C |
| split | train / val / test / unused |

### 執行方式

```bash
python src/data/build_metadata.py \
  --input_dir data/raw \
  --output_csv data/metadata/image_metadata.csv
```

### 驗收標準

- [ ] 產生 `image_metadata.csv`。
- [ ] 總列數接近原始圖片數。
- [ ] 壞圖有被標記，不會讓程式中斷。
- [ ] 有 blur_score 與 brightness。
- [ ] 可以用 pandas 讀取 CSV。

---

## Phase 2：人工分類車外 / 車內 / 低品質照片

### 目標

從混合照片中篩出外觀照片，避免車內圖片污染車損模型。

### 你要做什麼

建立 Streamlit 審查工具：

```text
src/app/image_review_app.py
```

讓你快速把圖片標成：

```text
exterior / interior / irrelevant / low_quality / unknown
```

### 執行方式

```bash
streamlit run src/app/image_review_app.py
```

### 建議流程

1. 先抽樣 500 張分類。
2. 檢查分類規則是否清楚。
3. 再擴大到 2,000～5,000 張。
4. 優先標出外觀正常照與容易誤判照片。

### 驗收標準

- [ ] 可以顯示圖片。
- [ ] 可以按鈕分類。
- [ ] 進度會存到 CSV。
- [ ] 可以過濾未審查圖片。
- [ ] 至少完成第一批外觀照片篩選。

---

## Phase 3：車損標註規則與 YOLO bbox 標註

### 目標

建立 YOLOv8 Detect 可訓練資料。

### 第一版標籤

```yaml
names:
  0: damage
```

### 要標註

- 刮傷
- 擦傷
- 凹陷
- 撞傷
- 掉漆
- 裂痕
- 破損

### 不標註

- 車身反光
- 車門縫
- 車燈輪廓
- 影子
- 水痕
- 污漬，除非專案定義為車況異常
- 糊到看不清楚的疑似損傷

### 工具建議

- CVAT：較適合正式標註與多人協作。
- Label Studio：較容易快速開始。

### 標註資料策略

| 類型 | 建議數量 |
|---|---:|
| 輕微車損 | 240 全部標 |
| 嚴重車損 | 53 全部標 |
| 外觀正常照 | 1,000～3,000 張，作為 negative samples |
| 反光 / 水痕 / 陰影 / 髒污 | 300～800 張，作為 hard negatives |

### 驗收標準

- [ ] 每張車損圖都有 YOLO label。
- [ ] 正常圖可以沒有 label 或 empty label。
- [ ] 標註格式為 `class_id x_center y_center width height`。
- [ ] 座標為 0～1 normalized。
- [ ] 類別只有 `0: damage`。

---

## Phase 4：建立 YOLO dataset 與資料切分

### 目標

把標註後資料整理成 YOLOv8 可訓練格式。

### 資料夾格式

```text
data/processed/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    ├── val/
    └── test/
```

### data.yaml

```yaml
path: data/processed
train: images/train
val: images/val
test: images/test

names:
  0: damage
```

### 重要原則

不要純隨機切圖。如果 metadata 裡有 vehicle_id 或 rental_id，應用 group split，避免同一台車或同一次租借流入 train 與 test。

### 驗收標準

- [ ] `configs/data.yaml` 存在。
- [ ] train / val / test 圖片與 label 對得起來。
- [ ] `validate_yolo_dataset.py` 通過。
- [ ] 類別只有 `damage`。

---

## Phase 5：Colab 訓練 YOLOv8 Detect baseline

### 目標

訓練第一版可運作的車損偵測模型。

### 建議設定

| 項目 | 設定 |
|---|---|
| model | yolov8s.pt |
| task | detect |
| class | damage |
| imgsz | 640 |
| epochs | 50～100 |
| batch | 依 Colab GPU 調整 |
| conf 測試 | 0.25 / 0.4 / 0.6 |

### 注意

`imgsz=640` 是 YOLO 訓練輸入尺寸，不代表你要手動把原圖硬拉成 640x640。

### 驗收標準

- [ ] Colab 可完成訓練。
- [ ] 產生 best.pt。
- [ ] 有 metrics、confusion matrix、sample prediction。
- [ ] 可以在 test images 上 predict。
- [ ] 保存模型到 `models/yolov8_damage_v1.pt`。

---

## Phase 6：模型評估與錯誤分析

### 目標

不要只看模型有沒有跑起來，而是找出錯誤來源並改善資料。

### 要看指標

| 指標 | 意義 |
|---|---|
| precision | 預測有車損時，有多少是真的 |
| recall | 真實車損有多少被抓到 |
| mAP50 | IoU 0.5 下的表現 |
| mAP50-95 | 更嚴格的定位表現 |
| false positive | 誤把正常特徵當車損 |
| false negative | 真車損沒有抓到 |

### 錯誤分析表

```text
outputs/reports/error_analysis.csv
```

欄位：

| 欄位 | 說明 |
|---|---|
| image_id | 圖片 ID |
| error_type | FP / FN / localization_error / low_confidence |
| reason | 反光、陰影、水痕、太小、模糊等 |
| action | 補資料、修標註、調 threshold |

### 驗收標準

- [ ] 至少整理 30～50 個錯誤案例。
- [ ] 知道模型最常誤判什麼。
- [ ] 有下一輪資料補強方向。

---

## Phase 7：PostgreSQL + Docker Compose

### 目標

把專案從 notebook demo 提升為完整工程專案。

### 你要做什麼

建立：

```text
docker-compose.yml
src/db/schema.sql
src/db/init_db.py
src/db/insert_metadata.py
src/db/insert_predictions.py
```

### 建議資料表

| 表名 | 用途 |
|---|---|
| image_metadata | 儲存圖片 metadata |
| vehicle_photos | 儲存車輛照片紀錄 |
| damage_predictions | 儲存 YOLO 預測結果 |
| damage_comparison_results | 儲存前後比對結果 |
| model_versions | 儲存模型版本與設定 |

### 驗收標準

- [ ] `docker compose up -d` 可啟動 PostgreSQL。
- [ ] schema 可以建立。
- [ ] metadata 可寫入 DB。
- [ ] prediction 可寫入 DB。
- [ ] DBeaver / pgAdmin 可查到資料。

---

## Phase 8：批次推論與 prediction pipeline

### 目標

讓訓練好的模型可以批次處理圖片，輸出結構化結果。

### 你要做什麼

建立：

```text
src/vision/predict_damage.py
```

輸出：

```text
outputs/predictions/damage_predictions.csv
outputs/predictions/annotated_images/
```

### 欄位

| 欄位 | 說明 |
|---|---|
| image_id | 圖片 ID |
| file_path | 圖片路徑 |
| class_id | 類別 ID |
| class_name | damage |
| confidence | 信心分數 |
| x1, y1, x2, y2 | bbox 座標 |
| image_width, image_height | 原始尺寸 |
| model_version | 模型版本 |

### 驗收標準

- [ ] 有車損圖片可輸出 bbox。
- [ ] 無車損圖片也有紀錄或明確處理方式。
- [ ] annotated images 可視覺檢查。
- [ ] prediction CSV 可寫入 PostgreSQL。

---

## Phase 9：借還車前後差異比對模組

### 目標

雖然目前沒有成對資料，但先建立可接收 pickup / return predictions 的規則模組。

### 判斷邏輯

| 狀況 | 結果 |
|---|---|
| 借車無損，還車無損 | no_new_damage |
| 借車有損，還車同位置也有損 | existing_damage |
| 借車無損，還車有損 | suspected_new_damage |
| 借車有損，還車不同位置出現新損 | suspected_new_damage |
| 圖片品質差或角度不一致 | review_required |

### 核心方法

- Match by `rental_id + vehicle_id + angle`
- 比較 return bbox 與 pickup bbox 的 IoU
- return confidence 高且 max IoU 低 → 疑似新增車損

### 驗收標準

- [ ] `calculate_iou()` 有 unit tests。
- [ ] 可讀 pickup predictions CSV 與 return predictions CSV。
- [ ] 可輸出 `damage_comparison_results.csv`。
- [ ] 可標記 `review_required`。

---

## Phase 10：Streamlit Dashboard

### 目標

把模型結果變成可展示、可檢查、可說服人的視覺化成果。

### Dashboard 頁面

1. 總覽頁
2. 圖片與 bbox 檢視頁
3. 案件比對頁
4. 錯誤分析頁
5. 模型版本比較頁

### 必備功能

- summary metrics
- confidence distribution
- result distribution
- image viewer
- bbox overlay
- filter by confidence / result / angle / model_version
- review_required case list

### 驗收標準

- [ ] 可啟動 dashboard。
- [ ] 可顯示圖片與 bbox。
- [ ] 可篩選疑似新增損傷。
- [ ] 可展示模型表現與錯誤案例。

---

## Phase 11：MLflow 實驗追蹤

### 目標

記錄每一次模型訓練，避免之後不知道哪個模型最好。

### 需要記錄

| 類型 | 內容 |
|---|---|
| params | model、imgsz、epochs、batch、conf |
| metrics | precision、recall、mAP50、mAP50-95 |
| artifacts | best.pt、data.yaml、confusion matrix、sample predictions |
| tags | dataset_version、model_version |

### 驗收標準

- [ ] MLflow UI 可啟動。
- [ ] 每次訓練有 run record。
- [ ] 可比較 v1、v2、v3。

---

## Phase 12：成果報告與專題展示

### 目標

把技術成果轉成可說服導師與小組的報告。

### 報告重點

1. 問題定義。
2. 現有資料限制。
3. 為什麼先做 YOLOv8 Detect。
4. 為什麼不直接做索賠分類。
5. 資料前處理流程。
6. 標註規則。
7. 模型訓練流程。
8. 評估結果。
9. 錯誤分析。
10. 前後比對規則。
11. Dashboard 展示。
12. 未來升級方向。

### 必須誠實說明

目前沒有真實大量借還車 paired data，所以本階段完成的是：

```text
單張外觀車損偵測模型 + 前後比對規則雛形
```

不是已經完成正式可上線的全自動索賠判斷系統。

