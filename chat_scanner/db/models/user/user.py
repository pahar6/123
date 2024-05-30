from __future__ import annotations

import re
import datetime
import traceback
from enum import StrEnum
from typing import TYPE_CHECKING

from loguru import logger
from sqlalchemy import select, ForeignKey, delete, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import mapped_column, Mapped, relationship

from .account import Account
from .base import BaseUser
from ..invoice import Invoice, InvoiceStatus
from ..project import Project

if TYPE_CHECKING:
    from chat_scanner.apps.account.dispatcher import Dispatcher


class Locale(StrEnum):
    """Language codes."""
    ENGLISH = 'en'
    RUSSIAN = 'ru'

    @staticmethod
    def attributes() -> dict:
        """
        Collect all attributes of class
        @return: {RUSSIAN: ru, ENGLISH: en, ...}

        """
        attrs = vars(Locale).items()
        response = {}
        for key, value in attrs:
            if key.isalpha() and key != 'attributes':
                response[key] = value
        return response


class User(BaseUser):
    __tablename__ = 'users'
    language_code: Mapped[Locale | None] = mapped_column(default=Locale.RUSSIAN)
    accounts: Mapped[list[Account]] = relationship(back_populates='user')
    projects: Mapped[list[Project]] = relationship(back_populates='user')

    invoices: Mapped[list[Invoice]] = relationship(back_populates='user')

    balance: Mapped[float] = mapped_column(default=0)
    subscription_duration: Mapped[int] = mapped_column(default=3)
    ban: Mapped[bool] = mapped_column(default=False)
    rate: Mapped[str | None] = mapped_column(String(), default=None)

    referrer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    referrer: Mapped[User | None] = relationship(back_populates="referrals", remote_side="User.id")
    referrals: Mapped[list[User]] = relationship(back_populates="referrer")

    def button_text(self) -> str:
        return f"{self.first_name} {self.last_name} (@{self.username})"

    async def change_language_code(self, session: AsyncSession, new_language_code: str) -> bool:
        """Change language-code for user"""

        try:
            self.language_code = mapped_column(default=new_language_code)  # mapped_column(Locale.RUSSIAN/ENGLISH/...)
            await session.commit()  # Save in DB
            return True
        except Exception as error:
            logger.exception(error)  # Save in logs
        return False


    async def set_referrer(self, session: AsyncSession, referrer: int) -> bool:
        # todo L1 26.11.2022 3:40 taima: Сделать работающим и для объекта User
        """Set referrer for user"""
        # join referrer

        if self.referrer_id or self.id == referrer:
            return False
        else:
            self.referrer_id = referrer
            await session.commit()
            return True

    @staticmethod
    async def is_have_invoices(session: AsyncSession, user_id: int):
        try:
            invoices = await session.execute(
                select(Invoice)
                .where(Invoice.user_id == user_id)
            )
            # logger.warning(f'[{user_id}] User-invoices: {len(invoices.all())}')
            if len(invoices.all()) > 0:  # Если ранее были оформлены покупки
                return True
            return False
        except Exception as error:
            # logger.exception(error)
            return False

    @staticmethod
    async def is_have_referrers(session: AsyncSession, user_id: int) -> bool:
        """Select referrers-users of user by user-id"""
        try:
            referrers = await session.execute(
                select(User)
                .where(User.referrer_id == user_id)
            )
            if len(referrers.all()) > 0:  # If user have referrers when return True
                return True
            return False
        except Exception:
            # logger.exception(error)
            return False

    @staticmethod
    async def is_referrer(session: AsyncSession, user_id: int) -> bool:
        """Check user is referrer"""
        try:
            referrer = await User.get(session=session, id=user_id)
            referrer_id = referrer.referrer_id
            if referrer_id is not None:  # If user is referrer when return True
                return True
            return False
        except Exception:
            # logger.exception(error)
            return False

    @staticmethod
    async def remove_user_by_id(session: AsyncSession, user_id: int) -> tuple[bool, str]:
        """Remove NOT BANNED user by id"""
        try:
            await session.execute(
                delete(User)
                .where(User.id == user_id)
                .where(User.ban.is_(False))
            )
            await session.commit()
            return True, 'ok'
        except Exception as error:
            # logger.exception(error)
            return False, str(error)

    async def get_referrals(self, session: AsyncSession) -> set[User]:
        result = await session.execute(select(User).where(User.referrer_id == self.id))
        return set(result.unique().scalars().all())

    async def get_last_paid_referrals(self, session: AsyncSession) -> set[User]:
        result = (
            await session.execute(
                select(User)
                .join(Invoice)
                .where(User.referrer_id == self.id)
                .where(Invoice.status == InvoiceStatus.SUCCESS)
                .order_by(Invoice.created_at.desc())
                .limit(20)
            )
        )
        return set(result.unique().scalars().all())

    async def update_projects_accounts(
            self,
            session: AsyncSession,
            account_dispatchers: dict[int, Dispatcher],
    ):
        user_projects = await Project.filter(session, Project.user_id == self.id)
        for project in user_projects:
            if project.account_id in account_dispatchers:
                dispatcher = account_dispatchers[project.account_id]
                await dispatcher.update_account(session)
                logger.info(f"[Scheduler] Dispatcher of account {project.account_id} updated")

    @classmethod
    async def today_count(cls, session: AsyncSession) -> int:
        result = await session.execute(
            select(cls).where(cls.created_at >= datetime.date.today())
        )
        return len(result.unique().all())

    async def expired_date(self, session: AsyncSession) -> datetime.date:
        user_invoices = await Invoice.filter(
            session,
            Invoice.user_id == self.id,
            Invoice.status == InvoiceStatus.SUCCESS
        )

        if len(user_invoices) == 0:
            created_at = min(str(self.created_at), str(self.updated_at))
            created_at_date = datetime.datetime.strptime(created_at.split('.')[0], '%Y-%m-%d %H:%M:%S')
            expired_paid_date = created_at_date + datetime.timedelta(days=3)
        elif len(user_invoices) == 1:
            user_last_invoice = user_invoices[0]
            if user_last_invoice.additional_info is None:
                last_invoice_date = max(str(user_last_invoice.created_at), str(user_last_invoice.updated_at))
                last_invoice_date = datetime.datetime.strptime(last_invoice_date.split('.')[0], '%Y-%m-%d %H:%M:%S')
                expired_paid_date = last_invoice_date + datetime.timedelta(days=self.subscription_duration)
            else:
                expired_paid_date = user_last_invoice.additional_info
        else:
            user_last_invoice = user_invoices[-1]
            if user_last_invoice.additional_info is None:
                last_invoice_date = max(str(user_last_invoice.created_at), str(user_last_invoice.updated_at))
                last_invoice_date = datetime.datetime.strptime(last_invoice_date.split('.')[0], '%Y-%m-%d %H:%M:%S')
                today = datetime.datetime.now().replace(microsecond=0)
                delta_invoice_today_date = today - last_invoice_date
                expired_paid_date = delta_invoice_today_date + datetime.timedelta(days=self.subscription_duration)
            else:
                expired_paid_date = user_last_invoice.additional_info

        expired_paid_date_str = str(expired_paid_date)

        # Проверяем формат и разбираем строку
        if "days" in expired_paid_date_str:
            match = re.match(r'(\d+) days, (\d+):(\d+):(\d+)', expired_paid_date_str)
            if match:
                days, hours, minutes, seconds = map(int, match.groups())
                expired_paid_date = datetime.datetime.now() + datetime.timedelta(days=days, hours=hours,
                                                                                 minutes=minutes, seconds=seconds)
            else:
                raise ValueError(f"Invalid time format: {expired_paid_date_str}")
        else:
            # Отсекаем микросекунды из строки даты
            expired_paid_date_str = expired_paid_date_str.split('.')[0]
            expired_paid_date = datetime.datetime.strptime(expired_paid_date_str, '%Y-%m-%d %H:%M:%S')

        return expired_paid_date

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_admin_text(self):
        # (юзернейм, айди, имя фамилия, телефон, дата)
        return f"@{self.username} | {self.id} | {self.full_name}"
