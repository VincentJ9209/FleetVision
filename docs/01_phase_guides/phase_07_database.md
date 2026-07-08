# Phase 07：PostgreSQL 與 Docker Compose

## 目的

建立接近實務的資料庫環境，用於儲存圖片 metadata、模型推論結果與未來借還車比對結果。

## 使用工具

- Docker Compose
- PostgreSQL
- DBeaver 或 pgAdmin

## 資料表建議

- `image_assets`
- `image_quality_metrics`
- `damage_predictions`
- `damage_comparison_results`
- `model_versions`
- `review_cases`

## 輸出

```text
docker-compose.yml
.env.example
sql/schema.sql
src/fleetvision/db/
```

## 驗收標準

- `docker compose up -d` 可啟動 PostgreSQL。
- schema 可成功建立。
- 可匯入 metadata。
- 可查詢 prediction result。
