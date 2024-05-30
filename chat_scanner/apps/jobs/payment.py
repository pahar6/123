from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from aiogram import Bot
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from chat_scanner.apps.account.dispatcher import Dispatcher
from chat_scanner.apps.bot.handlers.common.base import start
from chat_scanner.apps.bot.keyboards.common import common_kbs
from chat_scanner.apps.merchant import MerchantEnum
from chat_scanner.config.config import Settings
from chat_scanner.db.models import Invoice, User
from fluentogram import TranslatorHub

from chat_scanner.db.requests.base import change_user_rate_permissions

if TYPE_CHECKING:
    from chat_scanner.locales.stubs.ru.stub import TranslatorRunner

async def success_paid(
        session: AsyncSession,
        account_dispatchers: dict[int, Dispatcher],
        invoice: Invoice,
        bot: Bot,
        settings: Settings,
        l10n: TranslatorRunner,
        translator_hub: TranslatorHub
):
    await invoice.successfully_paid()
    user: User = invoice.user
    previous_rate = user.rate
    user.rate = invoice.rate
    l10n = translator_hub.get_translator_by_locale(user.language_code)

    # Добавить 10 процентов от суммы к балансу реферера
    if invoice.user.referrer_id:
        referrer = await User.get(session, id=invoice.user.referrer_id)
        referrer.balance += invoice.rub_amount * settings.bot.REFERRAL_PERCENT / 100

    await session.commit()
    logger.success("The invoice {} has been successfully paid", invoice)

    try:
        await bot.send_message(
            user.id,
            l10n.payment.success(
                duration=invoice.subscription_duration,
            )
        )
    except Exception as e:
        logger.exception(e)

    # Отправить сообщение в чат поддержки
    if settings.bot.SUPPORT_CHAT_ID:
        try:
            await bot.send_message(
                settings.bot.SUPPORT_CHAT_ID,
                f"Тариф {user.rate} #{invoice.subscription_duration // 30}\n"
                f"👤 @{user.username}(id:{user.id})\n"
                f"📅 {invoice.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"💰 {invoice.amount} {invoice.currency}\n"
                f"💳 {invoice.merchant}\n"
            )
        except Exception as e:
            logger.exception(e)

    # Изменение прав пользователя в зависимости от нового тарифа
    await change_user_rate_permissions(
        session=session,
        user_id=user.id,
        bot=bot,
        account_dispatchers=account_dispatchers,
        previous_rate=previous_rate,
        new_rate=invoice.rate# Передаем предыдущий тарифный план
    )

    # Перенаправить на функцию start
    await start(
        message=None,
        l10n=l10n,
        user=user,
        is_new=False,
        settings=settings,
        session=session,
        state=None,
        bot=bot,
        account_dispatchers=account_dispatchers
    )

# Payment verification job
async def payment_verification(
        session: AsyncSession,
        account_dispatchers: dict[int, Dispatcher],
        bot: Bot,
        settings: Settings,
        l10n: TranslatorRunner,
        translator_hub: TranslatorHub
):
    """Проверка оплаты."""
    logger.debug("Проверка оплаты")
    invoices = await Invoice.get_pending_invoices(session)
    for invoice in invoices:
        logger.trace("Check invoice {}", invoice)
        try:
            merchant = settings.get_merchant(invoice.merchant)
            if (not merchant) or (merchant.merchant == MerchantEnum.YOOKASSA):
                logger.warning("Merchant {} not found", invoice.merchant)
                continue
            if await merchant.is_paid(invoice.invoice_id):
                await success_paid(
                    session,
                    account_dispatchers,
                    invoice,
                    bot,
                    settings,
                    l10n,
                    translator_hub
                )
        except Exception as e:
            logger.exception(e)