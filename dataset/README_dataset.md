# FleetVision Dataset README

## 資料放置總覽

原始圖片請放：

```text
dataset/01_raw/01_general_fleet/images/
dataset/01_raw/02_claimable_damage/images/
dataset/01_raw/03_minor_damage/images/
```

Excel / catalog 請放：

```text
dataset/00_catalog/raw_excels/
```

## 原始資料不可修改

`dataset/01_raw/` 是原始資料區，請不要在裡面覆蓋、裁切、重新命名或刪除圖片。所有處理後結果請輸出到 `02_interim/`、`03_reviewed/`、`04_annotations/` 或 `05_yolo/`。

## 資料生命週期

```text
01_raw
  ↓
02_interim
  ↓
03_reviewed
  ↓
04_annotations
  ↓
05_yolo
  ↓
models / outputs / demo
```
