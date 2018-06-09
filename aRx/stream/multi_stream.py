# Internal
import typing as T

# Project
from ..promise import Promise
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

        self._observers = []  # type: T.List[BaseObserver[K]]

    async def __asend__(self, value: K) -> None:
        for obv in self._observers:
            # This is a somewhat rare situation, basically the stream processed
            # a send event after a observer closed but before it's done
            # callback, clearing it from the stream, was called
            if not obv.done():
                await obv.asend(value)

    async def __araise__(self, ex: Exception) -> bool:
        for obv in self._observers:
            # This is a somewhat rare situation, basically the stream processed
            # a raise event after a observer closed but before it's done
            # callback, clearing it from the stream, was called
            if not obv.done():  # This obv should be removed soon
                await obv.araise(ex)

        # MultiStream doesn't close on raise
        return False

    async def __aclose__(self) -> None:
        for obv in self._observers:
            # This is a somewhat rare situation, basically the stream processed
            # a close event after a observer closed but before it's done
            # callback, clearing it from the stream, was called
            if not (obv.done() or obv.keep_alive):
                await obv.aclose()

        self.set_result(None)

    async def __aobserve__(self, observer: BaseObserver[K]) -> Disposable:
        clean_up = None

        async def dispose(_=None) -> None:
            observer.remove_done_callback(clean_up)

            try:
                self._observers.remove(observer)
            except ValueError:
                self.logger.warning(
                    "Dispose for [%s] was called more than once",
                    type(observer).__name__
                )

        self._observers.append(observer)

        # Ensure stream closes if observer closes
        Promise(observer, loop=self.loop) & dispose

        return AnonymousDisposable(dispose)
