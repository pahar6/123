from typing import Callable, Dict, Any, Awaitable

from loguru import logger
from aiogram import BaseMiddleware
from aiogram.types import Message
# Грубо говоря - это l10n ок
from fluentogram import TranslatorHub  # Смотри - это объект для работы с переводом - если его нет то переводить не сможем


from chat_scanner.db.models import User, Locale

class TranslatorRunnerMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        hub: TranslatorHub = data.get('translator_hub')
        user: User = data.get('user')
        if not user and event.from_user:
            user = event.from_user

        if user:  # Если пользователь зашел не в первый раз - то выдаем ему язык который он выбрал раннее
            data['l10n'] = hub.get_translator_by_locale(user.language_code)
            data['hub'] = hub

        else:  # Если пользователь зашел впервые - по дефолту выдаем ему русскоязычную версию ответов
            data['l10n'] = hub.get_translator_by_locale(Locale.RUSSIAN)
            data['hub'] = hub

        return await handler(event, data)
