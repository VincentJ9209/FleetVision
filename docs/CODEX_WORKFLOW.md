# CODEX_WORKFLOW.md

# Cursor + Codex 工作流與 Prompt 集

> 使用方式：在 Cursor 中，每次只貼一個 Prompt。完成後先執行、檢查輸出、修正錯誤、commit，再貼下一個 Prompt。

---

## 0. 語言策略

本專案建議：

| 類型 | 語言 |
|---|---|
| README、說明文件、prompt | 繁體中文 |
| 程式檔名 | 英文 |
| 函數名稱 | 英文 |
| class name | 英文 |
| SQL table / column | 英文 |
| CLI arguments | 英文 |
| config keys | 英文 |
| 註解 | 繁體中文或簡短英文皆可 |

原因：

- 你正在學習中，說明文件用繁體中文最容易理解。
- 程式碼與資料表名稱用英文，較符合實務與業界慣例。
- Cursor / Codex 對中英文混合任務可以處理，但 prompt 要明確。

建議每個 prompt 都加：

```text
請使用繁體中文說明，但程式碼檔名、函數名稱、資料表欄位、CLI arguments 使用英文。
```

---

## 1. Cursor 使用原則

每次請 Cursor 做事時，要求它：

1. 先讀 `AGENTS.md`。
2. 不要一次改太多不相關檔案。
3. 每次任務完成後列出修改檔案。
4. 說明如何執行。
5. 說明如何驗證。
6. 說明新手需要理解的概念。
7. 如果需要假資料，請放在 `data/sample/`，不要污染正式資料夾。

---

## 2. 推薦工作節奏

```text
Prompt → 產生程式 → 執行 → 看錯誤 → 修正 → 檢查輸出 → commit → 下一個 Prompt
```

建議每個階段開 branch：

```bash
git checkout -b phase-01-metadata
```

完成後：

```bash
git add .
git commit -m "feat: build image metadata pipeline"
```

---

# Prompt 0：建立專案骨架

```text
請先閱讀 AGENTS.md，然後建立 iRent 車損辨識專案的基本資料夾結構。

背景：
本專案以 Cursor 為主、VS Code 為輔、Colab 訓練 YOLOv8 Detect、PostgreSQL + Docker Compose 管理資料、Streamlit 做 Dashboard、MLflow 做實驗追蹤。

請建立以下資料夾：
- data/raw
- data/interim
- data/processed
- data/metadata
- data/sample
- notebooks
- src/data
- src/vision
- src/db
- src/app
- configs
- models
- outputs/predictions
- outputs/reports
- outputs/metrics
- outputs/figures
- tests

請建立以下檔案：
- requirements.txt
- .env.example
- Dockerfile
- docker-compose.yml
- .gitignore

requirements.txt 至少包含：
- pandas
- numpy
- opencv-python
- pillow
- ultralytics
- matplotlib
- plotly
- streamlit
- scikit-learn
- pyyaml
- sqlalchemy
- psycopg2-binary
- python-dotenv
- mlflow
- pytest

請注意：
- 不要寫 YOLO 訓練程式。
- 不要加入大型資料。
- 產出後請說明資料夾用途、如何建立虛擬環境、如何安裝 dependencies。
```

---

# Prompt 1：建立 Docker Compose + PostgreSQL + MLflow 基礎服務

```text
請先閱讀 AGENTS.md，然後建立完整但簡潔的 Docker Compose 設定。

目標：
使用 Docker Compose 啟動以下服務：
1. PostgreSQL
2. pgAdmin 或 Adminer，請選一個較容易使用的工具
3. MLflow tracking server

請修改或建立：
- docker-compose.yml
- .env.example
- README.md 中的 Docker 使用說明

PostgreSQL 需求：
- database: irent_damage_db
- user / password 從 .env 讀取
- volume 持久化資料
- port 預設 5432

MLflow 需求：
- port 預設 5000
- artifacts 儲存在本機 volume

請提供：
- docker compose up -d 的執行方式
- 如何檢查 container 是否啟動
- 如何連線 PostgreSQL
- 新手需要理解的 Docker Compose 概念

請不要新增與本任務無關的功能。
```

---

# Prompt 2：建立 PostgreSQL schema

```text
請先閱讀 AGENTS.md，然後建立 src/db/schema.sql。

目標：
為 iRent 車損辨識專案建立 PostgreSQL schema。

請建立以下資料表：
1. image_metadata
2. vehicle_photos
3. damage_predictions
4. damage_comparison_results
5. model_versions

需求：
- 使用 PostgreSQL 語法。
- 每張表要有 primary key。
- 加入 created_at timestamp。
- 常查欄位要加 index，例如 image_id、vehicle_id、rental_id、angle、model_version。
- bbox 使用 x1, y1, x2, y2 numeric columns。
- model raw output 可用 JSONB 欄位。
- 欄位名稱使用英文。
- SQL 檔案中請加上繁體中文註解，說明每張表用途。

請同時建立 src/db/init_db.py：
- 從 .env 讀取 DB 連線設定。
- 執行 schema.sql。
- 顯示成功或失敗訊息。

請提供執行方式與驗收方式。
```

---

# Prompt 3：建立圖片 metadata 腳本

```text
請先閱讀 AGENTS.md，然後建立 src/data/build_metadata.py。

目標：
遞迴掃描 data/raw 或指定資料夾中的圖片，建立 data/metadata/image_metadata.csv。

每張圖片要收集：
- image_id
- file_path
- filename
- file_extension
- file_size_bytes
- image_width
- image_height
- aspect_ratio
- is_readable
- blur_score，使用 Laplacian variance
- brightness，使用 grayscale mean
- photo_type，預設 unknown
- angle，預設 unknown
- has_visible_damage，預設 unknown
- severity_label，預設 unknown
- source_group，預設 unknown
- split，預設 unused

需求：
- 使用 pathlib、pandas、cv2、numpy。
- 壞圖不可讓程式中斷，要標記 is_readable=False。
- 提供 CLI arguments：--input_dir、--output_csv。
- 執行後列印 summary：總圖片數、可讀圖片數、壞圖數、輸出路徑。
- 加入 type hints 與 docstrings。
- 不要修改原始圖片。

請提供執行指令、預期輸出與如何檢查 CSV。
```

---

# Prompt 4：建立圖片人工分類 Streamlit App

```text
請先閱讀 AGENTS.md，然後建立 src/app/image_review_app.py。

目標：
建立一個簡單的 Streamlit app，協助人工分類圖片類型。

輸入：
- data/metadata/image_metadata.csv

分類選項：
- exterior
- interior
- irrelevant
- low_quality
- unknown

功能需求：
- 一次顯示一張圖片。
- 顯示 filename、image_width、image_height、blur_score、brightness。
- 按鈕分類圖片。
- 將分類結果存到 data/metadata/image_review_labels.csv。
- 可以只顯示未審查圖片。
- 可以顯示目前已審查數量與剩餘數量。
- 不要使用複雜架構，先求穩定可用。

完成後請說明：
- 如何啟動 app。
- 如何確認結果有被保存。
- 新手應理解的 Streamlit state 概念。
```

---

# Prompt 5：建立標註規則文件

```text
請建立 docs/annotation_guideline.md。

目標：
為 YOLOv8 Detect 車損標註建立清楚規範。

內容需要包含：
1. 第一版類別只有 damage。
2. 要標註的情況：刮傷、擦傷、凹陷、撞傷、掉漆、裂痕、破損。
3. 不標註的情況：反光、車門縫、車身線條、影子、水痕、拍糊看不清楚。
4. 輕微不索賠與索賠車損都標成 damage，但 severity 留在 metadata。
5. bbox 應框住完整可見車損區域。
6. 正常圖可作為 negative samples。
7. 標註品質檢查規則。
8. 常見錯誤案例。

文件請用繁體中文撰寫，讓小組成員可以照著標註。
```

---

# Prompt 6：建立 YOLO dataset 驗證工具

```text
請先閱讀 AGENTS.md，然後建立 src/vision/validate_yolo_dataset.py。

目標：
檢查 Ultralytics YOLO detection dataset 是否正確。

輸入：
- --dataset_root
- --data_yaml
- --output_csv

檢查項目：
- data.yaml 是否存在且可讀。
- train / val / test images 資料夾是否存在。
- label 檔是否與 image 對應。
- label 每列是否有 5 個值。
- class_id 是否有效。
- x_center、y_center、width、height 是否介於 0 到 1。
- width、height 是否大於 0。
- 區分 missing label、empty label、invalid label。

輸出：
- outputs/reports/yolo_dataset_validation.csv

請加入 summary print，並提供執行方式與驗收方式。
```

---

# Prompt 7：建立 YOLOv8 訓練腳本

```text
請先閱讀 AGENTS.md，然後建立 src/vision/train_yolo.py。

目標：
訓練 YOLOv8 Detect 車損偵測模型。

需求：
- 使用 ultralytics YOLO。
- CLI arguments：
  --data_yaml
  --model，預設 yolov8s.pt
  --epochs，預設 100
  --imgsz，預設 640
  --batch，預設 16
  --project，預設 outputs/runs
  --name，預設 irent_damage_yolov8s_v1
- 檢查 data_yaml 是否存在。
- 將訓練設定另存成 outputs/reports/training_config.json。
- 完成後說明 results 儲存位置。
- 加入清楚錯誤訊息。

提醒：
第一版只有一個類別 damage。
不要做索賠分類。
不要手動把原始圖片硬拉成 640x640。

請同時提供 Colab 使用方式說明。
```

---

# Prompt 8：建立批次推論腳本

```text
請先閱讀 AGENTS.md，然後建立 src/vision/predict_damage.py。

目標：
使用訓練好的 YOLOv8 模型對圖片資料夾做批次推論，輸出 CSV 與標註圖。

CLI arguments：
- --model
- --source
- --conf，預設 0.25
- --output_csv，預設 outputs/predictions/damage_predictions.csv
- --annotated_dir，預設 outputs/predictions/annotated_images
- --model_version，預設 manual_input

CSV 欄位：
- image_id
- file_path
- class_id
- class_name
- confidence
- x1
- y1
- x2
- y2
- image_width
- image_height
- model_version

需求：
- 沒有 detection 的圖片也要能處理，不可報錯。
- 儲存 annotated images。
- summary print：總圖片數、有 detection 圖片數、總 detection 數、輸出路徑。
- 加入 type hints 與 docstrings。

請提供執行方式與檢查方式。
```

---

# Prompt 9：建立 PostgreSQL 寫入腳本

```text
請先閱讀 AGENTS.md，然後建立以下腳本：
- src/db/insert_metadata.py
- src/db/insert_predictions.py

目標：
將 image_metadata.csv 與 damage_predictions.csv 寫入 PostgreSQL。

需求：
- 使用 SQLAlchemy。
- 從 .env 讀取 DB 連線資訊。
- 支援 upsert 或至少避免重複寫入造成失敗。
- 寫入前檢查必要欄位是否存在。
- 列印寫入筆數。
- 發生錯誤時提供清楚錯誤訊息。

請提供：
- 執行指令。
- 如何用 SQL 檢查資料是否寫入成功。
- 新手需要理解的 table、row、column、primary key、index 概念。
```

---

# Prompt 10：建立新增車損比對模組

```text
請先閱讀 AGENTS.md，然後建立 src/vision/compare_damage.py。

目標：
建立 pickup 與 return YOLO detection 結果的比對模組。

背景：
目前尚未有大量真實借還車成對資料，所以此模組先以 rule-based 方式建立，可用模擬或人工配對資料測試。

輸入：
- --pickup_predictions_csv
- --return_predictions_csv
- --metadata_csv
- --output_csv
- --conf_threshold，預設 0.4
- --iou_threshold，預設 0.2

邏輯：
- 依 rental_id、vehicle_id、angle 配對。
- 對每個 return damage bbox，計算與 pickup bboxes 的 max IoU。
- return confidence >= conf_threshold 且 max IoU < iou_threshold，標記 suspected_new_damage。
- return confidence >= conf_threshold 且 max IoU >= iou_threshold，標記 existing_damage。
- 沒有 return damage，標記 no_new_damage。
- 圖片品質差或缺少必要資料，標記 review_required。

輸出欄位：
- rental_id
- vehicle_id
- angle
- result
- new_damage_count
- max_confidence
- review_required
- reason

請另外建立 tests/test_compare_damage.py，至少測試 calculate_iou()。

完成後請說明此模組的限制：沒有 paired data 前，不能宣稱已完成正式新增車損模型。
```

---

# Prompt 11：建立 Streamlit Dashboard

```text
請先閱讀 AGENTS.md，然後建立 src/app/streamlit_dashboard.py。

目標：
建立 iRent 車損辨識結果 Dashboard。

輸入資料：
- data/metadata/image_metadata.csv
- outputs/predictions/damage_predictions.csv
- outputs/reports/damage_comparison_results.csv，如果存在就讀取；不存在則顯示提示。

功能需求：
1. 總覽指標：總圖片數、有車損偵測圖片數、總 detection 數、平均 confidence。
2. 篩選器：model_version、confidence threshold、class_name、angle、photo_type。
3. 圖片顯示：顯示原圖並畫 bbox。
4. prediction table：顯示目前篩選後的預測結果。
5. 圖表：confidence distribution、detections by angle、result distribution。
6. 如果有 comparison results，顯示 suspected_new_damage 與 review_required 案件。

需求：
- 使用 Streamlit + pandas + plotly。
- 若圖片檔案不存在，要顯示友善提示，不要 crash。
- 程式保持簡單，先求可展示。

請提供啟動方式與 dashboard 操作說明。
```

---

# Prompt 12：建立 MLflow 實驗追蹤整合

```text
請先閱讀 AGENTS.md，然後幫 src/vision/train_yolo.py 加入可選的 MLflow logging。

需求：
- 新增 CLI argument：--use_mlflow。
- 新增 --experiment_name，預設 irent_damage_detection。
- 記錄 params：model、epochs、imgsz、batch、data_yaml、run name。
- 記錄 artifacts：training_config.json、data.yaml、best.pt 如果存在。
- 如果 metrics 可取得，記錄 precision、recall、mAP50、mAP50-95。
- 若 MLflow server 未啟動，給清楚錯誤提示，不要讓使用者困惑。

請更新 README 的 MLflow 使用說明。
```

---

# Prompt 13：建立錯誤分析 Notebook 或 Script

```text
請先閱讀 AGENTS.md，然後建立 notebooks/05_evaluate_model.ipynb 或 src/vision/error_analysis.py，依你判斷較適合的方式。

目標：
協助分析 YOLO 車損偵測模型的錯誤案例。

需求：
- 讀取 damage_predictions.csv。
- 可篩選 low confidence detections。
- 可篩選高 confidence 但可能是 false positive 的案例。
- 建立 outputs/reports/error_analysis_template.csv。
- 欄位包含 image_id、file_path、prediction、human_review_result、error_type、reason、action。
- 產生基礎圖表：confidence distribution、detections per image、detections by angle。

請用繁體中文說明如何人工填寫 error_analysis_template.csv，以及如何根據錯誤案例改善下一版資料。
```

---

# Prompt 14：建立 Colab 訓練 Notebook

```text
請先閱讀 AGENTS.md，然後建立 notebooks/04_train_yolov8_detect_colab.ipynb。

目標：
讓使用者可以在 Google Colab 上訓練 YOLOv8 Detect。

Notebook 需要包含：
1. 專案目標說明。
2. 安裝 ultralytics。
3. 掛載 Google Drive，可選。
4. 檢查 data.yaml。
5. 顯示資料集路徑與類別。
6. 訓練 YOLOv8s，imgsz=640，epochs=100。
7. 驗證模型。
8. 對 test images 推論。
9. 將 best.pt 複製到 models/。
10. 顯示訓練結果圖與 sample predictions。

請用繁體中文 markdown cell 解釋每個步驟，讓初學者可以照著跑。
```

---

# Prompt 15：專題報告整理

```text
請根據目前專案內容，建立 docs/project_report_outline.md。

報告需要包含：
1. 專案背景與問題定義。
2. 三階段系統架構。
3. 第二階段負責範圍。
4. 現有資料限制。
5. 為什麼採用 YOLOv8 Detect。
6. 為什麼第一版不做索賠分類。
7. 資料前處理流程。
8. 標註規則。
9. 模型訓練流程。
10. 評估指標。
11. 錯誤分析。
12. PostgreSQL + Docker Compose 架構。
13. Dashboard 展示。
14. 沒有 paired data 的限制與後續驗證計畫。
15. 未來升級 YOLOv8 Segmentation 與人工覆核回饋流程。

請用繁體中文撰寫，風格要適合課程專題報告。
```

---

## 3. 建議 Commit 節奏

| 階段 | Commit message 範例 |
|---|---|
| 專案骨架 | `chore: initialize project structure` |
| Docker / DB | `feat: add docker compose and postgres schema` |
| metadata | `feat: build image metadata pipeline` |
| image review | `feat: add image review streamlit app` |
| annotation guide | `docs: add annotation guideline` |
| YOLO dataset | `feat: validate yolo dataset format` |
| YOLO training | `feat: add yolo training script` |
| prediction | `feat: add batch damage prediction pipeline` |
| DB insert | `feat: add database ingestion scripts` |
| comparison | `feat: add damage comparison module` |
| dashboard | `feat: add streamlit dashboard` |
| MLflow | `feat: integrate mlflow tracking` |
| report | `docs: add project report outline` |

---

## 4. 每次問 Cursor 都要加的品質要求

```text
請完成後務必提供：
1. 修改了哪些檔案。
2. 如何執行。
3. 預期會產生哪些輸出。
4. 如何驗證成功。
5. 可能出錯的原因。
6. 我作為初學者需要理解的概念。
```

