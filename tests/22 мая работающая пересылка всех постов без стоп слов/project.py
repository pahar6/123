from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from aiogram import Bot
from aiogram.exceptions import TelegramMigrateToChat, TelegramForbiddenError, TelegramRetryAfter
from loguru import logger
from pyrogram.types import Message
from sqlalchemy import ForeignKey, String, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import mapped_column, Mapped, relationship

from chat_scanner.apps.account.client import Client
from chat_scanner.apps.bot.handlers.error.errors import add_to_ignorelist, get_ignore_duration, is_in_ignorelist
from .mixins import CheckMixin, SendMixin
from .. import Base


if TYPE_CHECKING:
    from .settings import ProjectSettings
    from .chat import ProjectChat
    from ..user import User, Account
    from .keyword import Keyword


class Project(Base, CheckMixin, SendMixin):
    __tablename__ = 'projects'

    id: Mapped[int] = mapped_column(primary_key=True)

    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
    account: Mapped[Account | None] = relationship(back_populates="projects", lazy='joined')

    name: Mapped[str] = mapped_column(String(100), index=True, default="⚙️ Общие настройки")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped[User] = relationship(back_populates="projects", lazy='joined')

    is_active: Mapped[bool] = mapped_column(default=True)
    forward_all_messages: Mapped[bool] = mapped_column(default=False)  # ВСЕПОСТЫ

    settings: Mapped[ProjectSettings] = relationship(
        back_populates="project",
        lazy='joined',
        cascade="all, delete-orphan",
    )
    # Ссылка для подключения к чату
    connect_link: Mapped[str | None] = mapped_column(String(100))

    # Список ключевых слов
    keywords: Mapped[list[Keyword]] = relationship(
        primaryjoin="and_(Keyword.project_id==Project.id, Keyword.is_stop_word==False, Keyword.is_username==False)",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy='joined'
    )

    # Список ключевых username
    allowed_senders: Mapped[list[Keyword]] = relationship(
        primaryjoin="and_(Keyword.project_id==Project.id, Keyword.is_stop_word==False, Keyword.is_username==True)",
        back_populates="project",
        cascade="all, delete-orphan",
        overlaps="keywords",
        lazy='joined'
    )

    # Список стоп-username
    stop_senders: Mapped[list[Keyword]] = relationship(
        primaryjoin="and_(Keyword.project_id==Project.id, Keyword.is_stop_word==True, Keyword.is_username==True)",
        back_populates="project",
        cascade="all, delete-orphan",
        overlaps="keywords",
        lazy='joined',
    )

    # Список стоп-слов
    stop_keywords: Mapped[list[Keyword]] = relationship(
        primaryjoin="and_(Keyword.project_id==Project.id, Keyword.is_stop_word==True , Keyword.is_username==False)",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy='joined',
        overlaps="keywords"
    )

    # Отправитель и получатель
    sender_id: Mapped[int | None] = mapped_column(ForeignKey("project_chats.id"))
    sender: Mapped[ProjectChat | None] = relationship(
        foreign_keys=[sender_id],
        back_populates="sender_projects",
        lazy='joined',
    )

    receiver_id: Mapped[int | None] = mapped_column(ForeignKey("project_chats.id"))
    receiver: Mapped[ProjectChat | None] = relationship(
        foreign_keys=[receiver_id],
        back_populates="receiver_projects",
        lazy='joined',
    )

    # async def trigger(
    #         self,
    #         client: Client,
    #         bot: Bot,
    #         message: Message
    # ):
    #     # Если forward_all_messages=True, пересылаем все сообщения
    #     if self.forward_all_messages:
    #         logger.info(f"[Project {self.name}] Пересылка всех сообщений включена, пересылаем сообщение.")
    #         await self.process_message(client, bot, message, None)
    #         return
    #     # # Если forward_all_messages=True, пересылаем все сообщения
    #     # if self.forward_all_messages: # ВСЕПОСТЫ
    #     #     logger.info(f"[Project {self.name}] Пересылка всех сообщений включена, пересылаем сообщение.")
    #     #     await self.send_message(client, bot, message, message.text, None)
    #     #     return
    #
    #     current_check_keyword = self.check(message)
    #     if not current_check_keyword:
    #         logger.debug(f"[Project {self.name}] Текущая проверка не пройдена")
    #     # Стоп фильтры
    #     if current_check_keyword is False:
    #         return
    #
    #     if not isinstance(current_check_keyword, bool):
    #         keyword = current_check_keyword
    #     else:
    #         return
    #
    #     if not self.receiver_id:
    #         await self.send_to_user(
    #             bot, f'Проект: {self.name}\n'
    #                  f'Сработал триггер, но не указан чат для отправки сообщений\n\n'
    #                  f'Project: {self.name}\n'
    #                  f'Trigger activated, but no chat specified for sending messages',
    #         )
    #         return
    #     try:
    #         # Отправить сообщение в чат с отложкой
    #         schedule_timeout_minutes = self.settings.time_sending
    #         await asyncio.sleep(schedule_timeout_minutes)
    #         #logger.warning(f"[Project {self.name}] Сработал триггер: {keyword.keyword}")
    #         settings: ProjectSettings = self.settings
    #         prepare_text = settings.prepare_response_text(message, self, keyword)
    #         logger.info(f"[PRE-TEXT] {prepare_text}")
    #         text = settings.prepare_action_keywords(
    #             message,
    #             self.keywords,
    #             prepare_text
    #         )
    #         markup = settings.prepare_response_buttons(message)
    #         sm = await self.send_message(client, bot, message, text, markup)  # Отправляем сообщение с установленным временем публикации
    #         await asyncio.sleep(1)
    #         return sm
    #     except TelegramMigrateToChat as e:
    #         await self.send_to_user(
    #             bot,
    #             f'<b>Проект: {self.name}</b>\n'
    #             f'Сработал триггер, но чат для отправки сообщений был изменен и обновлен до супергруппы. Переподключите проект.\n\n'
    #             f'<b>Project: {self.name}</b>\n'
    #             f'The trigger worked, but the chat for sending messages was changed and upgraded to a supergroup. Please reconnect the project.',
    #         )
    #         await asyncio.sleep(1)
    #         logger.warning(e)
    #     except TelegramRetryAfter as e:
    #         if 'flood' in str(e).lower():
    #             logger.warning(
    #                 f"Чат {message.chat.id} получил FLOOD ограничение на {e.retry_after} секунд. Добавляем в игнор-лист.")
    #
    #             # Проверяем, был ли добавлен в игнор-лист недавно
    #             if not is_in_ignorelist(message.chat.id):
    #                 duration = get_ignore_duration(message.chat.id)
    #                 add_to_ignorelist(message.chat.id)
    #                 await self.send_to_user(
    #                     bot,
    #                     f'<b>Внимание!</b>\n'
    #                     f'Получено ограничение на отправку постов в чат {message.chat.id} из-за частых публикаций. Блокировка будет снята через <b>{duration} мин.</b> Подробнее о проблеме <a href="https://redirect-bot.com/manual/#limitation">здесь</a>.\n\n'
    #                     f'<b>Attention!</b>\n'
    #                     f'Sending posts to chat {message.chat.id} has been restricted due to frequent publications. The block will be lifted in <b>{duration} min</b>. More details about the issue <a href="https://redirect-bot.com/language/en/instruction/#limitation">here</a>.'
    #                 )
    #     except TelegramForbiddenError as forbidden_error:
    #         if 'bot was kicked from' in str(forbidden_error):
    #             pass
    #     except Exception as e:
    #         ignore_errors = (
    #             'text buttons are unallowed',
    #             'must be non-empty'
    #         )
    #         if not any(list([error in str(e).lower() for error in ignore_errors])):
    #             logger.exception(e)
    #
    # async def process_message(
    #         self,
    #         client: Client,
    #         bot: Bot,
    #         message: Message,
    #         keyword: Keyword | None
    # ):
    #     try:
    #         # Отправить сообщение в чат с отложкой
    #         schedule_timeout_minutes = self.settings.time_sending
    #         await asyncio.sleep(schedule_timeout_minutes)
    #         settings: ProjectSettings = self.settings
    #         prepare_text = settings.prepare_response_text2(message, self, keyword)
    #         logger.info(f"[PRE-TEXT] {prepare_text}")
    #         text = settings.prepare_action_keywords(
    #             message,
    #             self.keywords,
    #             prepare_text
    #         )
    #         markup = settings.prepare_response_buttons(message)
    #         sm = await self.send_message(client, bot, message, text,
    #                                      markup)  # Отправляем сообщение с установленным временем публикации
    #         await asyncio.sleep(1)
    #         return sm
    #     except Exception as e:
    #         logger.exception(e)
    #         raise e

    async def trigger(
            self,
            client: Client,
            bot: Bot,
            message: Message
    ):
        # Если forward_all_messages=True, пересылаем все сообщения
        if self.forward_all_messages:
            logger.info(f"[Project {self.name}] Пересылка всех сообщений включена, пересылаем сообщение.")
            await self.process_message(client, bot, message, None, forward_all=True)
            return

        current_check_keyword = self.check(message)
        if not current_check_keyword:
            logger.debug(f"[Project {self.name}] Текущая проверка не пройдена")
            return

        if not isinstance(current_check_keyword, bool):
            keyword = current_check_keyword
        else:
            return

        if not self.receiver_id:
            await self.send_to_user(
                bot, f'Проект: {self.name}\n'
                     f'Сработал триггер, но не указан чат для отправки сообщений\n\n'
                     f'Project: {self.name}\n'
                     f'Trigger activated, but no chat specified for sending messages',
            )
            return

        await self.process_message(client, bot, message, keyword, forward_all=False)

    async def process_message(
            self,
            client: Client,
            bot: Bot,
            message: Message,
            keyword: Keyword | None,
            forward_all: bool
    ):
        try:
            # Отправить сообщение в чат с отложкой
            schedule_timeout_minutes = self.settings.time_sending
            await asyncio.sleep(schedule_timeout_minutes)
            settings: ProjectSettings = self.settings
            prepare_text = settings.prepare_response_text(message, self, keyword, forward_all)
            logger.info(f"[PRE-TEXT] {prepare_text}")
            text = settings.prepare_action_keywords(
                message,
                self.keywords,
                prepare_text
            )
            markup = settings.prepare_response_buttons(message)
            sm = await self.send_message(client, bot, message, text,
                                         markup)  # Отправляем сообщение с установленным временем публикации
            await asyncio.sleep(1)
            return sm
        except TelegramMigrateToChat as e:
            await self.send_to_user(
                bot,
                f'<b>Проект: {self.name}</b>\n'
                f'Сработал триггер, но чат для отправки сообщений был изменен и обновлен до супергруппы. Переподключите проект.\n\n'
                f'<b>Project: {self.name}</b>\n'
                f'The trigger worked, but the chat for sending messages was changed and upgraded to a supergroup. Please reconnect the project.',
            )
            await asyncio.sleep(1)
            logger.warning(e)
        except TelegramRetryAfter as e:
            if 'flood' in str(e).lower():
                logger.warning(
                    f"Чат {message.chat.id} получил FLOOD ограничение на {e.retry_after} секунд. Добавляем в игнор-лист.")

                # Проверяем, был ли добавлен в игнор-лист недавно
                if not is_in_ignorelist(message.chat.id):
                    duration = get_ignore_duration(message.chat.id)
                    add_to_ignorelist(message.chat.id)
                    await self.send_to_user(
                        bot,
                        f'<b>Внимание!</b>\n'
                        f'Получено ограничение на отправку постов в чат {message.chat.id} из-за частых публикаций. Блокировка будет снята через <b>{duration} мин.</b> Подробнее о проблеме <a href="https://redirect-bot.com/manual/#limitation">здесь</a>.\n\n'
                        f'<b>Attention!</b>\n'
                        f'Sending posts to chat {message.chat.id} has been restricted due to frequent publications. The block will be lifted in <b>{duration} min</b>. More details about the issue <a href="https://redirect-bot.com/language/en/instruction/#limitation">here</a>.'
                    )
        except TelegramForbiddenError as forbidden_error:
            if 'bot was kicked from' in str(forbidden_error):
                pass
        except Exception as e:
            ignore_errors = (
                'text buttons are unallowed',
                'must be non-empty'
            )
            if not any(list([error in str(e).lower() for error in ignore_errors])):
                logger.exception(e)
            raise e

    def get_sender_chat_id(self) -> int:
        sender_id = self.sender_id
        if self.sender:
            if self.sender.topic_id:
                sender_id = int(str(self.sender_id)[: -1 * len(str(self.sender.topic_id))])
        #logger.info(f"[GET-SENDER-CHAT-ID] Получен sender chat ID: {sender_id}")
        return sender_id

    def get_receiver_chat_id(self) -> int:
        receiver_id = self.receiver_id
        if self.receiver:
            if self.receiver.topic_id:
                receiver_id = int(str(self.receiver_id)[: -1 * len(str(self.receiver.topic_id))])
        #logger.info(f"[GET-RECEIVER-CHAT-ID] Получен receiver chat ID: {receiver_id}")
        return receiver_id

    def get_receiver_topic_id(self) -> int | None:
        if self.receiver:
            return self.receiver.topic_id if self.receiver.topic_id != 1 else None
        return None

    async def remove(self, session: AsyncSession, bot: Bot, account_dispatchers):
        logger.info(f"[REMOVE-PROJECT] Начинаем удаление проекта с ID: {self.id}")
        if self.sender_id and account_dispatchers:  # Если у проекта есть отправитель
            project_sender_id = self.get_sender_chat_id()
            logger.info(
                f"[REMOVE-PROJECT] Сохранённый sender chat ID: {self.sender_id}, Реальный sender chat ID: {project_sender_id}")
            has_similar = False
            # Все проекты в айди которого присутсвует данный основной чат
            all_project_like_main_sender_chat_id = await Project.filter(
                session,
                Project.account_id == self.account_id,
                Project.sender_id.cast(String).like(f"{project_sender_id}%")
            )
            for suspect_project in all_project_like_main_sender_chat_id:
                suspect_project_sender_id = suspect_project.get_sender_chat_id()
                logger.info(
                    f"[FILTER-SENDER-PROJECTS] Проверяем проект с ID: {suspect_project.id} для чата отправителя с ID: {project_sender_id}")

                if suspect_project.id == self.id:  # Пропускаем проверку на текущем проекте
                    continue
                # Если основной чат проверемого получателя такой же как и у основного получателя проекта
                # То не выходить из данной группы
                if suspect_project_sender_id == project_sender_id:
                    has_similar = True
                    break

            if not has_similar:  # Если нет проектов с такимже чатом получателем - то выйти из группы
                try:
                    dispatcher = account_dispatchers[self.account_id]
                    await dispatcher.client.leave_chat(project_sender_id, delete=True)
                    logger.success(f"[REMOVE-PROJECT] Успешно вышли из чата отправителя с ID: {project_sender_id}")
                except Exception as e:
                    logger.error(
                        f"[REMOVE-PROJECT] Ошибка при выходе из чата отправителя с ID: {project_sender_id}: {str(e)}")

        if self.receiver_id:  # Если у проекта есть получатель
            project_receiver_id = self.get_receiver_chat_id()
            logger.info(
                f"[REMOVE-PROJECT] Сохранённый receiver chat ID: {self.receiver_id}, Реальный receiver chat ID: {project_receiver_id}")
            has_similar = False
            # Все проекты в айди коорого присутсвует данный основнйо чат
            all_project_like_main_receiver_chat_id = await Project.filter(
                session,
                Project.receiver_id.cast(String).like(f"{project_receiver_id}%")
            )
            for suspect_project in all_project_like_main_receiver_chat_id:
                suspect_project_receiver_id = suspect_project.get_receiver_chat_id()
                logger.info(
                    f"[FILTER-RECEIVER-PROJECTS] Проверяем проект с ID: {suspect_project.id} для чата получателя с ID: {project_receiver_id}")

                if suspect_project.id == self.id:  # Пропускаем проверку на текущем проекте  отправь
                    continue
                # Если основной чат проверемого получателя такой же как и у основного получателя проекта
                # То не выходить из данной группы
                if suspect_project_receiver_id == project_receiver_id:
                    has_similar = True
                    break

            if not has_similar:  # Если нет проектов с такимже чатом получателем - то выйти из группы
                try:
                    await bot.leave_chat(project_receiver_id)
                    logger.success(f"[REMOVE-PROJECT] Успешно вышли из чата получателя с ID: {project_receiver_id}")
                except Exception as e:
                    logger.error(
                        f"[REMOVE-PROJECT] Ошибка при выходе из чата получателя с ID: {project_receiver_id}: {str(e)}")

        await session.delete(self)  # Удаляем проект из базы
        await session.commit()
        logger.success(f"[REMOVE-PROJECT] Успешно удален проект с ID: {self.id}")

    @staticmethod
    async def remove_project_by_user_id(session: AsyncSession, user_id: int) -> tuple[bool, str]:
        """Remove project by user_id"""
        try:
            await session.execute(delete(Project).where(Project.user_id == user_id))
            await session.commit()
            return True, 'ok'
        except Exception as error:
            # logger.exception(error)о
            return False, str(error)

    @staticmethod
    async def remove_project_by_project_id(
            session: AsyncSession,
            bot: Bot,
            project_id: int,
            account_dispatchers: dict[int]
    ) -> tuple[bool, str]:
        """Remove project by project_id"""
        try:
            # Получаем информацию о проекте по его ID
            project = await Project.get(session, id=project_id)
            logger.info(f"[REMOVE-PROJECT] Получен проект с ID: {project_id}")

            # Проверяем отправителя
            if project.sender_id and account_dispatchers:
                project_sender_id = project.get_sender_chat_id()
                logger.info(
                    f"[REMOVE-PROJECT] Сохранённый sender chat ID: {project.sender_id}, Реальный sender chat ID: {project_sender_id}")

                has_similar_sender = False
                all_project_like_main_sender_chat_id = await Project.filter(
                    session,
                    Project.account_id == project.account_id,
                    Project.sender_id.cast(String).like(f"{project_sender_id}%")
                )
                for suspect_project in all_project_like_main_sender_chat_id:
                    if suspect_project.id == project_id:
                        continue
                    if suspect_project.get_sender_chat_id() == project_sender_id:
                        has_similar_sender = True
                        break
                if not has_similar_sender:
                    try:
                        dispatcher = account_dispatchers[project.account_id]
                        await dispatcher.client.leave_chat(project_sender_id, delete=True)
                        logger.success(f"[REMOVE-PROJECT] Успешно вышли из чата отправителя с ID: {project_sender_id}")
                    except Exception as e:
                        logger.error(
                            f"[REMOVE-PROJECT] Ошибка при выходе из чата отправителя с ID: {project_sender_id}: {str(e)}")

            # Проверяем получателя
            if project.receiver_id:
                project_receiver_id = project.get_receiver_chat_id()
                logger.info(
                    f"[REMOVE-PROJECT] Сохранённый receiver chat ID: {project.receiver_id}, Реальный receiver chat ID: {project_receiver_id}")

                has_similar_receiver = False
                all_project_like_main_receiver_chat_id = await Project.filter(
                    session,
                    Project.receiver_id.cast(String).like(f"{project_receiver_id}%")
                )
                for suspect_project in all_project_like_main_receiver_chat_id:
                    if suspect_project.id == project_id:
                        continue
                    if suspect_project.get_receiver_chat_id() == project_receiver_id:
                        has_similar_receiver = True
                        break
                if not has_similar_receiver:
                    try:
                        await bot.leave_chat(project_receiver_id)
                        logger.success(f"[REMOVE-PROJECT] Успешно вышли из чата получателя с ID: {project_receiver_id}")
                    except Exception as e:
                        logger.error(
                            f"[REMOVE-PROJECT] Ошибка при выходе из чата получателя с ID: {project_receiver_id}: {str(e)}")

            # Удаляем проект из базы данных
            await session.execute(delete(Project).where(Project.id == project_id))
            await session.commit()
            logger.success(f"[REMOVE-PROJECT] Успешно удален проект с ID: {project_id}")

            return True, 'ok'

        except Exception as error:
            logger.error(f"[REMOVE-PROJECT] Ошибка при удалении проекта с ID: {project_id}: {str(error)}")
            return False, str(error)



