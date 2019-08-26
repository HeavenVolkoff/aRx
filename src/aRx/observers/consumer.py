# Internal
import typing as T

# Project
from ..error import ConsumerClosedError
from .observer import Observer

if T.TYPE_CHECKING:
    # Internal
    from asyncio import Future

    # Project
    from ..namespace import Namespace


# Generic Types
K = T.TypeVar("K")


class Consumer(Observer[K]):
    def __init__(self, **kwargs: T.Any) -> None:
        super().__init__(keep_alive=False, **kwargs)

        self.result: "Future"[K] = self.loop.create_future()

    async def _asend(self, value: K, _: "Namespace") -> None:
        if self.result.done():
            return

        self.result.set_result(value)

        # Use exception as shorthand for closing consumer
        raise ConsumerClosedError

    async def _athrow(self, exc: Exception, _: "Namespace") -> bool:
        if not self.result.done():
            self.result.set_exception(exc)
        return True

    async def _aclose(self) -> None:
        if not self.result.done():
            self.result.set_exception(ConsumerClosedError)


__all__ = ("Consumer",)
