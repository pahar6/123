from aiogram import Router

from . import bind, menu

router = Router(name="account")
router.include_router(menu.router)
router.include_router(bind.router)
