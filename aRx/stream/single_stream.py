__all__ = ("SingleStream",)

import typing as T
from asyncio import Future, CancelledError, InvalidStateError
from contextlib import suppress

from ..error import SingleStreamError
from ..promise import Promise
from ..abstract.observer import Observer
from ..abstract.disposable import Disposable
from ..abstract.observable import Observable

K = T.TypeVar("K")


class SingleStream(Observer[K, None], Observable[K]):
    """Cold stream tightly coupled with a single observer.

    .. Note::

        The SingleStream is cold in the sense that it will await a observer
        before forwarding any events.
    """

    def __init__(self, **kwargs) -> None:
        """SingleStream constructor.

        Arguments:
            kwargs: Super classes named parameters.

        """
        super().__init__(**kwargs)

        self._lock = self._loop.create_future()  # type: Future
        self._observer = None  # type: T.Optional[Observer[K, T.Any]]
        self._observer_close_promise = None  # type: T.Optional[Promise]

    @property
    def closed(self):
        """Property that indicates if this stream is closed or not."""
        return super().closed or (
            # Also report closed when observer is closed
            self._observer
            and self._observer.closed
        )

    async def __asend__(self, value: K):
        # Wait for observer
        try:
            await self._lock
        except CancelledError:
            pass
        else:
            if self._observer is None:
                raise RuntimeError("Observer is None")

            awaitable = self._observer.asend(value)

            # Remove reference early to avoid keeping large objects in memory
            del value

            await awaitable

    async def __araise__(self, ex: Exception) -> bool:
        try:
            await self._lock
        except CancelledError:
            pass
        else:
            if self._observer is None:
                raise RuntimeError("Observer is None")

            await self._observer.araise(ex)

        # SingleStream doesn't close on raise
        return False

    async def __aclose__(self):
        observer = self._observer
        self._observer = None

        # Cancel all awaiting event in the case we weren't subscribed
        self._lock.cancel()

        # Cancel observer close guard
        if self._observer_close_promise:
            self._observer_close_promise.cancel()

        # Resolve internal future
        with suppress(InvalidStateError):
            self.resolve(None)

        # Close observer if necessary
        if not (observer is None or observer.closed or observer.keep_alive):
            await observer.aclose()

    def __observe__(self, observer: Observer[K, T.Any]) -> Disposable:
        """Start streaming.

        Raises:
            SingleStreamMultipleError

        """
        if self._observer:
            raise SingleStreamError("Can't assign multiple observers to a SingleStream")

        # Set stream observer
        self._observer = observer

        # Close Stream when observer closes
        self._observer_close_promise = observer.lastly(self.aclose)

        # Release any awaiting event
        self._lock.set_result(None)

        return self
