from __future__ import annotations

from typing import TYPE_CHECKING, BinaryIO

from aiogram import Bot, types
from aiogram.types import BufferedInputFile
from loguru import logger
from pyrogram import enums
from pyrogram.enums import MessageMediaType
from pyrogram.types import Message

from chat_scanner.apps.account.client import Client

if TYPE_CHECKING:
    from ..project import Project


class SendMixin:

    @classmethod
    async def get_media_group(cls, client: Client, message: Message, text: str):
        text = None  # todo L1 TODO 15.05.2023 19:50 taima: Возможно стоит вообще убрать параметр text
        messages = await client.get_media_group(message.chat.id, message_id=message.id)
        medias = []
        for _message in messages:
            media_attr = getattr(_message, _message.media.value)
            if hasattr(media_attr, "file_size") and media_attr.file_size:
                if media_attr.file_size > 50 * 1024 * 1024:
                    logger.warning(f"File size is too big: {media_attr.file_size}")
                    continue

            media = await client.download_media(media_attr.file_id, in_memory=True)
            media.seek(0)
            buffer = BufferedInputFile(file=media.read(),
                                       filename=media.name)
            if _message.media == enums.MessageMediaType.PHOTO:
                medias.append(types.InputMediaPhoto(media=buffer, caption=text))
            elif _message.media in (enums.MessageMediaType.VIDEO, enums.MessageMediaType.VIDEO_NOTE):
                medias.append(types.InputMediaVideo(media=buffer, caption=text))
            elif _message.media == enums.MessageMediaType.AUDIO:
                medias.append(types.InputMediaAudio(media=buffer, caption=text))
            elif _message.media == enums.MessageMediaType.VOICE:
                medias.append(types.InputMediaVoice(media=buffer, caption=text))
            elif _message.media == enums.MessageMediaType.DOCUMENT:
                medias.append(types.InputMediaDocument(media=buffer, caption=text))
        return medias

    # async def send_media(self: Project, client: Client, bot: Bot, message: Message, text: str, markup):
    #     # logger.warning(str(message))
    #     media = getattr(message, message.media.value)
    #     # bot can send only 50 MB
    #     if not hasattr(media, "file_size") or media.file_size > 50 * 1024 * 1024:
    #         return await bot.send_message(
    #             self.get_receiver_chat_id(),
    #             text,
    #             disable_web_page_preview=True,
    #             message_thread_id=self.get_receiver_topic_id(),
    #             reply_markup=markup,
    #         )
    #
    #     # if message.media == MessageMediaType.PHOTO:
    #     #     logger.warning(f'[PROJECT-SEND-PHOTO] Media size: {media.file_size}')
    #
    #     media: BinaryIO = await client.download_media(media.file_id, in_memory=True)
    #     media.seek(0)
    #
    #     if message.media == MessageMediaType.PHOTO:
    #         # logger.warning(f'[PROJECT-SEND-PHOTO-BUFFER] Media size: {media.read()}')
    #         if not len(media.getbuffer()):
    #             return await bot.send_message(
    #                 self.get_receiver_chat_id(),
    #                 text,
    #                 disable_web_page_preview=True,
    #                 message_thread_id=self.get_receiver_topic_id(),
    #                 reply_markup=markup,
    #             )
    #         # buffered_file = BufferedInputFile(file=media.read(), filename="photo")
    #         if len(text) <= 1000:
    #             buffered_file = BufferedInputFile(file=bytes(media.getbuffer()), filename="photo")
    #             await bot.send_photo(
    #                 chat_id=self.get_receiver_chat_id(),
    #                 caption=text[:1000],
    #                 reply_markup=markup,
    #                 photo=buffered_file,
    #                 message_thread_id=self.get_receiver_topic_id(),
    #             )
    #         else:
    #             buffered_file = BufferedInputFile(file=bytes(media.getbuffer()), filename="photo")
    #             await bot.send_photo(
    #                 chat_id=self.get_receiver_chat_id(),
    #                 photo=buffered_file,
    #                 message_thread_id=self.get_receiver_topic_id(),
    #             )
    #             await bot.send_message(
    #                 chat_id=self.get_receiver_chat_id(),
    #                 text=text,
    #                 reply_markup=markup,
    #                 message_thread_id=self.get_receiver_topic_id(),
    #             )
    #     elif message.media == MessageMediaType.VIDEO:
    #         filename = message.video.file_name
    #         if len(text) > 1000:
    #             await bot.send_video(
    #                 chat_id=self.get_receiver_chat_id(),
    #                 video=BufferedInputFile(file=media.read(), filename=filename),
    #                 message_thread_id=self.get_receiver_topic_id(),
    #             )
    #             await bot.send_message(
    #                 chat_id=self.get_receiver_chat_id(),
    #                 text=text,
    #                 reply_markup=markup,
    #                 message_thread_id=self.get_receiver_topic_id(),
    #             )
    #         else:
    #             await bot.send_video(
    #                 chat_id=self.get_receiver_chat_id(),
    #                 caption=text,
    #                 reply_markup=markup,
    #                 message_thread_id=self.get_receiver_topic_id(),
    #                 video=BufferedInputFile(file=media.read(), filename=filename)
    #             )
    #     elif message.media == MessageMediaType.DOCUMENT:
    #         filename = message.document.file_name
    #         if len(text) > 1000:
    #             await bot.send_document(
    #                 chat_id=self.get_receiver_chat_id(),
    #                 message_thread_id=self.get_receiver_topic_id(),
    #                 document=BufferedInputFile(file=media.read(), filename=filename)
    #             )
    #             await bot.send_message(
    #                 chat_id=self.get_receiver_chat_id(),
    #                 message_thread_id=self.get_receiver_topic_id(),
    #                 text=text,
    #                 reply_markup=markup
    #             )
    #         else:
    #             await bot.send_document(
    #                 chat_id=self.get_receiver_chat_id(),
    #                 message_thread_id=self.get_receiver_topic_id(),
    #                 caption=text,
    #                 reply_markup=markup,
    #                 document=BufferedInputFile(file=media.read(), filename=filename)
    #             )
    #     elif message.media == MessageMediaType.AUDIO:
    #         filename = message.audio.file_name
    #         if len(text) > 1000:
    #             await bot.send_audio(
    #                 chat_id=self.get_receiver_chat_id(),
    #                 message_thread_id=self.get_receiver_topic_id(),
    #                 audio=BufferedInputFile(file=media.read(), filename=filename)
    #             )
    #             await bot.send_message(
    #                 chat_id=self.get_receiver_chat_id(),
    #                 message_thread_id=self.get_receiver_topic_id(),
    #                 text=text,
    #                 reply_markup=markup
    #             )
    #         else:
    #             await bot.send_audio(
    #                 chat_id=self.get_receiver_chat_id(),
    #                 message_thread_id=self.get_receiver_topic_id(),
    #                 caption=text,
    #                 reply_markup=markup,
    #                 audio=BufferedInputFile(file=media.read(), filename=filename)
    #             )
    #     elif message.media == MessageMediaType.VOICE:
    #         #filename = message.voice.file_name эту опцию я сделал
    #         if len(text) > 1000:
    #             await bot.send_voice(
    #                 chat_id=self.get_receiver_chat_id(),
    #                 message_thread_id=self.get_receiver_topic_id(),
    #                 voice=BufferedInputFile(file=media.read(), filename="voice.ogg")
    #             )
    #             await bot.send_message(
    #                 chat_id=self.get_receiver_chat_id(),
    #                 message_thread_id=self.get_receiver_topic_id(),
    #                 text=text,
    #                 reply_markup=markup
    #             )
    #         else:
    #             await bot.send_voice(
    #                 chat_id=self.get_receiver_chat_id(),
    #                 message_thread_id=self.get_receiver_topic_id(),
    #                 caption=text,
    #                 reply_markup=markup,
    #                 voice=BufferedInputFile(file=media.read(), filename="voice.ogg")
    #             )


    # async def send_message(
    #         self: Project,
    #         client: Client,
    #         bot: Bot,
    #         message: Message,
    #         text: str,
    #         markup
    # ):
    #     # logger.warning(str(message))
    #     if self.settings.include_media and message.media:
    #         # Проверить есть ли несклько фото в сообщении
    #         if message.media_group_id:
    #             try:
    #                 medias = await self.get_media_group(client, message, text)
    #             except Exception as e:
    #                 logger.warning(e)
    #                 return await self.send_media(client, bot, message, text, markup)
    #
    #             sm = await bot.send_media_group(
    #                 self.get_receiver_chat_id(),
    #                 medias,
    #                 message_thread_id=self.get_receiver_topic_id(),
    #             )
    #             return await bot.send_message(
    #                 self.get_receiver_chat_id(),
    #                 text,
    #                 reply_markup=markup,
    #                 message_thread_id=self.get_receiver_topic_id(),
    #                 reply_to_message_id=sm[0].message_id,
    #                 disable_web_page_preview=True,
    #                 parse_mode="HTML",
    #             )
    #         return await self.send_media(client, bot, message, text, markup)
    #
    #     else:  # message.text:
    #         return await bot.send_message(
    #             self.get_receiver_chat_id(),
    #             text,
    #             reply_markup=markup,
    #             parse_mode="HTML",
    #             message_thread_id=self.get_receiver_topic_id(),
    #             disable_web_page_preview=True
    #         )
    #
    # async def send_to_user(self: Project, bot: Bot, text: str):
    #     try:
    #         await bot.send_message(
    #             self.user_id,
    #             text,
    #             disable_web_page_preview=True
    #         )
    #     except Exception as e:
    #         logger.error(e)
    async def send_media(self: Project, client: Client, bot: Bot, message: Message, text: str, markup):
        # logger.warning(str(message))
        media = getattr(message, message.media.value)
        # bot can send only 50 MB
        if not hasattr(media, "file_size") or media.file_size > 50 * 1024 * 1024:
            return await bot.send_message(
                self.get_receiver_chat_id(),
                text,
                disable_web_page_preview=True,
                message_thread_id=self.get_receiver_topic_id(),
                reply_markup=markup,
            )

        media: BinaryIO = await client.download_media(media.file_id, in_memory=True)
        media.seek(0)

        if message.media == MessageMediaType.PHOTO:
            if not len(media.getbuffer()):
                return await bot.send_message(
                    self.get_receiver_chat_id(),
                    text,
                    disable_web_page_preview=True,
                    message_thread_id=self.get_receiver_topic_id(),
                    reply_markup=markup,
                )
            if len(text) <= 1000:
                buffered_file = BufferedInputFile(file=bytes(media.getbuffer()), filename="photo")
                await bot.send_photo(
                    chat_id=self.get_receiver_chat_id(),
                    caption=text[:1000],
                    reply_markup=markup,
                    photo=buffered_file,
                    message_thread_id=self.get_receiver_topic_id(),
                )
            else:
                buffered_file = BufferedInputFile(file=bytes(media.getbuffer()), filename="photo")
                await bot.send_photo(
                    chat_id=self.get_receiver_chat_id(),
                    photo=buffered_file,
                    message_thread_id=self.get_receiver_topic_id(),
                )
                await bot.send_message(
                    chat_id=self.get_receiver_chat_id(),
                    text=text,
                    reply_markup=markup,
                    message_thread_id=self.get_receiver_topic_id(),
                )
        elif message.media == MessageMediaType.VIDEO:
            filename = message.video.file_name
            if len(text) > 1000:
                await bot.send_video(
                    chat_id=self.get_receiver_chat_id(),
                    video=BufferedInputFile(file=media.read(), filename=filename),
                    message_thread_id=self.get_receiver_topic_id(),
                )
                await bot.send_message(
                    chat_id=self.get_receiver_chat_id(),
                    text=text,
                    reply_markup=markup,
                    message_thread_id=self.get_receiver_topic_id(),
                )
            else:
                await bot.send_video(
                    chat_id=self.get_receiver_chat_id(),
                    caption=text,
                    reply_markup=markup,
                    message_thread_id=self.get_receiver_topic_id(),
                    video=BufferedInputFile(file=media.read(), filename=filename)
                )
        elif message.media == MessageMediaType.DOCUMENT:
            filename = message.document.file_name
            if len(text) > 1000:
                await bot.send_document(
                    chat_id=self.get_receiver_chat_id(),
                    message_thread_id=self.get_receiver_topic_id(),
                    document=BufferedInputFile(file=media.read(), filename=filename)
                )
                await bot.send_message(
                    chat_id=self.get_receiver_chat_id(),
                    message_thread_id=self.get_receiver_topic_id(),
                    text=text,
                    reply_markup=markup
                )
            else:
                await bot.send_document(
                    chat_id=self.get_receiver_chat_id(),
                    message_thread_id=self.get_receiver_topic_id(),
                    caption=text,
                    reply_markup=markup,
                    document=BufferedInputFile(file=media.read(), filename=filename)
                )
        elif message.media == MessageMediaType.AUDIO:
            filename = message.audio.file_name
            if len(text) > 1000:
                await bot.send_audio(
                    chat_id=self.get_receiver_chat_id(),
                    message_thread_id=self.get_receiver_topic_id(),
                    audio=BufferedInputFile(file=media.read(), filename=filename)
                )
                await bot.send_message(
                    chat_id=self.get_receiver_chat_id(),
                    message_thread_id=self.get_receiver_topic_id(),
                    text=text,
                    reply_markup=markup
                )
            else:
                await bot.send_audio(
                    chat_id=self.get_receiver_chat_id(),
                    message_thread_id=self.get_receiver_topic_id(),
                    caption=text,
                    reply_markup=markup,
                    audio=BufferedInputFile(file=media.read(), filename=filename)
                )
        elif message.media == MessageMediaType.VOICE:
            # filename = message.voice.file_name эту опцию я сделал
            if len(text) > 1000:
                await bot.send_voice(
                    chat_id=self.get_receiver_chat_id(),
                    message_thread_id=self.get_receiver_topic_id(),
                    voice=BufferedInputFile(file=media.read(), filename="voice.ogg")
                )
                await bot.send_message(
                    chat_id=self.get_receiver_chat_id(),
                    message_thread_id=self.get_receiver_topic_id(),
                    text=text,
                    reply_markup=markup
                )
            else:
                await bot.send_voice(
                    chat_id=self.get_receiver_chat_id(),
                    message_thread_id=self.get_receiver_topic_id(),
                    caption=text,
                    reply_markup=markup,
                    voice=BufferedInputFile(file=media.read(), filename="voice.ogg")
                )
        elif message.media == MessageMediaType.ANIMATION:
            # обработка GIF файлов
            filename = message.animation.file_name
            if len(text) > 1000:
                await bot.send_animation(
                    chat_id=self.get_receiver_chat_id(),
                    message_thread_id=self.get_receiver_topic_id(),
                    animation=BufferedInputFile(file=media.read(), filename=filename)
                )
                await bot.send_message(
                    chat_id=self.get_receiver_chat_id(),
                    message_thread_id=self.get_receiver_topic_id(),
                    text=text,
                    reply_markup=markup
                )
            else:
                await bot.send_animation(
                    chat_id=self.get_receiver_chat_id(),
                    message_thread_id=self.get_receiver_topic_id(),
                    caption=text,
                    reply_markup=markup,
                    animation=BufferedInputFile(file=media.read(), filename=filename)
                )
        elif message.media == MessageMediaType.VIDEO_NOTE:
            await bot.send_video_note(
                chat_id=self.get_receiver_chat_id(),
                message_thread_id=self.get_receiver_topic_id(),
                video_note=BufferedInputFile(file=media.read(), filename="video_note.mp4")
            )
            if text:
                await bot.send_message(
                    chat_id=self.get_receiver_chat_id(),
                    text=text,
                    reply_markup=markup,
                    message_thread_id=self.get_receiver_topic_id(),
                )

    async def send_message(
            self: Project,
            client: Client,
            bot: Bot,
            message: Message,
            text: str,
            markup
    ):
        logger.info(f"Processing message with ID: {message.id} and media type: {message.media}")

        if self.settings.include_media and message.media:
            # Проверить есть ли несколько фото в сообщении
            if message.media_group_id:
                try:
                    medias = await self.get_media_group(client, message, text)
                except Exception as e:
                    logger.warning(e)
                    return await self.send_media(client, bot, message, text, markup)

                sm = await bot.send_media_group(
                    self.get_receiver_chat_id(),
                    medias,
                    message_thread_id=self.get_receiver_topic_id(),
                )
                return await bot.send_message(
                    self.get_receiver_chat_id(),
                    text,
                    reply_markup=markup,
                    message_thread_id=self.get_receiver_topic_id(),
                    reply_to_message_id=sm[0].message_id,
                    disable_web_page_preview=True,
                    parse_mode="HTML",
                )
            return await self.send_media(client, bot, message, text, markup)

        else:  # message.text:
            return await bot.send_message(
                self.get_receiver_chat_id(),
                text,
                reply_markup=markup,
                parse_mode="HTML",
                message_thread_id=self.get_receiver_topic_id(),
                disable_web_page_preview=True
            )





