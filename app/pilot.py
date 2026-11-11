"""Explicit one-slot technical pilot. Daily production and scheduling remain separate."""
import argparse
import json
from datetime import datetime
from pathlib import Path
import sqlite3

from app import autopilot, review

ROOT = review.ROOT


def prepare(db, root, plan):
    permission = autopilot.load(root, 'config/pilot.json')
    project = autopilot.load(root, 'config/project.json')
    if (permission.get('scope') != 'controlled_pilot_not_unattended_operations'
            or permission.get('flow_total_credit_cap') != 25
            or project.get('mode') != 'controlled_pilot'):
        raise review.ReviewError('Controlled pilot is not authorized/configured')
    if (plan.get('purpose') != 'technical_identity_test' or plan.get('character_id') != 'dinda'
            or plan.get('kind') != 'video' or plan.get('duration_seconds') != 6
            or len(plan.get('shots', [])) != 1 or plan['shots'][0].get('seconds') != 6
            or not plan['shots'][0].get('prompt') or not plan.get('caption')
            or plan.get('new_biography_facts') != [] or plan.get('promotional') is not False):
        raise review.ReviewError('Only the fixed Dinda identity test is accepted')
    if autopilot.reference_status(root, 'dinda')['state'] != 'ready':
        raise review.ReviewError('Dinda identity reference is not verified')
    day = permission['authorized_on']
    if datetime.now(autopilot.WIB).date().isoformat() != day:
        raise review.ReviewError('Pilot date has expired')
    slot_id = 'dinda-technical-pilot-' + day
    profile_hash = review.digest((root / 'characters/dinda/profile.json').read_bytes())
    with db:
        db.execute('BEGIN IMMEDIATE')
        if db.execute('SELECT 1 FROM daily_slots WHERE id=? OR (day=? AND character_id=?)',
                      (slot_id, day, 'dinda')).fetchone():
            raise review.ReviewError('Pilot already exists; inspect it instead of recreating')
        db.execute('''INSERT INTO daily_slots
            (id,day,character_id,kind,duration_seconds,state,plan_json,profile_sha256,created_at)
            VALUES(?,?,'dinda','video',6,'planned',?,?,?)''',
            (slot_id, day, json.dumps(plan, ensure_ascii=False), profile_hash, review.now()))
    return slot_id


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    args = parser.parse_args()
    try:
        with review.connect(ROOT) as db:
            print(json.dumps({'slot_id': prepare(db, ROOT, json.loads(args.plan.read_text()))}))
    except (review.ReviewError, ValueError, KeyError, sqlite3.Error) as exc:
        parser.exit(1, str(exc) + '\n')


if __name__ == '__main__':
    main()
