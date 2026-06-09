import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

from telethon.tl.types import (
    MessageMediaPhoto, MessageMediaDocument, MessageMediaPoll,
    MessageMediaGeo, MessageMediaContact, MessageMediaVenue,
    MessageMediaGeoLive, DocumentAttributeFilename,
    Message,
)

from click.testing import CliRunner

from tg_up.clone_operation import (
    _media_type_name, _is_cloneable,
    clone_message, UNSUPPORTED_MEDIA_TYPES,
)
from tg_up.management import clone
from tg_up.utils import async_to_sync


def _make_message(media=None, text='', id=1, entities=None, file_size=100, has_photo=False, has_document=False):
    msg = MagicMock(spec=Message)
    msg.id = id
    msg.media = media
    msg.raw_text = text
    msg.message = text
    msg.entities = entities or None
    msg.file = MagicMock()
    msg.file.size = file_size
    msg.photo = MagicMock() if has_photo else None
    msg.video = None
    msg.audio = None
    msg.voice = None
    msg.video_note = None
    msg.sticker = None
    msg.gif = None
    msg.document = MagicMock() if has_document else None
    return msg


def _make_doc_media(mime_type='application/zip', filename='test.zip'):
    doc = MagicMock(spec=MessageMediaDocument)
    doc.document = MagicMock()
    doc.document.mime_type = mime_type
    doc.document.attributes = [DocumentAttributeFilename(filename)]
    return doc


class TestMediaTypeName(unittest.TestCase):
    def test_text(self):
        msg = _make_message(media=None)
        self.assertEqual(_media_type_name(msg), 'text')

    def test_photo(self):
        msg = _make_message(media=MagicMock(spec=MessageMediaPhoto))
        self.assertEqual(_media_type_name(msg), 'photo')

    def test_document(self):
        doc = _make_doc_media()
        msg = _make_message(media=doc, has_document=True)
        self.assertEqual(_media_type_name(msg), 'document')

    def test_document_known_type(self):
        doc = _make_doc_media(mime_type='audio/mpeg', filename='song.mp3')
        msg = _make_message(media=doc, has_document=True)
        name = _media_type_name(msg)
        self.assertIn(name, ('audio', 'document'))

    def test_geo(self):
        msg = _make_message(media=MagicMock(spec=MessageMediaGeo))
        self.assertEqual(_media_type_name(msg), 'location')

    def test_geo_live(self):
        msg = _make_message(media=MagicMock(spec=MessageMediaGeoLive))
        self.assertEqual(_media_type_name(msg), 'live_location')

    def test_contact(self):
        msg = _make_message(media=MagicMock(spec=MessageMediaContact))
        self.assertEqual(_media_type_name(msg), 'contact')

    def test_venue(self):
        msg = _make_message(media=MagicMock(spec=MessageMediaVenue))
        self.assertEqual(_media_type_name(msg), 'venue')

    def test_poll(self):
        msg = _make_message(media=MagicMock(spec=MessageMediaPoll))
        self.assertEqual(_media_type_name(msg), 'poll')


class TestIsCloneable(unittest.TestCase):
    def test_text_is_cloneable(self):
        self.assertTrue(_is_cloneable(_make_message(media=None)))

    def test_photo_is_cloneable(self):
        self.assertTrue(_is_cloneable(_make_message(media=MagicMock(spec=MessageMediaPhoto))))

    def test_poll_is_not_cloneable(self):
        self.assertFalse(_is_cloneable(_make_message(media=MagicMock(spec=MessageMediaPoll))))

    def test_document_is_cloneable(self):
        doc = _make_doc_media(mime_type='application/pdf', filename='doc.pdf')
        self.assertTrue(_is_cloneable(_make_message(media=doc)))


class TestCloneMessage(unittest.TestCase):
    def _make_client(self):
        client = MagicMock()
        client.send_file = AsyncMock()
        client.send_message = AsyncMock()
        client.forward_messages = AsyncMock()
        client.download_media = AsyncMock()
        return client

    def _clone(self, client, msg, dest, **kw):
        return async_to_sync(clone_message(client, msg, dest, **kw))

    def test_dry_run_text(self):
        client = self._make_client()
        msg = _make_message(media=None, text='hello', id=42)
        result = self._clone(client, msg, 'dest', dry_run=True)
        self.assertEqual(result['status'], 'would_clone')
        self.assertEqual(result['id'], 42)
        self.assertEqual(result['method'], 'direct_copy')
        client.send_file.assert_not_called()
        client.send_message.assert_not_called()

    def test_dry_run_forward(self):
        client = self._make_client()
        msg = _make_message(media=None, text='hello', id=42)
        result = self._clone(client, msg, 'dest', dry_run=True, forward=True)
        self.assertEqual(result['status'], 'would_clone')
        self.assertEqual(result['method'], 'forward')

    def test_clone_text_direct(self):
        client = self._make_client()
        msg = _make_message(media=None, text='hello', id=1)
        result = self._clone(client, msg, 'dest')
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['method'], 'direct_copy')
        client.send_message.assert_awaited_once_with(
            'dest', 'hello', formatting_entities=None, parse_mode=None,
        )

    def test_clone_media_direct(self):
        client = self._make_client()
        media = MagicMock(spec=MessageMediaPhoto)
        msg = _make_message(media=media, text='caption', id=2)
        result = self._clone(client, msg, 'dest')
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['method'], 'direct_copy')
        client.send_file.assert_awaited_once_with(
            'dest', media, caption='caption', formatting_entities=None, parse_mode=None,
        )

    def test_clone_forward(self):
        client = self._make_client()
        msg = _make_message(media=None, text='hello', id=3)
        result = self._clone(client, msg, 'dest', forward=True)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['method'], 'forward')
        client.forward_messages.assert_awaited_once_with('dest', msg)

    def test_fallback_on_direct_failure(self):
        client = self._make_client()
        client.send_file.side_effect = [Exception('direct copy failed'), 'ok']
        client.download_media.return_value = '/tmp/downloaded_file'
        media = MagicMock(spec=MessageMediaDocument)
        media.document = MagicMock()
        media.document.mime_type = 'video/mp4'
        media.document.attributes = [DocumentAttributeFilename('video.mp4')]
        msg = _make_message(media=media, text='caption', id=4, file_size=500,
                            has_document=True)

        with patch('tg_up.clone_operation.tempfile.NamedTemporaryFile') as mock_tmp, \
             patch('tg_up.clone_operation.os.unlink'):
            mock_tmp.return_value.name = '/tmp/clone_tmp'
            result = self._clone(client, msg, 'dest')

        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['method'], 'fallback_download_upload')
        client.download_media.assert_awaited_once()
        self.assertEqual(client.send_file.await_count, 2)
        # verify attributes and mime_type were passed
        call_kwargs = client.send_file.call_args[1]
        self.assertEqual(call_kwargs.get('mime_type'), 'video/mp4')
        self.assertIsNotNone(call_kwargs.get('attributes'))

    def test_no_fallback_returns_failed(self):
        client = self._make_client()
        client.send_file.side_effect = Exception('direct copy failed')
        media = MagicMock(spec=MessageMediaPhoto)
        msg = _make_message(media=media, text='caption', id=5)
        result = self._clone(client, msg, 'dest', no_fallback=True)
        self.assertEqual(result['status'], 'failed')
        self.assertIn('no-fallback', result['reason'])

    def test_skip_unsupported_media(self):
        client = self._make_client()
        msg = _make_message(media=MagicMock(spec=MessageMediaPoll), text='poll', id=6)
        result = self._clone(client, msg, 'dest')
        self.assertEqual(result['status'], 'skipped')
        self.assertIn('unsupported', result['reason'])
        client.send_file.assert_not_called()


class TestCloneCli(unittest.TestCase):
    def setUp(self):
        asyncio.set_event_loop(asyncio.new_event_loop())

    def tearDown(self):
        asyncio.set_event_loop(None)

    @patch('tg_up.management.default_config')
    @patch('tg_up.management.TelegramManagerClient')
    def test_clone_requires_to(self, mock_client_class, _):
        runner = CliRunner()
        result = runner.invoke(clone, [])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('--to', result.output)

    @patch('tg_up.management.default_config')
    @patch('tg_up.management.TelegramManagerClient')
    @patch('tg_up.management.clone_message')
    def test_clone_dry_run_text(self, mock_clone, mock_client_class, _):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.get_entity.return_value = 'dest_entity'
        mock_client.find_files.return_value = [
            _make_message(media=None, text='hello', id=1),
        ]

        mock_clone.return_value = {
            'id': 1, 'type': 'text', 'status': 'would_clone', 'method': 'direct_copy',
        }

        runner = CliRunner()
        result = runner.invoke(clone, ['--to', '@dest', '--dry-run'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('WOULD clone', result.output)

    @patch('tg_up.management.default_config')
    @patch('tg_up.management.TelegramManagerClient')
    @patch('tg_up.management.clone_message')
    def test_clone_url(self, mock_clone, mock_client_class, _):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_entity.side_effect = lambda x: f'entity_{x}'
        mock_client.get_messages.return_value = [
            _make_message(media=None, text='a', id=1),
        ]

        mock_clone.return_value = {'id': 1, 'type': 'text', 'status': 'ok', 'method': 'direct_copy'}

        with patch('tg_up.management.parse_telegram_url') as mock_parse:
            mock_parse.return_value = ('@source', [1])
            runner = CliRunner()
            result = runner.invoke(clone, [
                '--to', '@dest',
                '--url', 'https://t.me/source/1',
            ])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Cloning 1 message(s)', result.output)

    @patch('tg_up.management.default_config')
    @patch('tg_up.management.TelegramManagerClient')
    @patch('tg_up.management.clone_message')
    def test_clone_ids(self, mock_clone, mock_client_class, _):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_entity.return_value = 'dest_entity'
        mock_client.get_messages.return_value = [
            _make_message(media=None, text='a', id=1),
            _make_message(media=None, text='b', id=2),
        ]

        mock_clone.return_value = {'id': 1, 'type': 'text', 'status': 'ok', 'method': 'direct_copy'}

        runner = CliRunner()
        result = runner.invoke(clone, [
            '--to', '@dest',
            '--from', '@source',
            '--ids', '1-2',
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Cloning 2 message(s)', result.output)

    @patch('tg_up.management.default_config')
    @patch('tg_up.management.TelegramManagerClient')
    def test_clone_url_and_from_mutually_exclusive(self, mock_client_class, _):
        runner = CliRunner()
        result = runner.invoke(clone, [
            '--to', '@dest',
            '--from', '@source',
            '--url', 'https://t.me/source/1',
        ])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('mutually exclusive', result.output)
