from __future__ import annotations

import asyncio
import datetime
import json
from typing import TYPE_CHECKING

from aiogram import Router, types, F, Bot
from aiogram.filters import Text, Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from chat_scanner.apps.bot.callback_data.payment import PaymentCallback, PaymentAction, PaymentSystem
from chat_scanner.apps.bot.commands.bot_commands import BaseCommands
from chat_scanner.apps.bot.handlers.common.base import get_method
from chat_scanner.apps.bot.keyboards.common import payment_kbs, common_kbs
from chat_scanner.apps.merchant import MerchantEnum, YooKassa, CryptoPay, Wallet
from chat_scanner.apps.merchant.gecko import Rate
from chat_scanner.config import Settings
from chat_scanner.db.models import User, Currency, Rates
from loguru import logger

if TYPE_CHECKING:
    from chat_scanner.locales.stubs.ru.stub import TranslatorRunner

router = Router()


@router.message(Command(BaseCommands.PAYMENT))
@router.callback_query(Text(BaseCommands.PAYMENT.command))
@router.callback_query(PaymentCallback.filter(F.action == PaymentAction.PAYMENT))
async def payment(
        message: types.Message | types.CallbackQuery,
        l10n: TranslatorRunner,
        user: User,
        session: AsyncSession,
        bot: Bot,
        state: FSMContext
):
    await state.clear()
    user_subscription_duration_date = user.subscription_duration
    if user_subscription_duration_date == 0:
        user_expired_date = await user.expired_date(session)
    else:
        user_expired_date = datetime.datetime.now() + datetime.timedelta(days=user_subscription_duration_date)

    if user.rate:
        _rate = user.rate
    else:
        _rate = l10n.status.rate_off()
    if isinstance(message, types.CallbackQuery):
        message = message.message
        await bot.send_message(
            chat_id=message.chat.id,
            text=l10n.payment(date=user_expired_date, rate=_rate),
            disable_web_page_preview=True,
            reply_markup=payment_kbs.payment(l10n)
        )
        try:
            await message.delete()
        except Exception:
            pass


@router.callback_query(PaymentCallback.filter(F.action == PaymentAction.CHOOSE_SUBSCRIPTION_RATE))
async def choose_subscription_rate(
        call: types.CallbackQuery,
        l10n: TranslatorRunner,
        settings: Settings
):
    method = get_method(call)
    await method(
        l10n.payment.tariff(),
        reply_markup=payment_kbs.choose_subscription(l10n)
    )


@router.callback_query(PaymentCallback.filter(F.action == PaymentAction.SUBSCRIPTION))
async def subscription(
        call: types.CallbackQuery,
        l10n: TranslatorRunner,
        settings: Settings,
        callback_data: PaymentCallback,
        user: User,
        state: FSMContext
):
    # #rate = callback_data.data
    # rate = user.rate
    #logger.info(f"Callback data: {callback_data}")  # Логируем данные

    rate = callback_data.data
    if not rate:
        rate = user.rate

    await call.message.edit_text(
        l10n.payment.subscription(rate=rate),
        reply_markup=payment_kbs.subscription(l10n, settings, rate)
    )



@router.callback_query(PaymentCallback.filter(F.action == PaymentAction.PAYMENT_SYSTEM))
async def payment_system(
        call: types.CallbackQuery,
        l10n: TranslatorRunner,
        user: User,
        callback_data: PaymentCallback,
        state: FSMContext
):
    await call.message.edit_text(
        l10n.payment.payment_system(),
        reply_markup=payment_kbs.payment_system(l10n, callback_data)
    )

@router.callback_query(PaymentCallback.filter(F.action == PaymentAction.PAYMENT_SYSTEM_CRYPTOBOT))#я делал
async def payment_system_cryptobot(
        call: types.CallbackQuery,
        l10n: TranslatorRunner,
        user: User,
        callback_data: PaymentCallback,
        state: FSMContext
):
    await call.message.edit_text(
        l10n.payment.payment_system(),
        reply_markup=payment_kbs.payment_system_cryptobot(l10n, callback_data)
    )

def get_provide_data(amount: int, payment_text: str) -> str:
    return json.dumps({
        "receipt": {
            "items": [
                {
                    "description": payment_text,
                    "quantity": "1",
                    "amount": {
                        "value": amount,
                        "currency": "RUB"
                    },
                    "vat_code": 1
                }
            ],
            "customer": {
                "email": "pahar@bk.ru"
            }
        }
    }
    )

@router.callback_query(PaymentCallback.filter(F.action == PaymentAction.BUY))
async def buy(
        call: types.CallbackQuery,
        session: AsyncSession,
        l10n: TranslatorRunner,
        user: User,
        callback_data: PaymentCallback,
        settings: Settings,
        state: FSMContext
):
    await call.answer(l10n.payment.loading())
    amount = callback_data.amount
    system = callback_data.system
    subscription_rate = callback_data.subscription_rate

    month_text = l10n.get(f"payment-description-month_{callback_data.duration}")
    # Формирование ссылки на оплату
    if system == PaymentSystem.YOOKASSA:
        merchant_enum = MerchantEnum.YOOKASSA
        merchant: YooKassa | CryptoPay = settings.get_merchant(merchant_enum)
        payment_text = l10n.payment.description(
            month=month_text,
            currency=Currency.RUB,
            price=amount,
            rate=subscription_rate
        )
        # YOOKASSA ПОКА ЧТО ОБОЙДЕМ СТОРОНОЙ -В НЕЙ НЕМНОГО ДРУГОЙ АЛГОРИТМ ОПЛАТЫ <--------------------------------
        await call.message.answer_invoice(
            title=payment_text,
            description=payment_text,
            provider_token=merchant.api_key.get_secret_value(),
            currency='rub',
            prices=[
                types.LabeledPrice(
                    label=payment_text,
                    amount=amount * 100
                )
            ],
            start_parameter='create_invoice',
            is_flexible=False,
            payload=callback_data.pack(),
            reply_markup=common_kbs.yookassa_payment(l10n),
            provider_data=get_provide_data(amount, payment_text)
        )
        await state.clear()
        return

    elif system == PaymentSystem.WALLET:
        merchant_enum = MerchantEnum.WALLET
        currency_amount = amount
        currency = Currency.RUB
        merchant: Wallet = settings.get_merchant(merchant_enum)
    else:
        merchant_enum = MerchantEnum.CRYPTO_PAY
        rate = await asyncio.to_thread(Rate.get_rate)
        rate = rate.get_amount(amount)
        currency_amount = round(getattr(rate, system.value), 2)
        currency = Currency[system.value.upper()]
        merchant: CryptoPay = settings.get_merchant(merchant_enum)
    month = callback_data.duration
    invoice = await merchant.create_invoice(
        user.id,
        currency_amount,
        currency,
        description=l10n.payment.description(
            month=month_text,
            currency=currency,
            price=currency_amount,
            rate=subscription_rate
        ),
        rate=subscription_rate
    )
    invoice.rub_amount = amount
    if month == 1:
        duration = 30
    elif month == 6:
        duration = 180
    elif month == 12:
        duration = 365
    else:
        duration = 30
    invoice.subscription_duration = duration
    session.add(invoice)
    await session.commit()

    await call.message.edit_text(
        l10n.payment.created(),
        reply_markup=payment_kbs.buy(invoice.pay_url, l10n)
    )
    await state.clear()

@router.callback_query(PaymentCallback.filter(F.action == PaymentAction.I_PAID))
async def i_paid(
        call: types.CallbackQuery,
        l10n: TranslatorRunner,
):
    await call.message.answer(
        l10n.payment.i_paid(),
    )
