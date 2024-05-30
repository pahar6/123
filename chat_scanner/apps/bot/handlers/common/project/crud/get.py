from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from chat_scanner.apps.bot.callback_data.base_callback import Action
from chat_scanner.apps.bot.callback_data.project import ProjectCallback, KeywordCallback, ProjectAction
from chat_scanner.apps.bot.filters.project import ProjectFilter
from chat_scanner.apps.bot.handlers.common.base import get_method
from chat_scanner.apps.bot.keyboards.common import project_kbs
from chat_scanner.config import Settings
from chat_scanner.db.models import KeywordType
from chat_scanner.db.models.project.project import Project

if TYPE_CHECKING:
    from chat_scanner.locales.stubs.ru.stub import TranslatorRunner

router = Router()


@router.callback_query(
    ProjectCallback.filter(F.action == Action.GET),
    ProjectFilter()
)
async def get_project(
        message: types.Message | types.CallbackQuery,
        l10n: TranslatorRunner,
        project: Project,
        state: FSMContext,
        user: User
):
    method = get_method(message)
    await method(
        l10n.project(name=project.name),
        reply_markup=project_kbs.get_project(project, l10n, user) #добавил юзер значение
    )


@router.callback_query(
    KeywordCallback.filter(
        F.action == Action.ALL
    ),
    ProjectFilter(from_keyword=True)
)
async def get_keywords(
        message: types.CallbackQuery | types.Message,
        l10n: TranslatorRunner,
        project: Project,
        callback_data: KeywordCallback,
        state: FSMContext,
):
    kw_types = KeywordType.get_all_types_text(l10n)
    method = get_method(message)
    keyword_type = callback_data.get_text(l10n, plural=True, possessive=True)
    keyword_type_poss = callback_data.get_text(l10n, possessive=True)

    formats_text = ""
    if not callback_data.username:
        formats_text = l10n.project.keywords.formats(
            types=kw_types,
        )
    sign = keyword_type[:1]
    keyword_type = keyword_type[1:]
    await method(
        l10n.project.keywords(
            sign=sign,
            keyword_type=keyword_type,
            formats=formats_text,
        ),
        reply_markup=project_kbs.get_keywords(project, callback_data, l10n)
    )


@router.callback_query(ProjectCallback.filter(F.action == ProjectAction.DETECT_DUPLICATES), ProjectFilter())
async def get_detect_duplicates(
        message: types.CallbackQuery | types.Message,
        l10n: TranslatorRunner,
        project: Project,
        settings: Settings,
        state: FSMContext,
):
    method = get_method(message)
    await method(
        l10n.project.duplicates(),  # ПО ДЕФОЛТУ СТРОКА БЫЛА ЗАКОММЕНЧЕНА А НИЖНЯ СТРОКА РАССКОМЕНЧЕНА - ТЕСТ
        # settings.bot.AUTO_DELETE_MESSAGE,
        reply_markup=project_kbs.get_detect_duplicates(project, l10n)
    )


@router.callback_query(ProjectCallback.filter(F.action == ProjectAction.RESPONSE), ProjectFilter())
async def get_response(
        message: types.CallbackQuery | types.Message,
        l10n: TranslatorRunner,
        project: Project,
        settings: Settings,
        state: FSMContext,
):
    method = get_method(message)
    await method(
        l10n.project.response(),
        # settings.bot.RESPONSE,
        reply_markup=project_kbs.get_response(project, l10n)
    )


@router.callback_query(ProjectCallback.filter(F.action == ProjectAction.POST_SETTINGS), ProjectFilter())
async def post_settings(
        message: types.CallbackQuery | types.Message,
        l10n: TranslatorRunner,
        project: Project,
        settings: Settings,
        state: FSMContext,
):
    method = get_method(message)
    await method(
        l10n.project.post_settings(),
        reply_markup=project_kbs.post_settings(project, l10n)
    )


@router.callback_query(ProjectCallback.filter(F.action == ProjectAction.DEFERRED_MESSAGES), ProjectFilter())
async def get_deferred_messages(
        message: types.CallbackQuery | types.Message,
        l10n: TranslatorRunner,
        project: Project
):
    method = get_method(message)
    await method(
        l10n.project.deferred_messages(),
        reply_markup=project_kbs.get_deferred_messages(project, l10n)
    )


