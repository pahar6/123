from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from aiogram.filters.callback_data import CallbackData

from chat_scanner.apps.bot.callback_data.base_callback import Action

if TYPE_CHECKING:
    from chat_scanner.locales.stubs.ru.stub import TranslatorRunner


class ProjectAction(StrEnum):
    CONNECT_GROUPS = "connect_groups"
    CONNECT_SENDER = "connect_sender"
    CONNECT_RECEIVER = "connect_receiver"
    CONNECT_FORUM: ProjectAction = "connect_forum"
    CHOOSE_RECEIVER = "choose_receiver"
    EDIT_NAME = "edit_name"

    SWITCH = "switch"
    UPGRADE_INFO = "upgrade_info" #добавил значение
    FORWARD_MODE = "forward_mode"
    DETECT_DUPLICATES = "detect_duplicates"
    RESPONSE = "response"
    POST_SETTINGS = "post_settings"
    SIGNATURES = "signatures"
    ADD_SIGNATURE = "add_signature"
    DELETE_SIGNATURE = "delete_signature"
    DEFERRED_MESSAGES = "deferred_messages"
    REPLACING_TEXT = "replacing_text"
    ADD_REPLACING_TEXT = "add_replacing_text"
    DELETE_REPLACING_TEXT = "delete_replacing_text"
    CONTINUE_SET_REPLACING_TEXT = 'continue_set_replacing_text'


class ProjectCallback(CallbackData, prefix="project"):
    id: int | None
    action: Action | ProjectAction
    data: str | int | None


class KeywordCallback(CallbackData, prefix="keyword"):
    id: int | None
    project_id: int | None
    action: Action
    stop_word: bool = False
    username: bool = False
    data: str | None

    def get_model_field(self, plural: bool = False) -> str:
        if self.username:
            if self.stop_word:
                kws = "stop_sender"
            else:
                kws = "allowed_sender"
        else:
            if self.stop_word:
                kws = "stop_keyword"
            else:
                kws = "keyword"
        if plural:
            kws += "s"
        return kws

    def get_text(self, l10n: TranslatorRunner, possessive: bool = False, plural: bool = False) -> str:
        field = self.get_model_field(plural)
        if possessive:
            field += "-possessive"
        return l10n.get(f"project-button-{field}")

    # create from self
    def copy_create(self, project_id: int) -> KeywordCallback:
        return self.copy(update={"project_id": project_id, "action": Action.CREATE})

    def copy_delete(self, id: int) -> KeywordCallback:
        return self.copy(update={"id": id, "action": Action.DELETE})

    def copy_all(self) -> KeywordCallback:
        return self.copy(update={"action": Action.ALL})
