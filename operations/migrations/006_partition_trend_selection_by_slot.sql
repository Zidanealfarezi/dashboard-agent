-- Migration 006: Partition trend selections by character, day, and slot (morning / evening)
-- Prevents morning and evening research runs from overwriting each other's decisions.

CREATE TABLE IF NOT EXISTS trend_selections_new (
    id TEXT PRIMARY KEY,
    day TEXT NOT NULL,
    character_id TEXT NOT NULL,
    slot TEXT NOT NULL DEFAULT 'morning',
    trend_id TEXT NOT NULL,
    title TEXT NOT NULL,
    viral_score REAL NOT NULL,
    rationale TEXT NOT NULL,
    source_urls TEXT NOT NULL,
    score_breakdown TEXT NOT NULL,
    decided_by TEXT NOT NULL DEFAULT 'pm_autonomous',
    created_at TEXT NOT NULL,
    UNIQUE(day, character_id, slot)
);

INSERT OR REPLACE INTO trend_selections_new (id, day, character_id, slot, trend_id, title, viral_score, rationale, source_urls, score_breakdown, decided_by, created_at)
SELECT id, day, character_id, 'morning', trend_id, title, viral_score, rationale, source_urls, score_breakdown, decided_by, created_at
FROM trend_selections;

DROP TABLE IF EXISTS trend_selections;
ALTER TABLE trend_selections_new RENAME TO trend_selections;

CREATE INDEX IF NOT EXISTS idx_selection_day_slot ON trend_selections(day, character_id, slot);
