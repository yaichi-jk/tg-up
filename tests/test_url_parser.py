import unittest

from tg_up.url_parser import parse_telegram_url, parse_ids_string, has_media, get_media_type


class TestParseTelegramURL(unittest.TestCase):
    def test_private_url_single(self):
        chat, ids = parse_telegram_url("https://t.me/c/2357852823/273/26071")
        self.assertEqual(chat, 2357852823)
        self.assertEqual(ids, [26071])

    def test_private_url_range(self):
        chat, ids = parse_telegram_url("https://t.me/c/2357852823/273/26071-26073")
        self.assertEqual(chat, 2357852823)
        self.assertEqual(ids, [26071, 26072, 26073])

    def test_private_url_reversed_range(self):
        chat, ids = parse_telegram_url("https://t.me/c/123/456/10-5")
        self.assertEqual(ids, [5, 6, 7, 8, 9, 10])

    def test_private_url_with_topic(self):
        chat, ids = parse_telegram_url("https://t.me/c/2357852823/273/26071")
        self.assertEqual(chat, 2357852823)
        self.assertEqual(ids, [26071])

    def test_private_url_range_with_topic(self):
        chat, ids = parse_telegram_url("https://t.me/c/2357852823/273/26071-26073")
        self.assertEqual(chat, 2357852823)
        self.assertEqual(ids, [26071, 26072, 26073])

    def test_private_url_no_topic(self):
        chat, ids = parse_telegram_url("https://t.me/c/123456789/555")
        self.assertEqual(chat, 123456789)
        self.assertEqual(ids, [555])

    def test_public_url_single(self):
        username, ids = parse_telegram_url("https://t.me/animeflix/123")
        self.assertEqual(username, "animeflix")
        self.assertEqual(ids, [123])

    def test_public_url_range(self):
        username, ids = parse_telegram_url("https://t.me/animeflix/100-105")
        self.assertEqual(username, "animeflix")
        self.assertEqual(ids, [100, 101, 102, 103, 104, 105])

    def test_url_without_protocol(self):
        chat, ids = parse_telegram_url("t.me/c/123/456")
        self.assertEqual(chat, 123)
        self.assertEqual(ids, [456])

    def test_url_with_trailing_slash(self):
        chat, ids = parse_telegram_url("https://t.me/c/123/456/")
        self.assertEqual(chat, 123)
        self.assertEqual(ids, [456])

    def test_invalid_url_no_message(self):
        with self.assertRaises(ValueError):
            parse_telegram_url("https://t.me/+abc123")

    def test_invalid_url_joinchat(self):
        with self.assertRaises(ValueError) as ctx:
            parse_telegram_url("https://t.me/joinchat/abc123")
        self.assertIn("invite link", str(ctx.exception))

    def test_invalid_url_plus(self):
        with self.assertRaises(ValueError) as ctx:
            parse_telegram_url("https://t.me/+abc123")
        self.assertIn("invite link", str(ctx.exception))

    def test_invalid_url_c_without_number(self):
        with self.assertRaises(ValueError):
            parse_telegram_url("https://t.me/c/something/123")

    def test_invalid_string(self):
        with self.assertRaises(ValueError):
            parse_telegram_url("not a url")


class TestParseIdsString(unittest.TestCase):
    def test_single_id(self):
        self.assertEqual(parse_ids_string("26071"), [26071])

    def test_comma_separated(self):
        self.assertEqual(parse_ids_string("1,2,3"), [1, 2, 3])

    def test_range(self):
        self.assertEqual(parse_ids_string("1-5"), [1, 2, 3, 4, 5])

    def test_mixed(self):
        self.assertEqual(parse_ids_string("1-3,10,20-22"), [1, 2, 3, 10, 20, 21, 22])

    def test_reversed_range(self):
        self.assertEqual(parse_ids_string("5-1"), [1, 2, 3, 4, 5])

    def test_empty(self):
        self.assertEqual(parse_ids_string(""), [])

    def test_with_spaces(self):
        self.assertEqual(parse_ids_string("1, 2, 3"), [1, 2, 3])

    def test_invalid_format(self):
        with self.assertRaises(ValueError):
            parse_ids_string("abc")


class TestHasMedia(unittest.TestCase):
    def test_no_media(self):
        msg = type("Msg", (), {"file": None})()
        self.assertFalse(has_media(msg))

    def test_with_media(self):
        msg = type("Msg", (), {"file": object()})()
        self.assertTrue(has_media(msg))

    def test_none_message(self):
        self.assertFalse(has_media(None))


class FakeMessage:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestGetMediaType(unittest.TestCase):
    def test_photo(self):
        msg = FakeMessage(photo=object(), video=None, audio=None, voice=None,
                          video_note=None, sticker=None, gif=None, document=None)
        self.assertEqual(get_media_type(msg), "photo")

    def test_video(self):
        msg = FakeMessage(photo=None, video=object(), audio=None, voice=None,
                          video_note=None, sticker=None, gif=None, document=None)
        self.assertEqual(get_media_type(msg), "video")

    def test_audio(self):
        msg = FakeMessage(photo=None, video=None, audio=object(), voice=None,
                          video_note=None, sticker=None, gif=None, document=None)
        self.assertEqual(get_media_type(msg), "audio")

    def test_voice(self):
        msg = FakeMessage(photo=None, video=None, audio=None, voice=object(),
                          video_note=None, sticker=None, gif=None, document=None)
        self.assertEqual(get_media_type(msg), "voice")

    def test_document(self):
        msg = FakeMessage(photo=None, video=None, audio=None, voice=None,
                          video_note=None, sticker=None, gif=None, document=object())
        self.assertEqual(get_media_type(msg), "document")

    def test_no_media(self):
        msg = FakeMessage(photo=None, video=None, audio=None, voice=None,
                          video_note=None, sticker=None, gif=None, document=None)
        self.assertEqual(get_media_type(msg), "unknown")
