from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from aiogram import Bot
from loguru import logger
from sqlalchemy.ext.asyncio import async_sessionmaker
from pyrogram.raw import functions
from loguru import logger

from chat_scanner.apps.account.dispatcher import Dispatcher
from chat_scanner.apps.bot.handlers.common.project.crud.update import dispatchers_update
from chat_scanner.apps.bot.keyboards.common import payment_kbs
from chat_scanner.db.models import User, Project
from chat_scanner.db.requests.base import remove_full_user_data, change_user_rate_permissions
from fluentogram import TranslatorHub

if TYPE_CHECKING:
    from chat_scanner.locales.stubs.ru.stub import TranslatorRunner

async def decr_subscription(
        session_maker: async_sessionmaker,
        account_dispatchers: dict[int, Dispatcher],
        bot: Bot,
        l10n: TranslatorRunner,
        translator_hub: TranslatorHub
):
    logger.info("[Scheduler] Running decr_subscription job")
    offset = 0
    limit = 100  # Размер порции пользователей для обработки за один раз
    while True:
        async with session_maker() as session:
            try:
                users = await User.filter(session, limit=limit, offset=offset)
                if not users:
                    #logger.info("No more users to process")
                    break
                #logger.info(f"Total users to process in this batch: {len(users)}")
                for user in users:
                    if user.subscription_duration > 0:
                        #logger.info(f"User {user.id}: Current subscription duration: {user.subscription_duration}")
                        user.subscription_duration -= 1
                        await session.commit()
                        #logger.info(f"User {user.id}: Updated subscription duration: {user.subscription_duration}")
                        if user.subscription_duration == 0:
                            await user.update_projects_accounts(session, account_dispatchers)
                            l10n = translator_hub.get_translator_by_locale(user.language_code)
                            try:
                                await bot.send_message(
                                    user.id,
                                    l10n.payment.subscription.expired(),
                                    reply_markup=payment_kbs.expired(l10n)
                                )
                            except Exception as e:
                                logger.error(f"[Scheduler] User {user.id} notification error: {e}")
            except Exception as e:
                logger.error(f"Error fetching users or processing batch: {e}")
            offset += limit


async def notify_users_with_expired_subscription(
        session_maker: async_sessionmaker,
        account_dispatchers: dict[int, Dispatcher],
        bot: Bot,
        l10n: TranslatorRunner,
        translator_hub: TranslatorHub
):
    logger.info("[Scheduler] notify_users_with_expired_subscription")
    today = datetime.datetime.now()
    async with session_maker() as session:
        users = await User.filter(session)
        for user in users:
            try:
                if user.subscription_duration == 0:
                    # ПОЛУЧАЕМ ПРОЕКТЫ ПОЛЬЗОВАТЕЛЯ
                    projects = await Project.filter(session, Project.user_id == user.id)
                    if len(projects) == 0:
                        continue
                    # ПРОВЕРЯЕМ ЕСТЬ ЛИ ИНВОЙСЫ У ПОЛЬЗОВАТЕЛЯ
                    expired_paid_date = await user.expired_date(session=session)
                    delta_expired = today - expired_paid_date
                    l10n = translator_hub.get_translator_by_locale(user.language_code)

                    if delta_expired.days == 3:  # 3 дня после истечения подписки
                        await bot.send_message(user.id, l10n.payment.subscription.expired_three_days(), reply_markup=payment_kbs.expired(l10n))

                    elif delta_expired.days == 5:  # 5 дней после истечения срока подписки
                        await bot.send_message(user.id, l10n.payment.subscription.expired_five_days(), reply_markup=payment_kbs.expired(l10n))

                    elif delta_expired.days >= 6:  # Шестой день и последующие после истечения подписки
                        await remove_full_user_data(
                            session,
                            user.id,
                            bot,
                            account_dispatchers,
                            remove_user=False
                        )
            except Exception as error:
                logger.warning(f"[SCHEDULER-SUBS-DURATION-ERROR] {error}")

