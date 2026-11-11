-- Migration 003: Trend & Content Learning Memory Engine
-- Digunakan untuk menyimpan bank riset permanen dan sistem pembelajaran berkelanjutan agen

CREATE TABLE IF NOT EXISTS trend_memory (
    id TEXT PRIMARY KEY,
    character_id TEXT NOT NULL REFERENCES characters(id),
    category TEXT NOT NULL,
    topic TEXT NOT NULL,
    hook_text TEXT NOT NULL,
    script_outline TEXT,
    viral_sound_title TEXT,
    viral_sound_url TEXT,
    source_evidence TEXT,
    status TEXT DEFAULT 'discovered' CHECK(status IN ('discovered', 'drafted', 'approved', 'rejected', 'published')),
    viral_score REAL DEFAULT 0.0,
    times_used INTEGER DEFAULT 0,
    last_used_at TEXT,
    performance_views INTEGER DEFAULT 0,
    performance_likes INTEGER DEFAULT 0,
    learnings TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_trend_char_status ON trend_memory(character_id, status);
CREATE INDEX IF NOT EXISTS idx_trend_score ON trend_memory(viral_score DESC);

CREATE TABLE IF NOT EXISTS content_learning_log (
    id TEXT PRIMARY KEY,
    character_id TEXT NOT NULL REFERENCES characters(id),
    content_topic TEXT NOT NULL,
    insight TEXT NOT NULL,
    what_worked TEXT,
    what_to_avoid TEXT,
    confidence_score REAL DEFAULT 1.0,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_learning_char ON content_learning_log(character_id);
