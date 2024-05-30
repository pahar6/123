from __future__ import annotations

import typing

from loguru import logger
from pyrogram.types import Message

if typing.TYPE_CHECKING:
    from ..project import Project
    from ..keyword import Keyword


class CheckMixin:
    @classmethod #если это проверка для отправителя на блэк лист, то можно сюда добавить еще проверку на id отправителя - так будет действеннее.
    def check_sender(cls, message: Message, sender: Keyword):
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        split_keyword = sender.keyword.split(" ")

        check = False
        if username and len(split_keyword) == 1:
            check = sender.check(username)
            logger.debug(f"[MSG ID {message.id}]: Проверка username: {username}, результат: {check}")


        if not check:
            if len(split_keyword) == 1:
                name = first_name or last_name
                check = sender.check(name)
                logger.debug(f"[MSG ID {message.id}]: Проверка имени: {name}, результат: {check}")

            else:
                name = f"{first_name} {last_name}"
                check = sender.check(name)
                logger.debug(f"[MSG ID {message.id}]: Проверка полного имени: {name}, результат: {check}")

        return check

    def check(self: Project, message: Message) -> Keyword | bool:

        if not self.settings.check(message):
            return False

        text = message.text or message.caption
        if not text:
            text = ""
        for keyword in self.stop_keywords:
            if keyword.check(text):
                logger.debug(f"[MSG ID {message.id}]: Найдено стоп слово {keyword.keyword}. Процесс остановлен")
                return False

        sender: Keyword
        for sender in self.stop_senders:
            if message.from_user:
                check = self.check_sender(message, sender)
                if check:
                    logger.debug(f"[MSG ID {message.id}]: Найден стоп username {sender.keyword}. Процесс остановлен")
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
                logger.debug(f"[MSG ID {message.id}]: Найдено ключевое слово [{keyword.keyword}] в тексте")
                return keyword

        logger.debug(f"[MSG ID {message.id}]: Не сработал триггер. Процесс остановлен")
        return False

    def check_stop_conditions(self: Project, message: Message) -> bool:
        # поверка дубликатов
        if not self.settings.check(message):
            return False

        text = message.text or message.caption or ""
        for keyword in self.stop_keywords:
            if keyword.check(text):
                logger.debug(f"[MSG ID {message.id}]: Найдено стоп слово {keyword.keyword}. Процесс остановлен")
                return False

        if message.from_user:
            for sender in self.stop_senders:
                if self.check_sender(message, sender):
                    logger.debug(f"[MSG ID {message.id}]: Найден стоп username {sender.keyword}. Процесс остановлен")
                    return False
        logger.debug(f"[MSG ID {message.id}]: Стоп фильтров не обнаружено")
        return True
