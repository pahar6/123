from __future__ import annotations

import typing

from loguru import logger
from pyrogram.types import Message

if typing.TYPE_CHECKING:
    from ..project import Project
    from ..keyword import Keyword


class CheckMixin:

    @classmethod
    def check_sender(cls, message: Message, sender: Keyword):
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        split_keyword = sender.keyword.split(" ")

        check = False
        if username and len(split_keyword) == 1:
            check = sender.check(username)

        if not check:
            if len(split_keyword) == 1:
                name = first_name or last_name
                check = sender.check(name)
            else:
                name = f"{first_name} {last_name}"
                check = sender.check(name)
        return check

    def check(self: Project, message: Message) -> Keyword | bool:

        # check settings
        if not self.settings.check(message):
            return False

        text = message.text or message.caption
        if not text:
            text = ""
        for keyword in self.stop_keywords:
            if keyword.check(text):
                logger.info(f"[Project {self.name}] Сработал стоп-триггер: {keyword.keyword}")
                return False

        sender: Keyword
        for sender in self.stop_senders:
            if message.from_user:
                check = self.check_sender(message, sender)
                if check:
                    logger.info(f"[Project {self.name}] Сработал стоп-триггер на юзернейм: {sender.keyword}")
                    return False

        # if self.allowed_senders:
        #     for sender in self.allowed_senders:
        #         if message.from_user:
        #             check = self.check_sender(message, sender)
        #             if check:
        #                 logger.info(f"[Project {self.name}] Сработал триггер на юзернейм: {sender.keyword}")
        #                 break
        #     else:
        #         logger.info(f"[Project {self.name}] Не сработал триггер на юзернейм")
        #         return False

        # Проверить сообщение на наличие ключевых слов
        for keyword in self.keywords:
            if keyword.check(text):
                logger.info(f"[Project {self.name}] Сработал триггер: {keyword.keyword}")
                return keyword

        logger.info(f"[Project {self.name}] Не сработал триггер")
        return False