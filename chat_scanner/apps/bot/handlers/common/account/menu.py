from __future__ import annotations

import asyncio
from functools import cache
from typing import TYPE_CHECKING

from aiogram import F, Router, types
from aiogram.filters import Text, Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from chat_scanner.apps.account.dispatcher import Dispatcher
from chat_scanner.apps.bot.callback_data.account import AccountCallback, Action
from chat_scanner.apps.bot.commands.bot_commands import AdminCommands
from chat_scanner.apps.bot.keyboards.common import account_kbs
from chat_scanner.db.models import User, Account

if TYPE_CHECKING:
    from chat_scanner.locales.stubs.ru.stub import TranslatorRunner

router = Router()

INVITE_TASKS = {}


@cache
def get_lock(user_id: int):
    return asyncio.Lock()


@router.callback_query(AccountCallback.filter(F.action == Action.MENU))
@router.callback_query(Text(AdminCommands.ACCOUNTS.command))
# @router.message(Text(startswith="👥"))
@router.message(Command(AdminCommands.ACCOUNTS))
async def menu(
        message: types.Message | types.CallbackQuery,
        session: AsyncSession,
        user: User,
        l10n: TranslatorRunner,
        state: FSMContext
):
    await state.clear()
    if isinstance(message, types.CallbackQuery):
        message = message.message
    # await session.refresh(user, {"accounts"})
    accounts = await Account.all(session)
    await message.answer(
        l10n.account.menu(),
        reply_markup=account_kbs.menu(accounts, l10n)
    )


@router.callback_query(AccountCallback.filter(F.action == Action.GET))
async def get(
        call: types.CallbackQuery,
        session: AsyncSession,
        user: User,
        account_dispatchers: dict[int, Dispatcher],
        callback_data: AccountCallback,
        l10n: TranslatorRunner,
        state: FSMContext
):
    await state.clear()
    account = await Account.get(session, id=callback_data.id)
    if account is None:
        await call.answer(l10n.account.not_found())
        return
    await call.message.answer(
        account.pretty(l10n),
        reply_markup=account_kbs.get_account(account, l10n)
    )
