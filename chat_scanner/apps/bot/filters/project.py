from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger

from aiogram import types
from aiogram.filters import BaseFilter
from fluentogram import TranslatorHub
from sqlalchemy.ext.asyncio import AsyncSession

from chat_scanner.apps.bot.callback_data.project import ProjectCallback, KeywordCallback
from chat_scanner.db.models.project.keyword import Keyword
from chat_scanner.db.models.project.project import Project

if TYPE_CHECKING:
    from chat_scanner.locales.stubs.ru.stub import TranslatorRunner


class ProjectFilter(BaseFilter):

    def __init__(self, from_keyword=False):
        self.from_keyword = from_keyword

    async def __call__(
            self,
            update: types.CallbackQuery,
            session: AsyncSession,
            callback_data: ProjectCallback | KeywordCallback,
            translator_hub: TranslatorHub,
    ) -> bool | dict[str, Any]:
        id = callback_data.id
        if self.from_keyword:
            id = callback_data.project_id
        project = await Project.get_or_none(session, id=id)
        if project:
            return {'project': project}
        l10n: TranslatorRunner = translator_hub.get_translator_by_locale(update.from_user.language_code)
        await update.answer(l10n.project.not_found())
        return False


class KeywordFilter(BaseFilter):
    async def __call__(
            self,
            update: types.CallbackQuery,
            session: AsyncSession,
            callback_data: KeywordCallback,
            translator_hub: TranslatorHub,
    ) -> bool | dict[str, Any]:
        # Получение ключевого слова из базы данных
        keyword = await Keyword.get_or_none(session, id=callback_data.id)
        if keyword:
            return {'keyword': keyword}

        l10n: TranslatorRunner = translator_hub.get_translator_by_locale(update.from_user.language_code)
        keyword_type = 'Default-Keyword'
        try:
            keyword_type = callback_data.get_text(l10n)
        except Exception as error:
            logger.warning(f'[KEYWORD] Get-text keyword error: {error}')

        await update.answer(l10n.project.keyword.not_found(keyword_type=keyword_type))
        return False
