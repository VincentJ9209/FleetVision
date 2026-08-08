# AGENTS.md

## 專案背景

本專案是 iRent 借還車新增車損車況辨識系統。目標是建立一套車輛外觀車損偵測與結果展示流程。

目前專案負責重點是第二階段：

- 使用 YOLOv8 Detect 建立車輛外觀車損偵測模型。
- 輸出 bbox、class、confidence、model_version。
- 將 metadata、prediction、comparison results 寫入 PostgreSQL。
- 使用 Streamlit 建立 dashboard。
- 預留 pickup / return 同角度前後差異比對模組。

## 使用者能力狀態

使用者正在學習 Python、資料分析、機器學習、SQL、Git、GitHub、Colab、Docker、Cursor。回覆與產生程式碼時，請兼顧：

1. 可執行。
2. 可理解。
3. 可逐步驗證。
4. 不要一次產生過度複雜的大型系統。
5. 每次修改後要說明如何執行與如何檢查結果。

## 最終工具決策

- 主力 IDE：Cursor
- 輔助 IDE：VS Code
- 模型訓練：Google Colab
- 資料庫：PostgreSQL
- 環境整合：Docker Compose
- 模型：Ultralytics YOLOv8 Detect
- Dashboard：Streamlit
- 實驗追蹤：MLflow
- 資料處理：Python、pandas、numpy、OpenCV、Pillow
- 版本控管：Git / GitHub

## 現有資料條件

- 27,367 張混合車況照片，包含車內、車外、各角度、不同品質。
- 240 張輕微不索賠車損照片。
- 53 張較嚴重索賠車損照片。
- 目前沒有同車、同角度、借車與還車成對照片。

## 核心建模策略

第一版模型只做一個 YOLO 類別：

```yaml
names:
  0: damage
```

不要直接訓練：

```text
normal / minor_damage / claim_damage
```

原因：

- 索賠級資料量太少。
- 索賠與否是業務規則與人工判斷，不只是視覺模型分類。
- 第一版應優先完成「可見車損偵測」。

## 不可違反的專案規則

1. 不要修改 `data/raw/` 原始圖片。
2. 不要把長方形原圖手動硬拉成 640x640。
3. YOLO 標註需使用 normalized xywh 格式。
4. 第一版只訓練 `damage` 單一類別。
5. 不要把「輕微不索賠」和「索賠」直接當成模型分類目標。
6. 沒有成對借還車資料前，不要宣稱模型已能準確判斷新增車損。
7. 新增車損判斷目前以 rule-based comparison module 實作。
8. 所有輸出都要保存到 `outputs/` 或資料庫。
9. 所有 config 放到 `configs/`。
10. notebooks 用於探索，正式可重用邏輯要放到 `src/`。
11. 每完成一個可執行功能，請更新 README 或補充執行方式。

## 程式碼風格

- 檔名、資料表欄位、函數名稱使用英文。
- 註解、README、使用說明使用繁體中文。
- 使用 type hints 與 docstrings。
- 使用 pathlib，不要大量硬編絕對路徑。
- 對資料處理腳本加入 CLI arguments。
- 每支腳本都要列印 summary，例如 input count、processed count、skipped count、output path。
- 錯誤處理要清楚，不要 silent fail。

## 每次任務完成後必須提供

1. 修改了哪些檔案。
2. 如何執行。
3. 預期輸出。
4. 如何檢查是否成功。
5. 新手需要理解的關鍵概念。
6. 建議下一步。

## Git 工作規則

建議每個階段開 branch：

```bash
git checkout -b phase-01-metadata
```

每完成一個小功能就 commit：

```bash
git add .
git commit -m "feat: build image metadata pipeline"
```

## 階段完成標準

一個階段只有在以下條件都達成時才算完成：

- 程式碼可以執行。
- 產出檔案存在。
- 錯誤狀況有處理。
- README 或文件有更新。
- 使用者知道如何重跑。
- 重要結果可以被檢查。

