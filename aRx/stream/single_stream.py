__all__ = ("SingleStream", )

# Internal
import typing as T

from asyncio import Future, CancelledError, InvalidStateError
from contextlib import suppress

# Project
from ..error import SingleStreamError
from ..abstract.observer import Observer
from ..abstract.disposable import Disposable
from ..abstract.observable import Observable

K = T.TypeVar("K")


class SingleStream(Observable, Observer[K]):
    """Cold stream tightly coupled with a single observer.

    .. Note::

        The SingleStream is cold in the sense that it will await a observer
        before forwarding any events.
    """

    def __init__(self, **kwargs) -> None:
        """SingleStream constructor.

        Arguments:
            kwargs: Super classes named parameters
        """
        super().__init__(**kwargs)

        self._lock = self._loop.create_future()  # type: Future
        self._observer = None  # type: T.Optional[Observer[K]]
        self._observer_close_promise = None

    @property
    def closed(self):
        """Property that indicates if this stream is closed or not."""
        return super().closed or (
            # Also report closed when observer is closed
            self._observer is not None and self._observer.closed
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

    async def __aclose__(self) -> None:
        observer = self._observer
        self._observer = None

        # Cancel all awaiting event in the case we weren't subscribed
        self._lock.cancel()

        # Cancel observer close guard
        if self._observer_close_promise is not None:
            self._observer_close_promise.cancel()

        # Resolve internal future
        with suppress(InvalidStateError):
            self.resolve(None)

        # Close observer if necessary
        if not (observer is None or observer.closed or observer.keep_alive):
            await observer.aclose()

    def __observe__(self, observer) -> Disposable:
        """Start streaming.

        Raises:
            SingleStreamMultipleError

        """
        if self._observer is not None:
            raise SingleStreamError(
                "Can't assign multiple observers to a SingleStream"
            )

        # Set stream observer
        self._observer = observer

        # Close Stream when observer closes
        self._observer_close_promise = observer.lastly(self.aclose)

        # Release any awaiting event
        self._lock.set_result(None)

        return self
