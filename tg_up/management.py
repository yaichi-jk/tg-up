# -*- coding: utf-8 -*-

"""Console script for tg-up."""
import json
import os

import click
from telethon.tl.types import User

from tg_up.cli import show_checkboxlist, show_radiolist
from tg_up.client import TelegramManagerClient, get_message_file_attribute
from tg_up.config import default_config, CONFIG_FILE
from tg_up.download_files import KeepDownloadSplitFiles, JoinDownloadSplitFiles
from tg_up.exceptions import catch
from tg_up.upload_files import NoDirectoriesFiles, RecursiveFiles, NoLargeFiles, SplitFiles, is_valid_file
from tg_up.url_parser import parse_telegram_url, parse_ids_string, has_media, get_media_type
from tg_up.utils import async_to_sync, amap, sync_to_async_iterator


try:
    from natsort import natsorted
except ImportError:
    natsorted = None


DIRECTORY_MODES = {
    'fail': NoDirectoriesFiles,
    'recursive': RecursiveFiles,
}
LARGE_FILE_MODES = {
    'fail': NoLargeFiles,
    'split': SplitFiles,
}
DOWNLOAD_SPLIT_FILE_MODES = {
    'keep': KeepDownloadSplitFiles,
    'join': JoinDownloadSplitFiles,
}


def get_file_display_name(message):
    display_name_parts = []
    is_document = message.document
    if is_document and message.document.mime_type:
        display_name_parts.append(message.document.mime_type.split('/')[0])
    if is_document and get_message_file_attribute(message):
        display_name_parts.append(get_message_file_attribute(message).file_name)
    if message.text:
        display_name_parts.append(f'[{message.text}]' if display_name_parts else message.text)
    from_user = message.sender and isinstance(message.sender, User)
    if from_user:
        display_name_parts.append('by')
    if from_user and message.sender.first_name:
        display_name_parts.append(message.sender.first_name)
    if from_user and message.sender.last_name:
        display_name_parts.append(message.sender.last_name)
    if from_user and message.sender.username:
        display_name_parts.append(f'@{message.sender.username}')
    display_name_parts.append(f'{message.date}')
    return ' '.join(display_name_parts)


async def interactive_select_files(client, entity: str):
    iterator = client.iter_files(entity)
    iterator = amap(lambda x: (x, get_file_display_name(x)), iterator,)
    return await show_checkboxlist(iterator)


async def interactive_select_local_files():
    iterator = filter(lambda x: os.path.isfile(x) and os.path.lexists(x), os.listdir('.'))
    iterator = sync_to_async_iterator(map(lambda x: (x, x), iterator))
    return await show_checkboxlist(iterator, 'Not files were found in the current directory '
                                             '(subdirectories are not supported). Exiting...')


async def interactive_select_dialog(client):
    iterator = client.iter_dialogs()
    iterator = amap(lambda x: (x, x.name), iterator,)
    value = await show_radiolist(iterator, 'Not dialogs were found in your Telegram session. '
                                           'Have you started any conversations?')
    return value.id if value else None


class MutuallyExclusiveOption(click.Option):
    def __init__(self, *args, **kwargs):
        self.mutually_exclusive = set(kwargs.pop('mutually_exclusive', []))
        help = kwargs.get('help', '')
        if self.mutually_exclusive:
            kwargs['help'] = help + (
                ' NOTE: This argument is mutually exclusive with'
                ' arguments: [{}].'.format(self.mutually_exclusive_text)
            )
        super(MutuallyExclusiveOption, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise click.UsageError(
                "Illegal usage: `{}` is mutually exclusive with "
                "arguments `{}`.".format(
                    self.name,
                    self.mutually_exclusive_text
                )
            )

        return super(MutuallyExclusiveOption, self).handle_parse_result(
            ctx,
            opts,
            args
        )

    @property
    def mutually_exclusive_text(self):
        return ', '.join([x.replace('_', '-') for x in self.mutually_exclusive])


@click.command()
@click.argument('files', nargs=-1)
@click.option('--to', default=None, help='Phone number, username, invite link or "me" (saved messages). '
                                         'By default "me".')
@click.option('--config', default=None, help='Configuration file to use. By default "{}".'.format(CONFIG_FILE))
@click.option('-d', '--delete-on-success', is_flag=True, help='Delete local file after successful upload.')
@click.option('--print-file-id', is_flag=True, help='Print the id of the uploaded file after the upload.')
@click.option('--force-file', is_flag=True, help='Force send as a file. The filename will be preserved '
                                                 'but the preview will not be available.')
@click.option('-f', '--forward', multiple=True, help='Forward the file to a chat (alias or id) or user (username, '
                                                     'mobile or id). This option can be used multiple times.')
@click.option('--directories', default='fail', type=click.Choice(list(DIRECTORY_MODES.keys())),
              help='Defines how to process directories. By default directories are not accepted and will raise an '
                   'error.')
@click.option('--large-files', default='fail', type=click.Choice(list(LARGE_FILE_MODES.keys())),
              help='Defines how to process large files unsupported for Telegram. By default large files are not '
                   'accepted and will raise an error.')
@click.option('--caption', type=str, help='Change file description. By default the file name.')
@click.option('--no-thumbnail', is_flag=True, cls=MutuallyExclusiveOption, mutually_exclusive=["thumbnail_file"],
              help='Disable thumbnail generation. For some known file formats, Telegram may still generate a '
                   'thumbnail or show a preview.')
@click.option('--thumbnail-file', default=None, cls=MutuallyExclusiveOption, mutually_exclusive=["no_thumbnail"],
              help='Path to the preview file to use for the uploaded file.')
@click.option('-p', '--proxy', default=None,
              help='Use an http proxy, socks4, socks5 or mtproxy. For example socks5://user:pass@1.2.3.4:8080 '
                   'for socks5 and mtproxy://secret@1.2.3.4:443 for mtproxy.')
@click.option('-a', '--album', is_flag=True,
              help='Send video or photos as an album.')
@click.option('--reply-to', default=None, type=int,
              help='Reply to a specific message ID.')
@click.option('-i', '--interactive', is_flag=True,
              help='Use interactive mode.')
@click.option('--sort', is_flag=True,
              help='Sort files by name before upload it. Install the natsort Python package for natural sorting.')
def upload(files, to, config, delete_on_success, print_file_id, force_file, forward, directories, large_files, caption,
           no_thumbnail, thumbnail_file, proxy, album, interactive, sort, reply_to):
    """Upload one or more files to Telegram using your personal account.
    The maximum file size is 2 GiB for free users and 4 GiB for premium accounts.
    By default, they will be saved in your saved messages.
    """
    client = TelegramManagerClient(config or default_config(), proxy=proxy)
    client.start()
    if interactive and not files:
        click.echo('Select the local files to upload:')
        click.echo('[SPACE] Select file [ENTER] Next step')
        files = async_to_sync(interactive_select_local_files())
    if interactive and not files:
        # No files selected. Exiting.
        return
    if interactive and to is None:
        click.echo('Select the recipient dialog of the files:')
        click.echo('[SPACE] Select dialog [ENTER] Next step')
        to = async_to_sync(interactive_select_dialog(client))
    elif to is None:
        to = 'me'
    files = filter(lambda file: is_valid_file(file, lambda message: click.echo(message, err=True)), files)
    files = DIRECTORY_MODES[directories](client, files)
    if directories == 'fail':
        # Validate now
        files = list(files)
    if no_thumbnail:
        thumbnail = False
    elif thumbnail_file:
        thumbnail = thumbnail_file
    else:
        thumbnail = None
    files_cls = LARGE_FILE_MODES[large_files]
    files = files_cls(client, files, caption=caption, thumbnail=thumbnail, force_file=force_file)
    if large_files == 'fail':
        # Validate now
        files = list(files)
    if isinstance(to, str) and to.lstrip("-+").isdigit():
        to = int(to)
    if sort and natsorted:
        files = natsorted(files, key=lambda x: x.name)
    elif sort:
        files = sorted(files, key=lambda x: x.name)
    if album:
        client.send_files_as_album(to, files, delete_on_success, print_file_id, forward, reply_to=reply_to)
    else:
        client.send_files(to, files, delete_on_success, print_file_id, forward, reply_to=reply_to)


def _print_raw_json(message, entity=None):
    file = message.file
    data = {
        "type": get_media_type(message),
        "id": message.id,
        "chat_id": message.chat_id,
        "date": str(message.date),
        "caption": message.text,
        "sender_id": message.sender_id,
        "reply_to_msg_id": message.reply_to_msg_id,
        "grouped_id": message.grouped_id,
        "out": message.out,
        "post": message.post,
        "via_bot_id": message.via_bot_id,
    }
    if file:
        data["file"] = {
            "id": file.id,
            "name": file.name,
            "ext": file.ext,
            "mime_type": file.mime_type,
            "size": file.size,
            "duration": file.duration,
            "width": file.width,
            "height": file.height,
            "title": file.title,
            "performer": file.performer,
            "emoji": file.emoji,
        }
    if message.forward:
        fwd = message.forward
        data["forward"] = {
            "sender_id": fwd.sender_id,
            "chat_id": fwd.chat_id,
            "date": str(fwd.date) if hasattr(fwd, 'date') else None,
        }
    click.echo(json.dumps(data))


@click.command()
@click.option('--from', '-f', 'from_', default='',
              help='Phone number, username, chat id or "me" (saved messages). By default "me".')
@click.option('--config', default=None, help='Configuration file to use. By default "{}".'.format(CONFIG_FILE))
@click.option('-d', '--delete-on-success', is_flag=True,
              help='Delete telegram message after successful download. Useful for creating a download queue.')
@click.option('-p', '--proxy', default=None,
              help='Use an http proxy, socks4, socks5 or mtproxy. For example socks5://user:pass@1.2.3.4:8080 '
                   'for socks5 and mtproxy://secret@1.2.3.4:443 for mtproxy.')
@click.option('-m', '--split-files', default='keep', type=click.Choice(list(DOWNLOAD_SPLIT_FILE_MODES.keys())),
              help='Defines how to download large files split in Telegram. By default the files are not merged.')
@click.option('-i', '--interactive', is_flag=True,
              help='Use interactive mode.')
@click.option('-u', '--url', multiple=True,
              help='Download specific message(s) by URL. Supports ranges: '
                   'https://t.me/c/123/456/789-792. Mutually exclusive with --from.')
@click.option('--ids', '-id', 'ids_', default='',
              help='Download message IDs from the chat specified with --from. '
                   'Supports ranges: "1-5,10,15-20".')
@click.option('--raw', is_flag=True,
              help='Print JSON metadata for each message (no download).')
@click.option('--raw-dl', is_flag=True,
              help='Print JSON metadata AND download files.')
def download(from_, config, delete_on_success, proxy, split_files, interactive, url, ids_, raw, raw_dl):
    """Download files from Telegram using your personal account.

    By default, downloads all latest file messages from "saved messages".
    Use --url to download specific messages by their Telegram URL,
    or --from + --ids to download specific message IDs from a chat.
    """
    client = TelegramManagerClient(config or default_config(), proxy=proxy)
    client.start()

    if url and from_:
        raise click.UsageError("--url is mutually exclusive with --from")
    if raw and raw_dl:
        raise click.UsageError("--raw and --raw-dl are mutually exclusive")

    do_raw = raw or raw_dl
    do_download = not raw

    if url:
        messages = []
        entity = None
        for url_str in url:
            chat_info, msg_ids = parse_telegram_url(url_str)
            if isinstance(chat_info, int):
                entity = client.get_entity(int(f"-100{chat_info}"))
            else:
                entity = client.get_entity(chat_info)
            batch = client.get_messages(entity, ids=msg_ids)
            for msg in batch:
                if msg and has_media(msg):
                    messages.append(msg)
                else:
                    click.echo(f"Skipping msg {msg.id}: not a media file", err=True)
        messages.sort(key=lambda m: m.id)
        if do_raw:
            for msg in messages:
                _print_raw_json(msg, entity)
        if do_download:
            download_files = DOWNLOAD_SPLIT_FILE_MODES[split_files](messages)
            client.download_files(entity, download_files, delete_on_success)

    elif ids_:
        if not from_:
            raise click.UsageError("--ids requires --from")
        ids_list = parse_ids_string(ids_)
        if isinstance(from_, str) and from_.lstrip("-+").isdigit():
            from_ = int(from_)
        entity = client.get_entity(from_)
        batch = client.get_messages(entity, ids=ids_list)
        messages = [m for m in batch if m and has_media(m)]
        if not messages:
            click.echo("No downloadable media found for the given IDs.", err=True)
            return
        messages.sort(key=lambda m: m.id)
        if do_raw:
            for msg in messages:
                _print_raw_json(msg, entity)
        if do_download:
            download_files = DOWNLOAD_SPLIT_FILE_MODES[split_files](messages)
            client.download_files(entity, download_files, delete_on_success)

    else:
        if not interactive and not from_:
            from_ = 'me'
        elif isinstance(from_, str) and from_.lstrip("-+").isdigit():
            from_ = int(from_)
        elif interactive and not from_:
            click.echo('Select the dialog of the files to download:')
            click.echo('[SPACE] Select dialog [ENTER] Next step')
            from_ = async_to_sync(interactive_select_dialog(client))
        if interactive:
            click.echo('Select all files to download:')
            click.echo('[SPACE] Select files [ENTER] Download selected files')
            messages = async_to_sync(interactive_select_files(client, from_))
        else:
            messages = client.find_files(from_)
        if do_raw:
            entity = client.get_entity(from_)
            for msg in messages:
                _print_raw_json(msg, entity)
        if do_download:
            messages_cls = DOWNLOAD_SPLIT_FILE_MODES[split_files]
            download_files = messages_cls(reversed(list(messages)))
            client.download_files(from_, download_files, delete_on_success)


upload_cli = catch(upload)
download_cli = catch(download)


if __name__ == '__main__':
    import sys
    import re
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    commands = {'upload': upload_cli, 'download': download_cli}
    if len(sys.argv) < 2:
        sys.stderr.write('A command is required. Available commands: {}\n'.format(
            ', '.join(commands)
        ))
        sys.exit(1)
    if sys.argv[1] not in commands:
        sys.stderr.write('{} is an invalid command. Valid commands: {}\n'.format(
            sys.argv[1], ', '.join(commands)
        ))
        sys.exit(1)
    fn = commands[sys.argv[1]]
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    sys.exit(fn())
