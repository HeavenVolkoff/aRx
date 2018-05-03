# Internal
import asyncio
import typing as T

# Project
from ..error import ReactiveError
from ..abstract import Disposable, Observer
from ..observer.base import BaseObserver
from ..observable.base import BaseObservable

K = T.TypeVar("K")


class SingleStream(BaseObservable, BaseObserver[K]):
    """An cold stream with a single observer.

    The SingleStream is cold in the sense that it will await an
    observer before forwarding any events.
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

    async def __asend__(self, value: K):
        self._logger.debug("AsyncSingleStream:__asend__(%s)", value)

        while self._observer is None:
            try:
                # Wait for observer
                await self._lock
            except asyncio.CancelledError:
                # We got disposed
                return

        await self._observer.asend(value)

    async def __araise__(self, ex: Exception) -> bool:
        self._logger.debug("AsyncSingleStream:__araise__(%s)", ex)

        while self._observer is None:
            try:
                # Wait for observer
                await self._lock
            except asyncio.CancelledError:
                # We got disposed, no need to close here
                return False

        return await self._observer.araise(ex)

    async def __aclose__(self) -> None:
        self._logger.debug("AsyncSingleStream:__aclose__()")

        if self._observer is not None:
            self._observer.aclose()
            self._observer = None

        if not self._lock.cancel():
            # Ensure that all waiting actions get cancelled
            self._lock = self._loop.create_future()
            self._lock.cancel()

    async def __aobserve__(self, observer: Observer) -> Disposable:
        """Start streaming."""
        if self._observer is not None:
            raise ReactiveError(
                "Can't assign multiple observers to a SingleStream"
            )

        self._observer = observer
        self._lock.set_result(None)

        return self
