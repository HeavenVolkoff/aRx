# Internal
import asyncio
import typing as T

# Project
from ..misc import coro_done_callback
from ..error import ReactiveError
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
        self._observer = None  # type: T.Optional[Observer]
        self._clean_up_listener = None  # type: T.Optional[T.Callable]

    async def __asend__(self, value: K):
        while self._observer is None:
            try:
                # Wait for observer
                await self._lock
            except asyncio.CancelledError:
                # We got disposed
                return

        await self._observer.asend(value)

    async def __araise__(self, ex: Exception) -> bool:
        while self._observer is None:
            try:
                # Wait for observer
                await self._lock
            except asyncio.CancelledError:
                # We got disposed, no need to close here
                return False

        return await self._observer.araise(ex)

    async def __aclose__(self) -> None:
        if self._observer is not None:
            self._observer.remove_done_callback(self._clean_up_listener)
            if not self._observer.keep_alive:
                await self._observer.aclose()
            self._observer = None

        if not self._lock.cancel():
            # Ensure that all waiting actions get cancelled
            self._lock = self._loop.create_future()
            self._lock.cancel()

        self.set_result(None)

    async def __aobserve__(self, observer: Observer) -> Disposable:
        """Start streaming."""
        if self._observer is not None:
            raise ReactiveError(
                "Can't assign multiple observers to a SingleStream"
            )

        # Ensure stream closes if observer closes
        self._clean_up_listener = coro_done_callback(
            observer, self.aclose(), loop=self.loop, logger=self.logger
        )

        self._observer = observer
        self._lock.set_result(None)

        return self
