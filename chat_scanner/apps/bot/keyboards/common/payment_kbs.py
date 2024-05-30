from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from aiogram.types import InlineKeyboardButton, KeyboardButton
from aiogram.utils import markdown as md
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fluentogram import TranslatorRunner

from .....db.models import Rates
from .common_kbs import custom_back_inline_button, menu_button
from ...callback_data.payment import PaymentCallback, PaymentAction, PaymentSystem
from .....config import Settings
from loguru import logger

IKB = InlineKeyboardButton
KB = KeyboardButton
md = md

if TYPE_CHECKING:
    from .....locales.stubs.ru.stub import TranslatorRunner


def payment(l10n: TranslatorRunner):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=l10n.payment.button.extend(),
        callback_data=PaymentCallback(action=PaymentAction.CHOOSE_SUBSCRIPTION_RATE)
    )
    builder.add(custom_back_inline_button(l10n.button.back()))
    builder.adjust(1)
    return builder.as_markup()


def expired(l10n: TranslatorRunner):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=l10n.payment.button.extend(),
        callback_data=PaymentCallback(action=PaymentAction.SUBSCRIPTION)
    )

    builder.add(custom_back_inline_button(l10n.button.back()))
    builder.adjust(1)
    return builder.as_markup()


def upgrade_subscription(l10n):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=l10n.payment.button.upgrade_subscription(),
        callback_data=PaymentCallback(
            action=PaymentAction.SUBSCRIPTION,
            data=Rates.PRO
        )
    )
    builder.row(menu_button(l10n))
    return builder.as_markup()

def choose_subscription(l10n):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=l10n.payment.tariff.button.standart(),
        callback_data=PaymentCallback(
            action=PaymentAction.SUBSCRIPTION,
            data=Rates.STANDART
        )
    )
    builder.button(
        text=l10n.payment.tariff.button.pro(),
        callback_data=PaymentCallback(
            action=PaymentAction.SUBSCRIPTION,
            data=Rates.PRO
        )
    )
    builder.add(custom_back_inline_button(
        l10n.button.back(),
        PaymentCallback(action=PaymentAction.PAYMENT))
    )
    builder.adjust(1)
    return builder.as_markup()

def subscription(l10n: TranslatorRunner, settings: Settings, rate: str):
    builder = InlineKeyboardBuilder()
    if rate == Rates.STANDART:
        builder.button(
            text=l10n.payment.subscription.button.month_1(price_1=settings.bot.SUBSCRIPTION_1_MONTH),
            callback_data=PaymentCallback.payment_system(settings.bot.SUBSCRIPTION_1_MONTH, 1, rate)
        )
        builder.button(
            text=l10n.payment.subscription.button.month_6(price_6=settings.bot.SUBSCRIPTION_6_MONTH),
            callback_data=PaymentCallback.payment_system(settings.bot.SUBSCRIPTION_6_MONTH, 6, rate)
        )

        builder.button(
            text=l10n.payment.subscription.button.month_12(price_12=settings.bot.SUBSCRIPTION_12_MONTH),
            callback_data=PaymentCallback.payment_system(settings.bot.SUBSCRIPTION_12_MONTH, 12, rate)
        )
    elif rate == Rates.PRO:
        builder.button(
            text=l10n.payment.subscription.button.month_1(price_1=settings.bot.SUBSCRIPTION_PRO_1_MONTH),
            callback_data=PaymentCallback.payment_system(settings.bot.SUBSCRIPTION_PRO_1_MONTH, 1, rate)
        )
        builder.button(
            text=l10n.payment.subscription.button.month_6(price_6=settings.bot.SUBSCRIPTION_PRO_6_MONTH),
            callback_data=PaymentCallback.payment_system(settings.bot.SUBSCRIPTION_PRO_6_MONTH, 6, rate)
        )

        builder.button(
            text=l10n.payment.subscription.button.month_12(price_12=settings.bot.SUBSCRIPTION_PRO_12_MONTH),
            callback_data=PaymentCallback.payment_system(settings.bot.SUBSCRIPTION_PRO_12_MONTH, 12, rate)
        )

    builder.add(custom_back_inline_button(
        l10n.button.back(),
        PaymentCallback(action=PaymentAction.CHOOSE_SUBSCRIPTION_RATE))
    )
    builder.adjust(1)
    return builder.as_markup()

def payment_system(l10n: TranslatorRunner, payment_callback: PaymentCallback):
    builder = InlineKeyboardBuilder()
    for system in PaymentSystem:
        if system in [PaymentSystem.WALLET, PaymentSystem.YOOKASSA]:
            builder.button(
                text=getattr(l10n.payment.payment_system.button, system.value)(),
                callback_data=payment_callback.buy(system)
            )
    builder.button(
        text=l10n.payment.payment_system.button.cryptobot(),
        callback_data=PaymentCallback(action=PaymentAction.PAYMENT_SYSTEM_CRYPTOBOT,
                                      subscription_rate=payment_callback.subscription_rate,
                                      amount=payment_callback.amount,
                                      duration=payment_callback.duration
                                      )
    )
    logger.info(f"[PAYMENT-SYSTEM] ПОЛНЫй КОЛБЭК: {payment_callback}")
    builder.adjust(1, 1, 1)
    builder.row(custom_back_inline_button(
        l10n.button.back(),
        PaymentCallback(action=PaymentAction.SUBSCRIPTION, data=payment_callback.subscription_rate))
    )
    return builder.as_markup()


def payment_system_cryptobot(l10n: TranslatorRunner, payment_callback: PaymentCallback):
    builder = InlineKeyboardBuilder()
    for system in PaymentSystem:
        if system in [PaymentSystem.USDT, PaymentSystem.TON, PaymentSystem.BTC]:
            builder.button(
                text=getattr(l10n.payment.payment_system.button, system.value)(),
                callback_data=payment_callback.buy(system)
            )
    logger.info(f"[PAYMENT-CRYPTOBOT] ПОЛНЫй КОЛБЭК: {payment_callback}")
    builder.adjust(3)
    builder.row(custom_back_inline_button(
        l10n.button.back(),
        PaymentCallback(action=PaymentAction.CHOOSE_SUBSCRIPTION_RATE))
    )
    return builder.as_markup()

def buy(pay_url: str, l10n: TranslatorRunner):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=l10n.payment.button.pay(),
        url=pay_url
    )
    builder.button(
        text=l10n.payment.button.i_paid(),
        callback_data=PaymentCallback(action=PaymentAction.I_PAID)
    )
    builder.adjust(1)
    return builder.as_markup()

