# Phase 01：圖片資料盤點與 metadata

## 目的

將所有圖片轉換成可管理的 metadata 表，避免只靠資料夾與檔名管理資料。

## 輸入資料

```text
dataset/01_raw/01_general_fleet/images/
dataset/01_raw/02_claimable_damage/images/
dataset/01_raw/03_minor_damage/images/
```

## 輸出資料

```text
outputs/metadata/image_metadata.csv
dataset/00_catalog/image_metadata.csv
outputs/metadata/image_quality_summary.csv
outputs/metadata/bad_images.csv
```

## metadata 建議欄位

| 欄位 | 說明 |
|---|---|
| image_id | 圖片唯一 ID |
| source_group | general_fleet / claimable_damage / minor_damage |
| file_path | 圖片路徑 |
| filename | 檔名 |
| image_width | 圖片寬 |
| image_height | 圖片高 |
| aspect_ratio | 長寬比 |
| file_size_bytes | 檔案大小 |
| is_readable | 是否能讀取 |
| blur_score | 模糊分數 |
| brightness | 平均亮度 |
| photo_type | exterior / interior / low_quality / irrelevant / unknown |
| angle | front / rear / left / right / front_left / front_right / rear_left / rear_right / unknown |
| has_visible_damage | 0 / 1 / unknown |
| severity_label | none / minor / moderate / severe / unknown |

## 驗收標準

- 能掃描三個 raw image folders。
- 壞圖不會讓程式中斷。
- 能輸出 CSV。
- 能統計每個來源資料夾的圖片數量。
