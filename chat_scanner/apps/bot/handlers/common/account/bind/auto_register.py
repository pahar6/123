from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from aiogram import Router, types, Bot
from aiogram.filters import Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from auto_selenium import BrowserArgs, BrowserSettings
# from auto_selenium import BrowserSettings, BrowserArgs
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from chat_scanner.apps.account.dispatcher import Dispatcher
from chat_scanner.apps.account.register_api import TelegramApiRegistrator
# from chat_scanner.apps.account.register_api import TelegramApiRegistrator
from chat_scanner.apps.bot.keyboards.common import account_kbs, common_kbs
from chat_scanner.config import LOG_DIR
from chat_scanner.db.models import User
from .bind import _bind_account

if TYPE_CHECKING:
    from chat_scanner.locales.stubs.ru.stub import TranslatorRunner

router = Router()


class AutoRegisterAccount(StatesGroup):
    phone = State()
    data = State()
    code = State()
    password = State()


@router.callback_query(StateFilter("register"), Text("register_me"))
async def register_me(
        call: types.CallbackQuery,
        l10n: TranslatorRunner,
        state: FSMContext
):
    await state.set_state(AutoRegisterAccount.phone)
    await call.message.answer(l10n.account.bind.enter_phone(), reply_markup=account_kbs.register_me(l10n))


async def _get_register_code_callback(
        queue: asyncio.Queue,
        phone_number: str,
        message: types.Message,
        l10n: TranslatorRunner,
        state: FSMContext
):
    await state.set_state(AutoRegisterAccount.code)
    # await message.answer(l10n("enter-account-code", {"phone": account.phone}))
    await message.answer(l10n.account.bind.enter_register_code())
    logger.info(f"Ожидание кода {message.from_user.id}")
    return queue


@router.message(AutoRegisterAccount.code)
async def register_code(
        message: types.Message,
        l10n: TranslatorRunner,
        state: FSMContext
):
    code = message.text
    data = await state.get_data()
    queue: asyncio.Queue = data.get("queue")
    await queue.put(code)
    await message.delete()
    await message.answer(l10n.account.bind.got_code())


@router.message(AutoRegisterAccount.phone)
async def register_phone(
        message: types.Message,
        bot: Bot,
        session: AsyncSession,
        user: User,
        l10n: TranslatorRunner,
        account_dispatchers: dict[str, Dispatcher],
        state: FSMContext
):
    if message.contact:
        phone_number = message.contact.phone_number
    else:
        phone_number = message.text
    await message.answer(l10n.account.bind.wait())
    queue = asyncio.Queue()
    await state.update_data(queue=queue)
    registrator = TelegramApiRegistrator(
        args=BrowserArgs(headless=True),
        settings=BrowserSettings(log_path=LOG_DIR / "browser.log")
    )
    try:
        api_id, api_hash = await registrator.async_register(
            phone_number,
            _get_register_code_callback(queue, phone_number, message, l10n, state),

        )
        # отправляем полученные данные пользователю
        data = f"{api_id}:{api_hash}:{phone_number}"
        await message.answer(
            l10n.account.bind.got_data(api_id=api_id, api_hash=api_hash, phone=phone_number, data=data))
        await message.answer(l10n.account.bind.wait_register())
    except asyncio.exceptions.TimeoutError:
        await message.answer(l10n.account.bind.timeout(), reply_markup=common_kbs.custom_back_kb())
        return
    except Exception as e:
        await message.answer(l10n.account.bind.error(error=str(e)), reply_markup=common_kbs.custom_back_kb())
        logger.exception(e)
        return
    await _bind_account(**locals())
