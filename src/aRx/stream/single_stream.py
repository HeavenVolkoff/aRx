__all__ = ("SingleStream",)

# Internal
import typing as T
from asyncio import Future, InvalidStateError
from contextlib import suppress

# Project
from ..error import SingleStreamError
from ..promise import Promise
from ..abstract.observer import Observer
from ..abstract.disposable import Disposable
from ..abstract.observable import Observable

# Generic Types
K = T.TypeVar("K")


class SingleStream(Observer[K, None], Observable[K]):
    """Cold stream tightly coupled with a single observer.

    .. Note::

        The SingleStream is cold in the sense that it is tightly connected to it's only observer.
        So that it will await until it is observed before redirecting any event, and all redirection
        wait for the observer action to execute.
    """

    def __init__(self, **kwargs: T.Any) -> None:
        """SingleStream constructor.

        Arguments:
            kwargs: Super classes named parameters.

        """
        super().__init__(**kwargs)

        # Internal
        self._lock: Future[None] = self._loop.create_future()
        self._observer: T.Optional[Observer[K, T.Any]] = None
        self._observer_close_promise: T.Optional[Promise[bool]] = None

    @property
    def closed(self) -> bool:
        """Property that indicates if this stream is closed or not."""
        return bool(
            super().closed
            or (
                # Also report closed when observer is closed
                self._observer
                and self._observer.closed
            )
        )

    async def __asend__(self, value: K) -> None:
        # Wait for observer
        await self._lock

        # _observer must be available at this point
        assert self._observer

        awaitable = self._observer.asend(value)

        # Remove reference early to avoid keeping large objects in memory
        del value

        await awaitable

    async def __araise__(self, exc: Exception) -> bool:
        # Wait for observer
        await self._lock

        # _observer must be available at this point
        assert self._observer

        await self._observer.araise(exc)

        # SingleStream doesn't close on raise
        return False

    async def __aclose__(self) -> None:
        # Cancel all awaiting event in the case we weren't subscribed
        self._lock.cancel()

        # Cancel observer close guard
        if self._observer_close_promise:
            self._observer_close_promise.cancel()

        # Resolve internal future
        with suppress(InvalidStateError):
            self.resolve(None)

        # Close observer if necessary
        if self._observer and not (self._observer.closed or self._observer.keep_alive):
            await self._observer.aclose()

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
