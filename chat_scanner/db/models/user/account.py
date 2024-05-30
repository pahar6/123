from __future__ import annotations

import base64
from enum import StrEnum
from typing import TYPE_CHECKING

# from loguru import logger

from aiogram.utils import markdown as md
from sqlalchemy import ForeignKey, BigInteger, select, func, or_
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import mapped_column, Mapped, relationship

from .base import BaseUser
from ..project import Project

if TYPE_CHECKING:
    from .user import User
    from chat_scanner.locales.stubs.ru.stub import TranslatorRunner

b = md.hbold
c = md.hcode
i = md.hitalic


class AccountStatus(StrEnum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    BLOCKED = 'blocked'

    def get_text(self, l10n: TranslatorRunner):
        return l10n.get(f"account-status-{self.value}")


class Account(BaseUser):
    __tablename__ = 'accounts'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    user: Mapped[User] = relationship(back_populates="accounts", lazy='joined')
    status: Mapped[AccountStatus] = mapped_column(default=AccountStatus.INACTIVE)
    phone_number: Mapped[str] = mapped_column(String(32), index=True)
    api_data: Mapped[str] = mapped_column(String(100), index=True)
    session_string: Mapped[str] = mapped_column(String(600))
    projects: Mapped[list[Project]] = relationship(back_populates="account", lazy='joined')

    def pretty(self, l10n: TranslatorRunner):
        return (
            f"{b(self.first_name)} {b(self.last_name)}\n\n"
            f"Username: @{self.username}\n"
            f"Phone: {i(self.phone_number)}\n"
            f"Status: {b(self.status.get_text(l10n))}"
        )

    def button(self):
        return (
            f"{self.first_name} {self.last_name} ({self.status})"
        )

    @classmethod
    def encode_api_data(cls, api_id: int | str, api_hash: str) -> str:
        return base64.b64encode(f'{api_id}:{api_hash}'.encode()).decode()

    @classmethod
    def decode_api_data(cls, api_data: str) -> tuple[int, str]:
        api_id, api_hash = base64.b64decode(api_data.encode()).decode().split(':')
        return int(api_id), api_hash

    def get_api_data(self) -> tuple[int, str]:
        return self.decode_api_data(self.api_data)

    @classmethod
    async def create_account(
            cls,
            session: AsyncSession,
            phone_number: str,
            api_id: str | int,
            api_hash: str,
            session_string: str
    ) -> Account:
        return await cls.create(
            session=session,
            phone_number=phone_number,
            api_data=cls.encode_api_data(api_id, api_hash),
            session_string=session_string
        )

    # Добавить новый проект в аккаунт у которого самое маленькое количество проектов
    @classmethod
    async def get_free_account(cls, session: AsyncSession, project: Project) -> Account:
        # Проверить существует ли незаблокированный аккаунт с таким же проектом или отправителем поекта (если он есть)
        account = await session.execute(
            select(cls).join(Project).filter(
                cls.status == AccountStatus.ACTIVE,  # Берем аккаунт если он ЖИВОЙ
                or_(
                    Project.sender_id == project.sender_id, # Или если отправитель и проект подходят по условиям
                    Project.id == project.id
                )
            ).limit(1)  # Вытаскиваем первый аккаунт
        )
        account = account.scalars().first()
        if account:  # Если аккаунт с такими условиями есть то выдаем его
            # logger.warning(f'[ACCOUNT] Have account by filters: {account.id}')
            return account
        # Если нет, то добавить проект в аккаунт у которого самое маленькое количество проектов
        account = await cls.get_account_with_min_projects(session)
        # logger.warning(f'[ACCOUNT] Havent account by filters - get account with min projects: {account.id}')
        return account

    @classmethod
    async def get_account_with_min_projects(cls, session: AsyncSession) -> Account:
        """
        Get account who have min projects count or not have projects
        :param session:
        :return:
        """

        account = await session.execute(
            select(cls)
            .outerjoin(Project)
            .group_by(cls.id)
            .order_by(func.count(Project.id))
            .limit(1)
        )
        return account.unique().scalars().first()

