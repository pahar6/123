from __future__ import annotations

from enum import StrEnum

from aiogram.filters.callback_data import CallbackData


class PaymentAction(StrEnum):
    PAYMENT = "payment"
    BUY = "buy"
    EXTEND = "extend"
    # Выбрать подписку
    CHOOSE_SUBSCRIPTION_RATE = 'choose_subscription_rate'
    SUBSCRIPTION = "subscription"
    PAYMENT_SYSTEM = "payment_system"
    PAYMENT_SYSTEM_CRYPTOBOT = "cryptobot" #я делал
    I_PAID = "i_paid"
    CANCEL = "cancel"


class PaymentSystem(StrEnum):
    # YOOMONEY = "yoomoney"
    WALLET = 'wallet'
    YOOKASSA = "yookassa"
    USDT = "usdt"
    TON = "ton"
    BTC = "btc"


class PaymentCallback(CallbackData, prefix="payment"):
    action: PaymentAction
    amount: float | int | None
    duration: int | None
    subscription_rate: str | None
    system: PaymentSystem | None
    data: str | None

    @classmethod
    def payment_system(cls, amount: int | float, duration: int, rate: str) -> PaymentCallback:
        return cls(action=PaymentAction.PAYMENT_SYSTEM, amount=amount, duration=duration, subscription_rate=rate)

    def buy(self, system: PaymentSystem) -> PaymentCallback:
        return self.copy(update={"action": PaymentAction.BUY, "system": system})
