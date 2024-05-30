from aiogram import Router, F

from . import menu, mailing, stats, subs

router = Router(name="admin")
router.message.filter(F.chat.type == "private")
router.include_routers(
    menu.router,
    mailing.router,
    stats.router,
    subs.router,
)
