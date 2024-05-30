from __future__ import annotations
from __future__ import annotations

import asyncio
from contextlib import suppress
from functools import partial
from typing import TYPE_CHECKING, Optional

from pyrogram.raw import functions

from aiogram import Router, types, Bot, F
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import ChatMemberUpdatedFilter, ADMINISTRATOR, Command, StateFilter
from aiogram.filters import CommandStart, CommandObject
from chat_scanner.apps.bot.callback_data.project import ProjectCallback, ProjectAction
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from chat_scanner.apps.account.dispatcher import Dispatcher
from chat_scanner.apps.bot.handlers.common.project.connect import send_connect_group_message
from chat_scanner.apps.bot.handlers.common.project.crud.update import dispatchers_update
from chat_scanner.config import Settings
from chat_scanner.config.config import IncludeSupportMessage
from chat_scanner.apps.bot.keyboards.common import project_kbs
from chat_scanner.db.models import User, Project, ProjectChat, Account


from loguru import logger
from datetime import datetime

if TYPE_CHECKING:
    from chat_scanner.locales.stubs.ru.stub import TranslatorRunner

router = Router()


# @router.message(CommandStart(deep_link=True))
# async def deep_start(
#         message: types.Message,
#         bot: Bot,
#         command: CommandObject,
#         session: AsyncSession,
#         user: User,
#         l10n: TranslatorRunner,
#         state: FSMContext
# ):
#     # logger.warning(f'[DEEPLINK-START] Message: {message}')

@router.channel_post(Command("connect"))
async def connect_channel(
        message: types.Message,
        bot: Bot,
        settings: Settings,
        command: CommandObject,
        session: AsyncSession,
        l10n: TranslatorRunner,
        account_dispatchers: dict[int, Dispatcher],
):
    # logger.warning(f'[RECEIVER-CONNECT_CHANNEL] Time use: {datetime.now()}')
    with suppress(TelegramAPIError):
        await message.delete()

    try:
        project_id = int(command.args.replace("⁩", "").replace("⁨", "").strip())
    except ValueError:
        return

    project: Optional[Project] = await session.get(Project, project_id)
    if not project:
        return

    project, _ = await _connect_group(bot, message.chat, project_id, session, l10n)
    if not project:
        return

    await session.commit()
    await session.refresh(project)

    await dispatchers_update(project, session, account_dispatchers)
    method = partial(bot.send_message, chat_id=project.user_id)
    await send_connect_group_message(method, project, l10n)


@router.message(F.chat.type != "private", Command("connect"))
async def connect_group(
        message: types.Message,
        bot: Bot,
        settings: Settings,
        command: CommandObject,
        session: AsyncSession,
        l10n: TranslatorRunner,
        account_dispatchers: dict[int, Dispatcher],
        state: FSMContext,
):
    # logger.warning(f'[RECEIVER-CONNECT_GROUP] Tim use: {datetime.now()}')
    if not command.args:
        await bot.send_message(message.chat.id, l10n.project.connect.receiver.not_found())
        return
    project_id = command.args.replace("⁩", "").replace("⁨", "").strip()
    if not project_id or not project_id.isdigit():
        print(command.args)
        await bot.send_message(message.chat.id, l10n.project.connect.receiver.not_found())
        return

    project_id = int(project_id)
    if project_id > 2147483647:
        await bot.send_message(message.chat.id, l10n.project.connect.receiver.not_found())
        return

    project: Project = await session.get(Project, project_id)
    if not project:
        await bot.send_message(message.chat.id, l10n.project.not_found())
        return

    if project.user_id != message.from_user.id:
        chat_members = await bot.get_chat_administrators(message.chat.id)
        if not any(chat_member.user.id == project.user_id for chat_member in chat_members):
            await bot.send_message(message.chat.id, l10n.project.connect.receiver.not_owner())
            return

    project, _ = await _connect_group(bot, message.chat, project_id, session, l10n)
    if not project:
        return
    await session.commit()
    await session.refresh(project)
    await dispatchers_update(project, session, account_dispatchers)
    method = partial(bot.send_message, chat_id=project.user_id)
    await send_connect_group_message(method, project, l10n)


async def _connect_group(
        bot: Bot,
        chat: types.Chat | str,
        project_id: int,
        session: AsyncSession,
        l10n: TranslatorRunner,
        topic_id: int | None = None
) -> tuple[Project, ProjectChat] | tuple[None, None]:
    # logger.warning(f'[RECEIVER-_CONNECT_GROUP] Time use: {datetime.now()}, chat: {chat}, chat-type: {type(chat)}')

    if type(chat) is str:
        chat_id = chat
        chat = await bot.get_chat(chat_id)
    chat_title, chat_domain, chat_id, chat_type = chat.title, chat.username, chat.id, chat.type
    receiver_chat_id = int(f"{chat_id}{topic_id}") if topic_id else chat_id
    project_chat, _ = await ProjectChat.get_or_create(
        session,
        id=receiver_chat_id,  # **kwargs
        defaults=dict(
            title=chat_title,
            username=chat_domain,
            type=chat_type,
        )
    )

    project: Project = await session.get(Project, project_id)
    if not project:
        await bot.send_message(chat.id, l10n.project.not_found())
        return None, None

    if str(project.receiver_id) == str(receiver_chat_id):
        await bot.send_message(
            chat_id,
            l10n.project.connect.receiver.already_set(name=project.name)
        )
        return None, None

    if topic_id:
        project_chat.topic_id = topic_id

    project.receiver = project_chat
    if not project.account_id:
        account = await Account.get_account_with_min_projects(session)
        project.account_id = account.id

    success_message = l10n.project.connect.receiver.success(name=project.name)
    for chat in (chat_id, project.user_id):
        await bot.send_message(
            chat,
            success_message
        )

    if not project or not project_chat:
        return None, None
    return project, project_chat


@router.callback_query(
    ProjectCallback.filter(F.action == ProjectAction.CHOOSE_RECEIVER)  # Нажали на кнопку выбора подключателя
) 
async def choose_receiver(
        update: types.CallbackQuery,
        l10n: TranslatorRunner,
        session: AsyncSession,
        callback_data: ProjectCallback,
        state: FSMContext
):
    # logger.warning(f'[CHOOSE-RECEIVER] Started')
    current_state = await state.get_state()
    if current_state == 'waiting_forum_receiver':
        await state.set_state(None)
    message = str(l10n.project.connect.instruction.instruction())

    user_id = callback_data.data  # Return in project_kbs -> connect_groups
    user_projects = await Project.filter(
        session,
        Project.user_id == int(user_id),
        Project.receiver_id != None
    )
    projects = []
    # status, user_projects = await get_user_projects(int(user_id), session)
    # logger.warning(f'[STATUS] Status: {status}; projects: {user_projects}')
    for user_project in user_projects:
        try:
            p_id = user_project.id
            p_receiver_id = user_project.receiver.id
            chat_type = user_project.receiver.type
            pretty_receiver = user_project.receiver.pretty() + f" | {chat_type}"  # TITLE | DOMAIN | ID | TYPE
            # logger.warning(f"[PRETTY-RECEIVER] Receiver: {pretty_receiver}")
            projects.append((p_id, p_receiver_id, pretty_receiver))
        except Exception as error:
            logger.exception(f"[COLLECT-USER-PROJECT-ERROR] ERROR: {error}")
    # logger.warning(f'[PROJECTS] Projects: {projects}')

    await update.message.edit_text(
        text=message,
        reply_markup=project_kbs.choose_connect_groups(
            l10n=l10n,
            project_id=callback_data.id,
            projects=projects
        )
    )

@router.callback_query(
    ProjectCallback.filter(F.action == ProjectAction.CONNECT_FORUM)
)
async def _wait_project_receiver_topic_id(
        update: types.CallbackQuery,
        l10n: TranslatorRunner,
        state: FSMContext,
        callback_data: ProjectCallback
):
    await state.set_state('waiting_forum_receiver')
    project_id = int(callback_data.id)
    kb = project_kbs.choose_forum(l10n, project_id, update.from_user.id)
    await update.message.edit_text(
        text=l10n.project.connect.receiver_forum(),
        reply_markup=kb
    )


@router.message(
    StateFilter('set_receiver_topic_id')
)
async def _set_project_topic_id(
        message: types.Message,
        bot: Bot,
        session: AsyncSession,
        l10n: TranslatorRunner,
        state: FSMContext
):
    data = await state.get_data()
    project_id = data.get('project_id')
    chat_id = data.get('chat_id')
    user_id = data.get('user_id')

    topic_id = None
    if not message.text:
        await state.clear()
        return

    if message.text.isdigit():  # Отправлен чисто идентификатор
        topic_id = int(message.text)
    elif '/' in message.text:  # Отправлена ссылка на миничат
        parts = message.text.split('/')
        if len(parts) == 2:
            topic_id = int(parts[1])
        else:
            topic_id = int(parts[-1])

    else:  # Отправлено сообщение не по формату
        pass

    if not topic_id:  # Не смогли спарсить топик-айди из ответа пользователя
        await message.answer(
            text=l10n.project.connect.receiver.minichat_not_found() #f'Неверный формат ссылки/идентификатора миничата\nГруппа-получатель не подключена!'
        )
        await state.clear()
        return

    topic_id_status = False
    try:
        if topic_id != 1:
            await bot.send_message(
                chat_id=chat_id,
                message_thread_id=topic_id,
                text=l10n.project.connect.sender.minichat_success() #'Миничат подключен к чату-отправителю!'
            )
            topic_id_status = True
        else:
            await bot.send_message(
                chat_id=chat_id,
                text=l10n.project.connect.sender.minichat_success() #'Миничат подключен к чату-отправителю!'
            )
            topic_id_status = True
    except Exception as error:
        logger.warning(f"[SEND-MESSAGE-ERROR] {error}")

    if topic_id_status:  # Получилось оптравить сообщение в миничат (бот подключен к чату и топик-айди существует)
        chat = await bot.get_chat(chat_id)
        project, project_chat = await _connect_group(
            bot=bot,
            chat=chat,
            project_id=project_id,
            session=session,
            l10n=l10n,
            topic_id=topic_id
        )
        await session.commit()
        await session.refresh(project)

        await bot.send_message(
            chat_id=project.user_id,
            text=l10n.project.connect.receiver.minichat_success() #'Миничат успешно добавлен к группе-поулчателю'
        )
        await send_connect_group_message(
            message.answer,
            project,
            l10n
        )

    await state.clear()


@router.callback_query(  # Случай 2
    ProjectCallback.filter(F.action == ProjectAction.CONNECT_RECEIVER)  # Нажали на кнопку повторного подключения к чату
)
async def _set_project_receiver_by_callback_connect_receiver(
        update: types.ChatMemberUpdated,
        bot: Bot,
        settings: Settings,
        session: AsyncSession,
        l10n: TranslatorRunner,
        state: FSMContext,
        account_dispatchers: dict[int, Dispatcher],
        callback_data: ProjectCallback | None
):
    # logger.warning(f"[SET-PROJECT-RECEIVER-BY-CALLBACK-CONNECT-RECEIVER] update: {update}")
    await set_project_receiver(
        update=update,
        bot=bot,
        settings=settings,
        session=session,
        l10n=l10n,
        state=state,
        account_dispatchers=account_dispatchers,
        callback_data=callback_data
    )


@router.my_chat_member(  # Случай 3
    ChatMemberUpdatedFilter(ADMINISTRATOR)  # Бота добавили в группу и передали права админа
)
async def _set_project_receiver_by_chat_member_update(
        update: types.ChatMemberUpdated,
        bot: Bot,
        settings: Settings,
        session: AsyncSession,
        l10n: TranslatorRunner,
        state: FSMContext,
        account_dispatchers: dict[int, Dispatcher]
):
    # logger.warning(f"[SET-PROJECT-RECEIVER-BY-CHAT-MEMBER-UPDATE] update: {update}")
    await set_project_receiver(
        update=update,
        bot=bot,
        settings=settings,
        session=session,
        l10n=l10n,
        state=state,
        account_dispatchers=account_dispatchers,
        callback_data=None
    )


async def set_project_receiver(  # Основная функция обработки подключения RECEIVER к чату
        update: types.ChatMemberUpdated,
        bot: Bot,
        settings: Settings,
        session: AsyncSession,
        l10n: TranslatorRunner,
        state: FSMContext,
        account_dispatchers: dict[int, Dispatcher],
        callback_data: ProjectCallback | None
):
    #logger.info(str(update))
    logger.info(f'[RECEIVER-SET_PROJECT_RECEIVER] Time use: {datetime.now()}')
    data = await state.get_data()
    # logger.warning(f'[RECEIVER-SET_PROJECT_RECEIVER] Data: {data}')
    project_id: int = data['project_id']
    chat_id = None
    topic_id = None
    if callback_data:
        chat_id_data: str = str(callback_data.data)
        if '/' in chat_id_data:
            chat_id_data: list[str] = chat_id_data.split('/')
            chat_id = int(chat_id_data[0])
            topic_id = int(chat_id_data[1])

    if not project_id:
        return

    current_state = await state.get_state()

    if current_state != 'waiting_forum_receiver' and not topic_id:  # Если не ждем выбор форума и не кликнули на подкл.
        if callback_data:
            chat_id = str(callback_data.data).replace(' ', '')
            chat = await bot.get_chat(chat_id)
            project, project_chat = await _connect_group(bot, chat, project_id, session, l10n)
        else:
            project, project_chat = await _connect_group(bot, update.chat, project_id, session, l10n)
        if not project:
            return

        await state.clear()
        await session.commit()
        await session.refresh(project)
        await dispatchers_update(project, session, account_dispatchers)

        last_message_id = data.get("last_message_id")
        method = partial(bot.send_message, chat_id=project.user_id)
        await send_connect_group_message(method, project, l10n)

    else:
        await state.update_data(project_id=project_id)
        project = await session.get(Project, project_id)
        await state.update_data(chat_id=update.chat.id if not callback_data else chat_id)
        user_id = project.user_id
        await state.update_data(user_id=user_id)
        await state.set_state('set_receiver_topic_id')
        await bot.send_message(
            chat_id=update.from_user.id,
            text=l10n.project.connect.receiver.input_id() #введите ссылку на миничат
        )


@router.message(F.chat.type != "private")
async def group_message(message: types.Message, bot: Bot, settings: Settings):
    # logger.warning(f'[RECEIVER-GROUP-MESSAGE] Time use: {datetime.now()}')
    if message.chat.id != settings.bot.SUPPORT_CHAT_ID:
        return

    if message.reply_to_message:
        to_user_message = IncludeSupportMessage(message_id=message.reply_to_message.message_id, chat_id=message.chat.id)
        if from_user_message := settings.bot.SUPPORT_MESSAGES.get(to_user_message):
            if message.photo:
                file_id = message.photo[-1].file_id
                await bot.send_photo(photo=file_id,
                                     chat_id=from_user_message.chat_id,
                                     caption=message.caption,
                                     reply_to_message_id=from_user_message.message_id)
            else:
                await bot.send_message(
                    chat_id=from_user_message.chat_id,
                    text=message.text,
                    reply_to_message_id=from_user_message.message_id,
                )
