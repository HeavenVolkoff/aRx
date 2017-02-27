import asyncio
from typing import TypeVar

from aioreactive import core

T = TypeVar('T')


class AsyncStreamBase(core.AsyncObserver):
    """A stream base for testing.

    Provides methods for sending, throwing, and closing at a later
    time both relative and absolute.
    """

    async def asend_at(self, when: float, value: T):
        async def task() -> None:
            await self.asend(value)

        def callback() -> None:
            asyncio.ensure_future(task())

        self._loop.call_at(when, callback)

    async def asend_later(self, delay: float, value: T) -> None:
        await asyncio.sleep(delay)
        await self.asend(value)

    async def asend_later_scheduled(self, delay: float, value: T) -> None:
        async def task() -> None:
            await asyncio.sleep(delay)
            await self.asend(value)
        asyncio.ensure_future(task())

    async def athrow_at(self, when: float, err: Exception) -> None:
        async def task() -> None:
            await self.athrow(err)

        def callback() -> None:
            asyncio.ensure_future(task())

        self._loop.call_at(when, callback)

    async def athrow_later(self, delay: float, err: Exception) -> None:
        await asyncio.sleep(delay)
        await self.athrow(err)

    async def athrow_later_scheduled(self, delay: float, err: Exception) -> None:
        async def task():
            await asyncio.sleep(delay)
            await self.athrow(err)
        asyncio.ensure_future(task())

    async def aclose_at(self, when: float):
        async def task():
            await self.aclose()

        def callback():
            asyncio.ensure_future(task())

        self._loop.call_at(when, callback)

    async def aclose_later(self, delay: float):
        await asyncio.sleep(delay)
        await self.aclose()

    async def close_later_scheduled(self, delay: float):
        async def task():
            await asyncio.sleep(delay)
            await self.aclose()
        asyncio.ensure_future(task())


class AsyncMultipleStream(core.AsyncStream, AsyncStreamBase):
    pass

AsyncStream = AsyncMultipleStream


class AsyncSingleStream(core.AsyncSingleStream, AsyncStreamBase):

    def __init__(self):
        super().__init__()
        #self._loop = asyncio.get_event_loop()
