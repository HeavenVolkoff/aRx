# Internal
import typing as T

# Project
from ..abstract import Disposable
from ..observer.base import BaseObserver
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

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self._observers = []  # type: T.List[BaseObserver]

    async def __asend__(self, value: K) -> None:
        for obv in list(self._observers):
            await obv.asend(value)

    async def __araise__(self, ex: Exception) -> bool:
        for obv in list(self._observers):
            await obv.araise(ex)

        # MultiStream doesn't close on raise
        return False

    async def __aclose__(self) -> None:
        for obv in list(self._observers):
            await obv.aclose()

    async def __aobserve__(self, observer: BaseObserver) -> Disposable:
        """Subscribe."""

        self._logger.debug("AsyncMultiStream:subscribe")

        self._observers.append(observer)

        async def dispose() -> None:
            self._logger.debug("AsyncMultiStream:dispose()")
            if observer in self._observers:
                print("Remove")
                # TODO: Should we close observer on dispose?
                self._observers.remove(observer)

        return AnonymousDisposable(dispose)
