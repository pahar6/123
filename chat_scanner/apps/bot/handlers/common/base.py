from __future__ import annotations

import asyncio
import os.path
import types
from typing import TYPE_CHECKING

from fluentogram import TranslatorHub
from aiogram import Router, types, Bot, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
# from aiogram.methods.send_chat_action import SendChatAction
from aiogram.filters import Command, Text, StateFilter, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.utils import deep_linking
from sqlalchemy.ext.asyncio import AsyncSession

from chat_scanner.apps.bot.commands.bot_commands import BaseCommands
from chat_scanner.apps.bot.callback_data.language import LanguageCallback, LanguageAction
from chat_scanner.apps.bot.keyboards.common import common_kbs, language_kbs
from chat_scanner.config import Settings
from chat_scanner.config.config import IncludeSupportMessage
from chat_scanner.db.models import User, Locale, Invoice, Status
from chat_scanner.db.requests.base import change_user_rate_permissions
from chat_scanner.utils.message import mailings
from loguru import logger
from chat_scanner.apps.account.dispatcher import Dispatcher #я добавил


if TYPE_CHECKING:
    from chat_scanner.locales.stubs.ru.stub import TranslatorRunner

router = Router()

BLOCK = False


def get_method(message: types.Message | types.CallbackQuery):
    if isinstance(message, types.CallbackQuery):
        return message.message.edit_text

    return message.answer


@router.message(Text(startswith='TestFile'))
async def check_file(message: types.Message):
    logger.warning(str(message))
    await message.answer('111111')


@router.message(CommandStart(deep_link=True))
async def deep_start(
        message: types.Message,
        bot: Bot,
        command: CommandObject,
        session: AsyncSession,
        user: User,
        is_new: bool,
        l10n: TranslatorRunner,
        settings: Settings,
        state: FSMContext
):
    """ Deep link start handler """
    await state.clear()
    referrer_id = int(command.args)
    if await user.set_referrer(session, referrer_id):
        referrer = await User.get(session, id=referrer_id)
    else:
        pass
    await start(message, l10n, user, is_new, settings, session, state, bot)

@router.message(Command(BaseCommands.START))
@router.message(Text(startswith="«"))
@router.callback_query(Text("start"))
async def start(
        message: types.Message | types.CallbackQuery = None,
        l10n: TranslatorRunner = None,
        user: User = None,
        is_new: bool = False,
        settings: Settings = None,
        session: AsyncSession = None,
        state: FSMContext = None,
        bot: Bot = None,
        account_dispatchers: dict[int, Dispatcher] = None,
):
    if state:
        await state.clear()

    if isinstance(message, types.CallbackQuery):
        message = message.message
        method = message.edit_text
    else:
        method = message.answer if message else bot.send_message

    if is_new:  # Если пользователь новый - то дожидаться события LanguageAction.SET_LANGUAGE
        return

    try:
        _status: str = l10n.status.on() if user.subscription_duration else l10n.status.off()
        if user.rate:
            _rate = user.rate
            # await change_user_rate_permissions(
            #     session=session,
            #     user_id=user.id,
            #     bot=bot,
            #     account_dispatchers=account_dispatchers
        else:
            _rate = l10n.status.rate_off()
    except Exception as error:
        logger.exception(error)
        _status = 'Error'

    try:
        await bot.send_animation(
            message.chat.id if message else user.id,
            animation='CgACAgIAAxkBAAIzx2YrkVCoS8iSsYtgVPJHljScISODAAINSQACELlZSaeGnhTGjBIqNAQ',
            caption=l10n.start(status=str(_status), rate=str(_rate)),
            reply_markup=common_kbs.start(l10n)
        )
        if message:
            try:
                await message.delete()
            except Exception:
                pass
    except Exception as error:
        await method(
            text=l10n.start(status=str(_status), rate=str(_rate)),
            disable_web_page_preview=True,
            reply_markup=common_kbs.start(l10n)
        )


@router.message(Command(BaseCommands.INVITE))
@router.callback_query(Text(BaseCommands.INVITE.command))
async def invite(
        message: types.Message | types.CallbackQuery,
        l10n: TranslatorRunner,
        session: AsyncSession,
        user: User,
        bot: Bot,
        state: FSMContext
):
    await state.clear()
    if isinstance(message, types.CallbackQuery):
        message = message.message

    referrals = await user.get_referrals(session)
    last_paid_referrals = await user.get_last_paid_referrals(session)
    list_str = ""
    for num, referral in enumerate(last_paid_referrals, 1):
        list_str += f"{num}. {referral.button_text()}\n"

    await bot.send_message(
        chat_id=message.chat.id,
        text=l10n.invite(
            balance=user.balance,
            count=len(referrals),
            list=list_str
        ),
        reply_markup=common_kbs.invite(l10n)
    )
    try:
        await message.delete()
    except Exception:
        pass


@router.callback_query(Text("invite-instruction"))
async def invite_instruction(
        call: types.CallbackQuery,
        session: AsyncSession,
        bot: Bot,
        user: User,
        l10n: TranslatorRunner,
        settings: Settings,
        state: FSMContext
):
    await state.clear()
    invite_link = await deep_linking.create_start_link(bot, user.id)
    invited_count = 0
    await call.message.edit_text(
        l10n.invite.instruction(
            link=invite_link,
            percent=settings.bot.REFERRAL_PERCENT,
            min=settings.bot.WITHDRAW_BALANCE,
        ),
        reply_markup=common_kbs.invite_instruction(l10n)
    )


@router.message(Command(BaseCommands.SUPPORT))
@router.callback_query(Text(BaseCommands.SUPPORT.command))
async def support(
        message: types.Message | types.CallbackQuery,
        l10n: TranslatorRunner,
        bot: Bot,
        state: FSMContext
):
    await state.clear()
    await bot.send_message(
        chat_id=message.from_user.id,
        text=l10n.support(),
        disable_web_page_preview=True,
        reply_markup=common_kbs.menu_button_kb(l10n)
    )
    try:
        await message.delete()
    except Exception:
        await message.message.delete()
    await state.set_state("support")


@router.message(StateFilter("support"))
async def support_message(
        message: types.Message,
        bot: Bot,
        l10n: TranslatorRunner,
        settings: Settings,
        state: FSMContext
):
    if settings.bot.SUPPORT_CHAT_ID:
        if message.from_user.username:
            text = (f"<b>📞 Тех поддержка</b>\n"
                    f'<b>Отправитель:</b> <b>@{message.from_user.username} {message.from_user.full_name} {message.from_user.id}</b>\n\n')
        else:
            text = (f"<b>📞 Тех поддержка</b>\n"
                    f'<b>Отправитель:</b> <b><a href="tg://user?id={message.from_user.id}">{message.from_user.full_name} {message.from_user.id}</a></b>\n\n')

        if message.photo:
            file_id = message.photo[-1].file_id
            if message.caption:
                text += message.caption
            messages = await mailings(
                bot=bot,
                text=text,
                users=settings.bot.SUPPORT_CHAT_ID,
                photo=file_id
            )
        else:
            text += message.text
            messages = await mailings(
                bot=bot,
                text=text,
                users=settings.bot.SUPPORT_CHAT_ID
            )
        if messages:
            sm = messages[0]
            from_user_message = IncludeSupportMessage(message_id=message.message_id, chat_id=message.chat.id)
            to_user_message = IncludeSupportMessage(message_id=sm.message_id, chat_id=sm.chat.id)
            settings.bot.SUPPORT_MESSAGES[to_user_message] = from_user_message

    method = get_method(message)
    await method(
        l10n.support.sent(),
        reply_markup=common_kbs.support_sent(l10n)
    )
    await state.clear()


@router.callback_query(Text(BaseCommands.INSTRUCTION.command))
async def instruction(
        call: types.CallbackQuery,
        l10n: TranslatorRunner,
        settings: Settings,
        bot: Bot,
        state: FSMContext):

    await state.clear()

    try:
        await bot.send_message(
            chat_id=call.message.chat.id,
            text=l10n.instruction(),
            reply_markup=common_kbs.menu_button_kb(l10n)
        )
        await call.message.delete()
    except Exception as error:
        logger.exception(error)


@router.message(Command(BaseCommands.LANGUAGE))
@router.callback_query(Text(BaseCommands.LANGUAGE.command))
async def choose_language(
        message: types.Message | types.CallbackQuery,
        l10n: TranslatorRunner,
        bot: Bot,
        state: FSMContext
):
    await state.clear()
    if isinstance(message, types.CallbackQuery):
        message = message.message

    try:
        # method = get_method(call)
        await bot.send_message(
            chat_id=message.chat.id,
            text=f"<b>Choose language | Выберите язык</b>",
            reply_markup=language_kbs.language(l10n)
        )
        await message.delete()
    except Exception as error:
        logger.exception(error)


@router.message(Command(BaseCommands.LANGUAGE))
@router.callback_query(Text(BaseCommands.LANGUAGE.command))
@router.callback_query(LanguageCallback.filter(F.action == LanguageAction.CHANGE))
async def change_language(
        call: types.Message | types.CallbackQuery,
        callback_data: LanguageCallback,
        l10n: TranslatorRunner,
        hub: TranslatorHub,
        user: User,
        session: AsyncSession,
        settings: Settings,
        bot: Bot,
        state: FSMContext
):
    try:
        await state.clear()

        method = get_method(call)

        language_code = callback_data.language_code
        languages_list = list(Locale.attributes().items())  # [(RUSSIAN, ru: Type locale), (ENGLISH, en: Type locale), ...]
        languages_codes = {}
        for key, value in languages_list:
            languages_codes[str(value)] = value

        user.language_code = languages_codes[language_code]
        l10n = hub.get_translator_by_locale(user.language_code)
        await session.commit()

        # await method(f'Set language: {language_code.upper()}')
        await start(call, l10n, user, False, settings, session, state, bot)

    except Exception as error:
        logger.exception(error)


@router.message(Command(BaseCommands.LANGUAGE))
@router.callback_query(Text(BaseCommands.LANGUAGE.command))
@router.callback_query(LanguageCallback.filter(F.action == LanguageAction.SET_LANGUAGE))
async def set_language(
        call: types.Message | types.CallbackQuery,
        callback_data: LanguageCallback,
        l10n: TranslatorRunner,
        hub: TranslatorHub,
        user: User,
        session: AsyncSession,
        settings: Settings,
        state: FSMContext
):
    try:
        await state.clear()

        method = get_method(call)

        language_code = callback_data.language_code
        languages_list = list(Locale.attributes().items())  # [(RUSSIAN, ru: Type locale), (ENGLISH, en: Type locale), ...]
        languages_codes = {}
        for key, value in languages_list:
            languages_codes[str(value)] = value

        user.language_code = languages_codes[language_code]
        l10n = hub.get_translator_by_locale(user.language_code)
        await session.commit()

        # await method(f'Set language: {language_code.upper()}')
        await method(
            text=l10n.bonus(bonus=settings.bot.BONUS),
            reply_markup=common_kbs.bonus(l10n)
        )

    except Exception as error:
        logger.exception(error)
