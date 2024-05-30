from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING

from loguru import logger
from aiogram.filters.callback_data import CallbackData
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from aiogram.utils import markdown as md
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from fluentogram import TranslatorRunner

from ...commands.bot_commands import BaseCommands
from ...callback_data.project import ProjectCallback
from .....db.models import Locale

IKB = InlineKeyboardButton
KB = KeyboardButton
md = md

if TYPE_CHECKING:
    from .....locales.stubs.ru.stub import TranslatorRunner


def bonus(l10n: TranslatorRunner):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=l10n.bonus.button.continue_(),
        callback_data=BaseCommands.START.command
    )
    # builder.add(custom_back_inline_button(l10n.button.back()))
    builder.adjust(1)
    return builder.as_markup()


@cache
def start(l10n: TranslatorRunner, is_admin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=l10n.button.instruction(), callback_data=BaseCommands.INSTRUCTION.command)
    builder.button(text=l10n.button.projects(), callback_data=BaseCommands.PROJECTS.command)
    builder.button(text=l10n.button.payment(), callback_data=BaseCommands.PAYMENT.command)
    builder.button(text=l10n.button.support(), callback_data=BaseCommands.SUPPORT.command)
    builder.button(text=l10n.button.invite(), callback_data=BaseCommands.INVITE.command)
    builder.button(text=l10n.button.language(), callback_data=BaseCommands.LANGUAGE.command)
    builder.adjust(1)
    return builder.as_markup()


def support_sent(l10n: TranslatorRunner):
    builder = InlineKeyboardBuilder()
    builder.button(text=l10n.support.sent.button.again(), callback_data=BaseCommands.SUPPORT.command)
    builder.adjust(1)
    # builder.row(custom_back_inline_button(text=l10n.support.sent.button.menu()))
    builder.row(custom_back_inline_button(text=l10n.button.back()))

    return builder.as_markup()


def invite(l10n: TranslatorRunner):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=l10n.button.instruction(),
        callback_data="invite-instruction"
    )
    builder.add(custom_back_inline_button(l10n.button.back()))
    builder.adjust(1)
    return builder.as_markup()


def invite_instruction(l10n: TranslatorRunner) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=l10n.invite.button.withdraw(),
        callback_data=BaseCommands.WITHDRAW.command
    )
    builder.add(custom_back_inline_button(
        l10n.button.back(),
        BaseCommands.INVITE.command
    ))
    builder.adjust(1)
    return builder.as_markup()


def withdraw(
        l10n: TranslatorRunner,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(custom_back_inline_button(
        l10n.button.back(),
        BaseCommands.INVITE.command
    ))
    builder.adjust(1)
    return builder.as_markup()


def yookassa_payment(l10n: TranslatorRunner) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=l10n.payment.button.pay(),
        pay=True
    )

    # builder.add(custom_back_inline_button(
    #     cd=PaymentCallback(action=PaymentAction.PAYMENT_SYSTEM)
    # ))
    builder.adjust(1)
    return builder.as_markup()


def menu_button(l10n: TranslatorRunner):
    return IKB(text=l10n.button.menu(), callback_data="start")


def back_button(l10n: TranslatorRunner):
    return IKB(text=l10n.button.back(), callback_data="start")


def menu_button_kb(l10n: TranslatorRunner):
    builder = InlineKeyboardBuilder()
    builder.row(menu_button(l10n))
    builder.adjust(1)
    return builder.as_markup()


def custom_back(
        l10n: TranslatorRunner,
        callback_data: str | CallbackData | ProjectCallback = "start"
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(custom_back_inline_button(text=l10n.button.back(), cd=callback_data))
    builder.adjust(1)
    return builder.as_markup()


def custom_back_kb(text: str = "« Назад", cb: str | CallbackData = "start") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=text, callback_data=cb)
    return builder.as_markup()


def what_currency(l10n: TranslatorRunner) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=l10n.withdraw.what_currency.button.btc(), callback_data="btc")
    builder.button(text=l10n.withdraw.what_currency.button.ton(), callback_data="ton")
    builder.button(text=l10n.withdraw.what_currency.button.usdt(), callback_data="usdt")
    builder.add(custom_back_inline_button(l10n.button.cancel()))
    builder.adjust(3, 1)
    return builder.as_markup()


def inline_button(text: str, cd: CallbackData | None = None, url: str | None = None) -> InlineKeyboardButton:
    if url:
        if cd:
            return IKB(text=text, url=url, callback_data=cd.pack())
        return IKB(text=text, url=url)
    if cd:
        return IKB(text=text, callback_data=cd.pack())


def custom_back_inline_button(text: str = "« Назад", cd: str | CallbackData = "start") -> InlineKeyboardButton:
    if not isinstance(cd, str):
        cd = cd.pack()
    return IKB(text=text, callback_data=cd)


def custom_reply_kb(text: str = "« Назад") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=text)
    return builder.as_markup(resize_keyboard=True)


def reply_back_button(l10n: TranslatorRunner) -> KeyboardButton:
    return KeyboardButton(text=l10n.button.back())


def reply_back() -> ReplyKeyboardMarkup:
    return custom_reply_kb()
