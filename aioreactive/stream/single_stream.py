# Internal
import asyncio
import typing as T

# Project
from ..observer.base import BaseObserver
from ..abstract.observer import Observer
from ..abstract.disposable import Disposable
from ..observable.base import BaseObservable

K = T.TypeVar("K")


class SingleStream(BaseObservable, BaseObserver[K]):
    """An stream with a single sink.

    Both an async multi future and async iterable. Thus you may
    .cancel() it to stop streaming, async iterate it using async-for.

    The AsyncSingleStream is cold in the sense that it will await an
    observer before forwarding any events.
    """

    def __init__(self, *args, **kwargs) -> None:
        BaseObservable.__init__(self, *args, **kwargs)
        BaseObserver.__init__(self, *args, **kwargs)

        self._wait = \
            self._loop.create_future()  # type: T.Optional[asyncio.Future]
        self._observer = None  # type: BaseObserver

    async def await_subscriber(self) -> None:
        while self._observer is None and self._wait is not None:
            self._logger.debug("AsyncSingleStream:await_subscriber()")
            await self._wait

    async def __asend__(self, value: K):
        self._logger.debug("AsyncSingleStream:__asend__(%s)", value)
        await self.await_subscriber()
        await self._observer.asend(value)

    async def __araise__(self, ex: Exception) -> None:
        self._logger.debug("AsyncSingleStream:__araise__(%s)", ex)
        await self.await_subscriber()
        await self._observer.araise(ex)

    async def __aclose__(self) -> None:
        self._logger.debug("AsyncSingleStream:__aclose__()")
        await self.await_subscriber()
        await self._observer.aclose()

    async def __adispose__(self) -> None:
        self._wait = None
        self._observer = None

        await BaseObserver.__adispose__(self)

    async def __aobserve__(self, observer: T.Optional[Observer]) -> Disposable:
        """Start streaming."""
        self._observer = observer

        if observer is None:
            if self._wait.done():
                self._wait = self._loop.create_future()
        else:
            if not self._wait.done():
                self._wait.set_result(True)

        return self
