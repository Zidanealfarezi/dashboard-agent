"""Explicit, gated Hermes worker launcher; importing or checking status starts nothing."""
import argparse
import fcntl
import json
from pathlib import Path
import subprocess

from app import review

ROOT = review.ROOT


def settings(root):
    return json.loads((root / 'config/hermes.json').read_text())


def command(root, character_id, task):
    cfg = settings(root)
    project = json.loads((root / 'config/project.json').read_text())
    autopilot = json.loads((root / 'config/autopilot.json').read_text())
    if character_id not in ('nara', 'dinda', 'rania', 'bang_ray', 'pak_vincent') or character_id not in cfg['profiles']:
        raise review.ReviewError('Karakter Hermes tidak dikenal.')
    if (not cfg['execution_enabled'] or project['mode'] == 'setup_only'
            or project['operator'] != 'hermes' or not autopilot['enabled']):
        raise review.ReviewError('Eksekusi Hermes untuk proyek masih nonaktif.')
    if not task.strip():
        raise review.ReviewError('Tugas lokal belum disiapkan.')
    profile = cfg['profiles'][character_id]
    name = 'ai-influencer-' + character_id.replace('_', '-')
    if profile['name'] != name:
        raise review.ReviewError('Pemetaan profil Hermes tidak sesuai karakter.')
    prompt = (f"Anda bekerja hanya untuk karakter {character_id}. "
              'Baca AGENTS.md, config/project.json dan docs/hermes-setup.md. '
              'Patuhi izin biaya, ACC per versi, dan status pekerjaan. '
              'Jangan mengubah flag izin atau mengaktifkan layanan.\n\nTugas lokal:\n' + task)
    return [str(Path.home() / '.local/bin/hermes'), '-p', name, '--in', str(root),
            'chat', '--provider', cfg['model']['provider'], '--oneshot', '-q', prompt]


def launch(root, character_id, task):
    args = command(root, character_id, task)  # Deny before creating files or spawning anything.
    lock_path = root / 'operations/hermes-worker.lock'
    with lock_path.open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise review.ReviewError('Satu worker Hermes masih berjalan; tunggu hasilnya.') from None
        return subprocess.run(args, cwd=str(root), check=False).returncode


def status(root):
    cfg = settings(root)
    return {'execution_enabled': cfg['execution_enabled'], 'expected_model': cfg['model'],
            'brain_test_status': cfg['brain_test_status'],
            'profile_smoke_tests': cfg['profile_smoke_tests'],
            'profiles': {cid: {'name': info['name'],
                              'config_exists': (Path(info['home']) / 'config.yaml').is_file(),
                              'soul_exists': (Path(info['home']) / 'SOUL.md').is_file(),
                              'active': info['active']} for cid, info in cfg['profiles'].items()},
            'review_transport': cfg['review_transport'],
            'native_telegram_gateway_used': cfg['native_telegram_gateway_used']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='action', required=True)
    subs.add_parser('status')
    run = subs.add_parser('run')
    run.add_argument('--character', required=True, choices=('nara', 'dinda', 'rania', 'bang_ray', 'pak_vincent'))
    run.add_argument('--task-file', required=True, help='Tugas lokal yang disiapkan pelaksana, bukan input harian pengguna')
    args = parser.parse_args()
    try:
        if args.action == 'status':
            print(json.dumps(status(ROOT), ensure_ascii=False, indent=2))
        else:
            return launch(ROOT, args.character, Path(args.task_file).read_text())
    except review.ReviewError as exc:
        parser.exit(1, str(exc) + '\n')
    except (OSError, ValueError, KeyError):
        parser.exit(1, 'Konfigurasi/tugas Hermes belum valid; tidak mencetak data rahasia.\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
