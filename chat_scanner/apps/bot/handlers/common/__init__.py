from aiogram import Router, F

from . import base, withdraw, payment, yookassa, group, project, account

router = Router(name="common")

united_router = Router(name="united")
united_router.message.filter(F.chat.type == "private")
united_router.include_routers(
    base.router,
    withdraw.router,
    payment.router,
    yookassa.router,
    account.router,
    project.router,
)

last_router = Router(name="last")
last_router.message.filter(F.chat.type == "private")
last_router.message.register(base.start)

router.include_routers(
    united_router,
    group.router,
    last_router,
)
