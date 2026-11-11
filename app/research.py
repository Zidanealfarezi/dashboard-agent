"""Local reference catalog: stable IDs, dated observations, no network or model calls."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]


def identity(url):
    parts = urlsplit(url)
    if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password:
        raise ValueError('A public HTTPS source URL is required')
    host = parts.hostname.lower()
    path = parts.path.rstrip('/') or '/'
    canonical = urlunsplit(('https', host, path, '', ''))
    if host == 'tiktok.com' or host.endswith('.tiktok.com'):
        match = re.search(r'/(video|photo)/(\d+)(?:/|$)', path)
        if match:
            return 'tiktok:post:' + match[2], canonical
        match = re.search(r'/music/[^/]*-(\d+)$', path)
        if match:
            return 'tiktok:sound:' + match[1], canonical
    return 'url:' + hashlib.sha256(canonical.encode()).hexdigest(), canonical


def connect(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript('''
        CREATE TABLE IF NOT EXISTS sources (
            id TEXT PRIMARY KEY, url TEXT NOT NULL, title TEXT NOT NULL,
            first_seen TEXT NOT NULL, last_seen TEXT NOT NULL, sound_id TEXT,
            sound_url TEXT);
        CREATE TABLE IF NOT EXISTS observations (
            source_id TEXT NOT NULL REFERENCES sources(id), observed_at TEXT NOT NULL,
            evidence TEXT NOT NULL, verification_status TEXT NOT NULL,
            metrics_json TEXT, published_at TEXT, PRIMARY KEY(source_id, observed_at));
        CREATE TABLE IF NOT EXISTS selections (
            source_id TEXT NOT NULL REFERENCES sources(id), character_id TEXT NOT NULL,
            plan_id TEXT NOT NULL, selected_at TEXT NOT NULL,
            PRIMARY KEY(source_id, character_id, plan_id));
    ''')
    return db


def record(db, candidate, observed_at):
    stamp = datetime.fromisoformat(observed_at.replace('Z', '+00:00'))
    if stamp.tzinfo is None or stamp > datetime.now(timezone.utc):
        raise ValueError('Observation time must have a timezone and not be in the future')
    observed_at = stamp.astimezone(timezone.utc).isoformat()
    key, url = identity(candidate['url'])
    title, evidence = candidate.get('title'), candidate.get('evidence')
    if not isinstance(title, str) or not title.strip() or not isinstance(evidence, str) or not evidence.strip():
        raise ValueError('Source title and actual observed evidence are required')
    status = candidate.get('verification_status', 'candidate_unverified')
    if status not in ('candidate_unverified', 'source_read', 'verified_context_source', 'trend_evidence_verified'):
        raise ValueError('Unknown evidence status')
    sound_url = candidate.get('sound_url')
    sound_id = identity(sound_url)[0] if sound_url else None
    existing = db.execute('SELECT id FROM sources WHERE id=?', (key,)).fetchone()
    same_sound = bool(sound_id and db.execute(
        'SELECT 1 FROM sources WHERE sound_id=? AND id<>?', (sound_id, key)).fetchone())
    with db:
        db.execute('''INSERT INTO sources VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
            url=excluded.url,title=excluded.title,
            first_seen=MIN(sources.first_seen,excluded.first_seen),
            last_seen=MAX(sources.last_seen,excluded.last_seen),
            sound_id=COALESCE(excluded.sound_id,sources.sound_id),
            sound_url=COALESCE(excluded.sound_url,sources.sound_url)''',
            (key, url, title, observed_at, observed_at, sound_id, sound_url))
        db.execute('''INSERT INTO observations VALUES(?,?,?,?,?,?)
            ON CONFLICT(source_id,observed_at) DO UPDATE SET evidence=excluded.evidence,
            verification_status=excluded.verification_status,metrics_json=excluded.metrics_json,
            published_at=excluded.published_at''',
            (key, observed_at, evidence, status,
             json.dumps(candidate.get('metrics'), ensure_ascii=False), candidate.get('published_at')))
    return {'id': key, 'classification': 'existing_reference' if existing else
            'new_reference_same_sound' if same_sound else 'new_reference', 'verification_status': status}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--import-json', type=Path)
    parser.add_argument('--observed-at')
    args = parser.parse_args()
    with connect(ROOT / 'shared/research/references.sqlite') as db:
        if args.import_json:
            data = json.loads(args.import_json.read_text())
            stamp = args.observed_at or datetime.now(timezone.utc).isoformat()
            print(json.dumps([record(db, c, stamp) for c in data['candidates']], ensure_ascii=False, indent=2))
        else:
            print(json.dumps([dict(r) for r in db.execute('SELECT * FROM sources ORDER BY last_seen DESC LIMIT 20')], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
