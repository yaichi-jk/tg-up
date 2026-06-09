import os
import tempfile

from telethon.tl.types import (
    MessageMediaPhoto, MessageMediaDocument,
    MessageMediaPoll, MessageMediaGame, MessageMediaInvoice,
    MessageMediaWebPage, MessageMediaUnsupported, MessageMediaDice,
    MessageMediaGeo, MessageMediaGeoLive, MessageMediaContact,
    MessageMediaVenue,
    DocumentAttributeFilename,
)

from tg_up.client.progress_bar import get_progress_bar
from tg_up.url_parser import get_media_type


UNSUPPORTED_MEDIA_TYPES = (
    MessageMediaPoll,
    MessageMediaGame,
    MessageMediaInvoice,
    MessageMediaWebPage,
    MessageMediaUnsupported,
    MessageMediaDice,
)


def _media_type_name(message):
    media = message.media
    if not media:
        return 'text'
    if isinstance(media, MessageMediaPhoto):
        return 'photo'
    if isinstance(media, MessageMediaDocument):
        type_name = get_media_type(message)
        return type_name if type_name != 'unknown' else 'document'
    if isinstance(media, MessageMediaGeo):
        return 'location'
    if isinstance(media, MessageMediaGeoLive):
        return 'live_location'
    if isinstance(media, MessageMediaContact):
        return 'contact'
    if isinstance(media, MessageMediaVenue):
        return 'venue'
    if isinstance(media, MessageMediaPoll):
        return 'poll'
    if isinstance(media, MessageMediaGame):
        return 'game'
    if isinstance(media, MessageMediaInvoice):
        return 'invoice'
    if isinstance(media, MessageMediaWebPage):
        return 'webpage'
    if isinstance(media, MessageMediaUnsupported):
        return 'unsupported'
    if isinstance(media, MessageMediaDice):
        return 'dice'
    return type(media).__name__.replace('MessageMedia', '').lower()


def _is_cloneable(message):
    if not message.media:
        return True
    return not isinstance(message.media, UNSUPPORTED_MEDIA_TYPES)


async def _try_direct_copy(client, message, dest):
    caption = message.raw_text or ''
    entities = message.entities or None

    if message.media:
        return await client.send_file(
            dest, message.media,
            caption=caption,
            formatting_entities=entities,
            parse_mode=None,
        )
    else:
        return await client.send_message(
            dest, caption,
            formatting_entities=entities,
            parse_mode=None,
        )


def _has_thumb(doc):
    if not doc:
        return False
    if hasattr(doc, 'thumbs') and doc.thumbs:
        return True
    if hasattr(doc, 'video_thumbs') and doc.video_thumbs:
        return True
    return False


async def _fallback_download_upload(client, message, dest, keep_files=False):
    caption = message.raw_text or ''
    entities = message.entities or None

    orig_filename = None
    orig_attributes = None
    orig_mime_type = None

    doc = None
    if isinstance(message.media, MessageMediaDocument):
        doc = message.media.document
    elif hasattr(message.media, 'document') and message.media.document:
        doc = message.media.document

    if doc:
        orig_mime_type = doc.mime_type
        orig_attributes = list(doc.attributes) if doc.attributes else None
        for attr in doc.attributes or []:
            if isinstance(attr, DocumentAttributeFilename):
                orig_filename = attr.file_name
                break

    has_thumb = _has_thumb(doc)

    suffix = f'_{orig_filename}' if orig_filename else '_clone'

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name

    thumb_path = None
    if has_thumb:
        with tempfile.NamedTemporaryFile(delete=False, suffix='_thumb') as tmp_thumb:
            thumb_path = tmp_thumb.name

    try:
        progress, bar = get_progress_bar('Downloading', str(message.id), message.file.size)
        downloaded = await client.download_media(message, file=tmp_path,
                                                  progress_callback=progress)
        bar.label = f'Downloaded  msg {message.id}'
        bar.update(1, 1)
        bar.render_finish()

        file_path = downloaded if isinstance(downloaded, str) else tmp_path

        if has_thumb and thumb_path:
            try:
                dl_thumb = await client.download_media(message, file=thumb_path, thumb=-1)
                thumb_path = dl_thumb if isinstance(dl_thumb, str) and os.path.isfile(dl_thumb) else thumb_path
            except Exception:
                thumb_path = None

        send_kwargs = dict(
            caption=caption,
            formatting_entities=entities,
            parse_mode=None,
        )
        if orig_attributes:
            send_kwargs['attributes'] = orig_attributes
        if orig_mime_type:
            send_kwargs['mime_type'] = orig_mime_type
        if thumb_path:
            send_kwargs['thumb'] = thumb_path

        result = await client.send_file(dest, file_path, **send_kwargs)
        return result
    finally:
        if not keep_files:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            if thumb_path:
                try:
                    os.unlink(thumb_path)
                except OSError:
                    pass


async def _forward_message(client, message, dest):
    return await client.forward_messages(dest, message)


async def clone_message(client, message, dest, *,
                        forward=False,
                        no_fallback=False,
                        keep_files=False,
                        dry_run=False):
    media_name = _media_type_name(message)

    if not _is_cloneable(message):
        return {
            'id': message.id,
            'type': media_name,
            'status': 'skipped',
            'reason': f'unsupported media type: {type(message.media).__name__}',
        }

    if dry_run:
        method = 'forward' if forward else 'direct_copy'
        return {
            'id': message.id,
            'type': media_name,
            'status': 'would_clone',
            'method': method,
        }

    try:
        if forward:
            await _forward_message(client, message, dest)
            return {'id': message.id, 'type': media_name, 'status': 'ok', 'method': 'forward'}
        else:
            try:
                await _try_direct_copy(client, message, dest)
                return {'id': message.id, 'type': media_name, 'status': 'ok', 'method': 'direct_copy'}
            except Exception:
                if no_fallback:
                    return {
                        'id': message.id,
                        'type': media_name,
                        'status': 'failed',
                        'reason': 'direct copy failed and --no-fallback is set',
                    }
                try:
                    await _fallback_download_upload(client, message, dest, keep_files=keep_files)
                    return {'id': message.id, 'type': media_name, 'status': 'ok',
                            'method': 'fallback_download_upload'}
                except Exception as e:
                    return {
                        'id': message.id,
                        'type': media_name,
                        'status': 'failed',
                        'reason': str(e),
                    }
    except Exception as e:
        return {
            'id': message.id,
            'type': media_name,
            'status': 'error',
            'reason': str(e),
        }
