from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils import deep_linking
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import make_transient

from chat_scanner.apps.account.dispatcher import Dispatcher
from chat_scanner.apps.bot.callback_data.base_callback import Action
from chat_scanner.apps.bot.callback_data.project import ProjectCallback, KeywordCallback
from chat_scanner.apps.bot.filters.project import ProjectFilter
from chat_scanner.apps.bot.keyboards.common import project_kbs
from chat_scanner.db.models import User
from chat_scanner.db.models.project import ProjectSettings
from chat_scanner.db.models.project.keyword import KeywordType, Keyword
from chat_scanner.db.models.project.project import Project
from .get import get_project, get_keywords
from .update import dispatchers_update

if TYPE_CHECKING:
    from chat_scanner.locales.stubs.ru.stub import TranslatorRunner

router = Router()


class CreateKeyword(StatesGroup):
    type = State()
    word = State()


@router.callback_query(ProjectCallback.filter(F.action == Action.CREATE))
async def create_project(
        call: types.CallbackQuery,
        bot: Bot,
        l10n: TranslatorRunner,
        session: AsyncSession,
        user: User,
        state: FSMContext
):
    project = Project(
        name="🔹Новый проект",
        user=user,
    )
    session.add(project)
    await session.flush()

    settings = await ProjectSettings.create(session, project_id=project.id)

    project.name = l10n.button.name_project() #Без названия
    start_link = await deep_linking.create_startgroup_link(bot, project.id)
    project.connect_link = start_link
    await session.commit()
    await session.refresh(project)
    await get_project(call, l10n, project, state, user) #ядобавил юзер


@router.callback_query(
    KeywordCallback.filter(F.action == Action.CREATE),
    ProjectFilter(from_keyword=True)
)
async def create_keyword(
        call: types.CallbackQuery,
        l10n: TranslatorRunner,
        callback_data: KeywordCallback,
        project: Project,
        state: FSMContext
):
    keyword_type_text = callback_data.get_text(l10n, possessive=True)
    await state.update_data(
        project_id=project.id,
        create_cd=callback_data,
        keyword_type_text=keyword_type_text
    )
    if not callback_data.username:

        await call.message.edit_text(
            l10n.project.keyword.create.type(
                keyword_type=keyword_type_text
            ),
            reply_markup=project_kbs.create_keyword_type(
                callback_data,
                l10n
            )
        )
        await state.set_state(CreateKeyword.type)
    else:
        await call.message.edit_text(
            l10n.project.keyword.create.word(
                keyword_type=keyword_type_text,
            ),
            reply_markup=project_kbs.create_keyword_word(
                callback_data,
                l10n
            )
        )
        await state.set_state(CreateKeyword.word)


@router.callback_query(CreateKeyword.type)
async def create_keyword_type(
        call: types.CallbackQuery,
        l10n: TranslatorRunner,
        state: FSMContext
):
    data = await state.update_data(type=call.data)
    create_cd: KeywordCallback = data['create_cd']
    keyword_type_text = create_cd.get_text(l10n, possessive=False)
    await call.message.edit_text(
        l10n.project.keyword.create.word(
            keyword_type=keyword_type_text,
        ),
        reply_markup=project_kbs.create_keyword_word(
            create_cd,
            l10n
        )
    )
    await state.set_state(CreateKeyword.word)


@router.message(CreateKeyword.word)
async def create_keyword_word(
        message: types.Message,
        session: AsyncSession,
        l10n: TranslatorRunner,
        account_dispatchers: dict[int, Dispatcher],
        state: FSMContext
):
    data = await state.get_data()
    create_cd: KeywordCallback = data['create_cd']
    type: KeywordType = data.get('type', KeywordType.EXACT)
    word = message.text.strip()
    if create_cd.username:
        word = word.replace('@', '')

    project = await Project.get(session, id=create_cd.project_id)

    # Привести все ключевые слова к формату "заглавная буква + нижний регистр"
    word_formatted = word.capitalize()

    # Проверка на дубль ключей
    keyword = await Keyword.get_or_none(
        session,
        keyword=word_formatted,
        project_id=project.id,
    )

    # Выдать предупреждение
    if keyword:
        await message.answer(
            l10n.project.keyword.create.warning()
        )
        await get_keywords(
            message,
            l10n,
            project,
            create_cd,
            state
        )
        await state.clear()
    else:
        # Сохранить ключевое слово, если ошибки нет
        keyword = Keyword(
            project=project,
            type=type,
            keyword=word_formatted,
            is_stop_word=create_cd.stop_word,
            is_username=create_cd.username,
        )
        session.add(keyword)
        await session.commit()
        await session.refresh(keyword)
        await session.refresh(project)

        await dispatchers_update(project, session, account_dispatchers)
        keyword_type_text = create_cd.get_text(l10n)
        await message.answer(
            l10n.project.keyword.create.success(
                keyword_type=keyword_type_text,
                keyword=keyword.keyword,
                project_name=project.name
            )
        )
        await get_keywords(
            message,
            l10n,
            project,
            create_cd.copy_all(),
            state
        )
        await state.clear()


