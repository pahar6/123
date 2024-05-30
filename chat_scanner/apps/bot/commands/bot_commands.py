from typing import NamedTuple

from aiogram.types import BotCommand


class _BaseCommands(NamedTuple):
    START: BotCommand = BotCommand(command="start", description="🏠 Главное меню")
    INSTRUCTION: BotCommand = BotCommand(command="instruction", description="📖 Инструкция")
    PROJECTS: BotCommand = BotCommand(command="projects", description="📁 Мои проекты")
    PAYMENT: BotCommand = BotCommand(command="payment", description="💳 Оплата")
    SUPPORT: BotCommand = BotCommand(command="support", description="📞 Тех поддержка")
    INVITE: BotCommand = BotCommand(command="invite", description="📨 Пригласить друга")
    WITHDRAW: BotCommand = BotCommand(command="withdraw", description="💰 Вывести средства")
    LANGUAGE: BotCommand = BotCommand(command="language", description="🌐 Выбрать язык")



class _AdminCommands(NamedTuple):
    ADMIN: BotCommand = BotCommand(command="admin", description="👮‍♂️ Админка")
    BASE_ADMIN: BotCommand = BotCommand(command="base_admin", description="👮‍♂️ Базовое админ меню")
    ACCOUNTS: BotCommand = BotCommand(command="accounts", description="👥 Аккаунты")


class _SuperAdminCommands(NamedTuple):
    SUPER_ADMIN: BotCommand = BotCommand(command="super_admin", description="👮‍♂️ Супер админка")


BaseCommands = _BaseCommands()
AdminCommands = _AdminCommands()
SuperAdminCommands = _SuperAdminCommands()

BaseCommandsCollection = BaseCommands
AdminCommandsCollection = AdminCommands + BaseCommandsCollection
SuperAdminCommandsCollection = SuperAdminCommands + AdminCommandsCollection
