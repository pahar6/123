from __future__ import annotations

import datetime
from abc import abstractmethod
from enum import StrEnum
from typing import Self, TypeVar, TYPE_CHECKING

from loguru import logger
from sqlalchemy import String, ForeignKey, select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload

from ..base import TimestampMixin
from ..base.declarative import Base
from ....apps.merchant.base import BaseMerchant, MerchantEnum, PAYMENT_LIFETIME, TIME_ZONE

if TYPE_CHECKING:
    from ..user import User

MerchantType = TypeVar("MerchantType", bound=BaseMerchant)


class Currency(StrEnum):
    """Currency codes."""
    USD = "USD"
    RUB = "RUB"
    EUR = "EUR"
    GBP = "GBP"

    USDT = "USDT"
    BTC = "BTC"
    TON = "TON"
    ETH = "ETH"
    USDC = "USDC"
    BUSD = "BUSD"


class Rates(StrEnum):
    """Tariff rates"""
    DEMO = 'DEMO'
    STANDART = 'STANDART'
    PRO = 'PRO'


class Status(StrEnum):
    """Invoice status."""
    PENDING = "pending"
    SUCCESS = "success"
    EXPIRED = "expired"
    FAIL = "fail"


class Invoice(Base, TimestampMixin):
    __tablename__ = "invoices"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped[User] = relationship(back_populates="invoices")
    currency: Mapped[Currency | None]
    rub_amount: Mapped[float | None]
    amount: Mapped[float | None]
    subscription_duration: Mapped[int]
    rate: Mapped[str | None] = mapped_column(String(100), default=Rates.STANDART)

    invoice_id: Mapped[str] = mapped_column(String(50), index=True)
    expire_at: Mapped[datetime.datetime | None] = mapped_column(
        default=func.now() + datetime.timedelta(seconds=PAYMENT_LIFETIME)
    )
    additional_info: Mapped[str | None] = mapped_column(String(255))
    pay_url: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[Status | None] = mapped_column(String(10), default=Status.PENDING)

    # CryptoCloud
    order_id: Mapped[str | None] = mapped_column(String(50), index=True, doc="Custom product ID")
    email: Mapped[str | None] = mapped_column(String(50), index=True, doc="Customer email")

    # CryptoPay, YooKassa, Qiwi
    description: Mapped[str | None] = mapped_column(String(255))

    merchant: Mapped[MerchantEnum | None] = mapped_column(String(20))

    def __str__(self):
        return f"[{self.__class__.__name__}] {self.user} {self.amount} {self.currency}"

    async def successfully_paid(self):
        """Successful payment."""
        self.status = Status.SUCCESS
        user_subscription_duration = self.user.subscription_duration
        if self.rate == Rates.PRO:
            if self.user.rate != Rates.PRO:
                user_subscription_duration = user_subscription_duration // 2  # половина от дней стандарт уйдет в ПРО
        user_subscription_duration += self.subscription_duration  # Добавить дни оплаченные в тарифе
        self.user.subscription_duration = user_subscription_duration
        # Добавить в addition дату окончания подписки пользователя
        self.additional_info = str(datetime.datetime.today() + datetime.timedelta(days=self.user.subscription_duration))

    @classmethod
    @abstractmethod
    async def create_invoice(
            cls,
            session: AsyncSession,
            merchant: MerchantType,
            user: User,
            amount: int | float | str,
            **kwargs,
    ) -> Self:
        """Create invoice."""
        raise NotImplementedError

    @classmethod
    async def get_pending_invoices(cls, session: AsyncSession) -> list[Invoice]:
        """Get pending invoices."""
        result = await session.execute(
            select(cls)
            .options(selectinload(cls.user))
            .where(cls.expire_at >= func.now())
            .where(cls.status == Status.PENDING)
        )
        return result.scalars().all()

    # статистика оплаченных пакетов, формат оплаты,дата
    def get_admin_text(self):
        """Get text for admin."""
        return f"{self.subscription_duration // 30} м.| {round(self.amount, 2)} {self.currency} | {self.created_at.astimezone(TIME_ZONE).strftime('%d.%m.%Y %H:%M')}"

    @staticmethod
    async def remove_invoices_by_user_id(session: AsyncSession, user_id: int):
        """Remove invoices by user_id"""
        try:
            await session.execute(
                delete(Invoice)
                .where(Invoice.user_id == user_id)
            )
            await session.commit()
            return True
        except Exception as error:
            logger.exception(error)
            return False
