# Internal
import asyncio
import typing as T

from collections.abc import AsyncIterator

# Project
from .utils import anoop
from .bases import AsyncObserver

K = T.TypeVar("K")


class AsyncIteratorObserver(AsyncObserver[K], AsyncIterator[K]):
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


class AsyncAnonymousObserver(AsyncObserver[K]):
    """An anonymous AsyncObserver.

    Creates as sink where the implementation is provided by three
    optional and anonymous functions, asend, araise and aclose. Used for
    listening to a source."""

    def __init__(
        self,
        asend_coro: T.Callable[[K], T.Awaitable[None]] = anoop,
        araise_coro: T.Callable[[Exception], T.Awaitable[None]] = anoop,
        aclose_coro: T.Callable[None, T.Awaitable[None]] = anoop
    ) -> None:
        super().__init__()

        if not asyncio.iscoroutinefunction(asend_coro):
            raise TypeError("asend must be a coroutine")

        if not asyncio.iscoroutinefunction(araise_coro):
            raise TypeError("araise must be a coroutine")

        if not asyncio.iscoroutinefunction(aclose_coro):
            raise TypeError("aclose must be a coroutine")

        self._send = asend_coro
        self._throw = araise_coro
        self._close = aclose_coro

    async def __asend__(self, value: K) -> None:
        await self._send(value)

    async def __araise__(self, ex: Exception) -> None:
        await self._throw(ex)

    async def __aclose__(self) -> None:
        await self._close()
