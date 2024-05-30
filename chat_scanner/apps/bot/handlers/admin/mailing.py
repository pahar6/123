import asyncio

from aiogram import Router, types, Bot
from aiogram.filters import Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils import markdown as md
from pyrogram.raw.functions.messages import DeleteHistory
from pyrogram.raw import functions
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...callback_data.base_callback import MailingAction
from ...keyboards.admin import admin_kbs
from ...keyboards.common import common_kbs
from .....db.models import User
from .....db.requests.base import remove_full_user_data

from chat_scanner.db.models.project.project import Project
from chat_scanner.apps.account.dispatcher import Dispatcher


router = Router()


@router.callback_query(Text("mailing"))
async def mailing(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.message.answer(
        "Кого будем рассылать?",
        reply_markup=admin_kbs.mailing_choose(),
    )


@router.callback_query(Text(MailingAction.USER))
async def mailing_user(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    await state.clear()
    await call.message.answer(
        "Введите id или username пользователя",
        reply_markup=common_kbs.custom_back_kb(cb="admin")
    )
    await state.update_data(action=call.data)
    await state.set_state("mailing_user")


@router.message(StateFilter("mailing_user"))
async def mailing_user_send(message: types.Message, session: AsyncSession, bot: Bot, state: FSMContext):
    if message.text.isdigit():
        user_id = int(message.text)
        user = await User.get(session, id=user_id)
    else:
        user = await User.get(session, username=message.text)
    if not user:
        await message.answer("Пользователь не найден")
        return
    await message.answer(
        "Напишите или перешлите сообщение, которое хотите разослать.",
        reply_markup=common_kbs.custom_back_kb(cb="admin")
    )
    await state.update_data(user_id=user.id)
    await state.set_state("mailing")


@router.callback_query(Text(MailingAction.ALL))
@router.callback_query(Text(MailingAction.SUBSCRIBED))
@router.callback_query(Text(MailingAction.EXPIRED))
async def mailing_all(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer(
        "Напишите или перешлите сообщение, которое хотите разослать.",
        reply_markup=common_kbs.custom_back_kb(cb="admin")
    )
    await state.update_data(action=call.data)
    await state.set_state("mailing")


@router.message(StateFilter("mailing"))
async def mailing_send(message: types.Message, session: AsyncSession, bot: Bot, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    action = data.get("action")
    user_id = data.get("user_id")
    if action == MailingAction.USER:
        users = [await User.get(session, id=user_id)]
    elif action == MailingAction.ALL:
        users = await User.all(session)
    elif action == MailingAction.SUBSCRIBED:
        # user subsc duration greater than 0
        results = await session.execute(select(User).where(User.subscription_duration > 0))
        users = results.scalars().unique().all()
    elif action == MailingAction.EXPIRED:
        # user subsc duration less or equal 0
        results = await session.execute(select(User).where(User.subscription_duration <= 0))
        users = results.scalars().unique().all()
    else:
        logger.error("Unknown mailing action: {}", action)
        await message.answer("Произошла ошибка")
        return
    time_emoji1 = "⏳ In progress"
    time_emoji2 = "⌛ In progress"
    done_emoji = "✅ Done"
    current_emoji = time_emoji1

    status_template = f"📨 Total: {{}}\n" \
                      f"✅ Success: {{}}\n" \
                      f"🚫 Failed: {{}}\n\n" \
                      f"{{}}\n"
    status_message = await message.answer(status_template.format(0, 0, 0, current_emoji))
    success = 0
    failed = 0

    async def mailings_status_updated():
        while True:
            try:
                await asyncio.sleep(5)
                nonlocal current_emoji
                current_emoji = time_emoji1 if current_emoji == time_emoji2 else time_emoji2
                await status_message.edit_text(
                    status_template.format(
                        md.hcode(success + failed),
                        md.hcode(success),
                        md.hcode(failed),
                        current_emoji
                    )
                )
            except Exception as status_change_error:
                logger.warning(f"[MAILING] Status-change-error: {status_change_error}")

    task = asyncio.create_task(mailings_status_updated())
    action_errors = []
    ignore_errors = [
        'peer_id_invalid',
        'user is deactivated',
        'chat not found',
        'bot was blocked by the user',
        'user_is_bot'
    ]
    # copy message
    for num, user in enumerate(users, 1):
        # === Проверка на то можем ли мы отправлять события пользователю ====
        # Цикл будет повторяться до тех пор пока мы не узнаем заблокировал нас пользователь или нет
        # На то чтобы это узнать у нас будет 3 попытки на 1 пользователя
        # Если мы не узнаем за 3 попытки заблокированы ли мы пользователем - то перейдем к следующему пользователю
        repeats = 0
        success_flag = False

        # logger.warning(f'[MAILING] UserId-mailing: {user.id}')

        while True:
            try:
                await bot.send_chat_action(user.id, action='typing')  # Отправить экшн печаатет...
                success_flag = True
                break
            except Exception as error:
                # logger.warning(f"[MAILING] Bad mailing ({user.id}) with error: {error}")
                # if any([action_error in str(error).lower() for action_error in
                #         action_errors]):  # Если бот заблокирован пользователем, то
                #     failed += 1  # Добавить 1 к ошибкам отправки
                #     # Удалить все данные пользователя который заблокировал бота и перейти к следующему
                #     await remove_full_user_data(session=session, user_id=user.id)
                #     break

                # Если ошибка из разряда IGNORE-ERRORS - то переходим к следующему пользователю
                if any([ignore_error in str(error).lower() for ignore_error in ignore_errors]):
                    failed += 1
                    break
                else:  # Если неизвестная ошибка то взять паузу на 2 минуты (пример оишкби - слишком частые запросы)
                    repeats += 1
                    # logger.warning(
                    #     f"Undetected error "
                    #     f"(try: {repeats}) in mailing "
                    #     f"from telegram: {error}\n\n"
                    #     f"Data: id: {user.id}"
                    # )
                    await message.answer(
                        f"Undetected error "
                        f"(try: {repeats}) in mailing "
                        f"from telegram: {str(error).replace('<', '-')}\n\n"
                        f"Data: id: {user.id}"
                    )
                    if repeats >= 2:
                        break
                    await asyncio.sleep(60 * 2)  # В случае если телега отдала другую ошибку - то 2 мин перерыва

        if not success_flag:  # Если мы не можем связаться с пользователем - то перейти к обработке следующего
            continue

        try:
            await bot.copy_message(
                user.id,
                message.chat.id,
                message.message_id,
            )
            success += 1
        except Exception as e:
            # logger.warning(f"[MAILING] Error while sending message to {user.id}: {e}")
            failed += 1
        await asyncio.sleep(0.17)
    task.cancel()
    try:
        await status_message.edit_text(
            status_template.format(
                md.hcode(success + failed),
                md.hcode(success),
                md.hcode(failed),
                done_emoji,
            )
        )
    except Exception as error:
        pass
        # logger.warning(f"[MAILING] Edit-text-error: {error}")  отправляй

    await message.answer(
        f'Рассылка завершена:\n\n'
        f'Total: {success + failed}\n'
        f'Succes: {success}\n'
        f'Failed: {failed}'
    )
    # await state.clear()


@router.callback_query(Text(MailingAction.DELETE_BLOCKED))
async def delete_block_users(
        call: types.CallbackQuery,
        session: AsyncSession,
        bot: Bot,
        account_dispatchers: dict[int, Dispatcher]

):
    """Удаление пользователей которым не получается отправить action TYPING"""

    blocked = 0
    checked = 0
    template = f"Проверка запускается...\n\nПроверено пользователей: {checked}\nЗаблокировано пользователей: {blocked}"
    msg = await bot.send_message(
        call.from_user.id,
        template
    )
    users = await User.all(session)
    action_errors = [
        'user is deactivated',
        'chat not found',
        'bot was blocked by the user',
        'user_is_bot',
        'peer_id_invalid'
    ]
    ignore_errors = []
    for num, user in enumerate(users, 1):
        repeats = 0
        success_flag = False
        checked += 1

        if checked % 10 == 0 or checked == 1:  # Обновлять данные о проверка каждые 10 провереных пользователей
            await msg.edit_text(
                f"Проверка в процессее...\n\n"
                f"Пользователей проверено: {checked}\n"
                f"Пользователей заблокировано: {blocked}"
            )

        while True:
            try:
                await bot.send_chat_action(user.id, action='typing')  # Отправить экшн печаатет...
                success_flag = True
                break
            except Exception as error:
                if any([action_error in str(error).lower() for action_error in action_errors]):  # Если бот заблокирован пользователем, то
                    # Удалить все данные пользователя который заблокировал бота и перейти к следующему
                    try:
                        status = await remove_full_user_data(
                            session=session,
                            user_id=user.id,
                            bot=bot,
                            account_dispatchers=account_dispatchers,
                            remove_user=True
                        )
                        if status:
                            blocked += 1  # Добавить 1 к ошибкам отправки
                    except Exception:
                        pass
                    #  await bot.send_message(
                    #     call.from_user.id,
                    #     f"User is blocked: {user.id}\nStatus: {status}"
                    # )
                    break
                # Если ошибка из разряда IGNORE-ERRORS - то переходим к следующему пользователю
                elif any([ignore_error in str(error).lower() for ignore_error in ignore_errors]):
                    break
                else:
                    repeats += 1
                    # logger.warning(
                    #     f"Undetected error "
                    #     f"(try: {repeats}) in mailing "
                    #     f"from telegram: {error}\n\n"
                    #     f"Data: id: {user.id}"
                    # )
                    await bot.send_message(
                        call.from_user.id,
                        f"Undetected error "
                        f"(try: {repeats}) in mailing "
                        f"from telegram: {str(error).replace('<', '-')}\n\n"
                        f"Data: id: {user.id}"
                    )
                    if repeats >= 2:
                        break
                    await asyncio.sleep(60 * 2)  # В случае если телега отдала другую ошибку - то 2 мин перерыва

        if not success_flag:  # Если мы не можем связаться с пользователем - то перейти к обработке следующего
            continue

    await msg.edit_text(
        f"Проверка завершена\n\n"
        f"Пользователей проверено: {checked}\n"
        f"Пользователей заблокировано: {blocked}"
    )


@router.callback_query(Text(MailingAction.EXIT_FROM_CHAT))  #функция которую я реализовал, но она не работает
async def exit_from_inactive_chats(
        call: types.CallbackQuery,
        session: AsyncSession,
        user: User,
        bot: Bot,
        account_dispatchers: dict[int, Dispatcher]
):
    logger.warning(f'[AUTO-EXIT] function starting')

    # Переменные для отчета
    checked = 0
    exits_from_chats = 0
    failed_leaves = 0
    failed_exits = ''  # Список чатов, из которых не удалось выйти юзерботам

    # Подготовка сообщения для администратора
    msg = await bot.send_message(
        user.id,
        f"Проверка запускается...\n\n"
        f"Чатов проверено: {checked}\n"
        f"Чатов покинуто: {exits_from_chats}\n"
        f"Неудачных попыток выйти: {failed_leaves}"
    )

    # Проходимся по аккаунтам дипатчера
    accounts = sorted(list(account_dispatchers.keys()))
    i = 0
    for account_id, dispatcher in sorted(account_dispatchers.items()):
        i += 1
        async for dialog in dispatcher.client.get_dialogs():  # Проходимся по чатам аккаунта (юзербота)
            checked += 1
            # logger.warning(f'[DIALOG] id - {dialog.chat.id}') же
            await asyncio.sleep(0.13)
            # Получаем проекты с такимже диалогом в сендерах у юзербота
            dialog_type = str(dialog.chat.type).lower()
            topic_ids = []
            if 'supergroup' in dialog_type:
                chat = await dispatcher.client.resolve_peer(dialog.chat.id)
                try:
                    topics = await dispatcher.client.invoke(
                        functions.channels.GetForumTopics(
                            channel=chat,
                            offset_date=0,
                            offset_topic=0,
                            offset_id=0,
                            limit=0
                        )
                    )
                    if topics.count > 0:
                        for topic in topics.topics:
                            topic_id = topic.id
                            topic_ids.append(topic_id)
                except Exception:
                    pass

            if topic_ids:  # Если есть миничаты то собрать из базы все варианты данного чата с миничатами
                project_senders_with_dialog_id = []
                for topic_id in topic_ids:
                    project_senders_with_topic_dialog_id = await Project.filter(
                        session,
                        Project.sender_id == int(str(dialog.chat.id) + str(topic_id)),
                        Project.account_id == account_id,
                        # Project.is_general == False
                    )
                    if project_senders_with_topic_dialog_id:  # Если нашли в базе проект с данным миничатом
                        project_senders_with_dialog_id.extend(project_senders_with_topic_dialog_id)
                        break
            else:
                project_senders_with_dialog_id = await Project.filter(
                    session,
                    Project.sender_id == dialog.chat.id,
                    Project.account_id == account_id,
                    # Project.is_general == False
                )

            # logger.warning(f'[PROJECTS-DIALOG] dialog ({dialog.chat.id}), len ({len(project_senders_with_dialog_id)})')
            # Если такие проекты существуют или данный чат - это личная переписка - то пропустим этот диалог
            # Но если это бот - то заблокируем его и очистим переписку
            if project_senders_with_dialog_id or 'private' in dialog_type or 'bot' in dialog_type:
                if 'bot' in dialog_type:
                    # logger.warning(f'[BOT-DIALOG] {dialog}')
                    try:
                        try:
                            await dispatcher.client.block_user(dialog.chat.id)
                        except Exception:
                            pass
                        peer = await dispatcher.client.resolve_peer(dialog.chat.id)
                        await dispatcher.client.invoke(DeleteHistory(max_id=0, peer=peer))
                        exits_from_chats += 1
                    except Exception as error:
                        pass
                        # logger.warning(f"[DELETE-BOT] error: {error}")
                if checked % 10 == 0 or checked == 1:  # Обновлять данные о проверка каждые 10 провереных чатов
                    await msg.edit_text(
                        f"Проверка в процессе ({account_id}/{i}/{len(accounts)})...\n\n"
                        f"Чатов проверено: {checked}\n"
                        f"Чатов покинуто: {exits_from_chats}\n"
                        f"Неудачный попыток выйти: {failed_leaves}\n"
                    )
                continue

            # Если таких диалогов не существует - то выходим из диалога и обновляем данные диспатчера
            try:
                await dispatcher.client.leave_chat(dialog.chat.id, delete=True)  # Юзербот покидает чат
                exits_from_chats += 1
            except Exception:
                failed_leaves += 1
                failed_exits += f"USERBOT: {account_id}, " \
                                f"Chat: " \
                                f"id-{dialog.chat.id} " \
                                f"title-{dialog.chat.title} " \
                                f"username-{dialog.chat.username}\n"

            if checked % 10 == 0 or checked == 1:  # Обновлять данные о проверка каждые 10 провереных чатов
                await msg.edit_text(
                    f"Проверка в процессе ({account_id}/{i}/{len(accounts)})...\n\n"
                    f"Чатов проверено: {checked}\n"
                    f"Чатов покинуто: {exits_from_chats}\n"
                    f"Неудачный попыток выйти: {failed_leaves}\n"
                )

    # Отправка окончательного сообщения администратору после завершения проверки и удаления
    await msg.edit_text(
        f"Проверка завершена\n\n"
        f"Чатов проверено: {checked}\n"
        f"Чатов покинуто: {exits_from_chats}\n"
        f"Неудачный попыток выйти: {failed_leaves}"
    )
    await asyncio.sleep(0.13)

    await bot.send_message(
        call.from_user.id,
        text=f"Проверка завершена\n\n"
             f"Чатов проверено: {checked}\n"
             f"Чатов покинуто: {exits_from_chats}\n"
             f"Неудачный попыток выйти: {failed_leaves}\n\n"
             f"Отладочная информация:\n"
             f"{failed_exits}"  # Добавление информации об ошибках в сообщение администратору
    )

