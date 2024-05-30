from io import BytesIO

import pandas as pd
from aiogram import Router, types
from aiogram.filters import Text
from aiogram.fsm.context import FSMContext
from aiogram.utils import markdown as md
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...keyboards.admin import admin_kbs
from .....db.models import User, Invoice, InvoiceStatus

router = Router()


@router.callback_query(Text("stats"))
async def stats(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    # Количество юзеров и количество юзеров за сегодня. Использовать md
    users_count = await User.count(session)
    users_today_count = await User.today_count(session)
    result = await session.execute(
        select(Invoice)
        .where(Invoice.status == InvoiceStatus.SUCCESS)
        .options(selectinload(Invoice.user))
        .order_by(Invoice.created_at.desc())
        .limit(10)
    )
    invoices: list[Invoice] = result.scalars().all()
    invoices_str = ""
    for num, invoice in enumerate(invoices, 1):
        invoices_str += f"{num}. {invoice.user.get_admin_text()}\n"
        invoices_str += f"{invoice.get_admin_text()}\n\n"

    await call.message.delete()
    await call.message.answer(
        f"Количество пользователей: {md.hcode(users_count)}\n"
        f"Количество пользователей за сегодня: {md.hcode(users_today_count)}\n"
        f"Последние 10 оплаченных пакетов:\n"
        f"{invoices_str}",
        reply_markup=admin_kbs.stats(),
    )


@router.callback_query(Text("export_users"))
async def export_users(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    await call.answer("Экспорт пользователей...")
    results = await session.execute(select(User))
    users: list[User] = results.unique().scalars().all()
    df = pd.DataFrame(
        {
            "id": [user.id for user in users],
            "username": [user.username for user in users],
            "first_name": [user.first_name for user in users],
            "last_name": [user.last_name for user in users],
            "balance": [user.balance for user in users],
            "subscription_duration_days": [user.subscription_duration for user in users],
            "created_at": [user.created_at.strftime("%Y-%m-%d %H:%M:%S") for user in users],
        }
    )
    memory_file = BytesIO()
    df.to_excel(memory_file, index=False)
    memory_file.seek(0)
    await call.message.answer_document(
        types.BufferedInputFile(memory_file.read(),
                                filename="users.xlsx")
    )
    await state.clear()


@router.callback_query(Text("export_invoices"))
async def export_invoices(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    await call.answer("Экспорт счетов...")
    results = await session.execute(select(Invoice))
    invoices: list[Invoice] = results.unique().scalars().all()
    df = pd.DataFrame(
        {
            "id": [invoice.id for invoice in invoices],
            "user_id": [invoice.user_id for invoice in invoices],
            "amount": [invoice.amount for invoice in invoices],
            "currency": [invoice.currency for invoice in invoices],
            "subs_duration_day": [invoice.subscription_duration * 30 for invoice in invoices],
            "created_at": [invoice.created_at.strftime("%Y-%m-%d %H:%M:%S") for invoice in invoices],
        }
    )
    memory_file = BytesIO()
    df.to_excel(memory_file, index=False)
    memory_file.seek(0)
    await call.message.answer_document(
        types.BufferedInputFile(memory_file.read(),
                                filename="invoices.xlsx")
    )
    await state.clear()
