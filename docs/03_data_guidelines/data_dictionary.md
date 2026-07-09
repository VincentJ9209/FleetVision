# Data Dictionary

## image_metadata.csv

| 欄位 | 型態 | 說明 |
|---|---|---|
| image_id | string | 圖片唯一 ID |
| source_group | string | general_fleet / claimable_damage / minor_damage |
| file_path | string | 圖片路徑 |
| filename | string | 檔名 |
| file_extension | string | 副檔名 |
| image_width | integer | 圖片寬度 |
| image_height | integer | 圖片高度 |
| aspect_ratio | float | 長寬比 |
| file_size_bytes | integer | 檔案大小 |
| is_readable | boolean | 是否可讀取 |
| blur_score | float | 模糊程度 |
| brightness | float | 平均亮度 |
| photo_type | string | exterior / interior / low_quality / irrelevant / unknown |
| angle | string | front / rear / left / right / front_left / front_right / rear_left / rear_right / unknown |
| has_visible_damage | string | 0 / 1 / unknown |
| severity_label | string | none / minor / moderate / severe / unknown |
| split | string | train / val / test / unused |
