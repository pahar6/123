from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import markdown as md
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fluentogram import TranslatorRunner

from .common_kbs import menu_button, inline_button
from ...callback_data.base_callback import Action
from ...callback_data.project import ProjectCallback, ProjectAction, KeywordCallback
from .....db.models.project import Project
from loguru import logger


from .....db.models.project.keyword import KeywordType, Keyword
from chat_scanner.db.models import User, Rates


md = md
IKB = InlineKeyboardButton
if TYPE_CHECKING:
    from .....locales.stubs.ru.stub import TranslatorRunner


MAX_KEYWORDS = {
    "keywords": 10,
    "stop_keywords": 100,
    "allowed_senders": 50,
    "stop_senders": 100,
    "replacing_text": 5,
}

admin_rights = 'manage_topics+add_admins+change_info+post_messages+edit_messages+delete_messages+ban_users+' \
               'invite_users+pin_messages+post_stories+delete_stories+edit_stories+other+restrict_members+' \
               'promote_members+manage_call+anonymous'
_connect_link = f"t.me/yoyoyotest_bot?startgroup="
#_connect_link = f"t.me/redirect_to_bot?startgroup="  # <- Надо изменить будет под основного


def get_connect_link(project_id):
    return f"{_connect_link}{project_id}&admin={admin_rights}"

def get_projects(
    projects: List[Project],
    l10n: TranslatorRunner,
    user: User,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Сортировка проектов по имени
    projects.sort(key=lambda x: x.name)

    for project in projects:
        builder.button(
            text=project.name,
            callback_data=ProjectCallback(
                action=Action.GET,
                id=project.id
            )
        )

    # Определение максимального количества проектов для каждого тарифа
    max_projects = {
        Rates.DEMO: 4,
        Rates.STANDART: 10,
        Rates.PRO: 20
    }

    # Проверка количества проектов и добавление кнопки для создания нового проекта
    if len(projects) < max_projects.get(user.rate, 0):
        builder.button(
            text=l10n.projects.button.create(),
            callback_data=ProjectCallback(action=Action.CREATE)
        )

    builder.adjust(2)
    builder.row(menu_button(l10n))
    return builder.as_markup()

def get_project(
        project: Project,
        l10n: TranslatorRunner,
        user: User
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    active_button_text = "disable" if project.is_active else "enable"
    forward_mode_text = l10n.project.button.posting_all() if project.forward_all_messages else l10n.project.button.posting_keywords()
    switch_cb = ProjectCallback(id=project.id, action=ProjectAction.SWITCH)

    proj_button = l10n.project.status.button
    builder.button(
        text=getattr(proj_button, active_button_text)(),
        callback_data=switch_cb.copy(update={"data": "is_active"})
    )
    builder.button(
        text=l10n.project.button.connect(),
        callback_data=ProjectCallback(id=project.id, action=ProjectAction.CONNECT_GROUPS)
    )
    builder.button(
        text=l10n.project.button.name(),
        callback_data=ProjectCallback(id=project.id, action=Action.UPDATE, data="name")
    )
    builder.button(
        text=l10n.project.button.post_settings(),
        callback_data=ProjectCallback(id=project.id, action=ProjectAction.POST_SETTINGS)
    )
    # Проверяем уровень подписки пользователя перед добавлением кнопки
    if user.rate != Rates.STANDART:
        builder.button(
            text=forward_mode_text,
            callback_data=switch_cb.copy(update={"data": "forward_all_messages"})
        )
    else:
        builder.button(
            text=forward_mode_text,
            callback_data=ProjectCallback(id=project.id, action=ProjectAction.UPGRADE_INFO)
        )
    if not project.forward_all_messages:
        builder.button(
            text=l10n.project.button.keywords(),
            callback_data=KeywordCallback(project_id=project.id, action=Action.ALL)
        )
    builder.button(
        text=l10n.project.button.stop_keywords(),
        callback_data=KeywordCallback(project_id=project.id, action=Action.ALL, stop_word=True)
    )
    builder.button(
        text=l10n.project.button.stop_senders(),
        callback_data=KeywordCallback(project_id=project.id, action=Action.ALL, username=True, stop_word=True)
    )
    builder.button(
        text=l10n.project.button.delete(),
        callback_data=ProjectCallback(id=project.id, action=Action.DELETE)
    )

    builder.adjust(1, 1, 1, 1, 1, 1, 1, 1)

    # Добавляем нижние кнопки в один ряд
    builder.row(
        menu_button(l10n),
        inline_button(
            l10n.button.back(),
            ProjectCallback(action=Action.ALL)
        )
    )

    return builder.as_markup()

def get_detect_duplicates(project: Project, l10n: TranslatorRunner) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    switch_cb = ProjectCallback(id=project.id, action=ProjectAction.SWITCH)
    enabled = l10n.project.duplicates.button.enabled()
    disabled = l10n.project.duplicates.button.disabled()
    settings = project.settings
    sign = enabled if settings.detect_text_duplicates else disabled
    text = l10n.project.duplicates.button.text()
    builder.button(
        text=f"{sign} {text}",
        callback_data=switch_cb.copy(update={"data": "detect_text_duplicates"})
    )

    sign = enabled if settings.detect_user_id_duplicates else disabled
    text = l10n.project.duplicates.button.user_id()
    builder.button(
        text=f"{sign} {text}",
        callback_data=switch_cb.copy(update={"data": "detect_user_id_duplicates"})
    )

    builder.adjust(1)
    builder.row(inline_button(
        l10n.button.back(),
        ProjectCallback(action=ProjectAction.POST_SETTINGS, id=project.id)
    ))
    return builder.as_markup()


def get_deferred_messages(project: Project, l10n: TranslatorRunner) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    switch_cb = ProjectCallback(id=project.id, action=ProjectAction.SWITCH)
    enabled = l10n.project.deferred_messages.button.enabled()
    disabled = l10n.project.deferred_messages.button.disabled()
    settings = project.settings

    sign = enabled if settings.time_sending == 300 else disabled
    text = l10n.project.deferred_messages.button.min_5()
    builder.button(
        text=f"{sign} {text}",
        callback_data=switch_cb.copy(update={"data": "time_sending=300"})
    )

    sign = enabled if settings.time_sending == 1800 else disabled
    text = l10n.project.deferred_messages.button.min_30()
    builder.button(
        text=f"{sign} {text}",
        callback_data=switch_cb.copy(update={"data": "time_sending=1800"})
    )

    sign = enabled if settings.time_sending == 3600 else disabled
    text = l10n.project.deferred_messages.button.hours_1()
    builder.button(
        text=f"{sign} {text}",
        callback_data=switch_cb.copy(update={"data": "time_sending=3600"})
    )

    sign = enabled if settings.time_sending == 10800 else disabled
    text = l10n.project.deferred_messages.button.hours_3()
    builder.button(
        text=f"{sign} {text}",
        callback_data=switch_cb.copy(update={"data": "time_sending=10800"})
    )

    sign = enabled if settings.time_sending == 21600 else disabled
    text = l10n.project.deferred_messages.button.hours_6()
    builder.button(
        text=f"{sign} {text}",
        callback_data=switch_cb.copy(update={"data": "time_sending=21600"})
    )

    sign = enabled if settings.time_sending == 86400 else disabled
    text = l10n.project.deferred_messages.button.hours_24()
    builder.button(
        text=f"{sign} {text}",
        callback_data=switch_cb.copy(update={"data": "time_sending=86400"})
    )

    builder.adjust(1)
    builder.row(inline_button(
        l10n.button.back(),
        ProjectCallback(id=project.id, action=ProjectAction.POST_SETTINGS)
    ))
    return builder.as_markup()


def get_response(project: Project, l10n: TranslatorRunner) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    switch_cb = ProjectCallback(id=project.id, action=ProjectAction.SWITCH)
    enabled = l10n.project.response.button.enabled()
    disabled = l10n.project.response.button.disabled()
    settings = project.settings

    sign = enabled if settings.include_project_name else disabled
    text = l10n.project.response.button.include_project_name()
    builder.button(
        text=f"{sign} {text}",
        callback_data=switch_cb.copy(update={"data": "include_project_name"})
    )

    sign = enabled if settings.include_username else disabled
    text = l10n.project.response.button.include_username()
    builder.button(
        text=f"{sign} {text}",
        callback_data=switch_cb.copy(update={"data": "include_username"})
    )

    sign = enabled if settings.include_text else disabled
    text = l10n.project.response.button.include_text()
    builder.button(
        text=f"{sign} {text}",
        callback_data=switch_cb.copy(update={"data": "include_text"})
    )

    sign = enabled if settings.include_media else disabled
    text = l10n.project.response.button.include_media()
    builder.button(
        text=f"{sign} {text}",
        callback_data=switch_cb.copy(update={"data": "include_media"})
    )

    sign = enabled if settings.include_hashtags else disabled
    text = l10n.project.response.button.include_hashtags()
    builder.button(
        text=f"{sign} {text}",
        callback_data=switch_cb.copy(update={"data": "include_hashtags"})
    )

    sign = enabled if settings.include_links_from_text else disabled
    text = l10n.project.response.button.include_links_from_text()
    builder.button(
        text=f"{sign} {text}",
        callback_data=switch_cb.copy(update={"data": "include_links_from_text"})
    )

    sign = enabled if settings.include_emoji else disabled
    text = l10n.project.response.button.include_emoji()
    builder.button(
        text=f"{sign} {text}",
        callback_data=switch_cb.copy(update={"data": "include_emoji"})
    )

    sign = enabled if settings.include_usernames else disabled
    text = l10n.project.response.button.include_usernames()
    builder.button(
        text=f"{sign} {text}",
        callback_data=switch_cb.copy(update={"data": "include_usernames"})
    )

    builder.adjust(1)
    builder.row(inline_button(
        l10n.button.back(),
        ProjectCallback(action=ProjectAction.POST_SETTINGS, id=project.id)
    ))
    return builder.as_markup()


def choose_connect_groups(
        l10n: TranslatorRunner,
        project_id: int,
        projects: list
) -> InlineKeyboardMarkup:

    connect_link = get_connect_link(project_id)
    channel_text = str(l10n.project.connect.button.channel())
    group_text = str(l10n.project.connect.button.channel_1())
    forum_text = str(l10n.project.connect.button.channel_2())

    new_group_button = inline_button(
        text=group_text,
        url=connect_link
    )

    new_forum_button = inline_button(
        text=forum_text,
        cd=ProjectCallback(
            action=ProjectAction.CONNECT_FORUM,
            data='',
            id=project_id
        )
    )

    new_channel_button = inline_button(
        text=channel_text,
        url=connect_link.replace('startgroup', 'startchannel')
    )

    keyboard_buttons = []

    # Ряд с тремя кнопками
    keyboard_buttons.append([
        new_group_button, new_forum_button, new_channel_button
    ])

    # По одной кнопке
    collected_receivers = []
    for pid, prid, pretty_receiver in projects:
        parts = pretty_receiver.split('|')

        if len(parts) >= 4:
            title = parts[0].strip()
            domain = parts[1].strip()
            _id = parts[2].strip()
            _type = '|'.join(parts[3:]).strip()  # Объединяем все оставшиеся части в _type
        else:
            logger.warning(f"Unexpected format for pretty_receiver: {pretty_receiver}")
            continue

        if '/' in domain:
            topic_id = domain.split('/')[1]
            domain = domain.split('/')[0]
            _id = _id.replace(' ', '') + f'/{topic_id}'

        if f"{title[:12]} | {domain}" in collected_receivers:
            continue
        collected_receivers.append(f"{title[:12]} | {domain}")
        keyboard_buttons.append([
            inline_button(
                f"{title[:12]} | {domain}",
                ProjectCallback(
                    id=project_id,
                    data=_id,  # chat_id/topic_id or chat_id
                    action=ProjectAction.CONNECT_RECEIVER
                )
            )
        ])
    #
    # # По одной кнопке
    # collected_receivers = []
    # for pid, prid, pretty_receiver in projects:
    #     title, domain, _id, _type = pretty_receiver.split('|')
    #     if '/' in domain:
    #         topic_id = domain.split('/')[1]
    #         domain = domain.split('/')[0]
    #         _id = _id.replace(' ', '') + f'/{topic_id}'
    #     if f"{title[:12]} | {domain}" in collected_receivers:
    #         continue
    #     collected_receivers.append(f"{title[:12]} | {domain}")
    #     keyboard_buttons.append([
    #         inline_button(
    #             f"{title[:12]} | {domain}",
    #             ProjectCallback(
    #                 id=project_id,
    #                 data=_id,   # chat_id/topic_id or chat_id
    #                 action=ProjectAction.CONNECT_RECEIVER
    #             )
    #         )
    #     ])

    # Ряд с двумя кнопками внизу
    footer_buttons = [
        menu_button(l10n),
        inline_button(
            l10n.button.back(),
            ProjectCallback(id=project_id, action=ProjectAction.CONNECT_GROUPS)
        )
    ]
    keyboard_buttons.append(footer_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def choose_forum(
        l10n: TranslatorRunner,
        project_id: int,
        user_id: int
) -> InlineKeyboardMarkup:
    choose_forum_button = inline_button(
        text=str(l10n.project.connect.button.choose_forum()),
        url=get_connect_link(project_id)
    )

    keyboard_buttons = [
        [choose_forum_button]
    ]
    footer_buttons = [
        menu_button(l10n),
        inline_button(
            l10n.button.back(),
            ProjectCallback(id=project_id, data=user_id, action=ProjectAction.CHOOSE_RECEIVER)
        )
    ]
    keyboard_buttons.append(footer_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def connect_groups(
        project: Project,
        l10n: TranslatorRunner
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        inline_button(
            text=l10n.project.connect.button.sender(),
            cd=ProjectCallback(
                id=project.id,
                action=ProjectAction.CONNECT_SENDER
            )
        ),
        inline_button(
            text=l10n.project.connect.button.receiver(),
            cd=ProjectCallback(
                id=project.id,
                data=f"{project.user_id}",
                action=ProjectAction.CHOOSE_RECEIVER
            )
        )
    )

    builder.row(
        menu_button(l10n),
        inline_button(
            l10n.button.back(),
            ProjectCallback(id=project.id, action=Action.GET)
        )
    )
    builder.adjust(2, 2)
    return builder.as_markup()


def post_settings(
        project: Project,
        l10n: TranslatorRunner
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        inline_button(
            text=l10n.project.response.button(),
            cd=ProjectCallback(
                id=project.id,
                action=ProjectAction.RESPONSE
            )
        ),
        inline_button(
            text=l10n.project.button.deferred_messages(),
            cd=ProjectCallback(
                id=project.id,
                action=ProjectAction.DEFERRED_MESSAGES
            )
        ),
        inline_button(
            text=l10n.project.button.duplicates(),
            cd=ProjectCallback(
                id=project.id,
                action=ProjectAction.DETECT_DUPLICATES
            )
        ),
        inline_button(
            text=l10n.project.button.replacing_text(),
            cd=ProjectCallback(
                id=project.id,
                action=ProjectAction.REPLACING_TEXT
            )
        ),
        inline_button(
            text=l10n.project.button.signatures(),
            cd=ProjectCallback(
                id=project.id,
                action=ProjectAction.SIGNATURES
            )
        )
    )

    builder.row(
        menu_button(l10n),
        inline_button(
            l10n.button.back(),
            ProjectCallback(id=project.id, action=Action.GET)
        )
    )
    builder.adjust(1, 1, 1, 1, 1, 2)
    return builder.as_markup()


def get_keywords(
        project: Project,
        callback_data: KeywordCallback,
        l10n: TranslatorRunner,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    model_field = callback_data.get_model_field(plural=True)
    kws: list[Keyword] = getattr(project, model_field)
    #  sort by name
    kws.sort(key=lambda x: x.keyword)
    action_kws = 0
    for keyword in kws:
        if keyword.type in (KeywordType.SIGNATURE, KeywordType.REPLACING):
            action_kws += 1
            continue
        builder.button(
            text=keyword.pretty(l10n),
            callback_data=callback_data.copy_delete(keyword.id)
        )

    if len(kws) - action_kws < MAX_KEYWORDS[model_field]:
        keyword_type = callback_data.get_text(l10n, possessive=False)
        sign = keyword_type[:1]
        keyword_type = keyword_type[1:]
        text = l10n.project.button.add.keyword(
            sign=sign,
            keyword_type=keyword_type
        )
        builder.button(
            text=text,
            callback_data=callback_data.copy_create(project.id)
        )

    builder.row(inline_button(
        l10n.button.back(),
        ProjectCallback(id=project.id, action=Action.GET)
    ))
    builder.adjust(1)
    return builder.as_markup()


def create_keyword_type(
        callback_data: KeywordCallback,
        l10n: TranslatorRunner,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    keyword_type: KeywordType
    for keyword_type in KeywordType:
        if keyword_type in (KeywordType.SIGNATURE, KeywordType.REPLACING):
            continue
        builder.button(
            text=keyword_type.get_text(l10n),
            callback_data=keyword_type
        )
    builder.row(inline_button(
        l10n.button.back(),
        callback_data.copy_all()
    ))
    builder.adjust(1)
    return builder.as_markup()


def create_keyword_word(
        callback_data: KeywordCallback,
        l10n: TranslatorRunner,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(inline_button(
        l10n.button.back(),
        callback_data.copy_all()
    ))
    builder.adjust(1)
    return builder.as_markup()


def update_project_name(
        project_id: int,
        l10n: TranslatorRunner,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(inline_button(
        l10n.button.back(),
        ProjectCallback(id=project_id, action=Action.GET)
    ))
    builder.adjust(1)
    return builder.as_markup()


def signatures(
        project_id: int,
        l10n: TranslatorRunner,
        action: str
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if action == ProjectAction.ADD_SIGNATURE:
        builder.row(
            inline_button(
                l10n.project.button.signatures(),
                ProjectCallback(id=project_id, action=ProjectAction.ADD_SIGNATURE)
            ),
            inline_button(
                l10n.button.back(),
                ProjectCallback(
                    id=project_id,
                    action=ProjectAction.POST_SETTINGS
                )
            )
        )
    elif action == ProjectAction.DELETE_SIGNATURE:
        builder.row(
            inline_button(
                l10n.project.button.delete_signature(),
                ProjectCallback(id=project_id, action=ProjectAction.DELETE_SIGNATURE)
            ),
            inline_button(
                l10n.button.back(),
                ProjectCallback(
                    id=project_id,
                    action=ProjectAction.POST_SETTINGS
                )
            )
        )
    builder.adjust(1)
    return builder.as_markup()


def replacing_text(
        project: Project,
        l10n: TranslatorRunner
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    project_keywords = project.keywords

    replacing_keywords_count = 0
    for keyword in project_keywords:
        if keyword.type == KeywordType.REPLACING:
            _replacing_text = keyword.replacing_text if keyword.replacing_text else '❌'
            builder.row(
                inline_button(
                    f"{keyword.keyword} / {_replacing_text}",
                    ProjectCallback(
                        id=project.id,
                        data=keyword.id,
                        action=ProjectAction.DELETE_REPLACING_TEXT
                    )
                )
            )
            replacing_keywords_count += 1
            if replacing_keywords_count >= MAX_KEYWORDS['replacing_text']:
                break

    if replacing_keywords_count < MAX_KEYWORDS['replacing_text']:
        builder.row(
            inline_button(
                l10n.project.replacing_text.button.add_keyword(),
                ProjectCallback(
                    id=project.id,
                    action=ProjectAction.ADD_REPLACING_TEXT
                )
            ),
            inline_button(
                l10n.button.back(),
                ProjectCallback(
                    id=project.id,
                    action=ProjectAction.POST_SETTINGS
                )
            ))
    else:
        builder.row(
            inline_button(
                l10n.button.back(),
                ProjectCallback(
                    id=project.id,
                    action=ProjectAction.POST_SETTINGS
                )
            ))

    builder.adjust(1)
    return builder.as_markup()


def replacing_text_attr_text(
        project_id: int,
        l10n: TranslatorRunner
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        inline_button(
            l10n.project.replacing_text.button.skip(),
            ProjectCallback(
                id=project_id,
                action=ProjectAction.CONTINUE_SET_REPLACING_TEXT
            )
        ),
        inline_button(
            l10n.button.back(),
            ProjectCallback(
                id=project_id,
                action=ProjectAction.ADD_REPLACING_TEXT
            )
        )
    )

    builder.adjust(1)
    return builder.as_markup()


