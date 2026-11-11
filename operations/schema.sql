PRAGMA foreign_keys=ON;
PRAGMA user_version=1;
CREATE TABLE characters (id TEXT PRIMARY KEY, name TEXT NOT NULL, account TEXT NOT NULL UNIQUE);
CREATE TABLE content (id TEXT PRIMARY KEY, character_id TEXT NOT NULL REFERENCES characters(id), kind TEXT NOT NULL CHECK(kind IN ('photo','video')), created_at TEXT NOT NULL);
CREATE TABLE versions (
 id TEXT PRIMARY KEY, content_id TEXT NOT NULL REFERENCES content(id), revision INTEGER NOT NULL CHECK(revision>0),
 media_path TEXT NOT NULL, media_sha256 TEXT NOT NULL CHECK(length(media_sha256)=64),
 caption TEXT NOT NULL, caption_sha256 TEXT NOT NULL CHECK(length(caption_sha256)=64),
 destination_account TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(content_id,revision));
CREATE TRIGGER immutable_version_update BEFORE UPDATE ON versions BEGIN SELECT RAISE(ABORT,'Create a new version instead'); END;
CREATE TRIGGER immutable_version_delete BEFORE DELETE ON versions BEGIN SELECT RAISE(ABORT,'Version history is immutable'); END;
CREATE TABLE approvals (id TEXT PRIMARY KEY, version_id TEXT NOT NULL REFERENCES versions(id), decision TEXT NOT NULL CHECK(decision IN ('approved','rejected','revise')), reviewer_id TEXT NOT NULL, channel TEXT NOT NULL, external_event_id TEXT UNIQUE, created_at TEXT NOT NULL);
CREATE VIEW current_approved_versions AS SELECT v.* FROM versions v WHERE
 v.revision=(SELECT MAX(v2.revision) FROM versions v2 WHERE v2.content_id=v.content_id)
 AND (SELECT a.decision FROM approvals a WHERE a.version_id=v.id ORDER BY a.rowid DESC LIMIT 1)='approved';
CREATE TABLE generation_jobs (id TEXT PRIMARY KEY, character_id TEXT NOT NULL REFERENCES characters(id), flow_account_id TEXT NOT NULL CHECK(flow_account_id IN ('flow_1','flow_2','flow_3')), idempotency_key TEXT NOT NULL UNIQUE, state TEXT NOT NULL CHECK(state IN ('planned','awaiting_budget','submitted','running','completed','failed','needs_user','unknown')), model TEXT, duration_seconds INTEGER, output_count INTEGER CHECK(output_count>0), authorized_credits INTEGER NOT NULL DEFAULT 0 CHECK(authorized_credits>=0), actual_credits INTEGER CHECK(actual_credits>=0), external_job_id TEXT, created_at TEXT NOT NULL);
CREATE TABLE publications (id TEXT PRIMARY KEY, version_id TEXT NOT NULL REFERENCES versions(id), idempotency_key TEXT NOT NULL UNIQUE, state TEXT NOT NULL CHECK(state IN ('planned','awaiting_approval','submitted','confirmed','failed','unknown')), platform_post_id TEXT UNIQUE, post_url TEXT, confirmed_at TEXT, CHECK(state!='confirmed' OR (platform_post_id IS NOT NULL AND post_url IS NOT NULL AND confirmed_at IS NOT NULL)));
CREATE TABLE research_sources (id TEXT PRIMARY KEY, character_id TEXT REFERENCES characters(id), url TEXT NOT NULL, retrieved_at TEXT NOT NULL, observation TEXT NOT NULL, interpretation TEXT);
CREATE TABLE story_events (id TEXT PRIMARY KEY, character_id TEXT NOT NULL REFERENCES characters(id), description TEXT NOT NULL, confirmed_publication_id TEXT REFERENCES publications(id), explicit_user_decision TEXT, CHECK(confirmed_publication_id IS NOT NULL OR explicit_user_decision IS NOT NULL));
