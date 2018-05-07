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

    async def __aclose__(self, *, close_observers: bool = False) -> None:
        if close_observers:
            for obv in list(self._observers):
                await obv.aclose()

        self.set_result(None)

    async def __aobserve__(self, observer: BaseObserver) -> Disposable:
        async def dispose() -> None:
            observer.remove_done_callback(dispose)

            try:
                self._observers.remove(observer)
            except ValueError:
                self._logger.warning(
                    "Dispose for [%s] was called more than once",
                    type(observer).__name__
                )

        self._observers.append(observer)

        observer.add_done_callback(dispose)

        return AnonymousDisposable(dispose)
