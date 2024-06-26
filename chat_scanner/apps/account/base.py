from loguru import logger
from pyrogram.handlers.handler import Handler

from .client import Client


class BaseDispatcher:

    def __init__(self, client: Client):
        self.client = client
        self.handlers: list[Handler] = []
        logger.debug(f"BaseDispatcher initialized with client: {client}")

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self):
        for handler in self.handlers:
            self.client.add_handler(handler)
        logger.success("Starting client")
        await self.client.start()

    async def stop(self):
        logger.debug("Stopping BaseDispatcher...")
        await self.client.__aexit__()

    def add_handler(self, handler: Handler):
        if not isinstance(handler, Handler):
            raise TypeError(f'Handler must be instance of {Handler}')
        self.handlers.append(handler)
        logger.debug(f"Handler added: {handler}")

