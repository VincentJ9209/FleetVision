---
name: postgres-docker-engineer
description: Build Docker Compose, PostgreSQL schemas, initialization scripts, and database ingestion utilities for the iRent ML project.
---

# PostgreSQL Docker Engineer Skill

Use this skill when creating Docker Compose, PostgreSQL schema, DB connection utilities, or scripts that insert metadata and prediction results into PostgreSQL.

## Preferred Files

- `docker-compose.yml`
- `.env.example`
- `src/db/schema.sql`
- `src/db/init_db.py`
- `src/db/insert_metadata.py`
- `src/db/insert_predictions.py`

## Tables

- image_metadata
- vehicle_photos
- damage_predictions
- damage_comparison_results
- model_versions

## Rules

- Use PostgreSQL for the complete project version.
- Use JSONB for raw model outputs when useful.
- Store bbox as numeric x1, y1, x2, y2 columns.
- Add indexes for common query fields.
- Read DB config from `.env`.
- Avoid hard-coded passwords.
- Include beginner-friendly run and validation instructions.

