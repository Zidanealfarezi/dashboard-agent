import sqlite3
from pathlib import Path
from app import autopilot

root = Path(__file__).resolve().parent.parent
conn = sqlite3.connect(root / 'operations/production.sqlite')
conn.row_factory = sqlite3.Row

# Slot is dinda-2026-11-09
job_id = autopilot.begin_submission(
    db=conn,
    root=root,
    slot_id='dinda-2026-11-09',
    account_id='flow_1',
    project_url='https://flow.google.com/project/3e9fe2ca-ee39-4235-81a1-9d8bfdee9603',
    model='Omni 1.1 Flash',
    duration=10,
    outputs=1,
    credits=12
)
print("Submission started successfully for job:", job_id)
