CREATE TABLE daily_slots (
 id TEXT PRIMARY KEY,
 day TEXT NOT NULL,
 character_id TEXT NOT NULL REFERENCES characters(id),
 kind TEXT NOT NULL CHECK(kind IN ('photo','video')),
 duration_seconds INTEGER,
 state TEXT NOT NULL CHECK(state IN ('needs_plan','planned','reserved','unknown','review_ready','awaiting_review')),
 plan_json TEXT,
 profile_sha256 TEXT,
 job_id TEXT UNIQUE REFERENCES generation_jobs(id),
 version_id TEXT UNIQUE REFERENCES versions(id),
 delivery_id TEXT UNIQUE REFERENCES review_deliveries(id),
 created_at TEXT NOT NULL,
 UNIQUE(day,character_id)
);
PRAGMA user_version=3;
