__all__ = ("IteratorObserver",)


# Internal
import typing as T
from asyncio import Future, InvalidStateError
from contextlib import suppress
from collections import deque

# External
from aRx.abstract.namespace import Namespace

# Project
from ..abstract.observer import Observer

# Generic Types
K = T.TypeVar("K")


class IteratorObserver(Observer[K], T.AsyncIterator[K]):
    """An async observer that can be iterated asynchronously."""

    def __init__(self, **kwargs: T.Any) -> None:
        """IteratorObserver constructor

        Arguments:
            kwargs: Keyword parameters for super.
        """
        super().__init__(**kwargs)

        # Private
        self._queue: T.Deque[T.Tuple[bool, T.Union[K, Exception]]] = deque()
        self._counter = 0
        self._control: "Future[None]" = self.loop.create_future()

    @property
    def _next_value(self) -> T.Tuple[bool, T.Union[K, Exception]]:
        """Shortcut to self._queue"""
        return self._queue.popleft()

    @_next_value.setter
    def _next_value(self, value: T.Tuple[bool, T.Union[K, Exception]]) -> None:
        self._queue.append(value)

        with suppress(InvalidStateError):
            self._control.set_result(None)

    def __aiter__(self) -> T.AsyncIterator[K]:
        return self

    async def __asend__(self, value: K, _: Namespace) -> None:
        self._counter += 1
        self._next_value = (False, value)

    async def __araise__(self, err: Exception, _: Namespace) -> bool:
        self._next_value = (True, err)
        return True

    async def __aclose__(self) -> None:
        pass

    async def __anext__(self) -> K:
        while not self._queue:
            if self.closed:
                raise StopAsyncIteration()

            await self._control
            self._control = self.loop.create_future()

        is_error, value = self._next_value

        if is_error:
            assert isinstance(value, Exception)
            raise value
        else:
            return T.cast(K, value)
