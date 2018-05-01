# Internal
import asyncio
import typing as T

from collections.abc import AsyncIterator

# Project
from .base import BaseObserver

K = T.TypeVar("K")


class IteratorObserver(BaseObserver[K], AsyncIterator[K]):
    """An async observer that might be iterated asynchronously."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._queue = []  # type: T.List[K]
        self._control = self._loop.create_future()  # type: asyncio.Future

    async def __asend__(self, value: K) -> None:
        self._queue.append((False, value))
        try:
            self._control.set_result(True)
        except asyncio.InvalidStateError:
            pass

    async def __araise__(self, err: Exception) -> None:
        self._queue.append((True, err))
        try:
            self._control.set_result(True)
        except asyncio.InvalidStateError:
            pass

    async def __aclose__(self) -> None:
        self._queue.append((True, StopAsyncIteration))
        try:
            self._control.set_result(True)
        except asyncio.InvalidStateError:
            pass

    async def __aiter__(self) -> AsyncIterator[K]:
        return self

    async def __anext__(self) -> T.Awaitable[K]:
        while not self._queue:
            await self._control
            self._control = self._loop.create_future()

        is_error, value = self._queue.pop(0)

        if is_error:
            raise value
        else:
            return value
