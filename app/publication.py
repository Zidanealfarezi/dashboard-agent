"""Book one manual TikTok submission of an approved version and record its evidence."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import re
import sqlite3
import uuid

from app import review

WIB = timezone(timedelta(hours=7))


def check_schedule_window(root, character_id, now_dt=None):
    project = json.loads((root / 'config/project.json').read_text())
    schedules = project.get('publication_schedules', {})
    if character_id not in schedules:
        return True
    sched = schedules[character_id]
    pub_time_str = sched.get('publish_time_wib')
    if not pub_time_str:
        return True
    window_mins = sched.get('allowed_publish_window_minutes', 120)

    if now_dt is None:
        now_dt = datetime.now(WIB)
    elif now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=WIB)
    else:
        now_dt = now_dt.astimezone(WIB)

    pub_h, pub_m = map(int, pub_time_str.split(':'))
    pub_start = now_dt.replace(hour=pub_h, minute=pub_m, second=0, microsecond=0)
    pub_end = pub_start + timedelta(minutes=window_mins)
    early_tolerance = pub_start - timedelta(minutes=5)

    if not (early_tolerance <= now_dt <= pub_end):
        raise review.ReviewError(
            f"Di luar jendela jadwal publikasi resmi untuk {character_id} "
            f"(jadwal: {pub_time_str} WIB, jendela: {window_mins} menit). Publikasi ditahan."
        )
    return True


def begin(db, root, version_id, observed_account, enforce_schedule=False, now_dt=None):
    with db:
        db.execute('BEGIN IMMEDIATE')
        project = json.loads((root / 'config/project.json').read_text())
        if project.get('production_hold'):
            raise review.ReviewError('Publikasi ditahan untuk rekonsiliasi.')
        if not project.get('publication_enabled'):
            raise review.ReviewError('Izin publikasi nonaktif.')
        version, _ = review.approved_package(db, root, version_id)
        if observed_account != version['destination_account']:
            raise review.ReviewError('Akun TikTok di browser berbeda dari tujuan ACC.')
        if enforce_schedule:
            check_schedule_window(root, version['character_id'], now_dt=now_dt)
        # Legacy scripts could write approval rows without an authenticated review callback.
        telegram = json.loads((root / 'config/telegram.json').read_text())
        approval = db.execute('''
            SELECT a.*, d.chat_id FROM approvals a
            LEFT JOIN review_deliveries d ON d.version_id=a.version_id AND d.state='decided'
              AND d.decision='approved' AND d.media_message_id IS NOT NULL AND d.card_message_id IS NOT NULL
            WHERE a.version_id=? ORDER BY a.rowid DESC LIMIT 1
        ''', (version_id,)).fetchone()
        if (approval['channel'] != 'telegram' or not approval['external_event_id']
                or approval['chat_id'] not in telegram['allowed_chat_ids']
                or approval['reviewer_id'] not in {str(user) for user in telegram['allowed_user_ids']}):
            raise review.ReviewError('ACC belum memiliki jejak callback Telegram yang sah.')
        if db.execute('''
            SELECT 1 FROM publications p JOIN versions v ON v.id=p.version_id
            WHERE v.content_id=? AND p.state IN ('submitted','confirmed','unknown')
        ''', (version['content_id'],)).fetchone():
            raise review.ReviewError('Konten sudah diajukan atau statusnya belum pasti. Rekonsiliasi sebelum mencoba lagi.')
        max_posts_per_day = int(project.get('posts_per_day', 1))
        ref_dt = now_dt or datetime.now(WIB)
        if ref_dt.tzinfo is None:
            ref_dt = ref_dt.replace(tzinfo=WIB)
        today_wib = ref_dt.astimezone(WIB).date().isoformat()
        pub_rows = db.execute('''
            SELECT p.state, p.confirmed_at, v.created_at FROM publications p
            JOIN versions v ON v.id=p.version_id
            JOIN content c ON c.id=v.content_id
            WHERE c.character_id=? AND p.state IN ('submitted','confirmed','unknown')
        ''', (version['character_id'],)).fetchall()
        today_count = 0
        for row in pub_rows:
            stamp_raw = row['confirmed_at'] if row['state'] == 'confirmed' and row['confirmed_at'] else row['created_at']
            if not stamp_raw:
                continue
            try:
                stamp_dt = datetime.fromisoformat(str(stamp_raw).replace('Z', '+00:00'))
                if stamp_dt.tzinfo is None:
                    stamp_dt = stamp_dt.replace(tzinfo=WIB)
                if stamp_dt.astimezone(WIB).date().isoformat() == today_wib:
                    today_count += 1
            except ValueError:
                pass
        if today_count >= max_posts_per_day:
            raise review.ReviewError(
                f"Batas maksimal {max_posts_per_day} kali posting per hari untuk {version['character_id']} sudah tercapai."
            )
        attempt = uuid.uuid4().hex
        db.execute("INSERT INTO publications (id,version_id,idempotency_key,state) VALUES (?,?,?,'submitted')",
                   (attempt, version_id, attempt))
        return {'publication_id': attempt, 'version_id': version_id,
                'account': version['destination_account'], 'media_path': version['media_path'],
                'caption': version['caption']}


def video_url(post_url, account):
    if not re.fullmatch(r'@[A-Za-z0-9_.]+', account):
        return None
    return re.fullmatch(r'https://www\.tiktok\.com/' + re.escape(account) + r'/video/([0-9]+)', post_url)


def confirm(db, publication_id, post_url):
    """Record a video URL observed by the operator after matching it to the submitted package."""
    with db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('''
            SELECT p.*, v.destination_account FROM publications p JOIN versions v ON v.id=p.version_id
            WHERE p.id=?
        ''', (publication_id,)).fetchone()
        if not row or row['state'] not in ('submitted', 'unknown', 'confirmed'):
            raise review.ReviewError('Percobaan publikasi tidak ditemukan.')
        match = video_url(post_url, row['destination_account'])
        if not match:
            raise review.ReviewError('Gunakan URL video TikTok dari akun tujuan, lengkap dengan ID video.')
        if row['state'] == 'confirmed':
            if row['post_url'] != post_url or row['platform_post_id'] != match[1]:
                raise review.ReviewError('Percobaan sudah dikonfirmasi dengan bukti berbeda.')
            return
        db.execute("""UPDATE publications SET state='confirmed', platform_post_id=?, post_url=?, confirmed_at=?
                      WHERE id=?""", (match[1], post_url, review.now(), publication_id))


def mark_unknown(db, publication_id):
    with db:
        if db.execute("UPDATE publications SET state='unknown' WHERE id=? AND state IN ('submitted','unknown')",
                      (publication_id,)).rowcount != 1:
            raise review.ReviewError('Percobaan publikasi tidak dapat ditandai belum pasti.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    submit = commands.add_parser('begin')
    submit.add_argument('--version', required=True)
    submit.add_argument('--account', required=True)
    submit.add_argument('--enforce-schedule', action='store_true', default=False,
                        help='Wajibkan publikasi berada dalam jendela jam tayang yang sah')
    submit.add_argument('--now', help='Override waktu ISO untuk pengujian')
    evidence = commands.add_parser('confirm')
    evidence.add_argument('--publication', required=True)
    evidence.add_argument('--video-url', required=True)
    uncertain = commands.add_parser('mark-unknown')
    uncertain.add_argument('--publication', required=True)
    args = parser.parse_args()
    try:
        with review.connect(review.ROOT) as db:
            if args.action == 'begin':
                now_override = None
                if args.now:
                    now_override = datetime.fromisoformat(args.now)
                result = begin(db, review.ROOT, args.version, args.account,
                               enforce_schedule=args.enforce_schedule, now_dt=now_override)
            elif args.action == 'confirm':
                confirm(db, args.publication, args.video_url)
                result = {'state': 'confirmed'}
            else:
                mark_unknown(db, args.publication)
                result = {'state': 'unknown'}
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except review.ReviewError as error:
        parser.exit(1, str(error) + '\n')
    except (sqlite3.Error, ValueError, OSError, KeyError):
        parser.exit(1, 'Data lokal belum valid atau ID video sudah tercatat. Periksa status sebelum mencoba lagi.\n')


if __name__ == '__main__':
    main()
