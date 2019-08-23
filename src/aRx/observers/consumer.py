# Internal
import typing as T
from asyncio import Future

# Project
from .observer import Observer
from ..namespace import Namespace

# Generic Types
K = T.TypeVar("K")


class ConsumerExit(Exception):
    pass


class Consumer(Observer[K]):
    def __init__(self, **kwargs: T.Any) -> None:
        super().__init__(keep_alive=False, **kwargs)

        self.result: "Future[K]" = self.loop.create_future()

    async def _asend(self, value: K, _: Namespace) -> None:
        if self.result.done():
            return

        self.result.set_result(value)

        # Use exception as shorthand for closing consumer
        raise ConsumerExit

    async def _athrow(self, exc: Exception, __: Namespace) -> bool:
        if not self.result.done():
            self.result.set_exception(exc)
        return True

    async def _aclose(self) -> None:
        self.result.cancel()


__all__ = ("Consumer",)
