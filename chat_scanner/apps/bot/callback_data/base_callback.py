from enum import Enum, StrEnum

from aiogram.filters.callback_data import CallbackData


class Action(str, Enum):
    GET = "get"
    CREATE = "create"
    DELETE = "delete"
    UPDATE = "update"
    ALL = "all"
    MENU = "menu"


class AdminAction(StrEnum):
    WANT_GET = "admin_want_get"
    GET = "admin_get"
    CREATE = "admin_create"
    DELETE = "admin_delete"
    UPDATE = "admin_update"
    ALL = "admin_all"
    MENU = "admin_menu"

    ADD_BALANCE = "admin_add_balance"
    SUBTRACT_BALANCE = "admin_subtract_balance"
    CHANGE_SUBSCRIPTION_DURATION = "admin_change_subscription_duration"
    CHANGE_SUBS_RATE = "a_change_sub_rate"
    CHANGE_SUBS_RATE_OPT = "a_change_subs_rate_opt"
    SEND_MESSAGE = "admin_send_message"
    ADD_BAN = "admin_add_ban"


class MailingAction(StrEnum):
    ALL = "mailing_all"
    DELETE_BLOCKED = "delete_block_users"
    EXIT_FROM_CHAT = "exit_from_inactive_chats"
    SUBSCRIBED = "mailing_subscribed"
    EXPIRED = "mailing_expired"
    USER = "mailing_user"


class UserCallback(CallbackData, prefix="user"):
    id: int | None
    action: Action | AdminAction


class SubscriptionCallback(CallbackData, prefix="subscription"):
    id: int | None
    action: Action | AdminAction
    months: int | None
    rate: str | None
