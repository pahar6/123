from __future__ import annotations

from enum import StrEnum

from aiogram.filters.callback_data import CallbackData


class LanguageAction(StrEnum):
    CHANGE = 'change_language'  # Изменить язык для не нового пользователя
    SET_LANGUAGE = 'set_language'  # Выбрать язык новому пользователю


class LanguageCallback(CallbackData, prefix='language'):
    action: LanguageAction
    language_code: str

