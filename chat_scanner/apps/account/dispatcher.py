from __future__ import annotations
import typing

from aiogram import Bot
from loguru import logger
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .base import BaseDispatcher
from .client import Client
from .methods import CachedMethods
from .observer import Observable
from ..bot.handlers.error.errors import is_in_ignorelist
from ...db.models import Project, Account, User #тут разве нужен user?

UserID: typing.TypeAlias = int


class Dispatcher(BaseDispatcher, Observable, CachedMethods):
    """Диспетчер аккаунта"""

    def __init__(self, client: Client, bot: Bot, account: Account):
        super().__init__(client)
        self.bot = bot
        self.account = account

    async def message_handler(self, client: Client, message: Message):

        logger.debug(f"Received message: {message.id} from chat: {message.chat.id}")

        if is_in_ignorelist(message.chat.id):
            logger.debug(f"Chat ID {message.chat.id} is in ignore list")
            return

        project: Project
        text = message.text or message.caption
        logger.debug(f"Message text: {text}")

        for project in self.account.projects:
            logger.debug(f"Checking project: {project.id} for chat: {message.chat.id}")
            message_from_topic_id = None
            if message.reply_to_message_id is not None: #пост является или нет ответом на другой пост
                try:
                    message_from_topic_id = int(message.reply_to_message_id)
                    logger.debug(f"Message from topic ID: {message_from_topic_id}")
                except Exception:
                    pass

            if message.chat.id != project.get_sender_chat_id():
                logger.debug(f"Message chat ID {message.chat.id} does not match project sender chat ID {project.get_sender_chat_id()}")
                continue

            if project.sender.topic_id:
                if not message_from_topic_id and project.sender.topic_id != 1:
                    logger.debug(f"Project topic ID {project.sender.topic_id} does not match and is not 1")
                    continue
                if project.sender.topic_id != message_from_topic_id and project.sender.topic_id != 1:
                    logger.debug(
                        f"Project topic ID {project.sender.topic_id} does not match message topic ID {message_from_topic_id}")
                    continue

            if project.is_active:
                if project.user.subscription_duration > 0:
                    logger.debug(
                        f"Processing message from {message.chat.id} for project {project.id} ({len(self.account.projects)} projects) ({self.account.username})")
                    await project.trigger(client, self.bot, message)
                else:
                    logger.debug(f"Subscription of {self.account.id} expired")
            else:
                logger.debug(f"Project {project.id} of {self.account.id} is not active")
                return


    async def update_account(self, session: AsyncSession):
        query = select(Account).options(
            joinedload(Account.projects).joinedload(Project.user)  # .joinedload(User.general_project)
        ).where(Account.id == self.account.id)
        result = await session.execute(query)
        account = result.unique().scalar()
        await session.refresh(account)
        self.account = account

    async def log_all_chats(self):
        dialogs = await self.get_dialogs()
        logger.info(f"Logging all chats the userbot is in. Total: {len(dialogs)}")
        for dialog in dialogs:
            logger.info(f"Chat ID: {dialog.chat.id}, Chat Name: {dialog.chat.title or 'None'}")

    async def start(self):
        self.add_handler(MessageHandler(self.message_handler))
        await super().start()
        await self.client.send_message("me", "Dispatcher started")
        await self.log_all_chats()  # Log all chats at start
