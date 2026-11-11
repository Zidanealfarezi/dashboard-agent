"""Store a replacement Telegram token locally. No network or bot startup."""
from pathlib import Path
import getpass
import json
import os
import re
import tempfile


def main():
    root = Path(__file__).resolve().parents[1]
    if not os.isatty(0):
        raise SystemExit('Jalankan di Terminal interaktif; jangan masukkan token ke chat.')
    token = getpass.getpass('Token BARU dari BotFather (input tersembunyi): ').strip()
    if not re.fullmatch(r'[0-9]+:[A-Za-z0-9_-]{30,}', token):
        raise SystemExit('Format token tidak sesuai. Tidak ada token disimpan.')
    folder = root / 'private' / 'credentials'
    folder.mkdir(parents=True, exist_ok=True)
    (root / 'private').chmod(0o700)
    folder.chmod(0o700)
    target = folder / 'telegram.json'
    fd, temporary = tempfile.mkstemp(prefix='.telegram-', dir=str(folder))
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump({'bot_token': token}, stream)
            stream.write('\n')
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    config_path = root / 'config' / 'telegram.json'
    config = json.loads(config_path.read_text())
    config['credential_reference'] = 'private/credentials/telegram.json'
    config['enabled'] = False
    config['connected'] = False
    config['note'] = 'Token disimpan lokal; belum diverifikasi. Bot dan polling nonaktif.'
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
    print('Token disimpan lokal dengan izin 600. Bot belum dijalankan; tidak ada koneksi jaringan.')


if __name__ == '__main__':
    main()
