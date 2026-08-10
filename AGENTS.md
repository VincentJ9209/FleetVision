# FleetVision Agent Instructions

本規則適用於 repository root 與所有子目錄。請使用繁體中文，中文使用全形標點，英文與數字兩側保留半形空白。

## Startup path

每次任務先讀取：

1. `START_HERE.md`
2. `PROJECT_CONTEXT_BRIEF.md`
3. `docs/02_workflow/PROJECT_STATUS.md`
4. `docs/02_workflow/HANDOFF_CURRENT.md`

依工作需要再讀取 `docs/02_workflow/PROTECTED_ASSETS.md`、`docs/02_workflow/WORKFLOW.md` 與適用決策記錄。開始前確認 Phase／Gate、授權範圍、允許與禁止路徑、工作樹狀態、測試證據，以及 commit／push 是否明確授權。衝突或未授權時停止。

## Protected asset rules

- `outputs/metadata/external_assets/` 不得 stage、commit、delete、clean、move 或 rewrite。
- `dataset/01_raw/`、canonical CSV／COCO／dataset manifests、Registry assets、internal holdout definitions、外部來源 archives、model/training acceptance artifacts 均受保護。
- 不得覆寫已完成或進行中的人工審核 workbook、reviewer manifest、manual-review ZIP、frozen backup 或 SHA256 manifest。
- 未經適用 Gate 授權，不得存取 Frozen Test、修改 raw／canonical assets、建立資料 split 或啟動 training／fine-tuning。
- 正式人工審核預設採本機繁體中文 Streamlit、SQLite live state、audit events、backup 與 no-overwrite export；Excel 僅為 export／exchange／archive，除非 Gate 核准例外。

## Immutable architecture

- 停用的 `irent-damage-detection` 不得恢復或混用。
- 首個 damage model 是 YOLOv8 Detect，且唯一第一版 YOLO class 是 `damage`。
- `minor_damage` 與 `claimable_damage` 不得成為第一版 YOLO class。
- CLIP 僅可作已核准的 `photo_type` suggestion；檔名 `_1`、`_2`、`_3`、`_4` 不得推論 angle。
- Phase 03.5 inference 保持 frozen；不得自動推論 damage／severity。
- 不得自動判定保險責任、理賠、法律結論或 claimability。

## Engineering and Git rules

- Production Python code 位於 `src/fleetvision/`；notebooks 不是主要 business logic。
- 不得在 application code 寫入使用者絕對路徑；使用 config、CLI arguments 或 repository-relative paths。
- 大型圖片、model weights、training runs、database dumps、review packages、generated artifacts 與 secrets 均留在 Git 外。
- 做最小且完整的變更，維持 deterministic ordering、schema／path 合約與 no-overwrite behavior；每個行為變更都需對應測試。
- 完成前執行適用測試、`git diff --check`、`git status --short` 與最後 diff 檢查，確認僅有授權路徑變更且沒有 partial output。
- 僅用 explicit paths stage；未明確授權不得 commit 或 push。

## Durable records

- 需要長期保存的決策、狀態、風險與 Gate evidence 必須寫入 repository 文件並納入已授權 checkpoint。
- Live Git facts 與 cryptographic identities 和敘事衝突時，以前者為準。
- 不以聊天紀錄、投影片或未驗證的外部摘要升級 artifact、metric 或 deployment claim。

## Stop conditions

不要修改檔案，並回報阻塞原因，如果 Phase／前置條件不明、治理文件矛盾、請求違反 immutable decision、protected asset 有覆寫風險、必要來源缺失、worktree 有非預期變更、license 不明、測試失敗無法解釋，或完成工作需要未授權的 scope expansion。
