from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router

if TYPE_CHECKING:
    pass

router = Router()

# @router.inline_query(Text(startswith="receiver"))