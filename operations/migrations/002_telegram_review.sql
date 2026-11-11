CREATE TABLE review_deliveries (
 id TEXT PRIMARY KEY,
 version_id TEXT NOT NULL REFERENCES versions(id),
 chat_id INTEGER NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('prepared','sending','sent','unknown','decided')),
 media_message_id INTEGER,
 card_message_id INTEGER,
 expires_at TEXT NOT NULL,
 decision TEXT CHECK(decision IN ('approved','rejected','revise')),
 created_at TEXT NOT NULL,
 UNIQUE(version_id, chat_id)
);
CREATE TABLE telegram_cursor (id INTEGER PRIMARY KEY CHECK(id=1), next_offset INTEGER NOT NULL);
INSERT INTO telegram_cursor VALUES (1,0);
PRAGMA user_version=2;
