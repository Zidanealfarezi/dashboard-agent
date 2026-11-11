"""Read-only local setup check; never starts integrations or production."""
from pathlib import Path
import json
import sqlite3

root = Path(__file__).resolve().parents[1]
config = json.loads((root / 'config/project.json').read_text())
assert config['mode'] in ('setup_only', 'controlled_pilot')
assert config['publication_enabled'] is False
assert config['scheduler_enabled'] is False
if config['mode'] == 'setup_only':
    for flag in ('generation_enabled', 'telegram_enabled'):
        assert config[flag] is False, flag
    assert config['generation_budget_authorized_credits'] == 0
else:
    pilot = json.loads((root / 'config/pilot.json').read_text())
    assert pilot['scope'] == 'controlled_pilot_not_unattended_operations'
    assert config['generation_budget_authorized_credits'] == pilot['flow_total_credit_cap'] == 25
    assert pilot['automatic_paid_retry'] is False
for p in root.rglob('*.json'):
    if 'private' not in p.relative_to(root).parts:
        json.loads(p.read_text())
uri = (root / 'operations/production.sqlite').as_uri() + '?mode=ro'
with sqlite3.connect(uri, uri=True) as db:
    assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    assert not db.execute('PRAGMA foreign_key_check').fetchall()
    assert db.execute('PRAGMA user_version').fetchone()[0] == 3
    assert {r[0] for r in db.execute('SELECT id FROM characters')} == {'nara', 'dinda', 'rania'}
    counts = {table: db.execute('SELECT count(*) FROM ' + table).fetchone()[0]
              for table in ('content', 'versions', 'approvals', 'generation_jobs', 'publications',
                            'story_events', 'review_deliveries', 'daily_slots')}
    if config['mode'] == 'setup_only':
        assert all(count == 0 for count in counts.values()), counts
    else:
        allocated = db.execute('SELECT COALESCE(SUM(COALESCE(actual_credits,authorized_credits)),0) FROM generation_jobs').fetchone()[0]
        assert allocated <= 25
        assert counts['publications'] == 0 and counts['story_events'] == 0
print(json.dumps({'ok': True, 'mode': config['mode'], 'database_counts': counts,
                  'publication_enabled': False, 'scheduler_enabled': False,
                  'network_used_by_check': False}, indent=2))
