import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from app import publication, review


class FakeAPI:
    def __init__(self, fail_on=None, updates=None):
        self.calls = []
        self.fail_on = fail_on
        self.updates = updates or []

    def call(self, method, fields, document=None):
        self.calls.append((method, fields, document))
        if method == self.fail_on:
            raise review.ReviewError('Simulated timeout')
        if method == 'getUpdates':
            return self.updates
        return {'message_id': 100 + len(self.calls)}


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = sqlite3.connect(':memory:')
        self.addCleanup(self.db.close)
        self.db.row_factory = sqlite3.Row
        self.db.executescript((review.ROOT / 'operations/schema.sql').read_text())
        self.db.executescript((review.ROOT / 'operations/migrations/002_telegram_review.sql').read_text())
        self.db.executemany('INSERT INTO characters VALUES (?,?,?)',
                            [('nara', 'Nara Adelia', '@nara.adelia_'),
                             ('dinda', 'Dinda Kemala', '@dinda.kemala_')])
        self.db.commit()
        self.media = self.root / 'characters/nara/content/example/photo.jpg'
        self.media.parent.mkdir(parents=True)
        self.media.write_bytes(b'local fixture bytes, not a generated character asset')
        (self.root / 'config').mkdir()
        self.config = {'enabled': True, 'token_verified': True, 'recipient_paired': True,
                       'allowed_user_ids': [7], 'allowed_chat_ids': [7], 'bot_id': 9}
        (self.root / 'config/project.json').write_text(json.dumps({'telegram_enabled': True}))
        (self.root / 'config/telegram.json').write_text(json.dumps(self.config))
        self.vid = self.register()

    def register(self):
        return review.register(self.db, self.root, 'nara', 'post1', 'photo',
                               str(self.media.relative_to(self.root)), 'Caption lengkap 😀')

    def sent(self, api=None):
        rid = review.prepare(self.db, self.root, self.vid, 7)
        review.send(self.db, self.root, rid, api or FakeAPI())
        return rid

    def query(self, rid, action='a', event='q1'):
        return {'id': event, 'from': {'id': 7, 'is_bot': False}, 'data': f'rv:{rid}:{action}',
                'message': {'message_id': 102, 'chat': {'id': 7, 'type': 'private'}, 'from': {'id': 9}}}

    def count(self):
        return self.db.execute('SELECT COUNT(*) FROM approvals').fetchone()[0]

    def test_publication_requires_acc_matching_account_and_real_video_url(self):
        (self.root / 'config/project.json').write_text(json.dumps({
            'publication_enabled': True, 'telegram_enabled': True,
        }))
        with self.assertRaises(review.ReviewError):
            publication.begin(self.db, self.root, self.vid, '@nara.adelia_')
        delivery = self.sent()
        review.handle_callback(self.db, self.root, self.query(delivery), self.config)
        with self.assertRaises(review.ReviewError):
            publication.begin(self.db, self.root, self.vid, '@dinda.kemala_')
        attempt = publication.begin(self.db, self.root, self.vid, '@nara.adelia_')['publication_id']
        publication.mark_unknown(self.db, attempt)
        with self.assertRaises(review.ReviewError):
            publication.begin(self.db, self.root, self.vid, '@nara.adelia_')
        with self.assertRaises(review.ReviewError):
            publication.confirm(self.db, attempt, 'https://www.tiktok.com/@nara.adelia_')
        publication.confirm(self.db, attempt, 'https://www.tiktok.com/@nara.adelia_/video/1234')
        row = self.db.execute('SELECT * FROM publications WHERE id=?', (attempt,)).fetchone()
        self.assertEqual((row['state'], row['platform_post_id']), ('confirmed', '1234'))

    def test_send_binds_media_caption_and_buttons(self):
        api = FakeAPI(); rid = self.sent(api)
        self.assertEqual([c[0] for c in api.calls], ['sendDocument', 'sendMessage'])
        self.assertEqual(api.calls[0][2][1], self.media.read_bytes())
        # Kebijakan caption 0% emoji (config/project.json caption_policy.no_emoji):
        # adapter membuang emoji dari teks yang dikirim, teks alfabet tetap utuh.
        self.assertIn('Caption lengkap', api.calls[1][1]['text'])
        self.assertNotIn('😀', api.calls[1][1]['text'])
        self.assertIn('@nara.adelia_', api.calls[1][1]['text'])
        for button in api.calls[1][1]['reply_markup']['inline_keyboard'][0]:
            self.assertLessEqual(len(button['callback_data'].encode()), 64)
            self.assertIn(rid, button['callback_data'])

    def test_acc_is_idempotent_and_does_not_publish(self):
        rid = self.sent(); query = self.query(rid)
        review.handle_callback(self.db, self.root, query, self.config)
        review.handle_callback(self.db, self.root, query, self.config)
        review.handle_callback(self.db, self.root, self.query(rid, 'x', 'q2'), self.config)
        self.assertEqual(self.count(), 1)
        review.approved_package(self.db, self.root, self.vid)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM publications').fetchone()[0], 0)

    def test_revise_and_reject_are_not_acc(self):
        for action in ('r', 'x'):
            with self.subTest(action=action):
                self.vid = self.register()
                rid = self.sent()
                review.handle_callback(self.db, self.root, self.query(rid, action, action), self.config)
                with self.assertRaises(review.ReviewError):
                    review.approved_package(self.db, self.root, self.vid)

    def test_unauthorized_sender_chat_message_and_bot(self):
        rid = self.sent()
        for field in ('user', 'chat', 'message', 'bot', 'group'):
            q = self.query(rid)
            if field == 'user': q['from']['id'] = 8
            if field == 'chat': q['message']['chat']['id'] = 8
            if field == 'message': q['message']['message_id'] = 999
            if field == 'bot': q['message']['from']['id'] = 999
            if field == 'group': q['message']['chat']['type'] = 'group'
            review.handle_callback(self.db, self.root, q, self.config)
        self.assertEqual(self.count(), 0)

    def test_new_revision_rejects_old_button_and_old_acc(self):
        rid = self.sent()
        review.handle_callback(self.db, self.root, self.query(rid), self.config)
        self.register()
        with self.assertRaises(review.ReviewError):
            review.approved_package(self.db, self.root, self.vid)
        self.vid = self.register(); rid2 = self.sent(); self.register()
        review.handle_callback(self.db, self.root, self.query(rid2, event='q2'), self.config)
        self.assertEqual(self.count(), 1)

    def test_changed_media_rejected_even_after_acc(self):
        rid = self.sent()
        review.handle_callback(self.db, self.root, self.query(rid), self.config)
        self.media.write_bytes(b'changed')
        with self.assertRaises(review.ReviewError):
            review.approved_package(self.db, self.root, self.vid)
        self.vid = self.register(); rid2 = self.sent(); self.media.write_bytes(b'changed again')
        review.handle_callback(self.db, self.root, self.query(rid2, event='q2'), self.config)
        self.assertEqual(self.count(), 1)

    def test_expired_button_rejected(self):
        rid = self.sent()
        with self.db:
            self.db.execute("UPDATE review_deliveries SET expires_at='2000-01-01' WHERE id=?", (rid,))
        review.handle_callback(self.db, self.root, self.query(rid), self.config)
        self.assertEqual(self.count(), 0)

    def test_unknown_delivery_never_retries(self):
        rid = review.prepare(self.db, self.root, self.vid, 7)
        api = FakeAPI(fail_on='sendMessage')
        with self.assertRaises(review.ReviewError): review.send(self.db, self.root, rid, api)
        self.assertEqual(self.db.execute('SELECT state FROM review_deliveries').fetchone()[0], 'unknown')
        with self.assertRaises(review.ReviewError): review.send(self.db, self.root, rid, api)
        self.assertEqual(len(api.calls), 2)
        review.handle_callback(self.db, self.root, self.query(rid), self.config)
        self.assertEqual(self.count(), 0)

    def test_duplicate_prepare_and_send_blocked(self):
        rid = self.sent()
        with self.assertRaises(review.ReviewError): review.prepare(self.db, self.root, self.vid, 7)
        api = FakeAPI()
        with self.assertRaises(review.ReviewError): review.send(self.db, self.root, rid, api)
        self.assertEqual(api.calls, [])

    def test_disabled_means_no_network_or_credentials_read(self):
        (self.root / 'config/project.json').write_text(json.dumps({'telegram_enabled': False}))
        with patch('urllib.request.urlopen', side_effect=AssertionError('Network forbidden')):
            with self.assertRaises(review.ReviewError):
                review.Telegram(self.root).call('getMe', {})
            with self.assertRaises(review.ReviewError):
                review.receive_once(self.db, self.root, FakeAPI())

    def test_replay_and_restart_cursor(self):
        rid = self.sent()
        api = FakeAPI(updates=[{'update_id': 50, 'callback_query': self.query(rid)}])
        review.receive_once(self.db, self.root, api)
        review.receive_once(self.db, self.root, api)
        self.assertEqual(self.count(), 1)
        gets = [c for c in api.calls if c[0] == 'getUpdates']
        self.assertEqual(gets[1][1]['offset'], 51)
        self.assertEqual(self.db.execute('SELECT next_offset FROM telegram_cursor').fetchone()[0], 51)

    def test_callback_updates_visible_card_and_removes_buttons(self):
        rid = self.sent()
        api = FakeAPI(updates=[{'update_id': 50, 'callback_query': self.query(rid)}])
        review.receive_once(self.db, self.root, api)
        edits = [c for c in api.calls if c[0] == 'editMessageText']
        self.assertEqual(len(edits), 1)
        self.assertIn('ACC tersimpan. Belum diposting.', edits[0][1]['text'])
        self.assertEqual(edits[0][1]['reply_markup']['inline_keyboard'], [])
        self.assertEqual(self.count(), 1)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM publications').fetchone()[0], 0)

    def test_card_edit_failure_does_not_lose_approval_or_cursor(self):
        rid = self.sent()
        api = FakeAPI(fail_on='editMessageText', updates=[{'update_id': 50, 'callback_query': self.query(rid)}])
        self.assertEqual(review.receive_once(self.db, self.root, api), 1)
        self.assertEqual(self.count(), 1)
        self.assertEqual(self.db.execute('SELECT next_offset FROM telegram_cursor').fetchone()[0], 51)

    def test_version_immutable_and_wrong_character_path_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE versions SET caption='changed'")
        self.db.rollback()
        with self.assertRaises(review.ReviewError):
            review.register(self.db, self.root, 'dinda', 'dinda1', 'photo',
                            str(self.media.relative_to(self.root)), 'Caption')

    def test_text_messages_never_become_approval(self):
        self.sent()
        api = FakeAPI(updates=[{'update_id': 60, 'message': {'text': 'ACC'}}])
        review.receive_once(self.db, self.root, api)
        self.assertEqual(self.count(), 0)


if __name__ == '__main__':
    unittest.main()
