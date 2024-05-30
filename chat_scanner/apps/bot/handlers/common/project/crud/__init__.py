from aiogram import Router

from . import get, create, update, delete

router = Router()
router.include_routers(
    get.router,
    create.router,
    update.router,
    delete.router
)
