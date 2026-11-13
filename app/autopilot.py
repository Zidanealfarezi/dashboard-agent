"""Codex-driven production workflow. No model API, generation or scheduler starts on import."""
import argparse
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
from urllib.parse import urlparse
import uuid

from app import media as video_editor, review

ROOT = review.ROOT
WIB = timezone(timedelta(hours=7))


def load(root, name):
    return json.loads((root / name).read_text())


def reference_status(root, cid):
    profile = load(root, f'characters/{cid}/profile.json')
    folder = (root / profile['reference_inbox']).resolve()
    if root.resolve() not in folder.parents:
        raise review.ReviewError('Folder referensi di luar proyek.')
    files = sorted(p for p in folder.iterdir() if p.is_file() and not p.is_symlink()
                   and p.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp')) if folder.is_dir() else []
    primary = [p for p in files if p.stem.lower() == 'utama']
    selected = None
    if profile.get('master_selection_status') == 'selected_from_user_references':
        selected = next((p for p in files if str(p.relative_to(root.resolve())) == profile.get('master_image')), None)
    chosen = (primary[0] if len(primary) == 1 else None if len(primary) > 1
              else selected if selected else files[0] if len(files) == 1 else None)
    state = 'ready_for_visual_check' if chosen else 'missing' if not files else 'choose_primary'
    if (chosen and profile.get('appearance_status') == 'reference_visually_verified'
            and profile.get('master_image') == str(chosen.relative_to(root.resolve()))
            and profile.get('master_image_sha256') == review.digest(chosen.read_bytes())):
        state = 'ready'
    return {'state': state, 'primary': str(chosen.relative_to(root.resolve())) if chosen else None,
            'references': [str(p.relative_to(root.resolve())) for p in files]}


def sync_references(root):
    """Recognize a supplied primary automatically; no generation or network."""
    result = {}
    for cid in load(root, 'config/autopilot.json')['character_ids']:
        state = reference_status(root, cid)
        if state['primary']:
            profile = load(root, f'characters/{cid}/profile.json')
            photo_hash = review.digest((root / state['primary']).read_bytes())
            unchanged = (profile.get('master_image') == state['primary']
                         and profile.get('master_image_sha256') == photo_hash)
            profile['master_image'] = state['primary']
            profile['master_image_sha256'] = photo_hash
            if not (unchanged and profile.get('appearance_status') == 'reference_visually_verified'):
                profile['appearance_status'] = 'reference_supplied_visual_check_pending'
            (root / f'characters/{cid}/profile.json').write_text(
                json.dumps(profile, ensure_ascii=False, indent=2) + '\n')
        result[cid] = state
    return result


def slot_spec(day_index):
    if not 0 <= day_index < 30:
        raise review.ReviewError('Tanggal di luar siklus 30 hari; jangan membuka siklus baru otomatis.')
    if day_index % 3 == 2:
        return 'photo', None
    video_index = day_index - day_index // 3
    return 'video', (6, 12)[video_index % 2]


def plan_day(db, root, day, kind=None, character_ids=None):
    requested_kind = kind
    settings = load(root, 'config/autopilot.json')
    if not settings['enabled'] or not settings['research_enabled']:
        raise review.ReviewError('Autopilot/riset belum aktif; tidak membuat pekerjaan harian.')
    if not settings['cycle_start_date']:
        raise review.ReviewError('Tanggal awal siklus belum ditetapkan.')
    day = date.fromisoformat(day)
    preferences = settings.get('generation_preferences', {})
    day_index = (day - date.fromisoformat(settings['cycle_start_date'])).days
    slot_kind, slot_duration = slot_spec(day_index)
    if kind is not None:
        if kind not in ('photo', 'video'):
            raise review.ReviewError('Jenis slot harus photo atau video.')
        slot_kind = kind
        slot_duration = None if kind == 'photo' else preferences.get('default_native_duration_seconds', 8)
        if slot_kind == 'video' and slot_duration not in project_native_options(preferences):
            raise review.ReviewError('Durasi native belum diverifikasi; periksa pilihan model Flow.')
    kind, duration = slot_kind, slot_duration
    if kind == 'video' and preferences.get('duration_policy') == 'adapt_to_available_native_model_options':
        duration = preferences.get('default_native_duration_seconds', 8)
        if duration not in preferences.get('verified_native_duration_options_seconds', [4, 6, 8, 10]):
            raise review.ReviewError('Durasi native belum diverifikasi; periksa pilihan model Flow.')
    targets = list(character_ids or settings['character_ids'])
    unknown = [c for c in targets if c not in settings['character_ids']]
    if unknown:
        raise review.ReviewError('Karakter tidak ada di siklus aktif: ' + ', '.join(unknown))
    with db:
        try:
            db.execute('BEGIN IMMEDIATE')
        except sqlite3.OperationalError:
            pass
        for cid in targets:
            slot_id = cid + '-' + day.isoformat()
            char_policy = settings.get('character_slot_policy', {}).get(cid, {})
            min_d = char_policy.get('min_duration_seconds', 10 if cid == 'pak_vincent' else None)
            max_d = char_policy.get('max_duration_seconds', 18 if cid == 'pak_vincent' else None)
            default_d = char_policy.get('default_duration_seconds', 12)
            is_adaptive = preferences.get('duration_policy') == 'adapt_to_available_native_model_options'
            if is_adaptive:
                c_kind = slot_kind
                c_duration = duration
            elif requested_kind is not None:
                c_kind = requested_kind
                c_duration = duration
                if c_kind == 'video' and (min_d is not None or max_d is not None):
                    c_dur = duration or preferences.get('default_native_duration_seconds', default_d)
                    min_val = min_d if min_d is not None else 0
                    max_val = max_d if max_d is not None else 30
                    c_duration = max(min_val, min(max_val, c_dur))
            elif char_policy.get('mode') == 'video_only' or cid == 'pak_vincent':
                c_kind = 'video'
                c_dur = slot_duration or default_d
                min_val = min_d if min_d is not None else 10
                max_val = max_d if max_d is not None else 18
                c_duration = max(min_val, min(max_val, c_dur))
            else:
                c_kind = slot_kind
                if c_kind == 'video' and (min_d is not None or max_d is not None):
                    c_dur = slot_duration or default_d
                    min_val = min_d if min_d is not None else 10
                    max_val = max_d if max_d is not None else 18
                    c_duration = max(min_val, min(max_val, c_dur))
                else:
                    c_duration = duration

            existing = db.execute(
                'SELECT kind,duration_seconds,state FROM daily_slots WHERE id=?', (slot_id,)).fetchone()
            if existing is None:
                db.execute('''INSERT INTO daily_slots
                    (id,day,character_id,kind,duration_seconds,state,created_at)
                    VALUES (?,?,?,?,?,'needs_plan',?)''',
                    (slot_id, day.isoformat(), cid, c_kind, c_duration, review.now()))
            elif existing['state'] == 'needs_plan' and (
                    existing['kind'] != c_kind or existing['duration_seconds'] != c_duration):
                # Slot yang belum direncanakan boleh dikoreksi lewat jalur resmi ini;
                # slot yang sudah planned/reserved tidak pernah diubah.
                db.execute('UPDATE daily_slots SET kind=?,duration_seconds=? WHERE id=?',
                           (c_kind, c_duration, slot_id))
    placeholders = ','.join('?' for _ in targets)
    return [dict(r) for r in db.execute(
        f'SELECT id,character_id,kind,duration_seconds,state FROM daily_slots '
        f'WHERE day=? AND character_id IN ({placeholders})', (day.isoformat(), *targets))]


def project_native_options(preferences):
    return (preferences.get('verified_native_duration_options_seconds')
            or preferences.get('supported_durations_seconds')
            or [4, 6, 8, 10])


def max_video_duration_for(project_config, character_id):
    """Return the character-specific maximum final video duration in seconds."""
    policy = project_config.get('video_policy', {})
    by_char = policy.get('max_duration_by_character', {})
    if character_id in by_char:
        return int(by_char[character_id])
    if character_id == 'bang_ray':
        return 30
    if character_id in ('dinda', 'isk'):
        return 20
    if character_id == 'pak_vincent':
        return 18
    return int(policy.get('max_duration_seconds', 20))


def validate_isk_video_plan(plan, max_final_duration=20):
    """Check the selected concept and timed storyboard before locking the Flow duration."""
    duration = plan.get('duration_seconds')
    max_body = max(1, int(max_final_duration) - 4)
    if type(duration) is not int or not 0 < duration <= max_body:
        raise review.ReviewError(
            f'Durasi klip utama video ISK maksimal {max_body} detik agar total bersama closing maksimal {max_final_duration} detik.'
        )
    final_dur = plan.get('final_duration_seconds')
    if (final_dur != duration + 3 and final_dur != duration + video_editor.BRAND_OUTRO_SECONDS
            and abs(final_dur - (duration + 4.07)) > 0.5):
        raise review.ReviewError('Durasi final ISK harus sama dengan durasi isi ditambah 3 detik closing.')
    if final_dur > max_final_duration + 0.5:
        raise review.ReviewError(f'Durasi final video ISK maksimal {max_final_duration} detik termasuk closing resmi.')

    creative = plan.get('creative')
    if not isinstance(creative, dict) or any(
        not isinstance(creative.get(key), str) or not creative[key].strip()
        for key in ('character', 'background', 'action', 'selection_reason')
    ):
        raise review.ReviewError('Tentukan karakter, latar, aksi utama, dan alasan pemilihan konsep ISK.')
    flow = plan.get('flow')
    if not isinstance(flow, dict) or not isinstance(flow.get('model'), str) or not flow['model'].strip():
        raise review.ReviewError('Catat nama model dari panel Flow sebelum mengunci durasi ISK.')
    options = flow.get('duration_options_seconds')
    if (not isinstance(options, list) or any(type(option) is not int for option in options)
            or (duration not in options and duration not in (10, 12, 14, 15, 16, 20))):
        raise review.ReviewError('Durasi isi ISK harus tersedia untuk model dan mode Flow yang dipilih.')
    shots = plan.get('shots')
    if (not isinstance(shots, list) or not 1 <= len(shots) <= 2
            or any(not isinstance(s, dict) or not s.get('prompt') or type(s.get('seconds')) is not int or s['seconds'] <= 0 for s in shots)
            or sum(s['seconds'] for s in shots) != duration):
        raise review.ReviewError('Siapkan klip dan prompt sesuai durasi isi ISK.')
    model = flow['model'].lower()
    if 'omni' in model and 'flash' in model:
        shot_durs = [s['seconds'] for s in shots]
        if any(
            ('1.1' in model and d not in (4, 6, 8, 10))
            or ('1.2' in model and not 3 <= d <= 20)
            for d in shot_durs
        ):
            raise review.ReviewError('Durasi isi tidak sesuai opsi native model Omni Flash tersebut.')

    dialogue = creative.get('dialogue')
    start = creative.get('dialogue_start_seconds')
    read = creative.get('dialogue_read_seconds')
    action_end = creative.get('action_end_seconds')
    if (not isinstance(dialogue, str) or any(type(value) not in (int, float) or not 0 <= value <= duration
            for value in (start, read, action_end)) or action_end == 0):
        raise review.ReviewError('Catat waktu mulai dialog, durasi baca, dan akhir aksi yang muat di klip.')
    if dialogue.strip():
        if read <= 0 or start + read + 1 > duration:
            raise review.ReviewError('Ringkas dialog atau pilih durasi native yang lebih panjang. Sisakan 1 detik setelah dialog.')
    elif start != 0 or read != 0:
        raise review.ReviewError('Untuk video tanpa dialog, catat waktu mulai dan durasi baca sebagai nol.')


def save_plan(db, root, slot_id, plan, clock=None):
    """Codex writes this structured plan after browsing; the user never fills it daily."""
    clock = clock or datetime.now(timezone.utc)
    settings = load(root, 'config/autopilot.json')
    if not settings['enabled'] or not settings['research_enabled']:
        raise review.ReviewError('Autopilot/riset belum aktif.')
    with db:
        try:
            db.execute('BEGIN IMMEDIATE')
        except sqlite3.OperationalError:
            pass
        slot = db.execute('SELECT * FROM daily_slots WHERE id=?', (slot_id,)).fetchone()
        if not slot or slot['state'] not in ('needs_plan', 'planned'):
            raise review.ReviewError('Slot tidak tersedia untuk rencana baru.')
        profile_bytes = (root / f"characters/{slot['character_id']}/profile.json").read_bytes()
        profile = json.loads(profile_bytes)
        duration = slot['duration_seconds']
        project_cfg = load(root, 'config/project.json')
        max_policy_duration = max_video_duration_for(project_cfg, slot['character_id'])
        isk_video = slot['character_id'] == 'isk' and slot['kind'] == 'video'
        bang_ray_video = slot['character_id'] == 'bang_ray' and slot['kind'] == 'video'
        dinda_video = slot['character_id'] == 'dinda' and slot['kind'] == 'video'
        pak_vincent_video = slot['character_id'] == 'pak_vincent' and slot['kind'] == 'video'
        if (plan.get('character_id') != slot['character_id'] or plan.get('kind') != slot['kind']
                or (not isk_video and not bang_ray_video and not dinda_video and not pak_vincent_video and plan.get('duration_seconds') != duration)):
            raise review.ReviewError('Karakter, jenis, atau durasi rencana tidak sesuai slot.')
        if isk_video:
            validate_isk_video_plan(plan, max_final_duration=max_policy_duration)
            duration = plan['duration_seconds']
        elif bang_ray_video:
            duration = plan.get('duration_seconds')
            if type(duration) is not int or not 3 <= duration <= max_policy_duration:
                raise review.ReviewError(f'Durasi video Bang Ray fleksibel antara 3 sampai {max_policy_duration} detik (maksimal {max_policy_duration} detik).')
        elif dinda_video:
            duration = plan.get('duration_seconds')
            if type(duration) is not int or not 3 <= duration <= max_policy_duration:
                raise review.ReviewError(f'Durasi video Dinda fleksibel antara 3 sampai {max_policy_duration} detik (maksimal {max_policy_duration} detik).')
        elif pak_vincent_video:
            duration = plan.get('duration_seconds')
            if type(duration) is not int or not 10 <= duration <= max_policy_duration:
                raise review.ReviewError(f'Durasi video Pak Vincent fleksibel antara 10 sampai {max_policy_duration} detik (minimal 10 detik, maksimal {max_policy_duration} detik).')
        if slot['kind'] == 'video' and (type(duration) is not int or duration > max_policy_duration):
            raise review.ReviewError(f'Durasi video melebihi batas maksimal {max_policy_duration} detik.')
        if not set(plan.get('role_tags', [])).intersection(profile['content_pillars']):
            raise review.ReviewError('Rencana tidak terkait peran karakter.')
        for key in ('title', 'hook', 'story', 'caption', 'image_prompt', 'role_reason'):
            if not isinstance(plan.get(key), str) or not plan[key].strip():
                raise review.ReviewError('Rencana kreatif belum lengkap: ' + key)
        if len(plan['caption'].encode('utf-16-le')) // 2 > 3000:
            raise review.ReviewError('Caption melampaui batas MVP Telegram.')
        if plan.get('new_biography_facts') != []:
            raise review.ReviewError('Biografi penting baru memerlukan keputusan pengguna.')
        if plan.get('promotional') is not False:
            raise review.ReviewError('Rasio promosi belum diputuskan; rencana promosi ditahan.')
        sources = plan.get('trend_sources', [])
        valid_urls = set()
        for source in sources:
            url = urlparse(source.get('url', ''))
            stamp = datetime.fromisoformat(source.get('observed_at', '').replace('Z', '+00:00'))
            if (url.scheme != 'https' or not url.hostname or not stamp.tzinfo
                    or not source.get('evidence') or not source.get('title')
                    or not timedelta(0) <= clock - stamp <= timedelta(hours=settings['trend_max_age_hours'])):
                raise review.ReviewError('Bukti tren tidak lengkap, kedaluwarsa, atau tanggal tidak valid.')
            valid_urls.add(source['url'])
        if len(valid_urls) < settings['minimum_trend_sources']:
            raise review.ReviewError('Butuh sedikitnya dua sumber tren terkini yang berbeda.')
        if slot['character_id'] == 'rania' and not plan.get('historical_fact_sources'):
            raise review.ReviewError('Rania memerlukan sumber fakta sejarah/budaya terpisah dari bukti tren.')
        if slot['kind'] == 'video':
            shots = plan.get('shots', [])
            if settings.get('generation_preferences', {}).get('max_generation_requests_per_content') == 1 and duration <= 10 and len(shots) != 1:
                raise review.ReviewError('Gunakan satu klip/prompt untuk satu generasi berdurasi <= 10 detik; sesuaikan durasi native.')
            if (not shots or any(not s.get('prompt') or type(s.get('seconds')) is not int
                                 or s['seconds'] <= 0 for s in shots)
                    or sum(s['seconds'] for s in shots) != duration):
                raise review.ReviewError('Storyboard harus lengkap dan sesuai total durasi.')
        db.execute("UPDATE daily_slots SET state='planned',plan_json=?,profile_sha256=?,duration_seconds=? WHERE id=?",
                   (json.dumps(plan, ensure_ascii=False), review.digest(profile_bytes), duration, slot_id))


def generation_account(root, account_id, clock):
    project = load(root, 'config/project.json')
    if project.get('production_hold'):
        raise review.ReviewError('Produksi ditahan untuk rekonsiliasi.')
    settings = load(root, 'config/autopilot.json')
    flow = load(root, 'config/flow_accounts.json')
    if (not settings['enabled'] or not project['generation_enabled'] or not flow['generation_permission']):
        raise review.ReviewError('Izin generasi belum aktif.')
    minimum_free = project.get('storage_policy_proposed', {}).get('minimum_free_gib', 10)
    if shutil.disk_usage(root).free < minimum_free * 1024**3:
        raise review.ReviewError('Ruang kosong tidak cukup; tidak menjalankan generasi.')
    account = next((a for a in flow['accounts'] if a['id'] == account_id), None)
    if (not account or not account['connected'] or not account['balance_verified']
            or account.get('verified_balance') is None or not account.get('project_url')
            or not account.get('balance_verified_at')):
        raise review.ReviewError('Akun, proyek, atau saldo Flow belum diverifikasi.')
    stamp = datetime.fromisoformat(account['balance_verified_at'].replace('Z', '+00:00'))
    if not stamp.tzinfo or not timedelta(0) <= clock - stamp <= timedelta(hours=24):
        raise review.ReviewError('Pemeriksaan saldo sudah kedaluwarsa.')
    return project, settings, account


def check_slot_identity(root, slot, account):
    if account['assigned_character'] != slot['character_id']:
        raise review.ReviewError('Akun Flow tidak sesuai karakter.')
    profile_path = root / f"characters/{slot['character_id']}/profile.json"
    profile_bytes = profile_path.read_bytes()
    profile = json.loads(profile_bytes)
    refs = reference_status(root, slot['character_id'])
    if (not refs['primary'] or profile.get('master_image') != refs['primary']
            or profile.get('appearance_status') != 'reference_visually_verified'
            or profile.get('master_image_sha256') != review.digest((root / refs['primary']).read_bytes())
            or review.digest(profile_bytes) != slot['profile_sha256']):
        raise review.ReviewError('Master/profil belum diperiksa atau berubah; perbarui rencana.')
    body_ref = profile.get('body_reference')
    if body_ref and (body_ref not in refs['references']
                     or profile.get('body_reference_sha256') != review.digest((root / body_ref).read_bytes())):
        raise review.ReviewError('Referensi tubuh tidak sesuai karakter atau berubah; periksa ulang.')


def credit_usage(db, account_id=None):
    totals = db.execute('''
        SELECT COALESCE(SUM(actual_credits), 0),
               COALESCE(SUM(CASE WHEN actual_credits IS NULL THEN authorized_credits ELSE 0 END), 0)
        FROM generation_jobs WHERE (? IS NULL OR flow_account_id=?)
    ''', (account_id, account_id)).fetchone()
    actual, reserved = totals
    return {'recorded_actual_credits': actual, 'reserved_or_unresolved_credits': reserved,
            'committed_credits': actual + reserved}


def check_credit_budget(db, project, settings, account, extra_credits):
    spent = credit_usage(db, account['id'])['committed_credits']
    total = credit_usage(db)['committed_credits']
    cap = settings['flow_account_budget_caps'].get(account['id'], 0)
    if (spent + extra_credits > cap or total + extra_credits > project['generation_budget_authorized_credits']
            or spent + extra_credits > account['verified_balance']):
        raise review.ReviewError('Batas kredit tidak cukup; tidak menjalankan generasi.')


def check_isk_submission(slot, plan, model):
    if slot['character_id'] == 'isk' and slot['kind'] == 'video':
        validate_isk_video_plan(plan)
        if plan['flow']['model'] != model or plan['duration_seconds'] != slot['duration_seconds']:
            raise review.ReviewError('Model atau durasi tidak cocok dengan brief ISK yang dikunci.')


def check_video_model(slot, settings, model):
    preferences = settings.get('generation_preferences', {})
    if slot['kind'] != 'video' or not preferences.get('fallback_model_requires_user_decision'):
        return
    preferred = preferences.get('preferred_model_family', '')
    actual = ' '.join(model.casefold().split())
    if preferred == 'Omni Flash':
        matches = 'omni' in actual and 'flash' in actual
    elif preferred == 'Omni 1.2 Flash':
        matches = actual in ('omni 1.2 flash', 'omni flash 1.2')
    else:
        matches = not preferred or actual == preferred.casefold()
    if not matches:
        raise review.ReviewError(f'Video Flow wajib memakai {preferred}.')


def reserve(db, root, slot_id, account_id, model, credits, clock=None):
    """Reserve budget for one slot. Claim it separately immediately before UI submission."""
    clock = clock or datetime.now(timezone.utc)
    if type(credits) is not int or credits < 0 or not model.strip():
        raise review.ReviewError('Model dan estimasi total kredit wajib diisi.')
    project, settings, account = generation_account(root, account_id, clock)
    with db:
        try:
            db.execute('BEGIN IMMEDIATE')
        except sqlite3.OperationalError:
            pass
        slot = db.execute('SELECT * FROM daily_slots WHERE id=?', (slot_id,)).fetchone()
        if not slot or slot['state'] != 'planned' or slot['job_id']:
            raise review.ReviewError('Slot sudah diproses atau belum memiliki rencana.')
        check_video_model(slot, settings, model)
        if slot['kind'] == 'video' and credits == 0:
            raise review.ReviewError('Biaya video belum terbukti nol; verifikasi biaya dan anggaran.')
        plan = json.loads(slot['plan_json'])
        check_isk_submission(slot, plan, model)
        check_slot_identity(root, slot, account)
        check_credit_budget(db, project, settings, account, credits)
        if db.execute("SELECT 1 FROM generation_jobs WHERE state IN ('planned','submitted','running','unknown','needs_user')").fetchone():
            raise review.ReviewError('Ada pekerjaan lain belum selesai; rekonsiliasi dahulu.')
        job = uuid.uuid4().hex
        outputs = len(plan.get('shots', [])) if slot['kind'] == 'video' else 1
        db.execute('''INSERT INTO generation_jobs
            (id,character_id,flow_account_id,idempotency_key,state,model,duration_seconds,
             output_count,authorized_credits,created_at) VALUES (?,?,?,?,'planned',?,?,?,?,?)''',
            (job, slot['character_id'], account_id, slot_id, model, slot['duration_seconds'], outputs, credits, review.now()))
        db.execute("UPDATE daily_slots SET state='reserved',job_id=? WHERE id=?", (job, slot_id))
    return job


def begin_submission(db, root, slot_id, account_id, project_url, model, duration, outputs, credits, clock=None):
    """Consume the reservation once, immediately before one manual Generate click."""
    with db:
        try:
            db.execute('BEGIN IMMEDIATE')
        except sqlite3.OperationalError:
            pass
        project, settings, account = generation_account(root, account_id, clock or datetime.now(timezone.utc))
        slot = db.execute('SELECT * FROM daily_slots WHERE id=?', (slot_id,)).fetchone()
        job = (db.execute('SELECT * FROM generation_jobs WHERE id=?', (slot['job_id'],)).fetchone()
               if slot and slot['state'] == 'reserved' else None)
        if not job or job['state'] != 'planned':
            raise review.ReviewError('Reservasi tidak tersedia atau sudah pernah dipakai. Periksa Flow sebelum percobaan lain.')
        check_video_model(slot, settings, model)
        expected = (job['flow_account_id'], account['project_url'], job['model'], job['duration_seconds'],
                    job['output_count'], job['authorized_credits'])
        if (account_id, project_url, model, duration, outputs, credits) != expected:
            raise review.ReviewError('Pengaturan yang terlihat di Flow tidak cocok dengan reservasi.')
        check_isk_submission(slot, json.loads(slot['plan_json']), model)
        check_slot_identity(root, slot, account)
        check_credit_budget(db, project, settings, account, 0)
        db.execute("UPDATE generation_jobs SET state='submitted' WHERE id=?", (job['id'],))
        return job['id']


def uncertain(db, slot_id):
    with db:
        slot = db.execute('SELECT job_id FROM daily_slots WHERE id=?', (slot_id,)).fetchone()
        if not slot or not slot['job_id']:
            raise review.ReviewError('Pekerjaan tidak ditemukan.')
        db.execute("UPDATE generation_jobs SET state='unknown' WHERE id=? AND state!='completed'", (slot['job_id'],))
        db.execute("UPDATE daily_slots SET state='unknown' WHERE id=? AND state='reserved'", (slot_id,))


def finish(db, root, slot_id, media, external_job_id, actual_credits, *, creative_checked=False):
    """Use the saved Codex caption; no daily media/caption entry is requested from the user."""
    with db:
        try:
            db.execute('BEGIN IMMEDIATE')
        except sqlite3.OperationalError:
            pass
        slot = db.execute('SELECT * FROM daily_slots WHERE id=?', (slot_id,)).fetchone()
        if not slot or slot['state'] != 'reserved' or not external_job_id.strip():
            raise review.ReviewError('Slot belum siap atau bukti pekerjaan eksternal belum ada.')
        job = db.execute('SELECT * FROM generation_jobs WHERE id=?', (slot['job_id'],)).fetchone()
        if not job or job['state'] not in ('submitted', 'running'):
            raise review.ReviewError('Belum ada pengajuan generasi yang dapat diselesaikan.')
        if db.execute('SELECT 1 FROM generation_jobs WHERE flow_account_id=? AND external_job_id=? AND id!=?',
                      (job['flow_account_id'], external_job_id, job['id'])).fetchone():
            raise review.ReviewError('Bukti pekerjaan Flow ini sudah tercatat untuk job lain.')
        if type(actual_credits) is not int or not 0 <= actual_credits <= job['authorized_credits']:
            raise review.ReviewError('Biaya aktual tidak sesuai anggaran pekerjaan.')
        plan = json.loads(slot['plan_json'])
        if slot['character_id'] == 'isk' and slot['kind'] == 'video' and 'creative' in plan:
            if not creative_checked:
                raise review.ReviewError('Cek dialog, aksi, subtitle dan tiga detik closing sebelum review ISK.')
            path = review.media_path(root, slot['character_id'], media)
            try:
                streams = video_editor.probe(path)['streams']
                video = next(s for s in streams if s['codec_type'] == 'video')
                duration = float(video['duration'])
            except (subprocess.SubprocessError, OSError, StopIteration, KeyError, ValueError) as exc:
                raise review.ReviewError('Durasi video final ISK tidak dapat diperiksa.') from exc
            if not abs(duration - plan['final_duration_seconds']) <= 0.5:
                raise review.ReviewError('Video final ISK harus sesuai durasi isi ditambah 3 detik closing.')
            if plan['creative']['dialogue'].strip() and not any(s['codec_type'] == 'audio' for s in streams):
                raise review.ReviewError('Video dengan dialog harus memiliki audio.')
        version = review.register(db, root, slot['character_id'], slot_id, slot['kind'], media,
                                  plan['caption'], manage_transaction=False)
        # Version and job checkpoint commit atomically; prepare-review can recover separately.
        db.execute("UPDATE daily_slots SET state='review_ready',version_id=? WHERE id=?", (version, slot_id))
        db.execute("UPDATE generation_jobs SET state='completed',external_job_id=?,actual_credits=? WHERE id=?",
                   (external_job_id, actual_credits, slot['job_id']))
    return prepare_review(db, root, slot_id)


def prepare_review(db, root, slot_id):
    slot = db.execute('SELECT * FROM daily_slots WHERE id=?', (slot_id,)).fetchone()
    if not slot or slot['state'] != 'review_ready':
        raise review.ReviewError('Paket belum siap untuk review.')
    config = load(root, 'config/telegram.json')
    if len(config['allowed_chat_ids']) != 1:
        raise review.ReviewError('Penerima review belum dipasangkan.')
    existing = db.execute('SELECT id FROM review_deliveries WHERE version_id=? AND chat_id=?',
                          (slot['version_id'], config['allowed_chat_ids'][0])).fetchone()
    delivery = existing['id'] if existing else review.prepare(db, root, slot['version_id'], config['allowed_chat_ids'][0])
    with db:
        db.execute("UPDATE daily_slots SET state='awaiting_review',delivery_id=? WHERE id=?", (delivery, slot_id))
    return delivery


def status(db, root):
    settings = load(root, 'config/autopilot.json')
    project = load(root, 'config/project.json')
    accounts = load(root, 'config/flow_accounts.json')['accounts']
    budget = credit_usage(db)
    budget['configured_project_cap'] = project['generation_budget_authorized_credits']
    budget['remaining_under_project_cap'] = max(0, budget['configured_project_cap'] - budget['committed_credits'])
    return {'execution_engine': project['operator'],
            'autopilot_enabled': settings['enabled'], 'research_enabled': settings['research_enabled'],
            'generation_enabled': project['generation_enabled'], 'telegram_enabled': project['telegram_enabled'],
            'publication_enabled': project['publication_enabled'], 'production_hold': project.get('production_hold'),
            'credit_budget': budget, 'cycle_start_date': settings['cycle_start_date'],
            'reference_folders': {cid: reference_status(root, cid) for cid in settings['character_ids']},
            'flow': [{'id': a['id'], 'character': a['assigned_character'], 'connected': a['connected'],
                      'balance_verified': a['balance_verified']} for a in accounts],
            'slots': [dict(r) for r in db.execute('''SELECT s.id,s.character_id,s.day,s.kind,s.state,s.delivery_id,
                d.state AS delivery_state,d.decision FROM daily_slots s
                LEFT JOIN review_deliveries d ON d.id=s.delivery_id ORDER BY s.day,s.character_id''')]}


def work_packet(db, root, slot_id):
    slot = db.execute('SELECT * FROM daily_slots WHERE id=?', (slot_id,)).fetchone()
    if not slot:
        raise review.ReviewError('Slot tidak ditemukan.')
    cid = slot['character_id']
    agent = 'Hermes' if load(root, 'config/project.json')['operator'] == 'hermes' else 'Codex'
    recent = db.execute('''SELECT day,plan_json FROM daily_slots WHERE character_id=?
        AND day<? AND plan_json IS NOT NULL ORDER BY day DESC LIMIT 14''', (cid, slot['day']))
    canon = root / f'characters/{cid}/story/canon.md'
    return {'slot': dict(slot), 'profile': load(root, f'characters/{cid}/profile.json'),
            'references': reference_status(root, cid), 'canon': canon.read_text() if canon.is_file() else '',
            'recent_plans': [{'day': r['day'], 'plan': json.loads(r['plan_json'])} for r in recent],
            'instructions': agent + ' mencari sumber tren dan membuat rencana sesuai docs/autopilot-runbook.md; bukan tugas input harian pengguna.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('status')
    commands.add_parser('sync-references')
    work = commands.add_parser('work'); work.add_argument('--slot', required=True)
    day = commands.add_parser('plan-day'); day.add_argument('--date', required=True)
    day.add_argument('--kind', choices=['photo', 'video'],
                     help='Override jenis slot untuk tanggal ini (default: rotasi slot_spec).')
    day.add_argument('--character', action='append', dest='characters',
                     help='Batasi pembuatan slot ke karakter tertentu; boleh diulang.')

    plan = commands.add_parser('save-plan'); plan.add_argument('--slot', required=True); plan.add_argument('--file', required=True)
    reserve_cmd = commands.add_parser('reserve'); reserve_cmd.add_argument('--slot', required=True)
    reserve_cmd.add_argument('--account', required=True); reserve_cmd.add_argument('--model', required=True)
    reserve_cmd.add_argument('--credits', required=True, type=int)
    submit = commands.add_parser('begin-submit')
    submit.add_argument('--slot', required=True); submit.add_argument('--account', required=True)
    submit.add_argument('--project-url', required=True); submit.add_argument('--model', required=True)
    submit.add_argument('--duration', type=int); submit.add_argument('--outputs', required=True, type=int)
    submit.add_argument('--credits', required=True, type=int)
    unknown = commands.add_parser('mark-unknown'); unknown.add_argument('--slot', required=True)
    complete = commands.add_parser('finish'); complete.add_argument('--slot', required=True)
    complete.add_argument('--media', required=True); complete.add_argument('--external-job', required=True)
    complete.add_argument('--actual-credits', required=True, type=int)
    complete.add_argument('--creative-checked', action='store_true',
                          help='Konfirmasi dialog, aksi, subtitle dan closing ISK sudah ditonton utuh.')
    prep = commands.add_parser('prepare-review'); prep.add_argument('--slot', required=True)
    args = parser.parse_args()
    try:
        with review.connect(ROOT) as db:
            if args.command == 'status': result = status(db, ROOT)
            elif args.command == 'sync-references': result = sync_references(ROOT)
            elif args.command == 'plan-day':
                result = plan_day(db, ROOT, args.date, kind=args.kind, character_ids=args.characters)
            elif args.command == 'work': result = work_packet(db, ROOT, args.slot)
            elif args.command == 'save-plan':
                save_plan(db, ROOT, args.slot, load(ROOT, args.file)); result = {'saved': True}
            elif args.command == 'reserve': result = {'job_id': reserve(db, ROOT, args.slot, args.account, args.model, args.credits)}
            elif args.command == 'begin-submit':
                result = {'job_id': begin_submission(db, ROOT, args.slot, args.account, args.project_url,
                                                    args.model, args.duration, args.outputs, args.credits),
                          'state': 'submitted'}
            elif args.command == 'mark-unknown': uncertain(db, args.slot); result = {'state': 'unknown'}
            elif args.command == 'finish':
                result = {'review_id': finish(db, ROOT, args.slot, args.media, args.external_job,
                                              args.actual_credits, creative_checked=args.creative_checked)}
            else: result = {'review_id': prepare_review(db, ROOT, args.slot)}
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (review.ReviewError, OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        # No network/secret values are included in these validation errors.
        if isinstance(exc, review.ReviewError): parser.exit(1, str(exc) + '\n')
        parser.exit(1, 'Draf/config belum valid; periksa format lokal tanpa membagikan rahasia.\n')


if __name__ == '__main__':
    main()
