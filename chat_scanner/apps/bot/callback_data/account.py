from enum import Enum

from aiogram.filters.callback_data import CallbackData

from .base_callback import Action


class AccountAction(str, Enum):
    BIND = "bind"
    UNBIND = "unbind"
    RESTART = "restart"
    UPDATE_STATISTICS = "update_statistics"
    START_INVITE = "start_invite"
    CANCEL_INVITE = "cancel_invite"


class AccountCallback(CallbackData, prefix="account"):
    id: int | None
    action: Action | AccountAction
