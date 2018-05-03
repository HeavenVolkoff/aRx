# Internal
import typing as T
from asyncio import iscoroutinefunction

# Project
from .. import abstract
from ..misc import anoop


class AnonymousDisposable(abstract.Disposable):
    def __init__(
        self, dispose: T.Callable[[], T.Awaitable[None]] = anoop, **kwargs
    ) -> None:
        if not iscoroutinefunction(dispose):
            raise TypeError("Parameter dispose must be a coroutine")

        super().__init__(**kwargs)

        self._dispose = dispose

    async def __adispose__(self) -> None:
        await self._dispose()
