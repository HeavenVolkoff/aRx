# Internal
import typing as T

from asyncio import Future, InvalidStateError
from contextlib import suppress

# Project
from ..error import SingleStreamMultipleError
from ..promise import Promise
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
        self._clean_up = None  # type: T.Optional[T.Callable]

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
        await self._lock
        await self._observer.asend(value)

    async def __araise__(self, ex: Exception) -> bool:
        await self._lock
        await self._observer.araise(ex)

        # SingleStream doesn't close on raise
        return False

    async def __aclose__(self) -> None:
        # Cancel all awaiting event in the case we weren't subscribed
        self._lock.cancel()

        # Clean up observer
        if self._observer is not None:
            # Cancel dispose promise
            self._clean_up.cancel()

            # Close observers that are open and don't need to outlive stream
            if not (self._observer.closed or self._observer.keep_alive):
                await self._observer.aclose()

        # Clear internal observer reference
        self._observer = None

        # Resolve internal future
        with suppress(InvalidStateError):
            self.future.set_result(None)

    def __observe__(self, observer: Observer[K]) -> Disposable:
        """Start streaming.

        Raises:
            SingleStreamMultipleError
        """
        if self._observer is not None:
            raise SingleStreamMultipleError(
                "Can't assign multiple observers to a SingleStream"
            )

        # Ensure stream closes if observer closes
        self._clean_up = Promise(observer, loop=self.loop).lastly(self.aclose)

        # Set stream observer
        self._observer = observer

        # Release any awaiting event
        self._lock.set_result(None)

        return self
