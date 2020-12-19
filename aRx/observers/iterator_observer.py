"""IteratorObserver

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

# Internal
import typing as T
from asyncio import Future, get_running_loop
from collections import deque

# Project
from .observer import Observer

if T.TYPE_CHECKING:
    # Project
    from ..namespace import Namespace


# Generic Types
K = T.TypeVar("K")


class IteratorObserver(Observer[K], T.AsyncIterator[K]):
    """An async observers that can be iterated asynchronously."""

    def __init__(self, **kwargs: T.Any) -> None:
        """IteratorObserver constructor

        Arguments:
            kwargs: Keyword parameters for super.
        """

        super().__init__(**kwargs)

        # Private
        self._queue: T.Deque[T.Tuple[bool, T.Union[K, Exception]]] = deque()
        self._counter = 0
        self._control: T.Optional["Future[bool]"] = None

    @property
    def _next_value(self) -> T.Tuple[bool, T.Union[K, Exception]]:
        """Shortcut to self._queue"""
        return self._queue.popleft()

    @_next_value.setter
    def _next_value(self, value: T.Tuple[bool, T.Union[K, Exception]]) -> None:
        self._queue.append(value)

        if self._control and not self._control.done():
            self._control.set_result(True)

    def __aiter__(self) -> T.AsyncIterator[K]:
        return self

    async def _asend(self, value: K, _: "Namespace") -> None:
        self._counter += 1
        self._next_value = (False, value)

    async def _athrow(self, err: Exception, _: "Namespace") -> bool:
        self._next_value = (True, err)
        return True

    async def _aclose(self) -> None:
        if self._control and not self._control.done():
            self._control.set_result(True)

    async def __anext__(self) -> K:
        loop = get_running_loop()

        while not self._queue:
            if self.closed:
                raise StopAsyncIteration()

            if self._control is None or (await self._control and not self.closed):
                self._control = loop.create_future()

        is_error, value = self._next_value

        if is_error:
            assert isinstance(value, Exception)
            raise value
        else:
            return T.cast(K, value)


__all__ = ("IteratorObserver",)
