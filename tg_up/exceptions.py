# -*- coding: utf-8 -*-

"""Exceptions for tg-up."""
import sys

import click
from telethon.errors import (
    ChatIdInvalidError,
    ChannelPrivateError,
    MessageIdInvalidError,
    UsernameNotOccupiedError,
    UsernameInvalidError,
    PeerIdInvalidError,
    ChannelInvalidError,
    ChatInvalidError,
)

from tg_up.config import prompt_config


class ThumbError(Exception):
    pass


class ThumbVideoError(ThumbError):
    pass


class TelegramUploadError(Exception):
    body = ''
    error_code = 1

    def __init__(self, extra_body=''):
        self.extra_body = extra_body

    def __str__(self):
        msg = self.__class__.__name__
        if self.body:
            msg += ': {}'.format(self.body)
        if self.extra_body:
            msg += ('. {}' if self.body else ': {}').format(self.extra_body)
        return msg


class MissingFileError(TelegramUploadError):
    pass


class InvalidApiFileError(TelegramUploadError):
    def __init__(self, config_file, extra_body=''):
        self.config_file = config_file
        super().__init__(extra_body)


class TelegramInvalidFile(TelegramUploadError):
    error_code = 3


class TelegramUploadNoSpaceError(TelegramUploadError):
    error_code = 28


class TelegramUploadDataLoss(TelegramUploadError):
    error_code = 29


class TelegramProxyError(TelegramUploadError):
    error_code = 30


class TelegramEnvironmentError(TelegramUploadError):
    error_code = 31


TELEGRAM_FETCH_ERROR_MESSAGES = {
    ChatIdInvalidError: "Invalid chat ID. Make sure the chat/channel exists.",
    ChannelPrivateError: "Cannot access the channel/group. Make sure you are a member and it exists.",
    MessageIdInvalidError: "Invalid message ID(s). The message may have been deleted or never existed.",
    UsernameNotOccupiedError: "Invalid username. No user/channel with that username exists.",
    UsernameInvalidError: "The provided username is invalid.",
    PeerIdInvalidError: "Invalid peer/chat ID. Make sure the ID is correct.",
    ChannelInvalidError: "Invalid channel. Make sure the channel exists.",
    ChatInvalidError: "Invalid chat. Make sure the chat exists.",
}


def format_telethon_error(exception):
    for exc_cls, msg in TELEGRAM_FETCH_ERROR_MESSAGES.items():
        if isinstance(exception, exc_cls):
            return msg
    return None


def catch(fn):
    def wrap(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except InvalidApiFileError as e:
            click.echo('The api_id/api_hash combination is invalid. Re-enter both values.')
            prompt_config(e.config_file)
            return catch(fn)(*args, **kwargs)
        except TelegramUploadError as e:
            sys.stderr.write('[Error] tg-up Exception:\n{}\n'.format(e))
            exit(e.error_code)
        except Exception as e:
            tele_msg = format_telethon_error(e)
            if tele_msg:
                sys.stderr.write('[Error] {}\n'.format(tele_msg))
            else:
                msg = str(e)
                if 'No user has' in msg or 'Cannot find any entity' in msg:
                    sys.stderr.write('[Error] Could not resolve entity: {}\n'.format(msg))
                else:
                    sys.stderr.write('[Error] {}\n'.format(msg))
            exit(1)
    return wrap
