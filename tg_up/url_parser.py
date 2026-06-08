import re


def parse_telegram_url(url: str):
    url = url.strip()
    for prefix in ['https://', 'http://', 'tg://']:
        if url.startswith(prefix):
            url = url[len(prefix):]
    url = url.rstrip('/')

    m = re.match(r'^t\.me/c/(\d+)/(\d+)/(\d+)(?:-(\d+))?$', url)
    if m:
        chat_id = int(m.group(1))
        start = int(m.group(3))
        end = int(m.group(4)) if m.group(4) else start
        if end < start:
            start, end = end, start
        return chat_id, list(range(start, end + 1))

    m = re.match(r'^t\.me/c/(\d+)/(\d+)(?:-(\d+))?$', url)
    if m:
        chat_id = int(m.group(1))
        start = int(m.group(2))
        end = int(m.group(3)) if m.group(3) else start
        if end < start:
            start, end = end, start
        return chat_id, list(range(start, end + 1))

    m = re.match(r'^t\.me/([a-zA-Z0-9_]+)/(\d+)(?:-(\d+))?$', url)
    if m:
        username = m.group(1)
        if username == 'c':
            raise ValueError("Invalid Telegram URL format (use t.me/c/... for private chats)")
        start = int(m.group(2))
        end = int(m.group(3)) if m.group(3) else start
        if end < start:
            start, end = end, start
        return username, list(range(start, end + 1))

    m = re.match(r'^t\.me/(\+|joinchat/)([\w]+)$', url)
    if m:
        raise ValueError("Telegram invite links do not contain message IDs")

    if url.startswith('t.me/c/'):
        raise ValueError("Invalid chat ID in private Telegram URL (must be numeric)")

    raise ValueError(f"Could not parse Telegram URL: {url.strip()}")


def parse_ids_string(ids_str: str):
    if not ids_str:
        return []
    parts = ids_str.replace(' ', '').split(',')
    result = []
    for part in parts:
        m = re.match(r'^(\d+)(?:-(\d+))?$', part)
        if not m:
            raise ValueError(f"Invalid ID format: {part}")
        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else start
        if end < start:
            start, end = end, start
        result.extend(range(start, end + 1))
    return result


def has_media(message) -> bool:
    return bool(message and message.file)


def get_media_type(message) -> str:
    if message.photo:
        return "photo"
    if message.video:
        return "video"
    if message.audio:
        return "audio"
    if message.voice:
        return "voice"
    if message.video_note:
        return "video_note"
    if message.sticker:
        return "sticker"
    if message.gif:
        return "gif"
    if message.document:
        return "document"
    return "unknown"
