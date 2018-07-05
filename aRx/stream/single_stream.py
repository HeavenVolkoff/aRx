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

        self._lock = self._loop.create_future()  # type: T.Optional[Future]
        self._observer = None  # type: T.Optional[Observer[K]]

    @property
    def closed(self):
        """Property that indicates if this observer is closed or not."""
        return super().closed or (
            # Guard against rare concurrence issue were a stream event can be
            # called after a observer closed, but before it is disposed.
            self._observer is not None and self._observer.closed
        )

    async def __asend__(self, value: K):
        # Wait for observer
        try:
            await self._lock
        except CancelledError:
            pass
        else:
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
            await self._observer.araise(ex)

        # SingleStream doesn't close on raise
        return False

    async def __aclose__(self) -> None:
        observer = self._observer
        self._observer = None

        # Cancel all awaiting event in the case we weren't subscribed
        self._lock.cancel()

        # Resolve internal future
        with suppress(InvalidStateError):
            self.resolve(None)

        # Close observer if necessary
        if not (observer is None or observer.closed or observer.keep_alive):
            await observer.aclose()

    def __observe__(self, observer: Observer[K]) -> Disposable:
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

        # Release any awaiting event
        self._lock.set_result(None)

        return self
