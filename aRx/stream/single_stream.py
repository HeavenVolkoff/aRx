# Internal
import asyncio
import typing as T

# Project
from ..error import ObserverClosedError, SingleStreamMultipleError
from ..promise import Promise
from ..abstract import Disposable, Observer
from ..observer.base import BaseObserver
from ..observable.base import BaseObservable

K = T.TypeVar("K")


class SingleStream(BaseObservable, BaseObserver[K]):
    """An cold stream tightly coupled with a single observer.

    The SingleStream is cold in the sense that it will await a observer before
    forwarding any events.
    """

    def __init__(self, **kwargs) -> None:
        """SingleStream constructor.

        Args:
            kwargs: Super classes named parameters
        """
        super().__init__(**kwargs)

        self._lock = \
            self._loop.create_future()  # type: T.Optional[asyncio.Future]
        self._observer = None  # type: T.Optional[Observer[K]]
        self._clean_up_listener = None  # type: T.Optional[T.Callable]

    async def __asend__(self, value: K):
        while self._observer is None:
            try:
                # Wait for observer
                await self._lock
            except asyncio.CancelledError:
                # We got disposed
                return

        # This is a somewhat rare situation, basically the stream processed
        # a send event after a observer closed but before it's done
        # callback, closing the stream, was called
        if not self._observer.done():
            await self._observer.asend(value)
        else:
            await self.aclose()
            raise ObserverClosedError(self)

    async def __araise__(self, ex: Exception) -> bool:
        while self._observer is None:
            try:
                # Wait for observer
                await self._lock
            except asyncio.CancelledError:
                # We got disposed, no need to close here
                return False

            # This is a somewhat rare situation, basically the stream processed
            # a raise event after a observer closed but before it's done
            # callback, closing the stream, was called
            if not self._observer.done():
                await self._observer.araise(ex)
            else:
                await self.aclose()
                raise ObserverClosedError(self)

    async def __aclose__(self) -> None:
        if self._observer is not None:
            self._observer.remove_done_callback(self._clean_up_listener)
            if not (self._observer.done() or self._observer.keep_alive):
                await self._observer.aclose()
            self._observer = None

        if not self._lock.cancel():
            # Ensure that all waiting actions get cancelled
            self._lock = self._loop.create_future()
            self._lock.cancel()

        self.set_result(None)

    async def __aobserve__(self, observer: Observer[K]) -> Disposable:
        """Start streaming."""
        if self._observer is not None:
            raise SingleStreamMultipleError(
                "Can't assign multiple observers to a SingleStream"
            )

        # Ensure stream closes if observer closes
        Promise(observer, loop=self.loop) & (lambda _: self.aclose())

        self._observer = observer
        self._lock.set_result(None)

        return self
