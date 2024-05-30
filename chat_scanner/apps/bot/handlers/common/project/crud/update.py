from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from chat_scanner.apps.account.dispatcher import Dispatcher
from chat_scanner.apps.bot.callback_data.base_callback import Action
from chat_scanner.apps.bot.callback_data.project import ProjectCallback, ProjectAction
from chat_scanner.apps.bot.filters.project import ProjectFilter
from chat_scanner.apps.bot.handlers.common.project.crud.get import get_project, get_detect_duplicates, get_response, get_deferred_messages
from chat_scanner.apps.bot.keyboards.common import project_kbs, payment_kbs
from chat_scanner.config import Settings
from chat_scanner.db.models.project.project import Project
from chat_scanner.db.models.user import User
from chat_scanner.db.models import Rates


if TYPE_CHECKING:
    from chat_scanner.locales.stubs.ru.stub import TranslatorRunner

router = Router()


async def dispatchers_update(
        project: Project,
        session: AsyncSession,
        account_dispatchers: dict[int, Dispatcher]
):
    if project.account_id and project.account_id in account_dispatchers:
        dispatcher = account_dispatchers[project.account_id]
        await dispatcher.update_account(session)

@router.callback_query(
    ProjectCallback.filter(
        (F.action == Action.UPDATE) &
        (F.data == "name")
    ),
    ProjectFilter()
)
async def update_project_name(
        call: types.CallbackQuery,
        l10n: TranslatorRunner,
        project: Project,
        state: FSMContext
):
    await state.update_data(project_id=project.id)
    await call.message.edit_text(
        l10n.project.name(),
        reply_markup=project_kbs.update_project_name(project.id, l10n)
    )
    await state.set_state("update_project_name")


@router.message(StateFilter("update_project_name"))
async def update_project_name_handler(
        message: types.Message,
        l10n: TranslatorRunner,
        state: FSMContext,
        session: AsyncSession,
        user: User
):
    data = await state.get_data()
    project_id: int = data["project_id"]
    project = await Project.get(session, id=project_id)
    project.name = message.text.strip()
    await session.commit()
    await message.answer(l10n.project.name.updated())

    await get_project(message, l10n, project, state, user)
    await state.clear()


@router.callback_query(
    ProjectCallback.filter(F.action == ProjectAction.SWITCH),
    ProjectFilter()
)
async def switch_project_active(
        call: types.CallbackQuery,
        l10n: TranslatorRunner,
        callback_data: ProjectCallback,
        project: Project,
        session: AsyncSession,
        settings: Settings,
        account_dispatchers: dict[int, Dispatcher],
        state: FSMContext,
        user: User  # Добавляем пользователя
):
    attr = callback_data.data
    if attr == "forward_all_messages":
        if user.rate == Rates.STANDART:
            await call.message.edit_text(
                l10n.payment.description.upgrade_info(),
                reply_markup=payment_kbs.upgrade_subscription(l10n)
            )
            return
    if 'time_sending' in str(attr):
        attr_data = str(attr).split('=')
        attr, value = attr_data[0], int(attr_data[1])
        if hasattr(project.settings, attr):  # Если в сеттингах проекта существует аттрибут time_sending
            if value == getattr(project.settings, attr):  # если пользваотель кликнул повторно на кнорпку
                setattr(project.settings, attr, 0)  # Передаем в базу отложку постов = 0  отправь
            else:  # В случае если пользователь нажал на другую кнопку
                setattr(project.settings, attr, value)  # Устанавливаем параметру time_sending значение кнопки (30/60...)
    else:
        if hasattr(project.settings, attr):
            setattr(project.settings, attr, not getattr(project.settings, attr))
        else:
            setattr(project, attr, not getattr(project, attr))

    await session.commit()

    await dispatchers_update(project, session, account_dispatchers)

    if "detect" in callback_data.data:
        await get_detect_duplicates(call, l10n, project, settings, state)
    elif "include" in callback_data.data:
        await get_response(call, l10n, project, settings, state)
    elif 'time_sending' in str(callback_data.data):
        await get_deferred_messages(call, l10n, project)
    else:
        await get_project(call, l10n, project, state, user) #я добавил юзер


