from __future__ import annotations

import re
from enum import StrEnum
from typing import TYPE_CHECKING

from loguru import logger

from sqlalchemy import ForeignKey, String, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .project import Project
from ..base import Base

if TYPE_CHECKING:
    from chat_scanner.locales.stubs.ru.stub import TranslatorRunner


class KeywordType(StrEnum):
    CONTAINS = 'contains'
    EXACT = 'exact'
    SIGNATURE = 'signature'
    REPLACING = 'replacing'

    # Получить текст из TranslatorRunner
    def get_text(self, l10n: TranslatorRunner) -> str:
        return l10n.get(f'project-keyword-type-{self.value}')

    @classmethod
    def get_all_types_text(cls, l10n: TranslatorRunner) -> str:
        response = ''
        for t in cls:
            if t in (cls.SIGNATURE, cls.REPLACING):
                continue
            response += t.get_text(l10n) + '\n'
        response = response.strip('\n')
        return response  # '\n'.join([t.get_text(l10n) for t in cls])


class Keyword(Base):
    __tablename__ = 'keywords'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey(Project.id))
    project: Mapped[Project] = relationship(back_populates="keywords", lazy='joined')

    # Тип ключевого слова
    type: Mapped[KeywordType] = mapped_column(default=KeywordType.CONTAINS)

    # Само ключевое слово
    keyword: Mapped[str] = mapped_column(String(100), index=True)

    is_stop_word: Mapped[bool] = mapped_column(default=False)
    is_username: Mapped[bool] = mapped_column(default=False)

    replacing_text: Mapped[str | None] = mapped_column(String(100), default=None)

    #Визуальная часть (инфографика) списка ключевиков
    def pretty(self, l10n: TranslatorRunner):
        if self.is_username:
            return f'(👤) {self.keyword}'
        sign = self.type.get_text(l10n)[0]
        return f'{sign} {self.keyword}'

    # Проверить текст на наличие ключевого слова
    def check(self, text: str) -> bool:
        keyword = self.keyword.lower()
        text = text.lower()  # Приводим текст к нижнему регистру
        if self.type == KeywordType.CONTAINS:
            return keyword in text
        elif self.type == KeywordType.EXACT:
            return keyword in text.split(" ")
        return False

    @staticmethod
    async def remove_keyword_by_user_id(session: AsyncSession, user_id: int) -> tuple[bool, str]:
        """Remove all keywords of projects where creator is user_id"""

        # Query с проектами пользователя
        user_project_ids = await session.execute(select(Project.id).where(Project.user_id == user_id))
        user_project_ids = [x[0] for x in tuple(user_project_ids)]

        try:
            # Удалить все элементы с настройками пользователя
            await session.execute(
                delete(Keyword)
                .where(
                    Keyword.project_id.in_(user_project_ids)
                )
            )
            await session.commit()
            return True, 'ok'
        except Exception as error:
            # logger.exception(error)
            return False, str(error)

    @staticmethod #это я добавил
    async def remove_keyword_by_project_id(session: AsyncSession, project_id: int) -> tuple[bool, str]:
        """Remove all keywords of a specific project by project_id"""

        try:
            # Удалить все ключевые слова для указанного проекта
            await session.execute(
                delete(Keyword)
                .where(
                    Keyword.project_id == project_id
                )
            )
            await session.commit()
            return True, 'ok'
        except Exception as error:
            # logger.exception(error)
            return False, str(error)
