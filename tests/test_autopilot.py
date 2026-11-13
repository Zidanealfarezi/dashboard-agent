from collections import Counter
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock, patch

from app import autopilot, publication, review


class AutopilotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'config').mkdir()
        self.db = sqlite3.connect(':memory:'); self.db.row_factory = sqlite3.Row
        self.addCleanup(self.db.close)
        for path in ['operations/schema.sql', 'operations/migrations/002_telegram_review.sql',
                     'operations/migrations/003_autopilot.sql']:
            self.db.executescript((autopilot.ROOT / path).read_text())
        for name in ['autopilot', 'project', 'flow_accounts']:
            self.write(f'config/{name}.json', autopilot.load(autopilot.ROOT, f'config/{name}.json'))
        self.write('config/telegram.json', {'allowed_chat_ids': [7], 'enabled': False})
        for cid, label in [('nara', 'Nara'), ('dinda', 'Dinda'), ('rania', 'Rania')]:
            profile = autopilot.load(autopilot.ROOT, f'characters/{cid}/profile.json')
            profile.update(master_image=None, master_image_sha256=None,
                           master_selection_status=None, body_reference=None,
                           body_reference_sha256=None, appearance_status='awaiting_actual_master')
            self.write(f'characters/{cid}/profile.json', profile)
            (self.root / profile['reference_inbox']).mkdir(parents=True)
            self.db.execute('INSERT INTO characters VALUES (?,?,?)',
                            (cid, profile['name'], profile['tiktok_account']))
        self.db.commit()
        self.settings = autopilot.load(self.root, 'config/autopilot.json')
        self.settings.update(enabled=True, research_enabled=True, cycle_start_date='2026-11-04',
                             character_ids=['nara', 'dinda', 'rania'])
        # Baseline tests exercise the original cadence; preference tests opt into the newer policy.
        self.settings.pop('generation_preferences', None)
        self.write('config/autopilot.json', self.settings)
        self.clock = datetime(2026, 11, 4, 10, tzinfo=timezone.utc)
        autopilot.plan_day(self.db, self.root, '2026-11-04')
        self.slot = 'nara-2026-11-04'
        self.plan = {'character_id': 'nara', 'kind': 'video', 'duration_seconds': 6,
                     'role_tags': ['beauty'], 'title': 'Test topic', 'hook': 'Test hook',
                     'story': 'Test story', 'caption': 'Caption written by Codex, not the user',
                     'image_prompt': 'Reference-consistent image', 'role_reason': 'Beauty role',
                     'new_biography_facts': [], 'promotional': False,
                     'trend_sources': [{'url': f'https://example.com/test-{n}', 'title': 'Test source',
                                        'observed_at': self.clock.isoformat(), 'evidence': 'Test fixture only'} for n in (1, 2)],
                     'shots': [{'seconds': 6, 'prompt': 'Test video prompt'}]}

    def write(self, name, data):
        p = self.root / name; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

    def enable_generation(self):
        cid = self.plan['character_id']
        project = autopilot.load(self.root, 'config/project.json')
        project.pop('production_hold', None)
        project.update(generation_enabled=True, generation_budget_authorized_credits=100)
        project['storage_policy_proposed']['minimum_free_gib'] = 0
        self.write('config/project.json', project)
        self.settings['flow_account_budget_caps']['flow_1'] = 100
        self.write('config/autopilot.json', self.settings)
        flow = autopilot.load(self.root, 'config/flow_accounts.json'); flow['generation_permission'] = True
        flow['accounts'][0].update(connected=True, balance_verified=True, verified_balance=100,
                                   assigned_character=cid, project_url='https://labs.google/test-project',
                                   balance_verified_at=self.clock.isoformat())
        self.write('config/flow_accounts.json', flow)
        profile_path = f'characters/{cid}/profile.json'
        profile = autopilot.load(self.root, profile_path)
        master = self.root / profile['reference_inbox'] / 'utama.jpg'
        master.write_bytes(b'test master')
        autopilot.sync_references(self.root)
        profile = autopilot.load(self.root, profile_path)
        profile['appearance_status'] = 'reference_visually_verified'
        self.write(profile_path, profile)
        autopilot.save_plan(self.db, self.root, self.slot, self.plan, self.clock)

    def reserve(self, credits=20):
        return autopilot.reserve(self.db, self.root, self.slot, 'flow_1', 'Test model', credits, self.clock)

    def begin(self, credits=20):
        return autopilot.begin_submission(self.db, self.root, self.slot, 'flow_1',
                                          'https://labs.google/test-project', 'Test model',
                                          6, 1, credits, self.clock)

    def test_omni_12_policy_blocks_old_model_at_both_gates(self):
        self.enable_generation()
        args = self.db, self.root, self.slot, 'flow_1'
        autopilot.reserve(*args, 'Omni 1.1 Flash', 20, self.clock)
        self.settings['generation_preferences'] = {
            'preferred_model_family': 'Omni 1.2 Flash',
            'fallback_model_requires_user_decision': True,
        }
        self.write('config/autopilot.json', self.settings)
        with self.assertRaisesRegex(review.ReviewError, 'Omni 1.2 Flash'):
            autopilot.begin_submission(*args, 'https://labs.google/test-project',
                                       'Omni 1.1 Flash', 6, 1, 20, self.clock)
        self.db.execute('UPDATE daily_slots SET state=\'planned\', job_id=NULL WHERE id=?', (self.slot,))
        self.db.execute('DELETE FROM generation_jobs')
        self.db.commit()
        with self.assertRaisesRegex(review.ReviewError, 'Omni 1.2 Flash'):
            autopilot.reserve(*args, 'Omni 1.1 Flash', 20, self.clock)
        job = autopilot.reserve(*args, 'Omni Flash 1.2', 20, self.clock)
        self.assertEqual(autopilot.begin_submission(*args, 'https://labs.google/test-project',
                                                    'Omni Flash 1.2', 6, 1, 20, self.clock), job)

    def plan_isk_video(self):
        profile = autopilot.load(autopilot.ROOT, 'characters/isk/profile.json')
        self.write('characters/isk/profile.json', profile)
        (self.root / profile['reference_inbox']).mkdir(parents=True)
        self.db.execute('INSERT INTO characters VALUES (?,?,?)',
                        ('isk', profile['name'], profile['tiktok_account']))
        self.db.commit()
        self.settings['character_ids'] = ['isk']
        self.write('config/autopilot.json', self.settings)
        autopilot.plan_day(self.db, self.root, '2026-11-04')
        self.slot = 'isk-2026-11-04'
        self.plan.update(character_id='isk', role_tags=['paku cap keris'],
                         duration_seconds=12, final_duration_seconds=15,
                         shots=[{'seconds': 12, 'prompt': 'One action and one line'}],
                         flow={'model': 'Omni Flash 1.2', 'duration_options_seconds': [10, 12, 15]},
                         creative={'character': 'Tukang bengkel', 'background': 'Meja kayu',
                                   'action': 'Buka kardus', 'selection_reason': 'Demo isi kemasan',
                                   'dialogue': 'Lihat isi kardusnya.',
                                   'dialogue_start_seconds': 2, 'dialogue_read_seconds': 8,
                                   'action_end_seconds': 10})

    def test_isk_rejects_dialogue_overrun_and_unavailable_duration_before_locking(self):
        self.plan_isk_video()
        self.plan['creative']['dialogue_read_seconds'] = 9.5
        with self.assertRaisesRegex(review.ReviewError, 'Sisakan 1 detik'):
            autopilot.save_plan(self.db, self.root, self.slot, self.plan, self.clock)
        self.plan['creative']['dialogue_read_seconds'] = 8
        self.plan['flow']['model'] = 'Omni 1.1 Flash'
        with self.assertRaisesRegex(review.ReviewError, 'opsi native model'):
            autopilot.save_plan(self.db, self.root, self.slot, self.plan, self.clock)
        self.assertEqual(self.db.execute('SELECT state FROM daily_slots WHERE id=?', (self.slot,)).fetchone()[0],
                         'needs_plan')

    def test_isk_locks_creative_duration_through_submission_and_checks_final(self):
        self.plan_isk_video()
        self.enable_generation()
        model = self.plan['flow']['model']
        autopilot.reserve(self.db, self.root, self.slot, 'flow_1', model, 20, self.clock)
        args = self.db, self.root, self.slot, 'flow_1', 'https://labs.google/test-project', model
        with self.assertRaisesRegex(review.ReviewError, 'tidak cocok dengan reservasi'):
            autopilot.begin_submission(*args, 10, 1, 20, self.clock)
        autopilot.begin_submission(*args, 12, 1, 20, self.clock)
        relative = Path('characters/isk/content/test.mp4')
        output = self.root / relative
        output.parent.mkdir()
        output.write_bytes(b'local test video')
        args = self.db, self.root, self.slot, str(relative), 'external-fixture-id', 20
        with self.assertRaisesRegex(review.ReviewError, 'Cek dialog'):
            autopilot.finish(*args)
        streams = [{'codec_type': 'video', 'duration': '12'}, {'codec_type': 'audio'}]
        with patch('app.autopilot.video_editor.probe', return_value={'streams': streams}):
            with self.assertRaisesRegex(review.ReviewError, '3 detik closing'):
                autopilot.finish(*args, creative_checked=True)
            streams[0]['duration'] = '15'
            self.assertTrue(autopilot.finish(*args, creative_checked=True))

    def test_cadence_exactly_twenty_videos_ten_photos(self):
        specs = [autopilot.slot_spec(i) for i in range(30)]
        self.assertEqual(Counter(k for k, d in specs), {'video': 20, 'photo': 10})
        self.assertEqual(Counter(d for k, d in specs if k == 'video'), {6: 10, 12: 10})

    def test_three_daily_slots_idempotent_no_generation(self):
        autopilot.plan_day(self.db, self.root, '2026-11-04')
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM daily_slots').fetchone()[0], 3)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM generation_jobs').fetchone()[0], 0)

    def test_adaptive_duration_uses_single_native_eight_second_clip(self):
        self.settings['generation_preferences'] = {'duration_policy': 'adapt_to_available_native_model_options',
            'default_native_duration_seconds': 8, 'verified_native_duration_options_seconds': [4,6,8,10],
            'max_generation_requests_per_content': 1}
        self.write('config/autopilot.json', self.settings)
        slots = autopilot.plan_day(self.db, self.root, '2026-11-05')
        self.assertTrue(all(s['duration_seconds'] == 8 for s in slots))
        plan = dict(self.plan, duration_seconds=8, shots=[{'seconds':4,'prompt':'a'},{'seconds':4,'prompt':'b'}])
        with self.assertRaises(review.ReviewError):
            autopilot.save_plan(self.db,self.root,'nara-2026-11-05',plan,self.clock)

    def test_setup_mode_blocks_daily_work(self):
        self.settings['enabled'] = False; self.write('config/autopilot.json', self.settings)
        with self.assertRaises(review.ReviewError): autopilot.plan_day(self.db, self.root, '2026-11-05')

    def test_reference_folder_automatic_single_or_primary(self):
        folder = self.root / 'FOTO_KARAKTER/Nara'
        self.assertEqual(autopilot.reference_status(self.root, 'nara')['state'], 'missing')
        (folder / 'one.jpg').write_bytes(b'test one')
        self.assertEqual(autopilot.reference_status(self.root, 'nara')['primary'], 'FOTO_KARAKTER/Nara/one.jpg')
        (folder / 'two.jpg').write_bytes(b'test two')
        self.assertEqual(autopilot.reference_status(self.root, 'nara')['state'], 'choose_primary')
        (folder / 'utama.png').write_bytes(b'test primary')
        result = autopilot.sync_references(self.root)
        self.assertEqual(result['nara']['primary'], 'FOTO_KARAKTER/Nara/utama.png')
        self.assertIsNone(autopilot.load(self.root, 'characters/dinda/profile.json')['master_image'])

    def test_selected_reference_needs_no_renaming_and_sync_preserves_review(self):
        folder = self.root / 'FOTO_KARAKTER/Nara'
        (folder / 'face-sheet.jpg').write_bytes(b'face fixture')
        (folder / 'outfit.jpg').write_bytes(b'outfit fixture')
        profile = autopilot.load(self.root, 'characters/nara/profile.json')
        profile.update(master_image='FOTO_KARAKTER/Nara/face-sheet.jpg',
                       master_image_sha256=review.digest(b'face fixture'),
                       master_selection_status='selected_from_user_references',
                       appearance_status='reference_visually_verified')
        self.write('characters/nara/profile.json', profile)
        self.assertEqual(autopilot.reference_status(self.root, 'nara')['state'], 'ready')
        autopilot.sync_references(self.root)
        self.assertEqual(autopilot.load(self.root, 'characters/nara/profile.json')['appearance_status'], 'reference_visually_verified')
        (folder / 'face-sheet.jpg').write_bytes(b'replaced fixture')
        autopilot.sync_references(self.root)
        self.assertEqual(autopilot.load(self.root, 'characters/nara/profile.json')['appearance_status'], 'reference_supplied_visual_check_pending')

    def test_reference_selection_cannot_take_another_characters_photo(self):
        folder = self.root / 'FOTO_KARAKTER/Nara'
        (folder / 'one.jpg').write_bytes(b'one')
        (folder / 'two.jpg').write_bytes(b'two')
        profile = autopilot.load(self.root, 'characters/nara/profile.json')
        profile.update(master_image='FOTO_KARAKTER/Dinda/face.jpg',
                       master_selection_status='selected_from_user_references')
        self.write('characters/nara/profile.json', profile)
        self.assertEqual(autopilot.reference_status(self.root, 'nara')['state'], 'choose_primary')

    def test_changed_body_reference_blocks_generation(self):
        self.enable_generation()
        body = self.root / 'FOTO_KARAKTER/Nara/body.jpg'
        body.write_bytes(b'body fixture')
        profile = autopilot.load(self.root, 'characters/nara/profile.json')
        profile.update(body_reference='FOTO_KARAKTER/Nara/body.jpg',
                       body_reference_sha256=review.digest(b'body fixture'))
        self.write('characters/nara/profile.json', profile)
        autopilot.save_plan(self.db, self.root, self.slot, self.plan, self.clock)
        body.write_bytes(b'replaced body fixture')
        with self.assertRaises(review.ReviewError): self.reserve()

    def test_stale_duplicate_or_future_sources_rejected(self):
        for case in ('stale', 'future', 'duplicate'):
            plan = json.loads(json.dumps(self.plan))
            if case == 'duplicate': plan['trend_sources'][1] = plan['trend_sources'][0]
            else:
                stamp = self.clock + timedelta(days=-4 if case == 'stale' else 1)
                plan['trend_sources'][0]['observed_at'] = stamp.isoformat()
            with self.subTest(case=case), self.assertRaises(review.ReviewError):
                autopilot.save_plan(self.db, self.root, self.slot, plan, self.clock)

    def test_wrong_role_biography_and_promotion_rejected(self):
        for field, value in [('role_tags', ['unrelated']), ('character_id', 'dinda'),
                             ('new_biography_facts', ['invented friend']), ('promotional', True)]:
            plan = dict(self.plan); plan[field] = value
            with self.subTest(field=field), self.assertRaises(review.ReviewError):
                autopilot.save_plan(self.db, self.root, self.slot, plan, self.clock)

    def test_wrong_duration_rejected(self):
        self.plan['shots'][0]['seconds'] = 12
        with self.assertRaises(review.ReviewError):
            autopilot.save_plan(self.db, self.root, self.slot, self.plan, self.clock)

    def test_default_generation_gate_closed(self):
        autopilot.save_plan(self.db, self.root, self.slot, self.plan, self.clock)
        with self.assertRaises(review.ReviewError): self.reserve()

    def test_zero_cap_and_changed_master_block_reservation(self):
        self.enable_generation()
        self.settings['flow_account_budget_caps']['flow_1'] = 0
        self.write('config/autopilot.json', self.settings)
        with self.assertRaises(review.ReviewError): self.reserve()
        self.settings['flow_account_budget_caps']['flow_1'] = 100
        self.write('config/autopilot.json', self.settings)
        (self.root / 'FOTO_KARAKTER/Nara/utama.jpg').write_bytes(b'replaced master')
        with self.assertRaises(review.ReviewError): self.reserve()

    def test_generation_reservation_idempotent_and_unknown_blocks_retry(self):
        self.enable_generation(); job = self.reserve()
        self.assertTrue(job)
        with self.assertRaises(review.ReviewError): self.reserve()
        autopilot.uncertain(self.db, self.slot)
        with self.assertRaises(review.ReviewError): self.reserve()
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM generation_jobs').fetchone()[0], 1)
        with self.assertRaises(review.ReviewError):
            autopilot.save_plan(self.db, self.root, self.slot, self.plan, self.clock)

    def test_submission_consumes_only_matching_reservation(self):
        self.enable_generation()
        with self.assertRaises(review.ReviewError):
            self.begin()
        job = self.reserve()
        with self.assertRaises(review.ReviewError):
            self.begin(21)
        self.assertEqual(self.begin(), job)
        self.assertEqual(self.db.execute('SELECT state FROM generation_jobs').fetchone()[0], 'submitted')
        with self.assertRaises(review.ReviewError):
            self.begin()

    def test_dinda_package_uses_one_credit_ledger_through_confirmed_publication(self):
        self.slot = 'dinda-2026-11-04'
        dinda = autopilot.load(self.root, 'characters/dinda/profile.json')
        self.plan.update(character_id='dinda', role_tags=[dinda['content_pillars'][0]])
        self.enable_generation()
        project = autopilot.load(self.root, 'config/project.json')
        project.update(publication_enabled=True, telegram_enabled=True)
        self.write('config/project.json', project)
        telegram = {'allowed_chat_ids': [7], 'allowed_user_ids': [7], 'bot_id': 9,
                    'enabled': True, 'token_verified': True, 'recipient_paired': True}
        self.write('config/telegram.json', telegram)

        job_id = self.reserve(20)
        self.assertEqual(autopilot.status(self.db, self.root)['credit_budget']['remaining_under_project_cap'], 80)
        self.assertEqual(self.begin(20), job_id)
        with self.assertRaises(review.ReviewError):
            self.begin(20)
        output = self.root / 'characters/dinda/content/dry-run.mp4'
        output.parent.mkdir()
        output.write_bytes(b'dry-run artifact')
        delivery_id = autopilot.finish(self.db, self.root, self.slot, str(output.relative_to(self.root)),
                                       'fixture-flow-id', 19)
        version_id = self.db.execute('SELECT version_id FROM review_deliveries WHERE id=?',
                                     (delivery_id,)).fetchone()[0]
        account = dinda['tiktok_account']
        with self.assertRaises(review.ReviewError):
            publication.begin(self.db, self.root, version_id, account)
        api = Mock()
        api.call.side_effect = [{'message_id': 101}, {'message_id': 102}]
        review.send(self.db, self.root, delivery_id, api)
        review.handle_callback(self.db, self.root, {
            'id': 'fixture-acc', 'from': {'id': 7, 'is_bot': False},
            'data': f'rv:{delivery_id}:a',
            'message': {'message_id': 102, 'chat': {'id': 7, 'type': 'private'}, 'from': {'id': 9}},
        }, telegram)

        with sqlite3.connect(self.root / 'restart.sqlite') as reopened:
            self.db.backup(reopened)
            reopened.row_factory = sqlite3.Row
            attempt = publication.begin(reopened, self.root, version_id, account)
            publication.confirm(reopened, attempt['publication_id'], f'https://www.tiktok.com/{account}/video/1234')
            row = reopened.execute('SELECT state,platform_post_id FROM publications').fetchone()
            self.assertEqual(tuple(row), ('confirmed', '1234'))
            self.assertEqual(autopilot.status(reopened, self.root)['credit_budget'], {
                'recorded_actual_credits': 19, 'reserved_or_unresolved_credits': 0, 'committed_credits': 19,
                'configured_project_cap': 100, 'remaining_under_project_cap': 81,
            })
            with self.assertRaises(review.ReviewError):
                publication.begin(reopened, self.root, version_id, account)

    def test_finish_uses_saved_caption_and_prepares_review_without_network(self):
        self.enable_generation(); self.reserve(); self.begin()
        output = self.root / 'characters/nara/content/output.mp4'
        output.parent.mkdir(); output.write_bytes(b'test result only')
        with patch('urllib.request.urlopen', side_effect=AssertionError('Network forbidden')):
            delivery = autopilot.finish(self.db, self.root, self.slot, str(output.relative_to(self.root)), 'external-fixture-id', 20)
        self.assertTrue(delivery)
        self.assertEqual(self.db.execute('SELECT caption FROM versions').fetchone()[0], self.plan['caption'])
        self.assertEqual(self.db.execute('SELECT state FROM review_deliveries').fetchone()[0], 'prepared')
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM publications').fetchone()[0], 0)
        with self.assertRaises(review.ReviewError):
            autopilot.finish(self.db, self.root, self.slot, str(output.relative_to(self.root)), 'same-job', 20)

    def test_review_prepare_failure_recovers_without_duplicate_version(self):
        self.enable_generation(); self.reserve(); self.begin()
        output = self.root / 'characters/nara/content/output.mp4'
        output.parent.mkdir(); output.write_bytes(b'test result only')
        with patch('app.review.prepare', side_effect=review.ReviewError('Simulated interruption')):
            with self.assertRaises(review.ReviewError):
                autopilot.finish(self.db, self.root, self.slot, str(output.relative_to(self.root)), 'fixture', 20)
        self.assertEqual(self.db.execute('SELECT state FROM daily_slots WHERE id=?', (self.slot,)).fetchone()[0], 'review_ready')
        autopilot.prepare_review(self.db, self.root, self.slot)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM versions').fetchone()[0], 1)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM review_deliveries').fetchone()[0], 1)

    def test_photo_can_reserve_verified_zero_credit_cost(self):
        self.enable_generation()
        autopilot.plan_day(self.db, self.root, '2026-11-06')
        self.slot = 'nara-2026-11-06'
        self.plan.update(kind='photo', duration_seconds=None, shots=[])
        autopilot.save_plan(self.db, self.root, self.slot, self.plan, self.clock)
        self.assertTrue(self.reserve(0))

    def test_failed_finish_rolls_back_without_losing_reservation(self):
        self.enable_generation(); self.reserve(); self.begin()
        with self.assertRaises(review.ReviewError):
            autopilot.finish(self.db, self.root, self.slot, 'characters/dinda/content/wrong.mp4', 'fixture', 20)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM versions').fetchone()[0], 0)
        self.assertEqual(self.db.execute('SELECT state FROM daily_slots WHERE id=?', (self.slot,)).fetchone()[0], 'reserved')

    def test_bang_ray_allows_flexible_video_duration(self):
        profile = autopilot.load(autopilot.ROOT, 'characters/bang_ray/profile.json')
        self.write('characters/bang_ray/profile.json', profile)
        self.db.execute('INSERT INTO characters VALUES (?,?,?)', ('bang_ray', 'Bang Ray', '@teuku.rayyan00'))
        self.db.execute("INSERT INTO daily_slots VALUES ('bang_ray-2026-11-04','2026-11-04','bang_ray','video',8,'needs_plan',NULL,NULL,NULL,NULL,NULL,'2026-11-04T10:00:00+00:00')")
        self.db.commit()
        flex_plan = dict(self.plan, character_id='bang_ray', duration_seconds=30,
                         role_tags=['tips dan trik tukang dan kerja bangunan praktis'],
                         shots=[{'seconds': 15, 'prompt': 'Bang Ray hook trik keramik 360p'},
                                {'seconds': 15, 'prompt': 'Bang Ray demonstrasi lanjutan 360p'}])
        autopilot.save_plan(self.db, self.root, 'bang_ray-2026-11-04', flex_plan, self.clock)
        self.assertEqual(self.db.execute("SELECT duration_seconds FROM daily_slots WHERE id='bang_ray-2026-11-04'").fetchone()[0], 30)
        over_plan = dict(flex_plan, duration_seconds=31, shots=[{'seconds': 15, 'prompt': 'Klip 1'}, {'seconds': 16, 'prompt': 'Terlalu panjang'}])
        with self.assertRaisesRegex(review.ReviewError, 'maksimal 30 detik'):
            autopilot.save_plan(self.db, self.root, 'bang_ray-2026-11-04', over_plan, self.clock)

    def test_dinda_and_isk_enforce_20s_cap(self):
        dinda_slot = 'dinda-2026-11-04'
        dinda_plan = dict(self.plan, character_id='dinda', duration_seconds=20,
                          role_tags=['lifestyle'],
                          shots=[{'seconds': 10, 'prompt': 'Dinda opening vlog 360p'},
                                 {'seconds': 10, 'prompt': 'Dinda penutup vlog 360p'}])
        autopilot.save_plan(self.db, self.root, dinda_slot, dinda_plan, self.clock)
        self.assertEqual(self.db.execute('SELECT duration_seconds FROM daily_slots WHERE id=?', (dinda_slot,)).fetchone()[0], 20)
        dinda_over = dict(dinda_plan, duration_seconds=21, shots=[{'seconds': 10, 'prompt': 'A'}, {'seconds': 11, 'prompt': 'B'}])
        with self.assertRaisesRegex(review.ReviewError, 'maksimal 20 detik'):
            autopilot.save_plan(self.db, self.root, dinda_slot, dinda_over, self.clock)

        self.plan_isk_video()
        ok_isk = dict(self.plan, duration_seconds=15, final_duration_seconds=19.07,
                      shots=[{'seconds': 15, 'prompt': 'Demo penuh produk ISK 360p'}],
                      flow={'model': 'Omni Flash 1.2', 'duration_options_seconds': [8, 12, 15]},
                      creative=dict(self.plan['creative'], dialogue_start_seconds=1, dialogue_read_seconds=12, action_end_seconds=14))
        autopilot.save_plan(self.db, self.root, self.slot, ok_isk, self.clock)
        bad_isk = dict(ok_isk, duration_seconds=17, final_duration_seconds=21.07,
                       shots=[{'seconds': 17, 'prompt': 'Terlalu panjang'}],
                       flow={'model': 'Omni Flash 1.2', 'duration_options_seconds': [15, 17]})
        with self.assertRaisesRegex(review.ReviewError, 'maksimal 20 detik'):
            autopilot.save_plan(self.db, self.root, self.slot, bad_isk, self.clock)


    def test_plan_day_kind_override_and_character_filter(self):
        # 2026-11-06 = indeks 2 -> rotasi foto; override resmi ke video untuk satu karakter.
        slots = autopilot.plan_day(self.db, self.root, '2026-11-06',
                                   kind='video', character_ids=['dinda'])
        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0]['character_id'], 'dinda')
        self.assertEqual(slots[0]['kind'], 'video')
        self.assertIn(slots[0]['duration_seconds'], (4, 6, 8, 10))
        # Tanpa override, rotasi tetap menghasilkan foto untuk ketiga karakter.
        plain = autopilot.plan_day(self.db, self.root, '2026-11-09')
        self.assertEqual(len(plain), 3)
        self.assertEqual({s['kind'] for s in plain}, {'photo'})
        self.assertEqual({s['duration_seconds'] for s in plain}, {None})

    def test_plan_day_rejects_unknown_kind_and_character(self):
        with self.assertRaisesRegex(review.ReviewError, 'photo atau video'):
            autopilot.plan_day(self.db, self.root, '2026-11-07', kind='audio')
        with self.assertRaisesRegex(review.ReviewError, 'tidak ada di siklus'):
            autopilot.plan_day(self.db, self.root, '2026-11-07', character_ids=['bang_ray'])


    def test_pak_vincent_video_duration_and_slot(self):
        # Pak Vincent wajib otomatis mendapat slot video dengan durasi 10-18 detik, bahkan di hari rotasi foto
        self.db.execute('INSERT INTO characters VALUES (?,?,?)', ('pak_vincent', 'Pak Vincent', '@pakvincent.riau'))
        self.settings['character_ids'].append('pak_vincent')
        self.settings['character_slot_policy'] = {
            'pak_vincent': {
                'mode': 'video_only',
                'min_duration_seconds': 10,
                'max_duration_seconds': 18,
                'default_duration_seconds': 10
            }
        }
        self.write('config/autopilot.json', self.settings)
        # 2026-11-06 = indeks 2 -> hari rotasi foto; Pak Vincent tetap otomatis video 10-18s
        slots = autopilot.plan_day(self.db, self.root, '2026-11-06', character_ids=['pak_vincent'])
        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0]['character_id'], 'pak_vincent')
        self.assertEqual(slots[0]['kind'], 'video')
        self.assertTrue(10 <= slots[0]['duration_seconds'] <= 18)


if __name__ == '__main__':
    unittest.main()
