from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fluentogram import TranslatorRunner, TranslatorHub
from loguru import logger
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..apps import jobs
from ..apps.account.dispatcher import Dispatcher
from ..config import TIME_ZONE, Settings
from ..db.models.project.settings import DUPLICATES

def setup_scheduler(
        session_maker: async_sessionmaker,
        account_dispatchers: dict[int, Dispatcher],
        bot: Bot,
        settings: Settings,
        l10n: TranslatorRunner,
        translator_hub: TranslatorHub
) -> AsyncIOScheduler:
    # Init scheduler
    scheduler = AsyncIOScheduler(timezone=TIME_ZONE)
    session = session_maker()

    #Проверка платежей каждые 1 минуту:
    scheduler.add_job(
        jobs.payment_verification,
        "interval",
        (session, account_dispatchers, bot, settings, l10n, translator_hub),
        minutes=1,
    )
    # Уменьшение подписки ежедневно в 12:00:
    scheduler.add_job(
        jobs.decr_subscription,
        "cron",
        (session_maker, account_dispatchers, bot, l10n, translator_hub),
        hour=12,
        minute=0,
    )

    # Уведомление пользователей с истекшей подпиской ежедневно в 13:00
    scheduler.add_job(
        jobs.notify_users_with_expired_subscription,
        "cron",
        (session_maker, account_dispatchers, bot, l10n, translator_hub),
        hour=13,
        minute=0,
    )

    #Очистка дубликатов каждые 2 часа:
    scheduler.add_job(
        DUPLICATES.clear,
        "interval",
        # seconds=1
        minutes=60 * 2,
    )

    # for tests every 1 minute
    # scheduler.add_job(
    #     jobs.decr_subscription,
    #     "interval",
    #     (session_maker, account_dispatchers, bot, l10n),
    #     seconds=3,
    # )

    # Start scheduler
    scheduler.start()

    logger.success("[Scheduler] Scheduler setup completed")

    return scheduler
