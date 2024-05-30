from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router, types, Bot
from aiogram.filters import Command, Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from chat_scanner.apps.bot.commands.bot_commands import BaseCommands
from chat_scanner.apps.bot.handlers.common.base import get_method
from chat_scanner.apps.bot.keyboards.common import common_kbs
from chat_scanner.config import Settings
from chat_scanner.db.models import User
from chat_scanner.utils.message import mailings

if TYPE_CHECKING:
    from chat_scanner.locales.stubs.ru.stub import TranslatorRunner

router = Router()


class WithdrawStates(StatesGroup):
    withdraw = State()
    withdraw_amount = State()
    withdraw_amount_currency = State()
    withdraw_amount_currency_wallet = State()


@router.message(Command(BaseCommands.WITHDRAW))
@router.callback_query(Text(BaseCommands.WITHDRAW.command))
async def withdraw(
        message: types.Message | types.CallbackQuery,
        user: User,
        l10n: TranslatorRunner,
        settings: Settings,
        state: FSMContext
):
    await state.clear()

    if user.balance < settings.bot.WITHDRAW_BALANCE:
        method = get_method(message)
        await method(
            l10n.invite.withdraw.not_enough(min=settings.bot.WITHDRAW_BALANCE),
            reply_markup=common_kbs.custom_back_kb()
        )
        return

    method = get_method(message)
    await method(
        l10n.withdraw.how_much(),
        reply_markup=common_kbs.custom_back_kb(text=l10n.button.cancel())
    )
    await state.set_state(WithdrawStates.withdraw_amount)


@router.message(StateFilter(WithdrawStates.withdraw_amount))
async def withdraw_amount(
        message: types.Message,
        l10n: TranslatorRunner,
        state: FSMContext
):
    if not message.text.isdigit():
        await message.answer(l10n.invite.withdraw.not_digit())
        return

    await state.update_data(amount=int(message.text))
    await message.answer(
        l10n.withdraw.what_currency(),
        reply_markup=common_kbs.what_currency(l10n)
    )
    await state.set_state(WithdrawStates.withdraw_amount_currency)


@router.callback_query(WithdrawStates.withdraw_amount_currency)
async def withdraw_amount_currency(
        query: types.CallbackQuery,
        l10n: TranslatorRunner,
        state: FSMContext
):
    await state.update_data(currency=query.data)
    await query.message.edit_text(
        l10n.withdraw.what_wallet(),
        reply_markup=common_kbs.custom_back_kb()
    )
    await state.set_state(WithdrawStates.withdraw_amount_currency_wallet)


@router.message(StateFilter(WithdrawStates.withdraw_amount_currency_wallet))
async def withdraw_message(
        message: types.Message,
        bot: Bot,
        l10n: TranslatorRunner,
        user: User,
        settings: Settings,
        state: FSMContext
):
    data = await state.update_data(wallet=message.text)
    amount = data.get("amount")
    currency = data.get("currency")
    wallet = data.get("wallet")
    if settings.bot.SUPPORT_CHAT_ID:
        await mailings(
            bot,
            f"Запрос на вывод средств:\n{message.text}"
            f"\n\nОтправитель: {message.from_user.full_name} (@{message.from_user.username})\n"
            f"Текущий баланс пользователя: {user.balance}\n"
            f"Информация для вывода:\n"
            f"Сумма: {amount}\n"
            f"Валюта: {currency}\n"
            f"Кошелек: {wallet}\n",
            settings.bot.SUPPORT_CHAT_ID
        )
    method = get_method(message)
    await method(
        l10n.invite.withdraw.sent(),
        reply_markup=common_kbs.custom_back_kb()
    )
    await state.clear()
