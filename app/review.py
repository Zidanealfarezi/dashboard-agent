"""Explicit local CLI for versioned Telegram review; no daemon or publication code."""
import argparse
from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import urllib.request
import uuid
import sys

# Ensure root is in path for shared modules
_ROOT_DIR = str(Path(__file__).resolve().parents[1])
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)
from shared.sanitizer import clean_emojis

ROOT = Path(__file__).resolve().parents[1]
DECISIONS = {'a': 'approved', 'r': 'revise', 'x': 'rejected'}


class ReviewError(Exception):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def connect(root):
    db = sqlite3.connect(str(root / 'operations/production.sqlite'), timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    if db.execute('PRAGMA user_version').fetchone()[0] not in (2, 3):
        db.close()
        raise ReviewError('Database memerlukan migrasi review versi 2.')
    return db


def media_path(root, character_id, relative):
    base = (root / 'characters' / character_id / 'content').resolve()
    path = (root / relative).resolve()
    if base not in path.parents or not path.is_file():
        raise ReviewError('Media harus berada di folder content karakter yang sesuai.')
    if path.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.webp', '.mp4', '.mov'):
        raise ReviewError('Gunakan foto atau video yang didukung.')
    if not 0 < path.stat().st_size <= 49_000_000:
        raise ReviewError('Ukuran media harus lebih dari nol dan maksimal 49 MB.')
    return path


def package(db, root, version_id):
    row = db.execute('''SELECT v.*, c.character_id, c.kind, ch.name,
        ch.account FROM versions v JOIN content c ON c.id=v.content_id
        JOIN characters ch ON ch.id=c.character_id WHERE v.id=?''', (version_id,)).fetchone()
    if row is None:
        raise ReviewError('Versi tidak ditemukan.')
    latest = db.execute('SELECT MAX(revision) FROM versions WHERE content_id=?',
                        (row['content_id'],)).fetchone()[0]
    if row['revision'] != latest:
        raise ReviewError('Versi lama; tinjau versi terbaru.')
    data = media_path(root, row['character_id'], row['media_path']).read_bytes()
    if digest(data) != row['media_sha256'] or digest(row['caption'].encode()) != row['caption_sha256']:
        raise ReviewError('Media/caption berubah; buat versi baru dan minta ACC ulang.')
    if row['destination_account'] != row['account']:
        raise ReviewError('Akun tujuan tidak sesuai karakter.')
    return row, data


def register(db, root, character_id, content_id, kind, media, caption, manage_transaction=True):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', content_id):
        raise ReviewError('ID konten hanya huruf, angka, strip, underscore; maksimal 80.')
    character = db.execute('SELECT * FROM characters WHERE id=?', (character_id,)).fetchone()
    if not character:
        raise ReviewError('Karakter tidak ditemukan.')
    path = media_path(root, character_id, media)
    if (kind == 'video') != (path.suffix.lower() in ('.mp4', '.mov')):
        raise ReviewError('Jenis konten tidak sesuai ekstensi media.')
    # Strict No-Emoji Enforcement: otomatis bersihkan emoji jika ada
    caption = clean_emojis(caption)
    if not caption.strip() or len(caption.encode('utf-16-le')) // 2 > 3000:
        raise ReviewError('Caption wajib diisi dan maksimal 3.000 unit UTF-16 pada MVP.')
    data = path.read_bytes()
    with db if manage_transaction else nullcontext():
        if manage_transaction:
            db.execute('BEGIN IMMEDIATE')
        existing = db.execute('SELECT * FROM content WHERE id=?', (content_id,)).fetchone()
        if existing and (existing['character_id'] != character_id or existing['kind'] != kind):
            raise ReviewError('ID konten sudah dimiliki karakter/jenis lain.')
        if not existing:
            db.execute('INSERT INTO content VALUES (?,?,?,?)', (content_id, character_id, kind, now()))
        revision = db.execute('SELECT COALESCE(MAX(revision),0)+1 FROM versions WHERE content_id=?',
                              (content_id,)).fetchone()[0]
        vid = uuid.uuid4().hex
        db.execute('INSERT INTO versions VALUES (?,?,?,?,?,?,?,?,?)',
                   (vid, content_id, revision, str(path.relative_to(root.resolve())),
                    digest(data), caption, digest(caption.encode()), character['account'], now()))
    return vid


def card(row):
    text = (f"REVIEW • {row['name']}\nTujuan: {row['destination_account']}\n"
            f"Konten: {row['content_id']} • versi {row['revision']}\n"
            f"Media SHA256: {row['media_sha256']}\n"
            f"Caption SHA256: {row['caption_sha256']}\n\n"
            f"CAPTION LENGKAP:\n{row['caption']}\n\n"
            'ACC hanya untuk paket ini. Tidak memposting atau mengizinkan biaya generasi.')
    if len(text.encode('utf-16-le')) // 2 > 4096:
        raise ReviewError('Kartu review terlalu panjang untuk Telegram.')
    return text


def prepare(db, root, version_id, chat_id):
    with db:
        db.execute('BEGIN IMMEDIATE')
        row, _ = package(db, root, version_id)
        card(row)
        delivery_id = uuid.uuid4().hex
        try:
            db.execute('INSERT INTO review_deliveries VALUES (?,?,?, ?,NULL,NULL,?,NULL,?)',
                       (delivery_id, version_id, chat_id, 'prepared',
                        (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(), now()))
        except sqlite3.IntegrityError:
            raise ReviewError('Review versi/penerima ini sudah ada; jangan kirim ulang secara buta.') from None
    return delivery_id


def live_config(root):
    project = json.loads((root / 'config/project.json').read_text())
    config = json.loads((root / 'config/telegram.json').read_text())
    if not project.get('telegram_enabled') or not config.get('enabled'):
        raise ReviewError('Telegram nonaktif; tidak ada permintaan jaringan dikirim.')
    if not config.get('token_verified') or not config.get('recipient_paired'):
        raise ReviewError('Token atau penerima belum diverifikasi.')
    return config


class Telegram:
    def __init__(self, root):
        self.root = root

    def call(self, method, fields, document=None):
        # Recheck the live gate on every call, including callback acknowledgements.
        config = live_config(self.root)
        credential = (self.root / config['credential_reference']).resolve()
        private = (self.root / 'private/credentials').resolve()
        if private not in credential.parents:
            raise ReviewError('Lokasi kredensial tidak sesuai.')
        token = json.loads(credential.read_text())['bot_token']
        if document is None:
            body = json.dumps(fields).encode()
            content_type = 'application/json'
        else:
            boundary = 'review' + uuid.uuid4().hex
            parts = []
            for key, value in fields.items():
                parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"'
                              f'\r\n\r\n{value}\r\n').encode())
            # Fixed filename avoids injecting filenames into multipart headers.
            parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="document"; '
                          'filename="review-media' + document[0] + '"\r\n'
                          'Content-Type: application/octet-stream\r\n\r\n').encode())
            parts.extend([document[1], f'\r\n--{boundary}--\r\n'.encode()])
            body = b''.join(parts)
            content_type = 'multipart/form-data; boundary=' + boundary
        try:
            request = urllib.request.Request('https://api.telegram.org/bot' + token + '/' + method,
                                             data=body, headers={'Content-Type': content_type})
            with urllib.request.urlopen(request, timeout=40) as response:
                result = json.load(response)
            if result.get('ok') is not True:
                raise ValueError('API failure')
            return result['result']
        except Exception:
            # Never propagate a URL containing the token, request body, or API error text.
            raise ReviewError('Permintaan Telegram gagal; jangan retry pengiriman sebelum rekonsiliasi.') from None


def send(db, root, delivery_id, api):
    config = live_config(root)
    with db:
        db.execute('BEGIN IMMEDIATE')
        delivery = db.execute('SELECT * FROM review_deliveries WHERE id=?', (delivery_id,)).fetchone()
        if not delivery or delivery['state'] != 'prepared':
            raise ReviewError('Review bukan prepared; pengiriman ulang diblokir.')
        if delivery['chat_id'] not in config['allowed_chat_ids']:
            raise ReviewError('Penerima tidak diizinkan.')
        if delivery['expires_at'] <= now():
            raise ReviewError('Review kedaluwarsa.')
        row, data = package(db, root, delivery['version_id'])
        text = card(row)
        db.execute("UPDATE review_deliveries SET state='sending' WHERE id=?", (delivery_id,))
    try:
        media = api.call('sendDocument', {'chat_id': delivery['chat_id'],
                         'caption': f"{row['name']} • {row['content_id']} • v{row['revision']}"},
                         document=(Path(row['media_path']).suffix.lower(), data))
        with db:
            db.execute('UPDATE review_deliveries SET media_message_id=? WHERE id=?',
                       (media['message_id'], delivery_id))
        keyboard = {'inline_keyboard': [[{'text': label, 'callback_data': f'rv:{delivery_id}:{code}'}
                                        for label, code in [('ACC', 'a'), ('Revisi', 'r'), ('Tolak', 'x')]]]}
        result = api.call('sendMessage', {'chat_id': delivery['chat_id'], 'text': text,
                          'reply_markup': keyboard,
                          'reply_parameters': {'message_id': media['message_id']},
                          'link_preview_options': {'is_disabled': True}})
        with db:
            db.execute("UPDATE review_deliveries SET state='sent',card_message_id=? WHERE id=?",
                       (result['message_id'], delivery_id))
    except BaseException:
        with db:
            db.execute("UPDATE review_deliveries SET state='unknown' WHERE id=?", (delivery_id,))
        raise


def handle_callback(db, root, query, config):
    sender = query.get('from', {})
    message = query.get('message', {})
    chat = message.get('chat', {})
    if (sender.get('is_bot') or sender.get('id') not in config['allowed_user_ids']
            or chat.get('id') not in config['allowed_chat_ids'] or chat.get('type') != 'private'
            or message.get('from', {}).get('id') != config['bot_id']):
        return 'Akun atau pesan tidak diizinkan.'
    match = re.fullmatch(r'rv:([0-9a-f]{32}):([arx])', query.get('data', ''))
    if not match or not query.get('id'):
        return 'Tombol tidak dikenal.'
    delivery_id, action = match.groups()
    with db:
        db.execute('BEGIN IMMEDIATE')
        delivery = db.execute('SELECT * FROM review_deliveries WHERE id=?', (delivery_id,)).fetchone()
        if (not delivery or delivery['chat_id'] != chat['id']
                or delivery['card_message_id'] != message.get('message_id')):
            return 'Pesan review tidak cocok.'
        if delivery['state'] == 'decided':
            return 'Keputusan sudah tercatat; revisi memerlukan versi baru.'
        if delivery['state'] != 'sent' or delivery['expires_at'] <= now():
            return 'Review tidak aktif atau kedaluwarsa.'
        try:
            package(db, root, delivery['version_id'])
        except ReviewError as exc:
            return str(exc)
        event_id = 'telegram:' + str(config['bot_id']) + ':' + str(query['id'])
        if db.execute('SELECT 1 FROM approvals WHERE external_event_id=?', (event_id,)).fetchone():
            return 'Keputusan sudah tercatat.'
        decision = DECISIONS[action]
        db.execute('INSERT INTO approvals VALUES (?,?,?,?,?,?,?)',
                   (uuid.uuid4().hex, delivery['version_id'], decision, str(sender['id']),
                    'telegram', event_id, now()))
        db.execute("UPDATE review_deliveries SET state='decided',decision=? WHERE id=?",
                   (decision, delivery_id))
    return {'approved': 'ACC tersimpan. Belum diposting.', 'revise': 'Permintaan revisi tersimpan.',
            'rejected': 'Penolakan tersimpan.'}[decision]


def approved_package(db, root, version_id):
    """Revalidate bytes, latest revision and current ACC before any future publishing adapter."""
    row, data = package(db, root, version_id)
    if not db.execute('SELECT 1 FROM current_approved_versions WHERE id=?', (version_id,)).fetchone():
        raise ReviewError('Paket belum memiliki ACC yang berlaku.')
    return row, data  # Does not grant publication permission or perform any upload.


def sync_card_decision(db, root, delivery_id, api):
    """Make an already durable decision visible; never creates approval or publishes."""
    config = live_config(root)
    delivery = db.execute('SELECT * FROM review_deliveries WHERE id=?', (delivery_id,)).fetchone()
    if (not delivery or delivery['state'] != 'decided'
            or delivery['chat_id'] not in config['allowed_chat_ids']):
        return False
    row, _ = package(db, root, delivery['version_id'])
    label = {'approved': 'ACC tersimpan. Belum diposting.',
             'revise': 'Permintaan revisi tersimpan.',
             'rejected': 'Penolakan tersimpan.'}[delivery['decision']]
    api.call('editMessageText', {'chat_id': delivery['chat_id'],
             'message_id': delivery['card_message_id'],
             'text': card(row) + '\n\nKeputusan: ' + label,
             'reply_markup': {'inline_keyboard': []},
             'link_preview_options': {'is_disabled': True}})
    return True


def receive_once(db, root, api):
    config = live_config(root)
    offset = db.execute('SELECT next_offset FROM telegram_cursor WHERE id=1').fetchone()[0]
    updates = api.call('getUpdates', {'offset': offset, 'timeout': 0, 'limit': 100,
                                     'allowed_updates': ['callback_query', 'message']})
    count = 0
    decided_cards = set()
    for update in updates:
        query = update.get('callback_query')
        if query:
            result = handle_callback(db, root, query, config)
            try:
                api.call('answerCallbackQuery', {'callback_query_id': query['id'], 'text': result})
            except ReviewError:
                pass  # Decision is durable even if the acknowledgement cannot be delivered.
            count += 1
            if result in ('ACC tersimpan. Belum diposting.', 'Permintaan revisi tersimpan.',
                          'Penolakan tersimpan.', 'Keputusan sudah tercatat; revisi memerlukan versi baru.'):
                decided_cards.add(query['data'].split(':')[1])
        # Offset advances only after processing; replayed callbacks cannot duplicate approval.
        # Text messages are deliberately not executed or considered approval.
        with db:
            db.execute('UPDATE telegram_cursor SET next_offset=MAX(next_offset,?) WHERE id=1',
                       (update['update_id'] + 1,))
    for delivery_id in decided_cards:
        try:
            sync_card_decision(db, root, delivery_id, api)
        except ReviewError:
            pass  # UI refresh failure cannot undo the durable decision.
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    add = commands.add_parser('register', help='Catat versi media yang sudah tersedia, tanpa jaringan')
    add.add_argument('--character', required=True, choices=['nara', 'dinda', 'rania', 'isk', 'aqara', 'bang_ray', 'pak_vincent'])
    add.add_argument('--content', required=True)
    add.add_argument('--kind', required=True, choices=['photo', 'video'])
    add.add_argument('--media', required=True, help='Path relatif proyek di folder content karakter')
    add.add_argument('--caption-file', required=True)
    prep = commands.add_parser('prepare', help='Siapkan kartu lokal, tanpa mengirim')
    prep.add_argument('--version', required=True)
    sending = commands.add_parser('send', help='Kirim satu review; diblokir selama Telegram nonaktif')
    sending.add_argument('--review', required=True)
    commands.add_parser('receive-once', help='Baca satu batch keputusan; tidak membuat loop/daemon')
    args = parser.parse_args()
    try:
        with connect(ROOT) as db:
            if args.command == 'register':
                print(register(db, ROOT, args.character, args.content, args.kind, args.media,
                               Path(args.caption_file).read_text()))
            elif args.command == 'prepare':
                config = json.loads((ROOT / 'config/telegram.json').read_text())
                if len(config['allowed_chat_ids']) != 1:
                    raise ReviewError('MVP memerlukan satu penerima yang sudah dipasangkan.')
                print(prepare(db, ROOT, args.version, config['allowed_chat_ids'][0]))
            elif args.command == 'send':
                send(db, ROOT, args.review, Telegram(ROOT))
                print('Review terkirim; belum diposting.')
            else:
                print('Callback diproses:', receive_once(db, ROOT, Telegram(ROOT)))
    except (ReviewError, OSError, ValueError, sqlite3.Error):
        # Generic CLI error prevents accidentally logging secrets from files or network errors.
        parser.exit(1, 'Operasi diblokir/gagal. Periksa status setup dan paket review; jangan retry kirim secara buta.\n')


if __name__ == '__main__':
    main()
