# Internal
import asyncio
import typing as T

# Project
from .base import BaseObserver

K = T.TypeVar("K")


class IteratorObserver(BaseObserver[K], T.AsyncIterator[K]):
    """An async observer that might be iterated asynchronously."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._queue = []  # type: T.List[T.Tuple[bool, K]]
        self._control = self.loop.create_future()  # type: asyncio.Future
        self._counter = 0

    @property
    def _next_value(self) -> T.Tuple[bool, K]:
        return self._queue.pop(0)

    @_next_value.setter
    def _next_value(self, value: T.Tuple[bool, K]) -> None:
        self._queue.append(value)
        try:
            self._control.set_result(True)
        except asyncio.InvalidStateError:
            pass

    def __aiter__(self) -> T.AsyncIterator[K]:
        return self

    async def __asend__(self, value: K) -> None:
        self._counter += 1
        self._next_value = (False, value)

    async def __araise__(self, err: Exception) -> bool:
        self._next_value = (True, err)
        return True

    async def __aclose__(self) -> None:
        self._next_value = (True, StopAsyncIteration())
        self.set_result(self._counter)

    async def __anext__(self) -> T.Awaitable[K]:
        if self.closed:
            raise StopAsyncIteration()

        while not self._queue:
            await self._control
            self._control = self.loop.create_future()

        is_error, value = self._next_value

        if is_error:
            raise value
        else:
            return value
