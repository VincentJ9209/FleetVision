# Phase 04.5M：標註修正提案人工複核

本階段只複核 Phase 04.5L F2 產生的兩筆 correction proposal，不直接修改 canonical annotation、canonical COCO、dataset、Registry、fixed splits 或模型。

## 1. 建立兩筆 review package

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "G:\Project\FleetVision\scripts\phase04_5_prepare_annotation_correction_review.ps1" -F2WorkspaceRoot "<F2 workspace>"
```

成功 classification：`PHASE_04_5M_ANNOTATION_CORRECTION_REVIEW_PACKAGE_PREPARED`。

## 2. 啟動繁體中文 Streamlit

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "G:\Project\FleetVision\scripts\phase04_5_launch_annotation_correction_review_app.ps1" -WorkspaceRoot "<04.5M workspace>"
```

網址：`http://127.0.0.1:8503`。SQLite 是 live source of truth；每次成功儲存都產生 audit event 與 backup。

## 3. 複核案例

- `l_687b939a3a89bb8e`：確認是否需要 `RESIZE_OR_REDRAW_BBOX`，指定單一 GT bbox 並輸入 replacement geometry。
- `l_e5875a8f94620ff1`：確認是否為重複框，使用 `REMOVE_DUPLICATE_BBOX` 並指定應移除的 GT bbox ID。

不得直接把 prediction 自動寫成 GT。Reviewer 必須自行確認 geometry。

## 4. 完成條件

```text
total=2
reviewed=2
pending=0
needs_adjudication=0
```

完成後在啟動 Streamlit 的 PowerShell 視窗按 `Ctrl+C`。

## 5. 匯出 completed proposals

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "G:\Project\FleetVision\scripts\phase04_5_export_annotation_correction_review.ps1" -WorkspaceRoot "<04.5M workspace>"
```

輸出 CSV、JSON、XLSX、proposed overlays、result JSON 與 SHA256SUMS。XLSX 僅作 archive／inspection，不可作 live review state。

## 6. 停止點

成功 classification：`PHASE_04_5M_ANNOTATION_CORRECTION_PROPOSALS_REVIEWED`。此時仍不得修改 canonical COCO；下一步是獨立 Phase 04.5N promotion Gate。
