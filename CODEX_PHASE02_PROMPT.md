# Codex Prompt - Phase 02 Image Review Builder

請先閱讀以下根目錄文件，並完全遵守：

```text
AGENTS.md
CODEX_WORKFLOW.md
PROJECT_CONTEXT_BRIEF.md
PHASE_GATE_CHECKLIST.md
README.md
```

目前專案是 FleetVision，請忽略任何舊的 `irent-damage-detection` 架構。

## Phase Gate 檢查

目前階段：Phase 02 - Image Review Builder  
上下文狀態：以 repo 根目錄文件為準  
主要工具：Codex 負責工程實作；Cursor 負責查看 diff、執行指令、Git 操作  
是否先 GitHub 上傳：若 Phase 00 / Phase 01 已通過 `pytest` 與 `python scripts/phase00_init_project.py --validate`，建議先 commit / push 後再開始 Phase 02  

## 目標

實作 Phase 02：根據 Phase 01 產生的 metadata，建立人工圖片覆核清單。

輸入：

```text
outputs/metadata/image_metadata.csv
```

主要輸出：

```text
dataset/02_interim/03_review_queue/review_queue.csv
outputs/metadata/review_queue_summary.csv
```

## 請新增或修改的檔案

請至少建立：

```text
src/fleetvision/data/build_review_queue.py
scripts/phase02_build_review_queue.py
tests/test_build_review_queue.py
```

並更新：

```text
docs/01_phase_guides/phase_02_image_review.md
```

如需要設定檔，可新增：

```text
configs/data/review_queue_config.yaml
```

## Review Queue 欄位建議

`review_queue.csv` 至少包含：

```text
review_id
image_id
source_group
file_path
filename
image_width
image_height
quality_status
brightness
blur_score
photo_type_review
angle_review
is_exterior_review
has_visible_damage_review
severity_review
review_status
reviewer
review_notes
priority
```

## CLI 要求

`scripts/phase02_build_review_queue.py` 需要支援：

```bash
python scripts/phase02_build_review_queue.py
python scripts/phase02_build_review_queue.py --input outputs/metadata/image_metadata.csv --output dataset/02_interim/03_review_queue/review_queue.csv
python scripts/phase02_build_review_queue.py --max-rows 100
```

## 測試要求

請加入 pytest 測試，至少驗證：

1. 可以從 sample metadata 建立 review queue。
2. 欄位完整。
3. bad / unreadable image 可以被標成低 priority 或排除，依你的設計明確定義。
4. source_group priority 排序符合規則。
5. CLI 或核心函數可在測試中執行。

## 驗收指令

完成後我會在 Cursor terminal 執行：

```bash
python scripts/phase00_init_project.py --validate
pytest
python scripts/phase02_build_review_queue.py --max-rows 100
```

## 不要做的事

- 不要修改 `dataset/01_raw/` 原始圖片。
- 不要產生或修改 YOLO labels。
- 不要訓練 YOLO。
- 不要把 `minor_damage` / `claimable_damage` 當成 YOLO 類別。
- 不要建立索賠判斷模型。
- 不要把大型圖片或模型權重加入 Git。
- 不要依賴個人電腦絕對路徑。


## Patch-only 注意事項

本階段請只新增或修改上方列出的 Phase 02 相關檔案。

不要重建整個 `FleetVision/` 專案資料夾。
不要移動或覆蓋 `dataset/01_raw/`。
不要修改與 Phase 02 無關的檔案。
若需要修改額外檔案，請先說明理由，並保持變更範圍最小。
