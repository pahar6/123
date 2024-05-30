from aiogram import Router

from . import bind

router = Router(name="account-bind")
router.include_router(bind.router)
# router.include_router(auto_register.router)
