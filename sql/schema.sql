-- FleetVision PostgreSQL schema starter

CREATE TABLE IF NOT EXISTS model_versions (
    model_version TEXT PRIMARY KEY,
    model_name TEXT NOT NULL,
    task TEXT NOT NULL,
    class_names JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS image_assets (
    image_id TEXT PRIMARY KEY,
    source_group TEXT,
    file_path TEXT NOT NULL,
    filename TEXT,
    image_width INTEGER,
    image_height INTEGER,
    aspect_ratio NUMERIC,
    file_size_bytes BIGINT,
    photo_type TEXT DEFAULT 'unknown',
    angle TEXT DEFAULT 'unknown',
    has_visible_damage TEXT DEFAULT 'unknown',
    severity_label TEXT DEFAULT 'unknown',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS image_quality_metrics (
    image_id TEXT PRIMARY KEY REFERENCES image_assets(image_id),
    is_readable BOOLEAN,
    blur_score NUMERIC,
    brightness NUMERIC,
    quality_label TEXT DEFAULT 'unknown',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS damage_predictions (
    prediction_id BIGSERIAL PRIMARY KEY,
    image_id TEXT REFERENCES image_assets(image_id),
    model_version TEXT REFERENCES model_versions(model_version),
    class_name TEXT,
    confidence NUMERIC,
    x1 NUMERIC,
    y1 NUMERIC,
    x2 NUMERIC,
    y2 NUMERIC,
    raw_output JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS damage_comparison_results (
    comparison_id BIGSERIAL PRIMARY KEY,
    rental_id TEXT,
    vehicle_id TEXT,
    angle TEXT,
    pickup_image_id TEXT,
    return_image_id TEXT,
    result TEXT,
    new_damage_count INTEGER DEFAULT 0,
    max_confidence NUMERIC,
    review_required BOOLEAN DEFAULT FALSE,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_image_assets_source_group ON image_assets(source_group);
CREATE INDEX IF NOT EXISTS idx_damage_predictions_image_id ON damage_predictions(image_id);
CREATE INDEX IF NOT EXISTS idx_damage_predictions_model_version ON damage_predictions(model_version);
CREATE INDEX IF NOT EXISTS idx_damage_comparison_vehicle_rental ON damage_comparison_results(vehicle_id, rental_id);
