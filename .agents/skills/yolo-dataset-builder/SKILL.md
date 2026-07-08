# YOLO Dataset Builder

## name

yolo-dataset-builder

## description

建立與驗證 YOLOv8 Detect 資料集，檢查 images/labels 配對、data.yaml 與 normalized bbox 格式。

## project context

本 skill 適用於 FleetVision 專案。FleetVision 第一版以 YOLOv8 Detect 單一類別 `damage` 為主，目標是建立共享車輛外觀照片的可見車損偵測流程。

## rules

1. 以 `AGENTS.md` 為最高專案規則。
2. 不要修改 `dataset/01_raw/` 原始資料。
3. 不要把大型圖片、模型權重、`.env` 放入 GitHub。
4. 不要把 `minor_damage` / `claimable_damage` 當成第一版 YOLO 類別。
5. 函數、檔名、欄位名稱使用英文；文件說明可用繁體中文。
6. 每個任務都要說明輸入、輸出、執行方式與驗收標準。

## expected output

依任務輸出程式、設定、文件或測試，並說明：

- 修改檔案
- 執行指令
- 輸出位置
- 驗收標準
- 可能風險
