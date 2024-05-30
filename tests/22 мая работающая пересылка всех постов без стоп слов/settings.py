from __future__ import annotations

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from pyrogram.enums import MessageEntityType
from dataclasses import dataclass, field
import re

from cachetools import TTLCache
from loguru import logger
from pyrogram.types import Message
from sqlalchemy import ForeignKey, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import mapped_column, Mapped, relationship

from ..user.user import User
from .keyword import Keyword
from .project import Project
from ..base import Base

DUPLICATES: dict[int, Duplicate] = {}
between_chars = (  # Символы которые могут/должны находиться в конце/начале проверяемой фразы
    '(', '[', '<',
    '!', ';', '.',
    '?', ')', ']',
    ':', ',', ' ',
    '>', '\n'  # \n обязан быть в конце списка так как длина данного символа больше всех остальных
)


@dataclass
class Duplicate:
    text: TTLCache = field(default_factory=lambda: TTLCache(maxsize=1000, ttl=60 * 30))
    user_id: TTLCache = field(default_factory=lambda: TTLCache(maxsize=1000, ttl=60 * 30))

    @classmethod
    def get_duplicate(cls, project_id: int) -> Duplicate:
        if project_id not in DUPLICATES:
            DUPLICATES[project_id] = cls()
        return DUPLICATES[project_id]


class ProjectSettings(Base):
    __tablename__ = "project_settings"
    id: Mapped[int] = mapped_column(primary_key=True)

    # Значения в базе данных
    detect_text_duplicates: Mapped[bool] = mapped_column(default=False)
    detect_user_id_duplicates: Mapped[bool] = mapped_column(default=False)

    # Включить поля в результат
    include_username: Mapped[bool] = mapped_column(default=True)
    include_project_name: Mapped[bool] = mapped_column(default=True)
    include_media: Mapped[bool] = mapped_column(default=True)
    include_text: Mapped[bool] = mapped_column(default=True)
    include_hashtags: Mapped[bool] = mapped_column(default=True)
    include_links_from_text: Mapped[bool] = mapped_column(default=True)
    include_emoji: Mapped[bool] = mapped_column(default=True)
    include_usernames: Mapped[bool] = mapped_column(default=True)

    #Время отложенной записи
    time_sending: Mapped[int] = mapped_column(default=0)

    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"))
    project: Mapped[Project | None] = relationship(
        back_populates="settings",
        lazy='joined',
    )

    @staticmethod
    async def remove_project_settings_by_user_id(session: AsyncSession, user_id: int) -> tuple[bool, str]:
        """Remove all setting of projects where creator is user_id"""

        # Query с проектами пользователя
        user_project_ids = await session.execute(select(Project.id).where(Project.user_id == user_id))
        user_project_ids = [x[0] for x in tuple(user_project_ids)]

        try:
            # Удалить все элементы с настройками пользователя
            await session.execute(
                delete(ProjectSettings)
                .where(
                    ProjectSettings.project_id.in_(user_project_ids)
                )
            )
            await session.commit()
            return True, 'ok'
        except Exception as error:
            # logger.exception(error)
            return False, str(error)

    @staticmethod
    async def remove_project_settings_by_project(session: AsyncSession, project_id: int) -> tuple[bool, str]:
        """Remove all settings of a specific project by project_id"""

        try:
            # Удалить все настройки для указанного проекта
            await session.execute(
                delete(ProjectSettings)
                .where(
                    ProjectSettings.project_id == project_id
                )
            )
            await session.commit()
            return True, 'ok'
        except Exception as error:
            # logger.exception(error)
            return False, str(error)

    # Удаление хэштегов из текста
    def remove_hashtags_from_text(self, text: str) -> str:
        # Разделяем текст на абзацы
        paragraphs = text.split('\n\n')  # Предполагаем, что разделителем абзацев являются двойные переносы строк

        # Если в абзаце есть только один перенос строки, разделим его на строки по Shift+Enter
        modified_paragraphs = []
        for paragraph in paragraphs:
            modified_lines = []
            for line in paragraph.split('\n'):
                # Разделяем строку на слова по пробелам
                words = line.split()
                # Фильтруем слова, оставляя только те, которые не начинаются с символа "#"
                words = [word for word in words if not word.startswith('#')]
                # Собираем отфильтрованные слова обратно в строку, разделяя их пробелами
                modified_lines.append(' '.join(words))
            # Собираем обработанные строки обратно в абзац, добавляя между ними переносы строк
            modified_paragraphs.append('\n'.join(modified_lines))

        # Собираем обработанные абзацы обратно в текст, добавляя между ними двойные переносы строк
        return '\n\n'.join(modified_paragraphs)

    # Удаление юзернеймов из текста
    def remove_usernames_from_text(self, text: str) -> str:
        return re.sub(r'@[\w_]+', '', text)

    def remove_links_from_text(self, text: str) -> str:
        """ Удаляет ссылки из текста """
        url_with_text_rgx = r'<a\s+href=[^>]*>(.*?)</a>'
        url_with_http_rgx = r'https?://\S+|www\.\S'
        url_without_http_rgx = r'\b\w+(\.\w+)+/\S*'

        text = re.sub(url_with_text_rgx, r'\1', text)
        text = re.sub(url_with_http_rgx, '', text)
        text = re.sub(url_without_http_rgx, '', text)

        return text

    # Удаление смайликов и эмодзи из текста
    def remove_emoji(self, text: str) -> str:
        emoji_pattern = re.compile("["
                                   u"\U0001F000-\U0001F9FF"  # эмодзи
                                   u"\U0001F300-\U0001F5FF"  # символы и пиктограммы
                                   u"\U0001F600-\U0001F64F"  # эмодзи с лицами
                                   u"\U0001F680-\U0001F6FF"  # транспорт и символы
                                   u"\U0001F700-\U0001F77F"  # символы игральных карт
                                   u"\U0001F780-\U0001F7FF"  # символы категорий
                                   u"\U0001F800-\U0001F8FF"  # символы астрологии
                                   u"\U0001F900-\U0001F9FF"  # символы дополнительной эмодзи
                                   u"\U0001FA00-\U0001FA6F"  # символы игральных карт (дополнительные)
                                   u"\U0001FA70-\U0001FAFF"  # символы еды
                                   u"\U00002702-\U000027B0"  # знаки карандаша
                                   u"\U000024C2-\U0001F251"
                                   "]+", flags=re.UNICODE)
        return emoji_pattern.sub(r'', text)

    def re_text_v4(self, key, text, new_text):
        """
        Заменяет ключевое слово на новое значение. Если новое значение пустое, удаляет строку,
        если она остается пустой после замены.
        """
        # Разделяем текст на строки
        lines = text.split('\n')

        # Создаем паттерн для поиска ключевого слова
        p = r'(<\w+[^\>]*>){0,}'
        n = len(key)
        for i, row in enumerate(key):
            if i < n - 1:
                p += r'(<\w+[^\>]*>){0,}(</\w+>){0,}' + row + r'(<\w+[^\>]*>){0,}(</\w+>){0,}'
            else:
                p += row

        # Итерируемся по строкам
        for i in range(len(lines)):
            line = lines[i]
            original_line = line  # Сохраняем оригинальную строку для проверки позже
            for pattern in list(re.finditer(p, line, re.IGNORECASE))[::-1]:
                html = re.search(r'(<.*>)', pattern.group(0))
                start, stop = pattern.span()

                # Заменяем или удаляем часть строки
                if new_text is not None:
                    if html:
                        line_new = html.group(0) + new_text
                    else:
                        line_new = new_text
                    line = line[:start] + line_new + line[stop:]
                else:
                    if html:
                        x_text = re.sub(fr'{pattern.group(0)}(.*?</{html.group(0)[1]}>)?', '', line[start:])
                        line = line[:start] + x_text
                    else:
                        line_new = ''
                        line = line[:start] + line_new + line[stop:]

            # Проверка, если строка стала пустой, удаляем ее
            if new_text is None and original_line.strip() != '' and line.strip() == '':
                lines[i] = None
            else:
                lines[i] = line

        # Собираем текст обратно из непустых строк
        text = '\n'.join([line for line in lines if line is not None])

        return text

    def prepare_response_text(
            self,
            message: Message,
            project: Project,
            keyword: Keyword | None,
            forward_all: bool
    ) -> str:
        if forward_all:
            logger.info(f"ЗАПУЩЕНА ОБРАБОТКА ФИЛЬТРОВ - ПЕРЕСЫЛКА ВСЕХ ПОСТОВ")
        else:
            logger.info(f"ЗАПУЩЕНА ОБРАБОТКА ФИЛЬТРОВ - ПЕРЕСЫЛКА ПОСТОВ ПО КЛЮЧЕВЫМ СЛОВАМ")

        text = ""
        if message.text:
            text = message.text.html
        elif message.caption:
            text = message.caption.html

        # Удаление хештегов, если опция выключена
        if not self.include_hashtags:
            text = self.remove_hashtags_from_text(text)
        # Удаление ссылок, если опция выключена
        if not self.include_links_from_text:
            text = self.remove_links_from_text(text)
        # Удаление эмодзи, если опция выключена
        if not self.include_emoji:
            text = self.remove_emoji(text)
        # Удаление юзернеймов, если опция выключена
        if not self.include_usernames:
            text = self.remove_usernames_from_text(text)

        if message.from_user:
            if message.from_user.username:
                sender = f"@{message.from_user.username}"
            else:
                full_name = message.from_user.first_name
                if message.from_user.last_name:
                    full_name += f" {message.from_user.last_name}"
                sender = full_name
        else:
            sender = "Неизвестный отправитель"

        link = f'<a href="{message.link}">{project.name}</a>'

        # Удаление html тегов из текста
        if text.find("</emoji>") > 0:
            while text.find("</emoji>") != -1:
                html_emoji = text[text.find("<emoji"):(text.find("</emoji>") + 8)]
                emoji = html_emoji[html_emoji.find(">") + 1:html_emoji.find("</emoji>")]
                text = text[0:text.find("<emoji")] + emoji + text[text.find("</emoji>") + 8:len(text)]
        text = text.replace("&quot;А", "")
        response = f"{text}"
        included_link = f"📁 {link}"
        included_keyword = f"({keyword.keyword})" if keyword else ""
        included_sender = f"{sender}:\n"

        response = (
            f"{included_link if self.include_project_name else ''} "
            f"{included_keyword if self.include_text else ''}\n"
            f"{included_sender if self.include_username else ''}"
            f"{response}"
        )

        logger.info(f"Final response: {response}")
        return response

    # def prepare_response_text(
    #         self,
    #         message: Message,
    #         project: Project,
    #         keyword: Keyword
    # ) -> str:
    #     logger.info(f"ЗАПУЩЕНА ОБРАБОТКА ФИЛЬТРОВ - ПЕРЕСЫЛКА ПОСТОВ ПО КЛЮЧЕВЫМ СЛОВАМ")
    #     text = ""
    #     if message.text:
    #         text = message.text.html
    #     elif message.caption:
    #         text = message.caption.html
    #
    #     # Удаление хештегов, если опция выключена
    #     if not self.include_hashtags:
    #         text = self.remove_hashtags_from_text(text)
    #     # Удаление ссылок, если опция выключена
    #     if not self.include_links_from_text:
    #         text = self.remove_links_from_text(text)
    #     # Удаление эмодзи, если опция выключена
    #     if not self.include_emoji:
    #         text = self.remove_emoji(text)
    #     # Удаление юзернеймов, если опция выключена
    #     if not self.include_usernames:
    #         text = self.remove_usernames_from_text(text)
    #
    #     if message.from_user:
    #         if message.from_user.username:
    #             sender = f"@{message.from_user.username}"
    #         else:
    #             full_name = message.from_user.first_name
    #             if message.from_user.last_name:
    #                 full_name += f" {message.from_user.last_name}"
    #             sender = full_name
    #     else:
    #         sender = "Неизвестный отправитель"
    #
    #     link = f'<a href="{message.link}">{project.name}</a>'
    #
    #     # Удаление html тегов из текста
    #     if text.find("</emoji>") > 0:
    #         while text.find("</emoji>") != -1:
    #             html_emoji = text[text.find("<emoji"):(text.find("</emoji>") + 8)]
    #             emoji = html_emoji[html_emoji.find(">") + 1:html_emoji.find("</emoji>")]
    #             text = text[0:text.find("<emoji")] + emoji + text[text.find("</emoji>") + 8:len(text)]
    #     text = text.replace("&quot;А", "")
    #     response = f"{text}"
    #     included_link = f"📁 {link}"
    #     included_keyword = f"({keyword.keyword})"
    #     included_sender = f"{sender}:\n"
    #
    #     response = (
    #         f"{included_link if self.include_project_name else ''} "
    #         f"{included_keyword if self.include_text else ''}\n"
    #         f"{included_sender if self.include_username else ''}"
    #         f"{response}"
    #     )
    #
    #     logger.info(f"Final response: {response}")
    #     return response
    #


    def prepare_action_keywords(
            self,
            message: Message,
            keywords: list[Keyword],
            prepare_text: str
    ) -> str:
        if prepare_text is None:
            logger.error("prepare_text is None, initializing to an empty string.")
            prepare_text = ""

        text = message.text or message.caption or ""
        for keyword in keywords[::-1]:
            if keyword.type.lower() == 'replacing':
                # Проверка на наличие ключевого слова в тексте
                if keyword.keyword.lower() in text.lower():
                    logger.info(f"Текст на вход '{prepare_text}'")
                    logger.info(f"Слово подлежащее замене '{keyword.keyword}' найдено в тексте.")
                    logger.info(f"Слово для замены в тексте: '{keyword.replacing_text}'")
                    prepare_text = self.re_text_v4(key=keyword.keyword, text=prepare_text, new_text=keyword.replacing_text)
                else:
                    logger.info(f"Слово подлежащее замене '{keyword.keyword}' не найдено в тексте.")
                    continue  # Пропускаем текущий keyword и переходим к следующему
            elif keyword.type.lower() == 'signature':
                if keyword.keyword != '':
                    prepare_text += f'\n\n{keyword.keyword}'
        logger.info(f"[PREPARE_ACTION_KEYWORDS] Текст после замены {prepare_text}")
        return prepare_text

    def prepare_response_buttons(
            self,
            message: Message,
    ):
        if message.reply_markup:
            try:
                buttons = message.reply_markup.inline_keyboard
            except Exception:  # Если нет инлайн-кейборд или прилетела удаленная клавиатура
                return None
            inline_builder = InlineKeyboardBuilder()
            for button in buttons:
                inline_builder.row(
                    *[InlineKeyboardButton(text=button_inner.text, url=button_inner.url) for button_inner in button])
            return inline_builder.as_markup()
        return None

    def check(self, message: Message) -> bool:
        text = message.text or message.caption
        logger.info(f"Checking Settings: {self.id}")
        duplicate = Duplicate.get_duplicate(self.id)
        text_cache = duplicate.text
        user_id_cache = duplicate.user_id

        # Проверить на дубликаты
        if self.detect_text_duplicates:
            if text in text_cache:
                logger.debug(f"[X] Duplicate text: {text}")
                return False
            text_cache[text] = True

        # Проверить на id
        if self.detect_user_id_duplicates:
            user_id = None
            if message.from_user:
                user_id = message.from_user.id  # Получаем идентификатор пользователя
                if user_id in user_id_cache:
                    logger.debug(f"[X] Duplicate user_id: {user_id}")
                    return False
                user_id_cache[user_id] = True

        return True
