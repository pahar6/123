from __future__ import annotations

import datetime
from pprint import pformat
from typing import TYPE_CHECKING

from aiogram import F, Router, types, Bot
from aiogram.fsm.context import FSMContext
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from fluentogram import TranslatorHub

from chat_scanner.apps.account.dispatcher import Dispatcher
from chat_scanner.apps.bot.callback_data.payment import PaymentCallback
from chat_scanner.apps.jobs.payment import success_paid
from chat_scanner.apps.merchant import MerchantEnum
from chat_scanner.config import Settings
from chat_scanner.db.models import User, Invoice, Currency

if TYPE_CHECKING:
    from chat_scanner.locales.stubs.ru.stub import TranslatorRunner

router = Router()


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    logger.info("process_pre_checkout_query")
    logger.info(pformat(pre_checkout_query.dict()))
    await pre_checkout_query.answer(ok=True, error_message='Test error message')


@router.message(F.content_type == types.ContentType.SUCCESSFUL_PAYMENT)
async def process_successful_payment(
        message: types.Message,
        bot: Bot,
        settings: Settings,
        session: AsyncSession,
        user: User,
        l10n: TranslatorRunner,
        hub: TranslatorHub,
        account_dispatchers: dict[int, Dispatcher],
        state: FSMContext
):
    logger.success("process_successful_payment")
    logger.debug(pformat(message.dict()))
    payment_cb = PaymentCallback.unpack(message.successful_payment.invoice_payload)
    invoice = Invoice(
        user_id=user.id,
        amount=payment_cb.amount,
        currency=Currency.RUB,
        invoice_id=message.successful_payment.invoice_payload,
        description=l10n.payment.description(
            month=payment_cb.duration,
            currency=Currency.RUB,
            price=payment_cb.amount,
            rate=payment_cb.subscription_rate
        ),
        merchant=MerchantEnum.YOOKASSA,
        rate=payment_cb.subscription_rate
    )
    invoice.rub_amount = payment_cb.amount
    invoice.subscription_duration = payment_cb.duration * 30
    # full_user_subscription_duration = user.subscription_duration + invoice.subscription_duration  # Текущая подписка + новая
    # invoice.additional_info = str(datetime.datetime.today() + datetime.timedelta(days=full_user_subscription_duration))
    session.add(invoice)
    await session.commit()
    await success_paid(session, account_dispatchers, invoice, bot, settings, l10n, hub)
    await state.clear()
