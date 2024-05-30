from __future__ import annotations

import traceback
from typing import TYPE_CHECKING

from loguru import logger
from aiogram.types import InlineKeyboardButton, KeyboardButton
from aiogram.utils import markdown as md
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fluentogram import TranslatorRunner

from .common_kbs import custom_back_inline_button
from ...callback_data.language import LanguageCallback, LanguageAction
from .....db.models import Locale

IKB = InlineKeyboardButton
KB = KeyboardButton
md = md

if TYPE_CHECKING:
    from .....locales.stubs.ru.stub import TranslatorRunner

#это рабочая функция по смене языка от разраба, я добавил к названию цифру1 тем самым создав рабочую копию для запуска в мидлваре,
#потому что функция language почему то не запускается в мидлваре, надо разобраться почему так и удалить функцию language1
#как я понял проблема незапуска функции language в мидлваре связана с l10n
def language1():
    try:
        languages = list(map(str, list(Locale.attributes().values())))  # ["en", "ru", ...]

        builder = InlineKeyboardBuilder()
        locale_language: str
        for locale_language in languages:
            builder.button(
                text=locale_language,
                callback_data=LanguageCallback(action=LanguageAction.CHANGE, language_code=locale_language)
            )
        builder.adjust(2)
        return builder.as_markup()
    except Exception as error:
        logger.exception(error)
    return None


def language(l10n: TranslatorRunner, is_new: bool = False):
    try:
        # Получаем список доступных языков
        languages = list(map(str, list(Locale.attributes().values())))

        builder = InlineKeyboardBuilder()
        language_code: str
        for language_code in languages:
            # Определяем название языка в зависимости от кода
            if language_code == "en":
                language_name = l10n.button.language.en()
            elif language_code == "ru":
                language_name = l10n.button.language.ru()
            else:
                # Добавьте обработку других языков по мере необходимости
                language_name = f"Unknown language: {language_code}"

            builder.button(
                text=language_name,
                callback_data=LanguageCallback(
                    action=LanguageAction.CHANGE if not is_new else LanguageAction.SET_LANGUAGE,
                    language_code=language_code
                )
            )
        builder.adjust(2)
        return builder.as_markup()
    except Exception as error:
        logger.exception(error)
    return None










