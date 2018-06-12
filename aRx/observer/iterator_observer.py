# Internal
import typing as T

from asyncio import Future, InvalidStateError
from contextlib import suppress
from collections import deque

# Project
from ..abstract.observer import Observer

K = T.TypeVar("K")


class IteratorObserver(Observer[K], T.AsyncIterator[K]):
    """An async observer that can be iterated asynchronously."""

    def __init__(self, **kwargs) -> None:
        """IteratorObserver constructor

        Args:
            kwargs: Keyword parameters for super.
        """
        super().__init__(**kwargs)

        # Private
        self._queue = deque()  # type: T.Deque[T.Tuple[bool, K]]
        self._control = self.loop.create_future()  # type: Future
        self._counter = 0

    @property
    def _next_value(self) -> T.Tuple[bool, K]:
        """Shortcut to self._queue"""
        return self._queue.popleft()

    @_next_value.setter
    def _next_value(self, value: T.Tuple[bool, K]) -> None:
        self._queue.append(value)

        with suppress(InvalidStateError):
            self._control.set_result(True)

    def __aiter__(self) -> T.AsyncIterator[K]:
        return self

    async def __asend__(self, value: K) -> None:
        self._counter += 1
        self._next_value = (False, value)

    async def __araise__(self, err: Exception) -> bool:
        self._next_value = (True, err)
        return True

    async def __aclose__(self) -> None:
        with suppress(InvalidStateError):
            self.future.set_result(self._counter)

    async def __anext__(self) -> T.Awaitable[K]:
        while not self._queue:
            if self.closed:
                raise StopAsyncIteration()

            await self._control
            self._control = self.loop.create_future()

        is_error, value = self._next_value

        if is_error:
            raise value
        else:
            return value
