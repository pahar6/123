from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from chat_scanner.apps.bot.callback_data.base_callback import UserCallback, AdminAction, SubscriptionCallback, \
    MailingAction
from chat_scanner.apps.bot.commands.bot_commands import AdminCommands
from chat_scanner.apps.bot.keyboards.common.common_kbs import custom_back_inline_button
from chat_scanner.config import Settings
from .....db.models import Rates

if TYPE_CHECKING:
    from chat_scanner.locales.stubs.ru.stub import TranslatorRunner


def admin_start():
    keywords = [
        # "mailing"
	    ("📊 Статистика", "stats"),
        ("📨 Рассылка", "mailing"),
        # "accounts"
        ("👥 Аккаунты", AdminCommands.ACCOUNTS.command),
        # Получить пользователя
        ("👤 Инфо о пользователе", UserCallback(action=AdminAction.WANT_GET)),
        # Настройки подписок
        ("💳 Настройки тарифов", SubscriptionCallback(action=AdminAction.MENU)),
        # Изменить процет от рефералки
        ("🧮 Процент рефералки", "change_ref_percent"),
        # Изменить сумму вывода
        ("💸 Сумма вывода рефералки", "change_withdraw_sum"),
        # Изменить процент скидки при покупке подписки на год
        ("📅 Скидка подписки на год", "change_discount"),
        # Изменить стартовую бонуску
        ("🎁 Сумма стартового бонуса", "update_bonus"),
        # Изменить служебный чат
        ("🔗 Адрес служебного чата", "change_support_chat"),
    ]
    builder = InlineKeyboardBuilder()

    for text, callback_data in keywords:
        builder.button(text=text, callback_data=callback_data)

    builder.adjust(1)
    builder.row(custom_back_inline_button())
    return builder.as_markup()
    # return get_inline_keyboard(keyword)


def mailing_choose():
    keywords = [
        ("📨 Рассылка всем пользователям", MailingAction.ALL),
        ("📨 Рассылка с подпиской", MailingAction.SUBSCRIBED),
        ("📨 Рассылка с истекшей подпиской", MailingAction.EXPIRED),
        ("📨 Рассылка отдельному пользователю", MailingAction.USER),
        ("🗑 Удалить неактивных участников", MailingAction.DELETE_BLOCKED),
        ("👥 Выход юзерботов из неактивных чатов", MailingAction.EXIT_FROM_CHAT),
    ]
    builder = InlineKeyboardBuilder()

    for text, callback_data in keywords:
        builder.button(text=text, callback_data=callback_data)

    builder.button(text="« Назад", callback_data="admin")
    builder.adjust(1)
    return builder.as_markup()

def stats():
    builder = InlineKeyboardBuilder()

    builder.button(text="📥 Выгрузить пользователей", callback_data="export_users")
    builder.button(text="📥 Выгрузить статистику оплат", callback_data="export_invoices")

    builder.button(text="« Назад", callback_data="admin")
    builder.adjust(1)
    return builder.as_markup()

def change_subscription_rate(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="Demo", callback_data=SubscriptionCallback(id=user_id, action=AdminAction.CHANGE_SUBS_RATE_OPT, rate=Rates.DEMO))
    builder.button(text="Standart", callback_data=SubscriptionCallback(id=user_id, action=AdminAction.CHANGE_SUBS_RATE_OPT, rate=Rates.STANDART))
    builder.button(text="Pro", callback_data=SubscriptionCallback(id=user_id, action=AdminAction.CHANGE_SUBS_RATE_OPT, rate=Rates.PRO))
    builder.button(text="Назад", callback_data=UserCallback(id=user_id, action=AdminAction.GET))
    builder.adjust(1)
    return builder.as_markup()


def get_user(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Пополнить баланс",
        callback_data=UserCallback(
            action=AdminAction.ADD_BALANCE,
            id=user_id)
    )
    builder.button(
        text="Списать баланс",
        callback_data=UserCallback(
            action=AdminAction.SUBTRACT_BALANCE,
            id=user_id)
    )
    builder.button(
        text="Изменить тариф подписки",
        callback_data=SubscriptionCallback(
            action=AdminAction.CHANGE_SUBS_RATE,
            id=user_id)
    )
    builder.button(
        text="Изменить длительность подписки",
        callback_data=UserCallback(
            action=AdminAction.CHANGE_SUBSCRIPTION_DURATION,
            id=user_id)
    )

    builder.button(
        text="Отправить сообщение",
        callback_data=UserCallback(
            action=AdminAction.SEND_MESSAGE,
            id=user_id)
    )

    builder.button(
        text="Блокировка пользователя",
        callback_data=UserCallback(
            action=AdminAction.ADD_BAN,
            id=user_id)
    )

    builder.button(
        text="« Назад",
        callback_data="admin"
    )
    builder.adjust(1)
    return builder.as_markup()


def subscription_menu(
        settings: Settings,
        l10n: TranslatorRunner
):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Standart: " + l10n.payment.subscription.button.month_1(price_1=settings.bot.SUBSCRIPTION_1_MONTH),
        callback_data=SubscriptionCallback(
            action=AdminAction.CHANGE_SUBSCRIPTION_DURATION,
            months=1,
            rate=Rates.STANDART
        )
    )
    builder.button(
        text="Standart: " + l10n.payment.subscription.button.month_6(price_6=settings.bot.SUBSCRIPTION_6_MONTH),
        callback_data=SubscriptionCallback(
            action=AdminAction.CHANGE_SUBSCRIPTION_DURATION,
            months=6,
            rate=Rates.STANDART
        )
    )
    builder.button(
        text="Standart: " + l10n.payment.subscription.button.month_12(price_12=settings.bot.SUBSCRIPTION_12_MONTH),
        callback_data=SubscriptionCallback(
            action=AdminAction.CHANGE_SUBSCRIPTION_DURATION,
            months=12,
            rate=Rates.STANDART
        )
    )

    builder.button(
        text="Pro: " + l10n.payment.subscription.button.month_1(price_1=settings.bot.SUBSCRIPTION_PRO_1_MONTH),
        callback_data=SubscriptionCallback(
            action=AdminAction.CHANGE_SUBSCRIPTION_DURATION,
            months=1,
            rate=Rates.PRO
        )
    )
    builder.button(
        text="Pro: " + l10n.payment.subscription.button.month_6(price_6=settings.bot.SUBSCRIPTION_PRO_6_MONTH),
        callback_data=SubscriptionCallback(
            action=AdminAction.CHANGE_SUBSCRIPTION_DURATION,
            months=6,
            rate=Rates.PRO
        )
    )

    builder.button(
        text="Pro: " + l10n.payment.subscription.button.month_12(price_12=settings.bot.SUBSCRIPTION_PRO_12_MONTH),
        callback_data=SubscriptionCallback(
            action=AdminAction.CHANGE_SUBSCRIPTION_DURATION,
            months=12,
            rate=Rates.PRO
        )
    )

    builder.add(custom_back_inline_button(
        l10n.button.back(),
        "admin",
    ))
    builder.adjust(1)
    return builder.as_markup()


def admin_button() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Админ панель", callback_data="admin")
    return builder.as_markup()


def back() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="« Назад", callback_data="admin")
    return builder.as_markup()
