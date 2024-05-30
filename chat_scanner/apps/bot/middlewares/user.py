from typing import Callable, Any, Awaitable
from typing import TYPE_CHECKING

from fluentogram import TranslatorHub
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from chat_scanner.apps.bot.keyboards.common import language_kbs
from chat_scanner.apps.bot.handlers.common.base import get_method
from chat_scanner.config import Settings
from chat_scanner.db.models import User, Project, Rates
from chat_scanner.db.models.project import ProjectSettings

if TYPE_CHECKING:
    from chat_scanner.locales.stubs.ru.stub import TranslatorRunner


class UserMiddleware(BaseMiddleware):

    async def __call__(
            self,
            handler: Callable[[Message | CallbackQuery, dict[str, Any]], Awaitable[Any]],
            #l10n: TranslatorRunner
            event: Message | CallbackQuery,
            data: dict[str, Any]
    ) -> Any:
        user = event.from_user
        session: AsyncSession = data["session"]
        logger.debug("Get user for User {}", user.id)
        db_user = await User.get_or_none(session, id=user.id)
        is_new = False
        if not db_user:
            if event.chat.id != user.id:  # Если первый ивент пользователя прилетел с беседы
                return  # остановить обрабокту запроса
            settings: Settings = data["settings"]
            logger.info(f"Новый пользователь {user=}")
            db_user = await User.create(session, **user.dict(), balance=float(settings.bot.BONUS), rate=Rates.DEMO)
            # project = await Project.create(session, user_id=db_user.id)  # , is_general=True)
            # await session.flush()
            # await ProjectSettings.create(session, project_id=project.id)
            await session.commit()
            await session.refresh(db_user)
            is_new = True
        else:
            # Првоерка на блокиовку пользовтаеля
            db_user = await User.get(session, id=user.id)
            if db_user.ban:
                return

        if is_new:  # Новый пользователь
            method = get_method(event)

            hub: TranslatorHub = data.get('translator_hub')
            l10n: TranslatorRunner = hub.get_translator_by_locale(db_user.language_code)
            await method(
                text=f"<b>Choose language | Выберите язык</b>",
                reply_markup=language_kbs.language(l10n, is_new=True)
            )

        data["user"] = db_user
        data["is_new"] = is_new
        return await handler(event, data)