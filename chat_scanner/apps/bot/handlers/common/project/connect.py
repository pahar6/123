from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING

from aiogram import Router, types, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger
from pyrogram.errors import UserAlreadyParticipant

from pyrogram.types import Message
from pyrogram.raw import functions, types

from sqlalchemy.ext.asyncio import AsyncSession

from chat_scanner.apps.account.dispatcher import Dispatcher
from chat_scanner.apps.bot.callback_data.project import ProjectCallback, ProjectAction
from chat_scanner.apps.bot.filters.project import ProjectFilter
from chat_scanner.apps.bot.keyboards.common import project_kbs
from chat_scanner.db.models import ProjectChat, Account
from chat_scanner.db.models.project import Project

if TYPE_CHECKING:
    from chat_scanner.locales.stubs.ru.stub import TranslatorRunner

router = Router()

timeouts = (
    1 * 60, 5 * 60, 10 * 60,
    30 * 60, 30 * 60, 30 * 60,
    1 * 60 * 60
)


async def send_connect_group_message(
        method: Callable,
        project: Project,
        l10n: TranslatorRunner
):
    # logger.warning(f'[SEND-CONNECT-GROUP-MESSAGE] Project: {project}; method: {method}')
    sender = project.sender.pretty() if project.sender else l10n.project.connect.sender.absent()
    receiver = project.receiver.pretty() if project.receiver else l10n.project.connect.sender.absent()
    # logger.warning(f'[SEND-CONNECT-GROUP-MESSAGE] SENDER: {sender}; RECEIVER: {receiver}')

    await method(
        text=l10n.project.connect(
            sender=sender,
            receiver=receiver,
            project_id=project.id,
        ),
        reply_markup=project_kbs.connect_groups(project, l10n)
    )


@router.callback_query(
    ProjectCallback.filter(F.action == ProjectAction.CONNECT_GROUPS),
    ProjectFilter()
)
async def connect_groups(
        call: types.CallbackQuery,
        l10n: TranslatorRunner,
        project: Project,
        state: FSMContext,
        bot: Bot,
        session: AsyncSession
):
    await state.update_data(
        project_id=project.id,
        last_message_id=call.message.message_id
    )
    await send_connect_group_message(call.message.edit_text, project, l10n)


@router.callback_query(
    ProjectCallback.filter(F.action == ProjectAction.CONNECT_SENDER),
    ProjectFilter()
)
async def connect_sender(
        call: types.CallbackQuery,
        bot: Bot,
        l10n: TranslatorRunner,
        project: Project,
        state: FSMContext,
):
    await state.update_data(project_id=project.id)
    await call.message.answer(
        l10n.project.connect.sender(),
    )
    await state.set_state("connect_sender")


async def _connect_from_invite(
        message: types.Message,
        l10n: TranslatorRunner,
        state: FSMContext,
        bot: Bot,
        session: AsyncSession,
        account_dispatchers: dict[int, Dispatcher],
        **kwargs,
):
    data = await state.get_data()
    project_id = data.get("project_id")
    project: Project = await Project.get(session, id=project_id)
    if not account_dispatchers:
        await message.answer(
            l10n.project.connect.sender.no_accounts()
        )
        return

    account = await Account.get_free_account(session, project)
    dispatcher = account_dispatchers[account.id]

    chat_id = message.text.strip()
    topic_id = None

    try:
        chat = await dispatcher.client.join_chat(chat_id=chat_id)
    except UserAlreadyParticipant as e:
        chat = await dispatcher.get_chat(message.text.strip())
    except Exception as e:
        if 'invite_request_sent' in str(e).lower():
            # Действия при отправки ссылки приглашения
            await message.answer(
                # l10n надо будет добавить,
                'В этот чат можно вступить только после одобрения заявки администратором. '
                'Юзербот ожидает одобрения, после чего можно настраивать проект дальше',
            )
            await state.set_state(None)
            for i in range(0, 55):  # 1 - 54
                timeout = timeouts[i if i < len(timeouts) else -1]
                await asyncio.sleep(timeout)
                project = await Project.get_or_none(session, id=project_id)

                if not project:  # Если проект уже удален
                    return None, None

                if project.sender_id:  # Если у проекта уже есть отправитель
                    return None, None

                try:
                    chat = await dispatcher.get_chat(message.text.strip())  # Если телеграм отдал данные чата
                    break
                except Exception:  # Если до сих пор не приняли заявку на вступление в чат
                    continue
        else:
            logger.warning(f"[CONNECTING-ERROR] {e}")
            return None, None
    project.account_id = account.id
    project_chat, _ = await ProjectChat.get_or_create_from_chat(session, chat, topic_id)

    if project.sender_id == project_chat.id and project_chat.topic_id == topic_id:
        await message.answer(
            l10n.project.connect.sender.already_set(name=project.name)
        )
        return
    project.sender_id = project_chat.id
    return dispatcher, account


async def _default_connect(
        message: types.Message,
        chat_id: str,
        project: Project,
        l10n: TranslatorRunner,
        session: AsyncSession,
        account_dispatchers: dict[int, Dispatcher],
        **kwargs,
):
    if not account_dispatchers:
        await message.answer(
            l10n.project.connect.sender.no_accounts()
        )
        return

    min_projects_account = await Account.get_account_with_min_projects(session)
    if not min_projects_account:
        await message.answer(
            l10n.project.connect.sender.no_accounts()
        )
        return
    min_projects_dispatcher = account_dispatchers[min_projects_account.id]

    topic_id = None
    if '/' in chat_id and chat_id.split('/')[1].isdigit():
        topic_id = int(chat_id.split('/')[1])
        chat_id = chat_id.split('/')[0]

    try:
        chat = await min_projects_dispatcher.get_chat(chat_id)
        logger.warning(str(chat))
    except Exception as e:
        logger.warning(e)
        await message.answer(
            l10n.project.connect.sender.can_not_get_chat()
        )
        return
    project_chat, _ = await ProjectChat.get_or_create_from_chat(session, chat, topic_id)

    if project.sender_id == project_chat.id and project_chat.topic_id == topic_id:
        await message.answer(
            l10n.project.connect.sender.already_set(name=project.name)
        )
        return

    project.sender_id = project_chat.id
    project.sender = project_chat
    # account = await Account.get_free_account(session, project)
    project.account_id = min_projects_account.id
    dispatcher = account_dispatchers[min_projects_account.id]
    try:
        await dispatcher.client.join_chat(chat_id=project.get_sender_chat_id())
    except UserAlreadyParticipant as e:
        pass
    except Exception as e:
        if 'invite_request_sent' in str(e).lower():
            # Действия при отправки ссылки приглашения
            await message.answer(
                # l10n надо будет добавить (второй - прошлый сюда не подойдет),
                'В этот чат можно вступить только после одобрения заявки администратором. '
                'Как только администратор примит заявку проект станет активным и будет пересылать посты',
            )
        else:
            logger.warning(f"[CONNECTING-ERROR] {e}")
            return None, None
    return dispatcher, min_projects_account


@router.message(StateFilter("connect_sender"))
async def connect_sender(
        message: types.Message,
        bot: Bot,
        l10n: TranslatorRunner,
        state: FSMContext,
        session: AsyncSession,
        account_dispatchers: dict[int, Dispatcher],
):
    try:
        await message.answer(l10n.project.connect.sender.processing())
        data = await state.get_data()
        project_id = data.get("project_id")
        project: Project = await Project.get(session, id=project_id)

        # Шаг 1: Удаляем все пробелы
        text = message.text.replace(" ", "")

        # Шаг 2: Удаляем "https://t.me/"
        if text.startswith("https://t.me/"):
            text = text[len("https://t.me/"):]

        # Шаг 3: Удаляем последний слеш, если он есть
        if text.endswith("/"):
            text = text[:-1]
        chat_id = text

        if chat_id.startswith("+"):
            logger.info(f"Подключаемся по ссылке приглашению: {chat_id}")
            is_connect = await _connect_from_invite(**locals())

        else:
            logger.info(f"Подключаемся по ссылке: {chat_id}")
            is_connect = await _default_connect(**locals())

        if not is_connect:
            return

        dispatcher, account = is_connect
        await session.commit()
        await session.refresh(account)
        await session.refresh(project)
        dispatcher.account = account
        await dispatcher.update_account(session)
        success_message = l10n.project.connect.sender.success(name=project.name)
        await message.answer(success_message)
        await send_connect_group_message(message.answer, project, l10n)

    except Exception as e:
        logger.exception(e)
        await message.answer(
            l10n.project.connect.sender.error()
        )
