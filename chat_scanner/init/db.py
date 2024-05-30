import asyncio

from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import close_all_sessions
from sqlalchemy_utils import database_exists, create_database

from chat_scanner.db.models import Base, User, Account
from ..config import SqliteDB, PostgresDB

Database = SqliteDB | PostgresDB


async def close_db():
    close_all_sessions()
    logger.info(f"Database closed")


async def dev_init_db(db: Database = PostgresDB.default()) -> async_sessionmaker:
    logger.info(f"Initializing Database {db.database}[{db.host}]...")
    engine = create_async_engine(db.url, echo=True)

    if not database_exists(db.sync_url):
        create_database(db.sync_url)
        logger.info(f"Database {db.database}[{db.host}] created")

    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    logger.info(f"Database {db.database}[{db.host}] initialized")
    return async_sessionmaker(engine, expire_on_commit=False)


async def init_db(db: Database = PostgresDB.default(), dev: bool = False) -> async_sessionmaker:
    if dev:
        return await dev_init_db(db)
    logger.info(f"Initializing {db}...")
    engine = create_async_engine(db.url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.success(f"[Database] Database {db} initialized")
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_user(maker, user_id):
    async with maker() as session:
        user, _ = await User.get_or_create(session, id=user_id)
        return user


async def main():
    maker = await init_db()
    async with maker() as session:
        account = await Account.get_account_with_min_projects(session)
        # print(account.username)


if __name__ == '__main__':
    asyncio.run(main())
