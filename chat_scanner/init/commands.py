from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BotCommandScopeDefault, BotCommandScopeChat, BotCommandScopeAllPrivateChats
from loguru import logger

from ..apps.bot.commands.bot_commands import BaseCommandsCollection, AdminCommandsCollection
from ..config import Settings


async def set_commands(bot: Bot, settings: Settings):
    """
    Set bot commands
    :param bot:
    :param settings:
    :return:
    """

    async def _set_commands(commands, scope):
        try:
            await bot.set_my_commands(commands, scope=scope)
        except TelegramBadRequest as e:
            logger.warning(f"Can't set commands for {scope}: {e}")

    _BaseCommandsCollection = [command for command in BaseCommandsCollection if command.command == "start"]
    await _set_commands(_BaseCommandsCollection, scope=BotCommandScopeAllPrivateChats())
    for admin in settings.bot.admins:
        _AdminCommandsCollection = [command for command in AdminCommandsCollection if
                                    command.command == "admin" or command.command == "start"]
        await _set_commands(_AdminCommandsCollection, scope=BotCommandScopeChat(chat_id=admin))
    # for super_admin in settings.bot.super_admins:
    #     await _set_commands(SuperAdminCommandsCollection, scope=BotCommandScopeChat(chat_id=super_admin))
    logger.success("[Bot Commands] Bot commands set")
