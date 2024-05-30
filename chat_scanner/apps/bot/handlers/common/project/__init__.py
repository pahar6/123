from aiogram import Router

from . import project, crud, connect

router = Router()
router.include_routers(
    project.router,
    crud.router,
    connect.router,
)
