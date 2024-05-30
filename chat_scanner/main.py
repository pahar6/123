import asyncio
import logging
from pprint import pformat

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy
from loguru import logger

from chat_scanner.config import CLIArgsSettings, init_logging
from chat_scanner.db.models import Locale
from chat_scanner.init import (
    set_commands,
    setup_middlewares,
    setup_routers,
    setup_scheduler,
    init_translator_hub,
    start_webhook,
    init_db,
    close_db,
    setup_account_dispatchers
)


async def on_startup():
    pass


async def on_shutdown():
    pass


async def main():
    # await db.main()
    # return

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    # Parse command line arguments
    cli_settings = CLIArgsSettings.parse_args()

    # Initialize logging
    init_logging(cli_settings.log)
    logging.getLogger('pyrogram').setLevel(logging.INFO)
    logger.success('LOGGER IS CREATED')

    from chat_scanner.config import Settings

    # Update Settings variables
    cli_settings.update_settings(Settings)
    
    # Initialize settings
    try:
        settings = Settings()
        #logger.info(f"Settings:\n{pformat(settings.dict())}")
    except Exception as settings_error:
        logger.exception(settings_error)
    logger.success(f"Settings-Merchants: {settings.merchants}")

    # Initialize database
    session_maker = await init_db(settings.db)

    # Initialize translator
    translator_hub = init_translator_hub()

    # Initialize bot
    bot = Bot(token=settings.bot.token.get_secret_value(), parse_mode="html")

    # Initialize account dispatchers
    try:
        async with session_maker() as session:
            account_dispatchers = await setup_account_dispatchers(session, bot)
    except Exception as e:
        logger.exception(f"[ACCOUNT-DISPATCHER-ERROR] {e}")

    # Initialize storage
    storage = MemoryStorage()

    # Initialize bot dispatcher
    dp = Dispatcher(
        storage=storage,
        settings=settings,
        fsm_strategy=FSMStrategy.GLOBAL_USER,
        translator_hub=translator_hub,
        account_dispatchers=account_dispatchers,
    )

    # Register startup and shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Setup filter for private messages only
    # dp.message.filter(F.chat.type == "private")

    # Setup routers
    await setup_routers(dp, settings)

    # Setup middlewares
    setup_middlewares(dp=dp, session_maker=session_maker)

    # Setup scheduler
    base_l10n = translator_hub.get_translator_by_locale(Locale.RUSSIAN)
    scheduler = setup_scheduler(
        session_maker,
        account_dispatchers,
        bot,
        settings,
        base_l10n,
        translator_hub
    )

    # Set bot commands
    await set_commands(bot, settings)

    # Start bot
    try:
        if not cli_settings.webhook:
            logger.success("Start bot in polling mode")
            await bot.delete_webhook()
            await dp.start_polling(
                bot,
                skip_updates=True,
                allowed_updates=dp.resolve_used_update_types(),
                scheduler=scheduler,
            )

        else:
            logger.info("Start bot in webhook mode")
            await start_webhook(bot, dp, settings)
    finally:
        await bot.session.close()
        await dp.storage.close()
        await close_db()


if __name__ == "__main__":
    try:
        try:
            import uvloop
        except ImportError:
            logger.warning("uvloop is not installed")
            asyncio.run(main())
        else:
            logger.info("uvloop is installed")
            with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
                runner.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
