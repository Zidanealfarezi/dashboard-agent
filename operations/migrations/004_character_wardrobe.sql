-- Migration 004: Character Virtual Wardrobe & Auto-Stylist Engine
-- Menyimpan lemari pakaian virtual karakter agar agen dapat memilih busana otomatis sesuai konsep konten

CREATE TABLE IF NOT EXISTS character_wardrobe (
    id TEXT PRIMARY KEY,
    character_id TEXT NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    color_palette TEXT,
    vibe_tags TEXT,
    hijab_type TEXT,
    top_description TEXT,
    bottom_description TEXT,
    footwear_accessories TEXT,
    closeup_photo_path TEXT NOT NULL,
    fullbody_photo_path TEXT NOT NULL,
    times_used INTEGER DEFAULT 0,
    last_used_at TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_wardrobe_character ON character_wardrobe(character_id);
CREATE INDEX IF NOT EXISTS idx_wardrobe_category ON character_wardrobe(category);
CREATE INDEX IF NOT EXISTS idx_wardrobe_status ON character_wardrobe(status);
