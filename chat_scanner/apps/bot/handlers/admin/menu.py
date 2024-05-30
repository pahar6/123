import traceback

from aiogram import Router, types, F, Bot
from aiogram.filters import Command, Text, StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from chat_scanner.apps.account.dispatcher import Dispatcher
from chat_scanner.config import Settings
from chat_scanner.db.models import User, Invoice, InvoiceStatus
from chat_scanner.utils.parser_csv import create_from_csv
from ...callback_data.base_callback import UserCallback, AdminAction, SubscriptionCallback
from ...commands.bot_commands import AdminCommands
from ...keyboards.admin import admin_kbs
from ...keyboards.common import common_kbs

router = Router()

async def get_user_info(user: User, session: AsyncSession) -> str:
    # Получить информацию о балансе и последних транзакциях
    results = await session.execute(
        select(Invoice)
        .where(Invoice.user_id == user.id)
        .where(Invoice.status == InvoiceStatus.SUCCESS)
        .order_by(Invoice.id.desc()).limit(5)
    )
    invoices: list[Invoice] = results.scalars().all()
    invoices_str = ""
    for invoice in invoices:
        invoices_str += f"{invoice.get_admin_text()}\n"
    ban_status = "заблокирован" if user.ban else "не заблокирован"
    info = (
        f"<b>Информация о пользователе:</b>\n"
        f"<b>ID:</b> {user.id}\n"
        f"<b>Username:</b> @{user.username}\n"
        f"<b>Тариф:</b> {user.rate}\n"
        f"<b>Статус:</b> {ban_status}\n"
        f"<b>Баланс:</b> {user.balance} р\n"
        f"<b>Длительность подписки:</b> {user.subscription_duration} дней\n"
        f"<b>Последние 5 транзакций:</b>\n"
        f"{invoices_str}"
    )
    return info


@router.callback_query(Text("admin"))
@router.message(Command(AdminCommands.ADMIN))
async def admin_start(message: types.CallbackQuery | types.Message, settings: Settings, state: FSMContext):
    await state.clear()
    if isinstance(message, types.CallbackQuery):
        message = message.message
    await message.delete()
    await message.answer(
        f"<b>👨‍💻Админ меню\n</b>"
        f"Стартовый бонус: {settings.bot.BONUS}\n"
        f"Процент от рефералки: {settings.bot.REFERRAL_PERCENT} %\n"
        f"Минимальная сумма вывода {settings.bot.WITHDRAW_BALANCE}\n",
        reply_markup=admin_kbs.admin_start()
    )


@router.callback_query(Text("texts_menu"))
async def handle_texts_menu(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.message.answer(
        "Редактирование текстов",
        reply_markup=admin_kbs.texts_menu(),
    )

@router.callback_query(Text("change_support_chat"))
async def change_support_chat(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.message.answer(
        "Введите id чата",
        reply_markup=common_kbs.custom_back_kb(cb="admin")
    )
    await state.set_state("change_support_chat")


@router.message(StateFilter("change_support_chat"))
async def change_support_chat(message: types.Message, settings: Settings, state: FSMContext):
    try:
        chat_id = int(message.text)
    except ValueError:
        await message.answer("Неверный формат id чата")
        return
    settings.bot.SUPPORT_CHAT_ID = chat_id
    await message.answer(
        f"Служебный чат изменен на {chat_id}",
        reply_markup=admin_kbs.admin_start()
    )
    settings.dump()
    await state.clear()


@router.callback_query(Text("change_ref_percent"))
async def change_ref_percent(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.message.answer(
        "Введите новый процент от рефералки",
        reply_markup=common_kbs.custom_back_kb(cb="admin")
    )
    await state.set_state("change_ref_percent")


@router.message(StateFilter("change_ref_percent"))
async def change_ref_percent(message: types.Message, settings: Settings, state: FSMContext):
    try:
        percent = float(message.text)
    except ValueError:
        await message.answer("Неверный формат процента")
        return
    settings.bot.REFERRAL_PERCENT = percent
    await message.answer(
        f"Процент от рефералки изменен на {percent} %",
        reply_markup=admin_kbs.admin_start()
    )
    settings.dump()
    await state.clear()


@router.callback_query(UserCallback.filter(F.action == AdminAction.WANT_GET))
async def admin_get_user(message: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await message.message.answer(
        "Введите id или username пользователя",
        reply_markup=common_kbs.custom_back_kb(cb="admin")
    )
    await state.set_state("admin_get_user")


# @router.message(StateFilter("admin_get_user"))
# @router.callback_query(UserCallback.filter(F.action == AdminAction.GET))
# async def admin_get_user(message: types.Message, session: AsyncSession, state: FSMContext,
#                          callback_data: UserCallback = None):
#     if isinstance(message, types.CallbackQuery):
#         message = message.message
#     # Приведение входных данных к нижнему регистру
#     search_text = message.text
#
#     # Поиск пользователя в базе данных
#     if search_text.isdigit():
#         user = await User.get(session, id=int(message.text))
#     else:
#         users = await User.filter(
#             session,
#             func.lower(User.username) == func.lower(search_text.replace('@', ''))
#         )
#         # user = await User.get(session, username=search_text.replace("@", ""))
#         if users:
#             user = users[0]
#         else:
#             user = None
#
#     if user:
#         #user = user[0]
#         # Получить информацию о балансе
#         results = await session.execute(
#             select(Invoice)
#             .where(Invoice.user_id == user.id)
#             .where(Invoice.status == InvoiceStatus.SUCCESS)
#             .order_by(Invoice.id.desc()).limit(5)
#         )
#         invoices: list[Invoice] = results.scalars().all()
#         invoices_str = ""
#         for invoice in invoices:
#             invoices_str += f"{invoice.get_admin_text()}\n"
#         ban_status = "заблокирован" if user.ban else "не заблокирован"
#         info = (
#             f"<b>Информация о пользователе:</b>\n"
#             f"<b>ID:</b> {user.id}\n"
#             f"<b>Username:</b> @{user.username}\n"
#             f"<b>Тариф:</b> {user.rate}\n"
#             f"<b>Статус:</b> {ban_status}\n"
#             f"<b>Баланс:</b> {user.balance} р\n"
#             f"<b>Длительность подписки:</b> {user.subscription_duration} дней\n"
#             f"<b>Последние 5 транзакций:</b>\n"
#             f"{invoices_str}"
#         )
#         await message.answer(info, reply_markup=admin_kbs.get_user(user.id))
#     await state.clear()

@router.message(StateFilter("admin_get_user"))
@router.callback_query(UserCallback.filter(F.action == AdminAction.GET))
async def admin_get_user(message: types.Message, session: AsyncSession, state: FSMContext,
                         callback_data: UserCallback = None):
    if isinstance(message, types.CallbackQuery):
        message = message.message
    # Приведение входных данных к нижнему регистру
    search_text = message.text

    # Поиск пользователя в базе данных
    if search_text.isdigit():
        user = await User.get(session, id=int(message.text))
    else:
        users = await User.filter(
            session,
            func.lower(User.username) == func.lower(search_text.replace('@', ''))
        )
        if users:
            user = users[0]
        else:
            user = None

    if user:
        info = await get_user_info(user, session)
        await message.answer(info, reply_markup=admin_kbs.get_user(user.id))
    await state.clear()


@router.callback_query(UserCallback.filter(F.action == AdminAction.SEND_MESSAGE))
async def admin_send_message(call: types.CallbackQuery, callback_data: UserCallback, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.message.answer(
        "Введите сообщение",
        reply_markup=common_kbs.custom_back_kb(cb="admin")
    )
    await state.set_state("admin_send_message")
    await state.update_data(bot_user_id=callback_data.id)


@router.message(StateFilter("admin_send_message"))
async def admin_send_message(message: types.Message, bot: Bot, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    bot_user = await User.get(session, id=data["bot_user_id"])
    await bot.send_message(bot_user.id, message.text)
    await message.answer(
        "Сообщение отправлено",
        reply_markup=common_kbs.custom_back_kb(cb=UserCallback(id=data["bot_user_id"], action=AdminAction.GET))
    )
    await state.clear()


@router.callback_query(UserCallback.filter(F.action == AdminAction.ADD_BALANCE))
async def admin_add_balance(call: types.CallbackQuery, callback_data: UserCallback, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.message.answer(
        "Введите сумму для пополнения баланса",
        reply_markup=common_kbs.custom_back_kb(cb="admin")
    )
    await state.set_state("admin_add_balance")
    await state.update_data(user_id=callback_data.id)


@router.message(StateFilter("admin_add_balance"))
async def admin_add_balance(message: types.Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    user = await User.get(session, id=data["user_id"])
    if user:
        try:
            balance = float(message.text)
        except ValueError:
            await message.answer("Неверный формат суммы")
            return
        user.balance += balance
        await session.commit()
        await message.answer(
            f"Баланс пользователя {user.id} пополнен на {balance}",
            reply_markup=common_kbs.custom_back_kb(cb=UserCallback(id=user.id, action=AdminAction.GET))
        )
    else:
        await message.answer("Пользователь не найден")
    await state.clear()


@router.callback_query(UserCallback.filter(F.action == AdminAction.SUBTRACT_BALANCE))
async def admin_subtract_balance(call: types.CallbackQuery, callback_data: UserCallback, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.message.answer(
        "Введите сумму для списания с баланса",
        reply_markup=common_kbs.custom_back_kb(cb="admin")
    )
    await state.set_state("admin_subtract_balance")
    await state.update_data(user_id=callback_data.id)


@router.message(StateFilter("admin_subtract_balance"))
async def admin_subtract_balance(message: types.Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    user = await User.get(session, id=data["user_id"])
    if user:
        try:
            balance = float(message.text)
        except ValueError:
            await message.answer("Неверный формат суммы")
            return
        user.balance -= balance
        await session.commit()
        await message.answer(
            f"С баланса пользователя {user.id} списано {balance}",
            reply_markup=common_kbs.custom_back_kb(cb=UserCallback(id=user.id, action=AdminAction.GET))

        )
    else:
        await message.answer("Пользователь не найден")
    await state.clear()


@router.callback_query(UserCallback.filter(F.action == AdminAction.CHANGE_SUBSCRIPTION_DURATION))
async def admin_change_subscription_duration(call: types.CallbackQuery, callback_data: UserCallback, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.message.answer(
        "Введите новую длительность подписки в днях",
        reply_markup=common_kbs.custom_back_kb(cb="admin")
    )
    await state.set_state("admin_change_subscription_duration")
    await state.update_data(user_id=callback_data.id)


@router.message(StateFilter("admin_change_subscription_duration"))
async def admin_change_subscription_duration(
        message: types.Message,
        session: AsyncSession,
        account_dispatchers: dict[int, Dispatcher],
        state: FSMContext
):
    data = await state.get_data()
    user = await User.get(session, id=data["user_id"])
    if user:
        try:
            duration = int(message.text)
        except ValueError:
            await message.answer("Неверный формат длительности подписки")
            return
        user.subscription_duration = duration
        await session.commit()

        # await user.update_projects_accounts(session, account_dispatchers)
        await message.answer(
            f"Длительность подписки пользователя {user.id} изменена на {duration} дней",
            reply_markup=common_kbs.custom_back_kb(cb=UserCallback(id=user.id, action=AdminAction.GET))
        )
    else:
        await message.answer("Пользователь не найден")
    await state.clear()


# Бан пользователей
@router.callback_query(UserCallback.filter(F.action == AdminAction.ADD_BAN))
async def admin_add_ban(
        call: types.CallbackQuery,
        session: AsyncSession,
        callback_data: UserCallback,
        state: FSMContext):
    user = await User.get(session, id=callback_data.id)

    if not user:
        await call.message.answer("Пользователь не найден")
        await state.clear()
        return

    user.ban = not user.ban
    await session.commit()
    updated_user = await User.get(session, id=user.id)

    status_message = "Пользователь заблокирован" if updated_user.ban else "Пользователь разблокирован"
    await call.message.answer(status_message)
    
    await state.clear()
    await state.set_state("admin_get_user")


@router.callback_query(Text("change_withdraw_sum"))
async def change_withdraw_sum(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.message.answer(
        "Введите новую минимальную сумму для вывода",
        reply_markup=common_kbs.custom_back_kb(cb="admin")
    )
    await state.set_state("change_withdraw_sum")


@router.message(StateFilter("change_withdraw_sum"))
async def change_withdraw_sum(
        message: types.Message,
        session: AsyncSession,
        settings: Settings,
        state: FSMContext
):
    await state.clear()
    settings.bot.WITHDRAW_BALANCE = float(message.text)
    settings.dump()
    await message.answer(
        "Минимальная сумма для вывода обновлена",
        reply_markup=common_kbs.custom_back_kb(cb="admin")
    )


@router.callback_query(Text("change_discount"))
async def change_discount(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.message.answer(
        "Введите новую скидку",
        reply_markup=common_kbs.custom_back_kb(cb="admin")
    )
    await state.set_state("change_discount")


@router.message(StateFilter("change_discount"))
async def change_discount(
        message: types.Message,
        session: AsyncSession,
        settings: Settings,
        state: FSMContext
):
    await state.clear()
    settings.bot.SUBSCRIPTION_12_MONTH_DISCOUNT = int(message.text)
    settings.dump()
    await message.answer(
        "Скидка обновлена",
        reply_markup=common_kbs.custom_back_kb(cb="admin")
    )


@router.callback_query(Text("update_bonus"))
async def update_bonus(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.message.answer(
        "Введите новый бонус",
        reply_markup=common_kbs.custom_back_kb(cb="admin")
    )
    await state.set_state("update_bonus")


@router.message(StateFilter("update_bonus"))
async def update_bonus(
        message: types.Message,
        session: AsyncSession,
        settings: Settings,
        state: FSMContext
):
    await state.clear()
    settings.bot.BONUS = float(message.text)
    settings.dump()
    await message.answer(
        "Бонус обновлен",
        reply_markup=common_kbs.custom_back_kb(cb="admin")
    )


@router.message(Text("/create_old_users_from_csv"))
async def create_old_users_from_csv(
        message: types.Message,
        session: AsyncSession,
        settings: Settings,
        state: FSMContext
):
    await create_from_csv(session)
    await message.answer(
        "Пользователи созданы",
    )
