from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router, types, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ...callback_data.base_callback import SubscriptionCallback, AdminAction
from ...keyboards.admin import admin_kbs
from ...keyboards.common import common_kbs
from .....config import Settings
from .....db.models import User, Rates
from chat_scanner.apps.account.dispatcher import Dispatcher
from chat_scanner.db.requests.base import change_user_rate_permissions
from .menu import get_user_info



if TYPE_CHECKING:
    from .....locales.stubs.ru.stub import TranslatorRunner

router = Router()


@router.callback_query(SubscriptionCallback.filter(F.action == AdminAction.MENU))
async def subscription_menu(
        call: types.CallbackQuery,
        l10n: TranslatorRunner,
        settings: Settings,
):
    await call.message.delete()
    await call.message.answer(
        "<b>💳 Настройки тарифов</b>\n\nНажмите для изменения цены👇",
        reply_markup=admin_kbs.subscription_menu(settings, l10n)
    )


@router.callback_query(SubscriptionCallback.filter(F.action == AdminAction.CHANGE_SUBSCRIPTION_DURATION))
async def change_subscription_duration(
        call: types.CallbackQuery,
        callback_data: SubscriptionCallback,
        state: FSMContext
):
    await call.message.answer(
        f"Ведите новую цену подписки в рублях для подписки <b>{callback_data.rate}</b> на <b>{callback_data.months} мес.</b>",
        reply_markup=common_kbs.custom_back_kb(cb="admin")
    )
    await state.update_data(months=callback_data.months, rate=callback_data.rate)
    await state.set_state("change_subscription_duration")


@router.message(StateFilter("change_subscription_duration"))
async def change_subscription_duration_handler(
        message: types.Message,
        l10n: TranslatorRunner,
        settings: Settings,
        state: FSMContext
):
    try:
        new_price = float(message.text)
    except ValueError:
        await message.answer("Неверный формат ввода. Попробуйте еще раз")
        return
    data = await state.get_data()
    months = data.get("months")
    rate = data.get("rate")
    if rate == Rates.STANDART:
        if months == 1:
            settings.bot.SUBSCRIPTION_1_MONTH = new_price
        elif months == 6:
            settings.bot.SUBSCRIPTION_6_MONTH = new_price
        elif months == 12:
            settings.bot.SUBSCRIPTION_12_MONTH = new_price
    elif rate == Rates.PRO:
        if months == 1:
            settings.bot.SUBSCRIPTION_PRO_1_MONTH = new_price
        elif months == 6:
            settings.bot.SUBSCRIPTION_PRO_6_MONTH = new_price
        elif months == 12:
            settings.bot.SUBSCRIPTION_PRO_12_MONTH = new_price

    settings.dump()
    await message.answer(
        f"Цена подписки <b>{rate}</b> на <b>{months} мес.</b> изменена на <b>{new_price} руб.</b>",
        reply_markup=admin_kbs.subscription_menu(settings, l10n)
    )
    await state.clear()

@router.callback_query(SubscriptionCallback.filter(F.action == AdminAction.CHANGE_SUBS_RATE))
async def admin_change_subscription_rate_menu(
        call: types.CallbackQuery,
        callback_data: SubscriptionCallback,
        state: FSMContext,
        session: AsyncSession,
):
    logger.info("Запуск admin_change_subscription_rate_menu")
    user = await User.get(session, id=callback_data.id)
    if user:
        await state.clear()
        await call.message.delete()
        await call.message.answer(
            f"Текущая подписка: {user.rate}\nВыберите новый тарифный план",
            reply_markup=admin_kbs.change_subscription_rate(callback_data.id)
        )
    else:
        await call.message.answer("Пользователь не найден")
        await state.clear()

@router.callback_query(SubscriptionCallback.filter(F.action == AdminAction.CHANGE_SUBS_RATE_OPT))
async def admin_change_subscription_rate(
        call: types.CallbackQuery,
        callback_data: SubscriptionCallback,
        state: FSMContext,
        session: AsyncSession,
        bot: Bot,
        account_dispatchers: dict[int, Dispatcher]
):
    logger.info("Запуск admin_change_subscription_rate")
    user = await User.get(session, id=callback_data.id)
    if user:
        logger.info(f"Найден пользователь с ID {user.id}, текущая подписка: {user.rate}")
        previous_rate = user.rate
        user.rate = callback_data.rate
        await session.commit()
        logger.info(f"Изменение подписки пользователя {user.id} с {previous_rate} на {callback_data.rate}")
        await change_user_rate_permissions(
            session=session,
            user_id=user.id,
            bot=bot,
            account_dispatchers=account_dispatchers,
            new_rate=callback_data.rate,
            previous_rate=previous_rate
        )
        updated_user = await User.get(session, id=user.id)
        logger.info(f"Текущая подписка пользователя {user.id} после изменения: {updated_user.rate}")

        info = await get_user_info(updated_user, session)
        await call.message.answer(
            f"Тарифный план пользователя {user.id} изменен на {callback_data.rate}\n\n{info}",
            reply_markup=admin_kbs.get_user(user.id)
        )
    else:
        logger.error(f"Пользователь с ID {callback_data.id} не найден")
        await call.message.answer("Пользователь не найден")
    await state.clear()