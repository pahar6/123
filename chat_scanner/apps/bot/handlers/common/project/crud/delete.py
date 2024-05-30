from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession

from pyrogram.raw import functions

from chat_scanner.apps.account.dispatcher import Dispatcher
from chat_scanner.apps.bot.callback_data.base_callback import Action
from chat_scanner.apps.bot.callback_data.project import KeywordCallback, ProjectCallback
from chat_scanner.apps.bot.filters.project import KeywordFilter, ProjectFilter
from chat_scanner.apps.bot.handlers.common.project.crud.get import get_keywords
from chat_scanner.apps.bot.handlers.common.project.crud.update import dispatchers_update
from chat_scanner.apps.bot.handlers.common.project.project import get_projects
from chat_scanner.db.models import User
from chat_scanner.db.models.project.keyword import Keyword
from chat_scanner.db.models.project.project import Project
from chat_scanner.db.models import ProjectChat, Account

if TYPE_CHECKING:
    from chat_scanner.locales.stubs.ru.stub import TranslatorRunner

router = Router()


@router.callback_query(
    KeywordCallback.filter(F.action == Action.DELETE),
    KeywordFilter()
)
async def delete_keyword(
        call: types.CallbackQuery,
        session: AsyncSession,
        keyword: Keyword,
        l10n: TranslatorRunner,
        callback_data: KeywordCallback,
        account_dispatchers: dict[str, Dispatcher],
        state: FSMContext
):
    data = await state.get_data()
    path = callback_data.get_model_field()
    key = f"{path}_{keyword.project_id}_{keyword.id}"
    confirm = data.get(key)

    if confirm:
        await session.delete(keyword)
        await session.commit()
        keyword_type = callback_data.get_text(l10n)
        await call.answer(l10n.project.keyword.deleted(
            keyword_type=keyword_type,
        ))

        project = await Project.get(session, id=keyword.project_id)
        if project.account_id:
            dispatcher = account_dispatchers[project.account_id]
            await dispatcher.update_account(session)
        else:
            await dispatchers_update(project, session, account_dispatchers)

        await get_keywords(
            call,
            l10n,
            project,
            callback_data.copy_all(),
            state
        )
    else:
        await call.answer(l10n.project.keyword.delete.confirm())
        await state.update_data({key: True})


@router.callback_query(
    ProjectCallback.filter(F.action == Action.DELETE),
    ProjectFilter()
)
async def delete_project(
        call: types.CallbackQuery,
        session: AsyncSession,
        user: User,
        project: Project,
        l10n: TranslatorRunner,
        bot: Bot,
        account_dispatchers: dict[int, Dispatcher],
        state: FSMContext
):
    data = await state.get_data()
    key = f"project_{project.id}"
    confirm = data.get(key)  # True/False
    if confirm:
        await project.remove(
            session=session,
            bot=bot,
            account_dispatchers=account_dispatchers
        )
        await call.answer(l10n.project.deleted())  # Отвечаем пользователю - проект
        # await dispatchers_update(project, session, account_dispatchers)
        await get_projects(call, l10n, user, session, bot, state)
    else:
        await call.answer(l10n.project.delete.confirm())
        await state.update_data({key: True})

