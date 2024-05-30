from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from aiogram import Router, types, F, Bot
from aiogram.filters import Command, Text, StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from chat_scanner.apps.account.dispatcher import Dispatcher
from chat_scanner.apps.bot.callback_data.base_callback import Action
from chat_scanner.apps.bot.callback_data.project import ProjectCallback, ProjectAction
from chat_scanner.apps.bot.filters.project import ProjectFilter
from chat_scanner.db.models.project.keyword import KeywordType, Keyword
from chat_scanner.apps.bot.commands.bot_commands import BaseCommands
from chat_scanner.apps.bot.handlers.common.base import get_method
from chat_scanner.apps.bot.keyboards.common import project_kbs, common_kbs, payment_kbs
from chat_scanner.db.models import User, Rates
from chat_scanner.db.models.project.project import Project
from chat_scanner.config import Settings



if TYPE_CHECKING:
    from chat_scanner.locales.stubs.ru.stub import TranslatorRunner

router = Router()


@router.callback_query(ProjectCallback.filter(F.action == Action.ALL))
@router.callback_query(Text(BaseCommands.PROJECTS.command))
@router.message(Command(BaseCommands.PROJECTS))
async def get_projects(
        message: types.Message | types.CallbackQuery,
        l10n: TranslatorRunner,
        user: User,
        session: AsyncSession,
        bot: Bot,
        state: FSMContext
):
    await state.clear()
    if isinstance(message, types.CallbackQuery):
        message = message.message
    projects = await Project.filter(
        session,
        Project.user_id == user.id,
    )
    await bot.send_message(
        chat_id=message.chat.id,
        text=l10n.projects(),
        reply_markup=project_kbs.get_projects(
            projects,
            l10n,
            user #я добавил для 20 проектов
        )
    )
    await message.delete()


@router.callback_query(ProjectCallback.filter(F.action == ProjectAction.UPGRADE_INFO), ProjectFilter())
async def show_upgrade_info(call: types.CallbackQuery, l10n: TranslatorRunner):
    await call.message.edit_text(
        l10n.payment.description.upgrade_info(),
        reply_markup=payment_kbs.upgrade_subscription(l10n)
    )

@router.callback_query(ProjectCallback.filter(F.action == ProjectAction.SIGNATURES), ProjectFilter())
async def signatures_handler(
        message: types.CallbackQuery | types.Message,
        l10n: TranslatorRunner,
        project: Project,
        session: AsyncSession,
        settings: Settings,
        state: FSMContext,
):
    method = get_method(message)
    _signatures = await Keyword.filter(
        session,
        Keyword.project_id == project.id,
        Keyword.type == KeywordType.SIGNATURE
    )
    if _signatures:
        if _signatures[0].keyword == '':
            _signatures.pop(0)
    action_type = ProjectAction.ADD_SIGNATURE if not _signatures else ProjectAction.DELETE_SIGNATURE
    if action_type == ProjectAction.ADD_SIGNATURE:
        text = l10n.project.signatures()
    else:
        text = l10n.project.keyword.delete.signature(
            signature=_signatures[0].keyword
        )
    await method(
        text,
        reply_markup=project_kbs.signatures(project.id, l10n, action_type)
    )


@router.callback_query(ProjectCallback.filter(F.action == ProjectAction.ADD_SIGNATURE), ProjectFilter())
async def add_signatures(
        message: types.CallbackQuery | types.Message,
        l10n: TranslatorRunner,
        project: Project,
        settings: Settings,
        user: User,
        state: FSMContext,
):
    method = get_method(message)

    if user.rate == Rates.STANDART:  # Опция тарифа PRO
        await method(
            l10n.payment.description.upgrade_info(),  # Эта опция доступна только на тарифе PRO
            reply_markup=payment_kbs.upgrade_subscription(l10n)
        )
        return

    await method(
        l10n.project.keyword.create.word(
            keyword_type=KeywordType.SIGNATURE.get_text(l10n)
        ),
        reply_markup=common_kbs.custom_back(
            l10n,
            callback_data=ProjectCallback(
                id=project.id,
                action=ProjectAction.SIGNATURES
            )
        )
    )

    await state.clear()
    await state.update_data(project_id=project.id)
    await state.set_state('signature')


@router.message(StateFilter('signature'))
async def set_signatures(
        message: types.Message,
        l10n: TranslatorRunner,
        settings: Settings,
        session: AsyncSession,
        account_dispatchers: dict[int, Dispatcher],
        state: FSMContext,
):
    method = get_method(message)
    data = await state.get_data()
    project_id = data['project_id']
    await state.clear()
    project = await Project.get(session, id=project_id)

    signature = await Keyword.filter(
        session,
        Keyword.project_id == project.id,
        Keyword.type == KeywordType.SIGNATURE
    )
    if signature:
        await session.delete(signature[0])
        await session.commit()

    signature = message.text.replace('<', '(').replace('>', ')')

    keyword = Keyword(
        project=project,
        type=KeywordType.SIGNATURE,
        keyword=signature,
        is_stop_word=False,
        is_username=False,
    )
    session.add(keyword)
    await session.commit()
    if project.account_id:
        dispatcher = account_dispatchers[project.account_id]
        await dispatcher.update_account(session)

    await signatures_handler(
        message,
        l10n,
        project,
        session,
        settings,
        state
    )


@router.callback_query(ProjectCallback.filter(F.action == ProjectAction.DELETE_SIGNATURE), ProjectFilter())
async def delete_signature(
        callback_query: types.CallbackQuery,
        l10n: TranslatorRunner,
        project: Project,
        settings: Settings,
        session: AsyncSession,
        account_dispatchers: dict[int, Dispatcher],
        state: FSMContext
):
    data = await state.get_data()
    key = f"project_sign_{project.id}"
    confirm = data.get(key)  # True/False

    if confirm:
        # Удаляем все подписи для данного проекта
        signatures_list = await Keyword.filter(
            session,
            Keyword.project_id == project.id,
            Keyword.type == KeywordType.SIGNATURE
        )
        for signature in signatures_list:
            logger.info(f"Удаляем подпись: {signature.keyword}")
            await session.delete(signature)
        await session.commit()

        # Очистка подписей в проекте
        project.keywords = [
            kw for kw in project.keywords if kw.type != KeywordType.SIGNATURE
        ]

        # Обновляем информацию в диспетчере аккаунтов, если нужно
        if project.account_id:
            dispatcher = account_dispatchers.get(project.account_id)
            if dispatcher:
                await dispatcher.update_account(session)

        # Отправляем сообщение о успешном удалении
        await callback_query.answer("✅")
        # Вызываем функцию signatures_handler после успешного удаления
        await signatures_handler(
            callback_query,
            l10n,
            project,
            session,
            settings,
            state
        )

    else:
        confirm_message = l10n.project.delete.confirm()
        if confirm_message:
            await callback_query.answer(confirm_message)
            await state.update_data({key: True})
        else:
            logger.error("Localization for confirmation message is missing.")
            await callback_query.answer("Please confirm the deletion.")


@router.callback_query(ProjectCallback.filter(F.action == ProjectAction.REPLACING_TEXT), ProjectFilter())
async def get_replacing_text(
        call: types.CallbackQuery | types.Message,
        l10n: TranslatorRunner,
        project: Project
):
    method = get_method(call)

    await method(
        l10n.project.replacing_text(),
        reply_markup=project_kbs.replacing_text(
            project,
            l10n,
        )
    )


@router.callback_query(ProjectCallback.filter(F.action == ProjectAction.ADD_REPLACING_TEXT), ProjectFilter())
async def add_replacing_text(
        call: types.CallbackQuery,
        l10n: TranslatorRunner,
        user: User,
        project: Project,
        state: FSMContext,
):
    await state.clear()
    method = get_method(call)

    if user.rate == Rates.STANDART:
        await method(
            l10n.payment.description.upgrade_info(), #Эта опция доступна только на тарифе PRO
            reply_markup=payment_kbs.upgrade_subscription(l10n)
        )
        return

    await method(
        l10n.project.replacing_text_1(),
        reply_markup=common_kbs.custom_back(
            l10n,
            callback_data=ProjectCallback(
                id=project.id,
                action=ProjectAction.REPLACING_TEXT
            )
        )
    )
    await state.update_data(project_id=project.id)
    await state.set_state('set_replacing_text-keyword')




@router.message(StateFilter('set_replacing_text-keyword'))
async def set_replacing_text_attr_keyword(
        message: types.Message,
        l10n: TranslatorRunner,
        state: FSMContext,
        session: AsyncSession
):
    method = get_method(message)
    data = await state.get_data()
    project_id = data.get('project_id')
    replacing_keyword = str(message.text.replace('<', '(').replace('>', ')')).strip()
    replacing_keyword = replacing_keyword.lower()
    replacing_keyword = replacing_keyword.capitalize()

    if len(replacing_keyword) > 100:
        await method(
            l10n.project.replacing_text.warning_long(), #'СЛИШОМ ДЛИННОЕ КЛЮЧЕВОЕ СЛОВО!
            reply_markup=common_kbs.custom_back(
                l10n,
                callback_data=ProjectCallback(
                    id=project_id,
                    action=ProjectAction.REPLACING_TEXT
                )
            )
        )
        return
    # Проверка дублирования ключевых слов только для типа "replacing"
    similar_keywords = await Keyword.filter(
        session,
        Keyword.project_id == project_id,
        Keyword.keyword == replacing_keyword,
        Keyword.type == KeywordType.REPLACING
    )

    if similar_keywords:
        await method(
            l10n.project.replacing_text.warning_dublicate(),  #'Данное ключеове слово уже есть - напишите другое,
            reply_markup=common_kbs.custom_back(
                l10n,
                callback_data=ProjectCallback(
                    id=project_id,
                    action=ProjectAction.REPLACING_TEXT
                )
            )
        )
        return

    await state.update_data(replacing_keyword=replacing_keyword)
    await state.set_state('set_replacing_text-text')

    await method(
        l10n.project.replacing_text_2(),
        reply_markup=project_kbs.replacing_text_attr_text(
            project_id=project_id,
            l10n=l10n
        )
    )


@router.message(StateFilter('set_replacing_text-text'))
async def set_replacing_text_attr_text(
        message: types.Message,
        l10n: TranslatorRunner,
        session: AsyncSession,
        account_dispatchers: dict[int, Dispatcher],
        state: FSMContext
):
    method = get_method(message)
    #_replacing_text = ' ' + str(message.text.replace('<', '(').replace('>', ')')) + ' '
    _replacing_text = str(message.text.replace('<', '(').replace('>', ')')).strip()

    data = await state.get_data()
    project_id = data.get('project_id')
    replacing_keyword = str(data.get('replacing_keyword'))

    if replacing_keyword == _replacing_text:
        await method(
            l10n.project.replacing_text.warning_dublicate(),
            reply_markup=project_kbs.replacing_text_attr_text(project_id, l10n)
        )
        return

    if len(_replacing_text) > 100:
        await method(
            l10n.project.replacing_text.warning_long(),
            reply_markup=project_kbs.replacing_text_attr_text(project_id, l10n)
        )
        return

    project = await Project.get(session, id=project_id)

    keyword = Keyword(
        project=project,
        type=KeywordType.REPLACING,
        keyword=replacing_keyword,
        replacing_text=_replacing_text,
        is_stop_word=False,
        is_username=False,
    )
    session.add(keyword)
    await session.commit()
    if project.account_id:
        dispatcher = account_dispatchers[project.account_id]
        await dispatcher.update_account(session)

    await get_replacing_text(
        message,
        l10n,
        project
    )
    await state.clear()


@router.callback_query(ProjectCallback.filter(F.action == ProjectAction.CONTINUE_SET_REPLACING_TEXT), ProjectFilter())
async def continue_replacing_text_attr_text(
        message: types.CallbackQuery | types.Message,
        l10n: TranslatorRunner,
        project: Project,
        session: AsyncSession,
        account_dispatchers: dict[int, Dispatcher],
        state: FSMContext,
):
    method = get_method(message)
    _replacing_text = None

    data = await state.get_data()
    project_id = data.get('project_id')
    replacing_keyword = data.get('replacing_keyword')

    project = await Project.get(session, id=project_id)

    keyword = Keyword(
        project=project,
        type=KeywordType.REPLACING,
        keyword=replacing_keyword,
        replacing_text=_replacing_text,
        is_stop_word=False,
        is_username=False,
    )
    session.add(keyword)
    await session.commit()
    if project.account_id:
        dispatcher = account_dispatchers[project.account_id]
        await dispatcher.update_account(session)

    await get_replacing_text(
        message,
        l10n,
        project
    )
    await state.clear()


@router.callback_query(ProjectCallback.filter(F.action == ProjectAction.DELETE_REPLACING_TEXT), ProjectFilter())
async def delete_replacing_text(
        message: types.CallbackQuery,
        l10n: TranslatorRunner,
        project: Project,
        session: AsyncSession,
        account_dispatchers: dict[int, Dispatcher],
        callback_data: ProjectCallback,
        state: FSMContext,
):
    data = await state.get_data()
    keyword_id = callback_data.data
    key = f"project_replacing_{project.id}_{keyword_id}"
    confirm = data.get(key)  # True/False

    if confirm:
        replacing = await Keyword.filter(
            session,
            Keyword.project_id == project.id,
            Keyword.type == KeywordType.REPLACING,
            Keyword.id == int(keyword_id)
        )
        if replacing:
            await session.delete(replacing[0])
            await session.commit()

        if project.account_id:
            dispatcher = account_dispatchers[project.account_id]
            await dispatcher.update_account(session)

        project = await Project.get(session, id=project.id)
        project_keywords = []
        for keyword in project.keywords:
            if keyword.keyword == replacing[0].keyword:
                continue
            project_keywords.append(keyword)
        project.keywords = project_keywords

        await get_replacing_text(
            message,
            l10n,
            project
        )
        await state.clear()
    else:
        await message.answer(l10n.project.delete.confirm())
        await state.update_data({key: True})


