#!/usr/bin/env python3
"""Build a local weekly report from verified publication and metric evidence.
Strict 0% Emoji Policy.
"""
import argparse
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.publication import video_url

WIB = timezone(timedelta(hours=7))
METRICS = ('views', 'likes', 'comments')


def read_snapshots(path):
    if path is None:
        default_file = ROOT / 'operations' / 'reports' / 'metrics_snapshots.json'
        if default_file.is_file():
            path = default_file
        else:
            return {}
    if not path.is_file():
        return {}
    rows = json.loads(path.read_text())
    snapshots = {}
    for row in rows:
        stamp = datetime.fromisoformat(row['observed_at'].replace('Z', '+00:00'))
        if stamp.tzinfo is None or stamp > datetime.now(timezone.utc):
            raise ValueError('Waktu observasi metrik harus valid dan memiliki zona waktu.')
        if any(type(row.get(key)) is not int or row[key] < 0 for key in METRICS):
            raise ValueError('Metrik harus berupa hitungan nonnegatif.')
        url = row['video_url']
        if url not in snapshots or stamp > snapshots[url][0]:
            snapshots[url] = (stamp, {key: row[key] for key in METRICS})
    return snapshots


def build_report(db, start, end, snapshots):
    if start >= end:
        raise ValueError('Tanggal awal harus sebelum tanggal akhir.')
    period = tuple(datetime.combine(d, datetime.min.time(), WIB).isoformat() for d in (start, end))
    report = {
        'start_wib': start.isoformat(),
        'end_wib_exclusive': end.isoformat(),
        'generated_at_wib': datetime.now(WIB).isoformat(),
        'characters': {}
    }
    for character in db.execute('SELECT id,name,account FROM characters ORDER BY id'):
        posts = []
        for row in db.execute("""
            SELECT p.post_url,p.platform_post_id,p.confirmed_at,c.kind
            FROM publications p JOIN versions v ON v.id=p.version_id
            JOIN content c ON c.id=v.content_id
            WHERE p.state='confirmed' AND c.character_id=? AND v.destination_account=?
              AND datetime(p.confirmed_at)>=datetime(?) AND datetime(p.confirmed_at)<datetime(?)
              AND (
                EXISTS (
                  SELECT 1 FROM review_deliveries d WHERE d.version_id=v.id AND d.state='decided'
                    AND d.decision='approved' AND d.card_message_id IS NOT NULL AND d.media_message_id IS NOT NULL
                )
                OR EXISTS (
                  SELECT 1 FROM approvals a WHERE a.version_id=v.id AND a.decision='approved'
                )
              )
            ORDER BY p.confirmed_at
        """, (character['id'], character['account'], *period)):
            match = video_url(row['post_url'], character['account'])
            if not match or match[1] != row['platform_post_id']:
                continue
            post = {
                'video_url': row['post_url'],
                'confirmed_at': row['confirmed_at'],
                'format': row['kind']
            }
            snapshot = snapshots.get(row['post_url'])
            confirmed = datetime.fromisoformat(row['confirmed_at'].replace('Z', '+00:00'))
            if snapshot and snapshot[0] >= confirmed:
                stamp, counts = snapshot
                views = counts.get('views', 0)
                likes = counts.get('likes', 0)
                comments = counts.get('comments', 0)
                if views > 0:
                    er_val = round(((likes + comments) / views) * 100, 2)
                    er_display = f"{er_val}%"
                else:
                    er_display = 'belum_ada_data'
                post.update(
                    metrics=counts,
                    engagement_rate=er_display,
                    observed_at=stamp.isoformat(),
                    hours_since_confirmation=round((stamp - confirmed).total_seconds() / 3600, 2)
                )
            else:
                post.update(
                    metrics=None,
                    engagement_rate='belum_ada_data'
                )
            posts.append(post)

        valid_metric_posts = [p for p in posts if p.get('metrics') and (p['metrics'].get('views') or 0) > 0]
        if valid_metric_posts:
            tot_views = sum(p['metrics']['views'] for p in valid_metric_posts)
            tot_interactions = sum(p['metrics']['likes'] + p['metrics']['comments'] for p in valid_metric_posts)
            overall_er = f"{round((tot_interactions / tot_views) * 100, 2)}%" if tot_views > 0 else 'belum_ada_data'
        else:
            overall_er = 'belum_ada_data'

        credits = db.execute("""
            SELECT SUM(CASE WHEN state='completed' THEN actual_credits END),
                   SUM(CASE WHEN state IN ('submitted','running','unknown','needs_user') THEN 1 ELSE 0 END)
            FROM generation_jobs WHERE character_id=? AND datetime(created_at)>=datetime(?)
              AND datetime(created_at)<datetime(?)
        """, (character['id'], *period)).fetchone()

        report['characters'][character['id']] = {
            'name': character['name'],
            'account': character['account'],
            'verified_posts': posts,
            'total_verified_posts': len(posts),
            'engagement_rate': overall_er,
            'metrics_status': 'has_snapshots' if any(post.get('metrics') for post in posts) else 'belum_ada_data',
            'recorded_actual_credits': credits[0] or 0,
            'unreconciled_jobs': credits[1] or 0,
        }
    return report


def format_markdown_summary(report):
    lines = [
        f"*LAPORAN EVALUASI MINGGUAN AI INFLUENCER*",
        f"Periode: {report['start_wib']} s/d {report['end_wib_exclusive']} WIB",
        f"Waktu Laporan: {report['generated_at_wib']}\n"
    ]
    for cid, data in report['characters'].items():
        lines.append(f"*{data['name']}* ({data['account']}):")
        lines.append(f"- Post Terverifikasi: {data['total_verified_posts']}")
        lines.append(f"- Status Metrik: {data['metrics_status']}")
        lines.append(f"- Rata-rata Engagement Rate: {data['engagement_rate']}")
        lines.append(f"- Kredit Flow Tercatat: {data['recorded_actual_credits']} kredit")
        lines.append(f"- Job Belum Terekonsiliasi: {data['unreconciled_jobs']}")
        if data['verified_posts']:
            lines.append("  Daftar Tayang:")
            for p in data['verified_posts']:
                lines.append(f"  * {p['video_url']} ({p['format']}) - ER: {p['engagement_rate']}")
        lines.append("")
    return "\n".join(lines)


def send_telegram_summary(report_text):
    from app.review import live_config
    config = live_config(ROOT)
    credential = (ROOT / config['credential_reference']).resolve()
    private_dir = (ROOT / 'private/credentials').resolve()
    if private_dir not in credential.parents or not credential.is_file():
        raise RuntimeError('Kredensial Telegram tidak sah atau tidak ditemukan.')
    token = json.loads(credential.read_text())['bot_token']
    chat_id = config['allowed_chat_ids'][0]

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": report_text,
        "parse_mode": "Markdown"
    }).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode('utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    # Default end-date covers through today inclusive
    default_end = (datetime.now(WIB) + timedelta(days=1)).date()
    parser.add_argument('--end-date', type=date.fromisoformat, default=default_end,
                        help='Tanggal akhir eksklusif WIB (default: besok 00:00 WIB agar hari ini terhitung)')
    parser.add_argument('--metrics-file', type=Path, help='JSON berisi snapshot metrik yang sudah diverifikasi')
    parser.add_argument('--save', action='store_true', help='Simpan laporan ke operations/reports/')
    parser.add_argument('--send-telegram', action='store_true', help='Kirim ringkasan laporan ke Telegram Owner via kredensial terverifikasi')
    args = parser.parse_args()

    try:
        path = ROOT / 'operations' / 'production.sqlite'
        with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as db:
            db.row_factory = sqlite3.Row
            report = build_report(db, args.end_date - timedelta(days=7), args.end_date,
                                  read_snapshots(args.metrics_file))

        json_output = json.dumps(report, ensure_ascii=False, indent=2)
        print(json_output)

        if args.save:
            out_file = ROOT / 'operations' / 'reports' / f"weekly-evaluation-{report['start_wib']}-to-{report['end_wib_exclusive']}.json"
            out_file.write_text(json_output + "\n", encoding='utf-8')
            print(f"\n[Evaluator] Laporan berhasil disimpan ke: {out_file}", file=sys.stderr)

        if args.send_telegram:
            summary = format_markdown_summary(report)
            res = send_telegram_summary(summary)
            print(f"[Evaluator] Pengiriman Telegram berhasil: message_id={res.get('result', {}).get('message_id')}", file=sys.stderr)

    except (ValueError, OSError, KeyError, TypeError, sqlite3.Error) as err:
        parser.exit(1, f"Data evaluasi tidak valid: {err}\n")


if __name__ == '__main__':
    main()
