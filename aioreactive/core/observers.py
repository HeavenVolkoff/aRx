import asyncio
from typing import TypeVar, AsyncIterator, AsyncIterable, List, Any, Optional
import logging

from .bases import AsyncObserverBase
from .utils import anoop

log = logging.getLogger(__name__)

T = TypeVar("T")


class AsyncIteratorObserver(AsyncObserverBase[T], AsyncIterable[T]):
    """An async observer that might be iterated asynchronously."""

    def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        super().__init__()
        self._loop = loop if loop is not None else asyncio.get_event_loop()
        self._queue = []  # type: List[Any]
        self._control = self._loop.create_future()  # type: asyncio.Future

    async def asend_core(self, value: T) -> None:
        self._queue.append((False, value))
        self._control.set_result(True)

    async def athrow_core(self, err: Exception) -> None:
        self._queue.append((True, err))
        self._control.set_result(True)

    async def aclose_core(self) -> None:
        self._queue.append((True, StopAsyncIteration))
        self._control.set_result(True)

    async def __aiter__(self) -> AsyncIterator:
        return self

    async def __anext__(self) -> T:
        while not self._queue:
            await self._control

        is_error, value = self._queue.pop(0)

        if is_error:
            return value
        else:
            raise value


class AsyncAnonymousObserver(AsyncObserverBase):
    """An anonymous AsyncObserver.

    Creates as sink where the implementation is provided by three
    optional and anonymous functions, asend, athrow and aclose. Used for
    listening to a source."""

    def __init__(self, asend=anoop, athrow=anoop, aclose=anoop) -> None:
        super().__init__()

        assert asyncio.iscoroutinefunction(asend)
        self._send = asend

        assert asyncio.iscoroutinefunction(athrow)
        self._throw = athrow

        assert asyncio.iscoroutinefunction(aclose)
        self._close = aclose

    async def asend_core(self, value: T) -> None:
        await self._send(value)

    async def athrow_core(self, ex: Exception) -> None:
        await self._throw(ex)

    async def aclose_core(self) -> None:
        await self._close()


class AsyncNoopObserver(AsyncAnonymousObserver):
    """An no operation Async Observer."""

    def __init__(self, asend=anoop, athrow=anoop, aclose=anoop) -> None:
        super().__init__(asend, athrow, aclose)
