
import sys
import datetime

from aiogram import Bot, Router
from aiogram.exceptions import DetailedAiogramError
from aiogram.types import User
from aiogram.types.error_event import ErrorEvent
from collections import defaultdict
from aiohttp import ContentTypeError
from loguru import logger

router = Router()
ignore_errors = (
    'bot was kicked from',
    '406 CHANNEL_PRIVATE',
    'is not accessible',
    'is no longer valid',
    'must be non-empty',
    'message is not modified',
    'is too old',
    'too many requests'
)

# Словарь с пабликами, ограниченными в пересылке в целях оптимизации основного бота
# Format: {chat_id: [(timestamp, duration)]}
ignorelist: defaultdict[int, list[tuple[datetime.datetime, int]]] = defaultdict(list)

# История блокировок чатов за последний час
block_history: defaultdict[int, list[datetime.datetime]] = defaultdict(list)

# Время последнего срабатывания FLOOD-ограничения
last_flood_times: defaultdict[int, datetime.datetime] = defaultdict(lambda: datetime.datetime.min)


def clean_up_history(chat_id: int):
    """Удалить устаревшие записи из истории блокировок."""
    now = datetime.datetime.now()
    last_hour = now - datetime.timedelta(hours=1)
    block_history[chat_id] = [timestamp for timestamp in block_history[chat_id] if timestamp > last_hour]


def get_ignore_duration(chat_id: int) -> int:
    now = datetime.datetime.now()
    clean_up_history(chat_id)

    if not block_history[chat_id]:
        return 1  # 1 минута для первого раза
    elif len(block_history[chat_id]) == 1:
        return 5  # 5 минут для второго раза
    elif len(block_history[chat_id]) == 2:
        return 30  # 30 минут для третьего раза
    else:
        return 180  # 3 часа для четвертого и последующих раз


def add_to_ignorelist(chat_id: int):
    """Добавить чат в игнор-лист с вычисленным временем."""
    now = datetime.datetime.now()
    last_flood_time = last_flood_times[chat_id]

    # Если с последнего FLOOD-ограничения прошло менее 2 секунд, считаем это тем же самым событием
    if (now - last_flood_time).total_seconds() < 2:
        logger.info(f"Чат {chat_id} получил повторное FLOOD ограничение в течение 2 секунд, не добавляем новое.")
        return

    duration = get_ignore_duration(chat_id)
    ignorelist[chat_id].append((now + datetime.timedelta(minutes=duration), duration))
    last_flood_times[chat_id] = now
    block_history[chat_id].append(now)
    logger.warning(f"Чат {chat_id} получил FLOOD ограничение от REDIRECT BOT на {duration} минут.")


def is_in_ignorelist(chat_id: int) -> bool:
    """Проверить, находится ли чат в игнор-листе и если время истекло, удалить из списка."""
    now = datetime.datetime.now()
    if chat_id in ignorelist:
        ignorelist[chat_id] = [(timestamp, duration) for timestamp, duration in ignorelist[chat_id] if timestamp > now]
        if not ignorelist[chat_id]:
            ignorelist.pop(chat_id)
            return False
        return True
    return False


@router.errors()
async def error_handler(event: ErrorEvent):
    exception = event.exception
    if any(list([error in str(exception) for error in ignore_errors])):
        return
    if isinstance(exception, (DetailedAiogramError, ContentTypeError)):
        _type, _, tb = sys.exc_info()
        logger.opt(exception=(_type, None, tb)).error(exception.message)
    else:
        logger.exception(exception)
    # await bot.send_message(event_from_user.id, text, parse_mode=None)


