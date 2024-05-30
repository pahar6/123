from __future__ import annotations

from aiogram import Bot
from loguru import logger
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from chat_scanner.apps.account.dispatcher import Dispatcher
from ..models.project.project import Project
from ..models.project.settings import ProjectSettings
from ..models.project.keyword import Keyword, KeywordType
from ..models.user.user import User
from ..models import Rates


async def __remove_keywords_with_pro_permission(
    session: AsyncSession,
    user_id: int
):
    """Удаляем кейворды, которые были созданы в ПРО тарифе"""
    projects = await Project.filter(
        session,
        Project.user_id == user_id
    )
    for project in projects:
        # Удаление ключевых слов типа REPLACING
        remove_replacing_keywords = await Keyword.filter(
            session,
            Keyword.project_id == project.id,
            Keyword.type == KeywordType.REPLACING
        )
        for keyword in remove_replacing_keywords:
            await session.delete(keyword)

        # Удаление ключевых слов типа SIGNATURE
        remove_signature_keywords = await Keyword.filter(
            session,
            Keyword.project_id == project.id,
            Keyword.type == KeywordType.SIGNATURE
        )
        for keyword in remove_signature_keywords:
            await session.delete(keyword)

        await session.commit()

    return True

async def __remove_pro_projects(
    session: AsyncSession,
    user_id: int,
    bot: Bot,
    account_dispatchers: dict[int, Dispatcher]
):
    """Удаляем проекты, которые превышают значение 10 тарифа STANDART"""
    # Получить все проекты пользователя
    user_projects = await Project.filter(
        session,
        Project.user_id == user_id
    )

    # Проверяем количество проектов пользователя
    if len(user_projects) > 10:
        # Удаляем оставшиеся проекты (больше 10)
        projects_to_remove = user_projects[10:]
        logger.info(f"[REMOVE-PRO-PROJECTS] Объекты для удаления: {[project.id for project in projects_to_remove]}")
        for project in projects_to_remove:
            logger.info(f"[REMOVE-PRO-PROJECTS] Удаляем проект с ID: {project.id}")
            try:
                await Keyword.remove_keyword_by_project_id(session=session, project_id=project.id)
                await ProjectSettings.remove_project_settings_by_project(session=session, project_id=project.id)
                await Project.remove_project_by_project_id(session=session, bot=bot, project_id=project.id, account_dispatchers=account_dispatchers)
                logger.success(f"[REMOVE-PRO-PROJECTS] Удален проект с ID: {project.id}")
            except Exception as e:
                logger.error(f"[REMOVE-PRO-PROJECTS] Ошибка при удалении проекта с ID: {project.id}: {e}")
                return False
    return True


async def __update_projects_forward_all_messages(
    session: AsyncSession,
    user_id: int
):
    """Обновляем значение forward_all_messages на false для всех проектов пользователя"""
    projects = await Project.filter(
        session,
        Project.user_id == user_id
    )
    logger.info(f"Updating forward_all_messages to false for user {user_id} in {len(projects)} projects")
    for project in projects:
        if project.forward_all_messages:
            project.forward_all_messages = False
            logger.info(f"Updated forward_all_messages to false for project {project.id}")
        else:
            logger.info(f"Project {project.id} already has forward_all_messages set to false")
    await session.commit()
    logger.info(f"Successfully updated forward_all_messages for all projects of user {user_id}")
    return True


async def _set_user_pro_permissions():
    return  # Ничего не менять так как у про полный доступ

async def _set_user_standart_permissions(
    session: AsyncSession,
    user_id: int,
    bot: Bot,
    account_dispatchers: dict[int, Dispatcher],
):
    logger.info(f"Setting STANDART permissions for user {user_id}")
    await __remove_keywords_with_pro_permission(session, user_id)
    await __remove_pro_projects(session, user_id, bot, account_dispatchers)
    await __update_projects_forward_all_messages(session, user_id)
    logger.info(f"Successfully set STANDART permissions for user {user_id}")



async def _set_user_demo_permissions(
        session: AsyncSession,
        user_id: int,
        bot: Bot,
        account_dispatchers: dict[int, Dispatcher],
 ):
    return  # Ничего не менять так как у демо полный доступ

async def change_user_rate_permissions(
        session: AsyncSession,
        user_id: int,
        bot: Bot,
        account_dispatchers: dict[int, Dispatcher],
        new_rate: str = None,
        previous_rate: str = None
):
    user = await User.get_or_none(session, id=user_id)
    if not user:
        logger.warning(f"User with ID {user_id} not found")
        return

    logger.info(f"Changing user {user_id} rate from {previous_rate} to {new_rate}")

    # Если тарифный план меняется с PRO на STANDART, выполнить дополнительные действия
    if previous_rate == Rates.PRO and new_rate == Rates.STANDART:
        logger.info(f"User {user_id} is switching from PRO to STANDART")
        await _set_user_standart_permissions(
            session=session,
            user_id=user_id,
            bot=bot,
            account_dispatchers=account_dispatchers
        )
    elif new_rate == Rates.STANDART:
        await _set_user_standart_permissions(
            session=session,
            user_id=user_id,
            bot=bot,
            account_dispatchers=account_dispatchers
        )
    elif new_rate == Rates.PRO:
        await _set_user_pro_permissions()
    elif new_rate == Rates.DEMO:
        await _set_user_demo_permissions(
            session=session,
            user_id=user_id,
            bot=bot,
            account_dispatchers=account_dispatchers
        )

    logger.info(f"Successfully changed rate for user {user_id} to {new_rate}")


async def remove_full_user_data(
        session: AsyncSession,
        user_id: int,
        bot: Bot,
        account_dispatchers: dict[int, Dispatcher],
        remove_user: bool = True
) -> bool:
    """Remove all data of user from Database"""

    user_projects = await Project.filter(
        session,
        Project.user_id == user_id
    )
    for project in user_projects:  # Удалить все проекты пользователя
        await project.remove(
            session=session,
            bot=bot,
            account_dispatchers=account_dispatchers
        )
    try:
        # Удалить ключевые слова
        status, error = await Keyword.remove_keyword_by_user_id(session=session, user_id=user_id)
        if not status:
            raise ValueError(f'Bad keyword removing: {error}')

        # Удалить настройки проектов
        status, error = await ProjectSettings.remove_project_settings_by_user_id(session=session, user_id=user_id)
        if not status:
            raise ValueError(f'Bad project-settings removing: {error}')

        # Удалить проекты
        status, error = await Project.remove_project_by_user_id(session=session, user_id=user_id)
        if not status:
            raise ValueError(f'Bad project removing: {error}')

        if remove_user:  # Если надо удалить пользователя, то
            # Получить данные о покупках пользователя
            user_is_have_invoice = await User.is_have_invoices(session=session, user_id=user_id)
            if user_is_have_invoice:  # Если пользователь делал покупки то не удалять его
                return False

            # Если пользователь приглашал друзей в бота то не удалять его
            status = await User.is_have_referrers(session=session, user_id=user_id)
            if status:
                raise ValueError(f"[have_referrers] User have referrers")

            # Если пользователь был приглашен пользователем то не удалять его
            status = await User.is_referrer(session=session, user_id=user_id)
            if status:
                raise ValueError(f'[referrer] User is referrer (referrer: {status})')

            # Удалить пользователя
            status, error = await User.remove_user_by_id(session=session, user_id=user_id)
            if not status:
                raise ValueError(f'Bad user removing: {error}')
    except ValueError as error:
        if '[referrer]' in str(error) or '[have_referrers]' in str(error):
            logger.warning(f"User [{user_id}] not removed by: {error}")
            return False
        logger.exception(f"User [{user_id}] not removed with error: {error}")
        return False
    return True
