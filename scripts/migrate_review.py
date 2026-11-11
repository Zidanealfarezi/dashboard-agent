"""Local schema migration with a consistent backup; never contacts Telegram."""
from datetime import datetime, timezone
from pathlib import Path
import sqlite3


def main():
    root = Path(__file__).resolve().parents[1]
    path = root / 'operations/production.sqlite'
    if not path.is_file():
        raise SystemExit('Database belum tersedia; tidak membuat database kosong.')
    with sqlite3.connect(str(path)) as db:
        version = db.execute('PRAGMA user_version').fetchone()[0]
        if version == 3:
            print('Schema autopilot v3 sudah tersedia; tidak ada perubahan.')
            return
        if version not in (1, 2):
            raise SystemExit('Versi database tidak dikenali; migrasi dibatalkan.')
        folder = root / 'operations/backups'
        folder.mkdir(exist_ok=True)
        folder.chmod(0o700)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        backup = folder / ('before-autopilot-v3-' + stamp + '.sqlite')
        backup.touch(mode=0o600, exist_ok=False)
        with sqlite3.connect(str(backup)) as destination:
            db.backup(destination)
        names = ['002_telegram_review.sql', '003_autopilot.sql'] if version == 1 else ['003_autopilot.sql']
        sql = '\n'.join((root / 'operations/migrations' / name).read_text() for name in names)
        try:
            db.executescript('BEGIN IMMEDIATE;\n' + sql + '\nCOMMIT;')
        except Exception:
            db.rollback()
            raise
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
    print('Migrasi lokal v3 selesai; backup konsisten tersedia di operations/backups/.')


if __name__ == '__main__':
    main()
