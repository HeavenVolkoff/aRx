# Internal
import typing as T

# Project
from ..observer.base import BaseObserver
from ..abstract.observer import Observer
from ..abstract.disposable import Disposable
from ..observable.base import BaseObservable
from ..disposable.anonymous_disposable import AnonymousDisposable

K = T.TypeVar("K")


class MultiStream(BaseObservable, BaseObserver[K]):
    """An stream with a multiple observers.

    Both an async multi future and async iterable. Thus you may
    .cancel() it to stop streaming, async iterate it using async-for.

    The AsyncMultiStream is hot in the sense that it will drop events
    if there are currently no observer running.
    """

    def __init__(self, *args, **kwargs) -> None:
        BaseObservable.__init__(self, *args, **kwargs)
        BaseObserver.__init__(self, *args, **kwargs)

        self._observers = []  # type: T.List[BaseObserver]

    async def __asend__(self, value: K) -> None:
        for obv in list(self._observers):
            await obv.asend(value)

    async def __araise__(self, ex: Exception) -> None:
        for obv in list(self._observers):
            await obv.araise(ex)

    async def __aclose__(self) -> None:
        for obv in list(self._observers):
            await obv.aclose()

    async def __aobserve__(self, observer: Observer) -> Disposable:
        """Subscribe."""

        self._logger.debug("AsyncMultiStream:subscribe")

        self._observers.append(observer)

        async def dispose() -> None:
            self._logger.debug("AsyncMultiStream:dispose()")
            if observer in self._observers:
                print("Remove")
                self._observers.remove(observer)

        return AnonymousDisposable(dispose)
