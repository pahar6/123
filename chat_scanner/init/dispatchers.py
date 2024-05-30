from aiogram import Bot
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from chat_scanner.apps.account.client import Client
from chat_scanner.apps.account.dispatcher import Dispatcher
from chat_scanner.db.models import Account, AccountStatus


async def setup_account_dispatchers(session: AsyncSession, bot: Bot) -> dict[int, Dispatcher]:
    accounts = await Account.all(session)
    dispatchers: dict[int, Dispatcher] = {}
    for account in accounts:
        try:
            dispatcher = await run_dispatcher(account, bot, session)
        except Exception as e:
            logger.error(f"[Dispatcher] for {account.id} failed to start: {e}")
            continue
        account.status = AccountStatus.ACTIVE
        await session.commit()
        dispatchers[account.id] = dispatcher
        await dispatcher.update_account(session)
    logger.success(f"[Dispatcher] Successfully started {len(dispatchers)} dispatchers")
    return dispatchers


def raise_exception():
    raise Exception("Phone code or password is required")


async def run_dispatcher(
        account: Account,
        bot: Bot,
        session: AsyncSession | None = None
) -> Dispatcher:
    api_id, api_hash = account.get_api_data()
    client = Client(
        api_id=api_id,
        api_hash=api_hash,
        phone_number=account.phone_number,
        phone_code=raise_exception,
        session_string=account.session_string,
    )
    dispatcher = Dispatcher(
        client=client,
        bot=bot,
        account=account
    )
    await dispatcher.start()
    return dispatcher
