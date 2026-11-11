-- Migration 005: Autonomous trend selection log
-- Menyimpan keputusan agen: satu topik terpilih per karakter per hari, beserta
-- skor, alasan, dan sumber bukti yang dibaca. Menggantikan pengiriman opsi A/B/C
-- ke Owner; Owner tidak memilih, PM/AI menentukan 100%.

CREATE TABLE IF NOT EXISTS trend_selections (
    id TEXT PRIMARY KEY,
    day TEXT NOT NULL,
    character_id TEXT NOT NULL,
    trend_id TEXT NOT NULL,
    title TEXT NOT NULL,
    viral_score REAL NOT NULL,
    rationale TEXT NOT NULL,
    source_urls TEXT NOT NULL,
    score_breakdown TEXT NOT NULL,
    decided_by TEXT NOT NULL DEFAULT 'pm_autonomous',
    created_at TEXT NOT NULL,
    UNIQUE(day, character_id)
);

CREATE INDEX IF NOT EXISTS idx_selection_day ON trend_selections(day, character_id);
