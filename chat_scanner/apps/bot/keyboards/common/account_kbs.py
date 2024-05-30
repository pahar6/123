from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, ReplyKeyboardBuilder

from chat_scanner.apps.bot.callback_data.account import AccountAction, AccountCallback, Action
from chat_scanner.db.models import Account
from .common_kbs import custom_back_inline_button, reply_back_button

IKB = InlineKeyboardButton
if TYPE_CHECKING:
    from .....locales.stubs.ru.stub import TranslatorRunner


def menu(accounts: list[Account], l10n: TranslatorRunner) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for account in accounts:
        builder.button(
            text=account.button(),
            callback_data=AccountCallback(id=account.id, action=Action.GET)
        )

    builder.button(text=l10n.account.button.bind_account(), callback_data=AccountCallback(action=AccountAction.BIND))
    builder.add(custom_back_inline_button(cd="admin"))
    builder.adjust(1)
    return builder.as_markup()


def get_account(account: Account, l10n: TranslatorRunner) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text=l10n.account.button.unbind_account(),
        callback_data=AccountCallback(id=account.id, action=AccountAction.UNBIND)
    )
    builder.add(custom_back_inline_button())
    builder.adjust(1)
    return builder.as_markup()


def bind_account(l10n: TranslatorRunner) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # builder.button(text=l10n.account.bind.button.register_me(), callback_data="register_me")
    builder.button(text=l10n.account.bind.button.i_registered(), callback_data="i_registered")
    builder.add(custom_back_inline_button())
    builder.adjust(1)
    return builder.as_markup()


def register_me(l10n: TranslatorRunner) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=l10n.account.bind.button.send_contact(), request_contact=True)
    builder.add(reply_back_button(l10n))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def unbind_account(account: Account, l10: TranslatorRunner) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=l10.button.yes(),
        callback_data=AccountCallback(action=Action.DELETE, id=account.id)
    )
    builder.button(
        text=l10.button.no(),
        callback_data=AccountCallback(action=Action.GET, id=account.id)
    )
    builder.adjust(1)
    return builder.as_markup()
