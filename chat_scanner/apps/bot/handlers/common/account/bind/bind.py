from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from aiogram import F, Router, types, Bot
from aiogram.filters import StateFilter, Text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils import markdown as md
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from chat_scanner.apps.account.client import Client
from chat_scanner.apps.account.dispatcher import Dispatcher
from chat_scanner.apps.bot.callback_data.account import AccountAction, AccountCallback
from chat_scanner.apps.bot.callback_data.base_callback import Action
from chat_scanner.apps.bot.handlers.common.project.connect import _default_connect, send_connect_group_message
from chat_scanner.apps.bot.keyboards.common import account_kbs, common_kbs
from chat_scanner.config import Settings
from chat_scanner.db.models import Account, Project
from chat_scanner.db.models import User
from chat_scanner.db.models.user.account import AccountStatus
from chat_scanner.init.dispatchers import run_dispatcher

if TYPE_CHECKING:
    from chat_scanner.locales.stubs.ru.stub import TranslatorRunner

router = Router()


class UnbindAccount(StatesGroup):
    unbind = State()


class ConnectAccount(StatesGroup):
    phone = State()
    data = State()
    code = State()
    password = State()


link = md.hlink("ссылке", "https://my.telegram.org/auth?to=apps ")


@router.callback_query(AccountCallback.filter(F.action == AccountAction.BIND))
async def bind(
        call: types.CallbackQuery,
        session: AsyncSession,
        user: User,
        settings: Settings,
        l10n: TranslatorRunner,
        state: FSMContext
):
    await state.clear()
    await session.refresh(user, {"accounts"})
    # base_limit = settings.constants.BIND_ACCOUNTS_LIMIT
    # if not user.can_bind_account(base_limit):
    #     await call.message.answer(l10n.account.bind.limit(limit=base_limit))
    #     return

    await call.message.answer(
        l10n.account.bind(link=link),
        reply_markup=account_kbs.bind_account(l10n)
    )
    await state.set_state("register")


async def _get_password_callback(
        queue: asyncio.Queue,
        phone_number: str,
        message: types.Message,
        l10n: TranslatorRunner,
        state: FSMContext
):
    await state.set_state(ConnectAccount.password)
    await message.answer(l10n.account.bind.enter_password(phone=phone_number))
    logger.info(f"Ожидание пароля {message.from_user.id}")
    return queue


async def _get_code_callback(
        queue: asyncio.Queue,
        phone_number: str,
        message: types.Message,
        l10n: TranslatorRunner,
        state: FSMContext
):
    await state.set_state(ConnectAccount.code)
    await message.answer(l10n.account.bind.enter_code(phone=phone_number))
    logger.info(f"Ожидание кода {message.from_user.id}")
    return queue


async def _bind_account(
        session: AsyncSession,
        bot: Bot,
        user: User,
        api_id: int,
        api_hash: str,
        phone_number: str,
        message: types.Message,
        l10n: TranslatorRunner,
        account_dispatchers: dict[str, Dispatcher],
        state: FSMContext,
        **kwargs
):
    api_data = Account.encode_api_data(api_id, api_hash)
    account = await Account.get_or_none(session, api_data=api_data)
    # if account:
    #     await message.answer(l10n.account.bind.already_exists())
    #     await state.clear()
    #     return
    account_exists = False
    if account:
        account_exists = True

    if not account:
        account = Account(
            user=user,
            phone_number=phone_number,
            api_data=api_data,
        )

    logger.info(f"{user.username}| Полученные данные {api_id}|{api_hash}|{phone_number}")

    queue = asyncio.Queue()
    await state.update_data(queue=queue)
    client = Client(
        api_id=api_id,
        api_hash=api_hash,
        phone_number=phone_number,
        phone_code=lambda: _get_code_callback(queue, phone_number, message, l10n, state),
        password=lambda: _get_password_callback(queue, phone_number, message, l10n, state),
        timeout=120,
        in_memory=True,
    )
    try:
        logger.info("Запуск регистрации {user}", user=user)
        async with Dispatcher(client, bot, account) as dispatcher:
            account_user = await dispatcher.client.get_me()
            session_string = await dispatcher.client.export_session_string()
            account.update(**account_user.__dict__, session_string=session_string)
            account.status = AccountStatus.ACTIVE
            if not account_exists:
                session.add(account)

        await message.answer(l10n.account.bind.success(phone=phone_number))
        await session.commit()
        logger.info(f"{user.username}| Аккаунт успешно привязан")
        await session.refresh(account)
        dispatcher = await run_dispatcher(account, bot)
        if old_dispatcher := account_dispatchers.get(account.id):
            try:
                await old_dispatcher.stop()
            except Exception as e:
                logger.warning(e)

        account_dispatchers[account.id] = dispatcher
        logger.success(f"{user.username}| Диспетчер запущен")

    except asyncio.exceptions.TimeoutError:
        logger.info(f"{user.username}| Время ожидания кода истекло")
        await message.answer(l10n.account.bind.timeout())

    await state.clear()


@router.callback_query(StateFilter("register"), Text("i_registered"))
async def i_registered(
        call: types.CallbackQuery,
        l10n: TranslatorRunner,
        state: FSMContext
):
    await state.set_state(ConnectAccount.data)
    await call.message.answer(l10n.account.bind.enter_data())

    await state.set_state(ConnectAccount.data)


@router.message(StateFilter(ConnectAccount.data))
async def bind_account_data(
        message: types.Message,
        bot: Bot,
        session: AsyncSession,
        user: User,
        l10n: TranslatorRunner,
        account_dispatchers: dict[str, Dispatcher],
        state: FSMContext,
):
    api_id, api_hash, phone_number = tuple(map(lambda x: x.strip(), message.text.split(":")))
    # remove \u2069 and \u2068
    api_id = api_id.replace("\u2069", "").replace("\u2068", "")
    api_hash = api_hash.replace("\u2069", "").replace("\u2068", "")
    if (not api_id.isdigit()) or (not api_hash.isalnum()):
        await message.answer(l10n.account.bind.invalid_data())
        return
    phone_number = phone_number.replace("\u2069", "").replace("\u2068", "")
    api_id = int(api_id)
    await _bind_account(**locals())


@router.message(StateFilter(ConnectAccount.password))
async def get_password(
        message: types.Message,
        state: FSMContext,
):
    password = message.text
    data = await state.get_data()
    queue: asyncio.Queue = data.get("queue")
    await queue.put(password)
    await message.delete()


@router.message(StateFilter(ConnectAccount.code))
async def get_code(
        message: types.Message,
        l10n: TranslatorRunner,
        state: FSMContext,
):
    code = message.text
    if code.isdigit():
        await message.answer(
            # l10n("incorrect-code-input"),
            l10n.account.bind.incorrect_code_input(),
            reply_markup=common_kbs.custom_back_kb(l10n.button.back())
        )
        await state.clear()
        return

    code = message.text.replace("code", "").strip()
    if not code.isdigit():
        # await message.answer(l10n("incorrect-code-string"))
        await message.answer(l10n.account.bind.incorrect_code_string())
        return

    data = await state.get_data()
    queue: asyncio.Queue = data.get("queue")
    await queue.put(code)
    await message.delete()


@router.callback_query(AccountCallback.filter(F.action == AccountAction.UNBIND))
async def unbind_account(
        call: types.CallbackQuery,
        session: AsyncSession,
        callback_data: AccountCallback,
        l10n: TranslatorRunner,
        state: FSMContext,
):
    await state.clear()
    account = await Account.get_or_none(session, id=callback_data.id)
    if not account:
        # await call.message.answer(l10n("account-not-found"))
        await call.message.answer(l10n.account.not_found())
        return
    account_str = account.pretty(l10n)
    await call.message.answer(
        # l10n("unbind-account-confirm", {"identifier": account.identifier}),
        l10n.account.unbind.confirm(account=account_str),
        reply_markup=account_kbs.unbind_account(account, l10n, ),
    )


@router.callback_query(AccountCallback.filter(F.action == Action.DELETE))
async def delete_account(
        call: types.CallbackQuery,
        session: AsyncSession,
        callback_data: AccountCallback,
        l10n: TranslatorRunner,
        account_dispatchers: dict[str, Dispatcher],
        state: FSMContext,
):
    account = await Account.get(session, id=callback_data.id)
    await session.delete(account)
    await session.commit()
    if account.id in account_dispatchers:
        try:
            await account_dispatchers[account.id].stop()
            if account.projects:
                for project in account.projects:
                    project.sender_id = None
            await session.commit()
            del account_dispatchers[account.id]
        except Exception as e:
            logger.exception(e)
    await call.message.answer("Аккаунт удален", reply_markup=common_kbs.custom_back_kb(cb="admin"))
    await state.clear()
    await call.message.answer(
        f"Переключение проектов на другой аккаунт"
    )
    projects = await Project.filter(session, Project.sender_id == None)
    for nut, project in enumerate(projects, 1):
        try:
            is_connect = await _default_connect(**locals())
            if not is_connect:
                return
            dispatcher, account = is_connect
            await session.commit()
            await session.refresh(account)
            await session.refresh(project)
            dispatcher.account = account
            success_message = l10n.project.connect.sender.success(name=project.name)
            await call.message.answer(success_message)
            await send_connect_group_message(call.message.answer, project, l10n)
        except Exception as e:
            logger.exception(e)
            await call.message.answer(f"Ошибка переключения проекта {project.name}")
        await call.message.answer(f"Проектов переключено {nut} из {len(projects)}")
        await asyncio.sleep(5)
    await call.message.answer("Переключение проектов завершено")
