from __future__ import annotations

import abc
from abc import ABC
from typing import Generic, TypeVar
from loguru import logger

T = TypeVar('T', bound='Observer')

class Observer(ABC):
    @abc.abstractmethod
    async def trigger(self, *args, **kwargs):
        raise NotImplementedError

    async def __call__(self, *args, **kwargs):
        return await self.trigger(*args, **kwargs)


class Observable(Generic[T]):
    def __init__(self):
        self.observers: list[T] = []

    def register(self, observer: T) -> None:
        if observer not in self.observers:
            self.observers.append(observer)
            logger.info(f"Observer {observer} registered.")


    def unregister(self, observer: T) -> None:
        if observer in self.observers:
            self.observers.remove(observer)
            logger.info(f"Observer {observer} unregistered.")


    async def trigger(self, *args, **kwargs) -> None:
        logger.info("Triggering observers.")
        for observer in self.observers:
            await observer.trigger(*args, **kwargs)
            logger.debug(f"Observer {observer} triggered.")

