import typing as T
import asyncio

from .bases import AsyncObserver
from .observables import AsyncObservable
from .disposables import AsyncDisposable

K = T.TypeVar("K")


class AsyncSingleStream(AsyncObserver[K], AsyncObservable[K], AsyncDisposable):
    """An stream with a single sink.

    Both an async multi future and async iterable. Thus you may
    .cancel() it to stop streaming, async iterate it using async-for.

    The AsyncSingleStream is cold in the sense that it will await an
    observer before forwarding any events.
    """

    def __init__(self) -> None:
        super().__init__()

        self._wait = Future()  # type: asyncio.Future
        self._observer = None  # type: AsyncObserver

    async def asend_core(self, value: K):
        log.debug("AsyncSingleStream:asend(%s)", value)

        # AsyncSingleStreams are cold and will await a sink.
        if self._observer is None:
            log.debug("AsyncSingleStream:asend:awaiting start")
            await self._wait
            log.debug("AsyncSingleStream:asend:awaiting:done")

        await self._observer.asend(value)

    async def athrow_core(self, ex: Exception) -> None:
        log.debug("AsyncSingleStream:athrow()")

        await self.await_subscriber()
        await self._observer.araise(ex)

    async def aclose_core(self) -> None:
        log.debug("AsyncSingleStream:aclose()")

        if self._observer is None:
            log.debug("AsyncSingleStream:aclose:awaiting start")
            await self._wait

        await self._observer.aclose()

    async def await_subscriber(self):
        while self._observer is None:
            log.debug("AsyncSingleStream:await_subscriber()")
            await self._wait

    async def __adispose__(self):
        self._observer = None
        self._is_stopped = True
        self.cancel()

    async def __asubscribe__(self, observer: AsyncObserver) -> AsyncDisposable:
        """Start streaming."""

        self._observer = observer

        if not self._wait.done():
            self._wait.set_result(True)

        return AsyncDisposable(self.__adispose__)


class AsyncMultiStream(AsyncObserver[K], AsyncObservable[K]):
    """An stream with a multiple observers.

    Both an async multi future and async iterable. Thus you may
    .cancel() it to stop streaming, async iterate it using async-for.

    The AsyncMultiStream is hot in the sense that it will drop events
    if there are currently no observer running.
    """

    def __init__(self) -> None:
        super().__init__()
        self._observers = []  # type: List[AsyncObserver]

    async def asend_core(self, value: K) -> None:
        for obv in list(self._observers):
            await obv.asend(value)

    async def athrow_core(self, ex: Exception) -> None:
        for obv in list(self._observers):
            await obv.araise(ex)

    async def aclose_core(self) -> None:
        for obv in list(self._observers):
            await obv.aclose()

    async def __asubscribe__(self, observer: AsyncObserver) -> AsyncDisposable:
        """Subscribe."""

        log.debug("AsyncMultiStream:subscribe")

        self._observers.append(observer)

        async def dispose() -> None:
            log.debug("AsyncMultiStream:dispose()")
            if observer in self._observers:
                print("Remove")
                self._observers.remove(observer)

        return AsyncDisposable(dispose)


# Alias
AsyncStream = AsyncMultiStream
