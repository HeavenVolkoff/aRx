# Internal
import typing as T

from asyncio import InvalidStateError
from contextlib import suppress
from warnings import warn

# Project
from ..promise import Promise
from ..abstract import Disposable
from ..abstract.observer import Observer
from ..abstract.observable import Observable
from ..disposable.anonymous_disposable import AnonymousDisposable

K = T.TypeVar("K")


class MultiStream(Observable, Observer[K]):
    """A hot stream that can be observed by multiple observers.

    .. Note::

        The AsyncMultiStream is hot in the sense that it will drop events if
        there are currently no observer running.
    """

    def __init__(self, **kwargs) -> None:
        """MultiStream constructor

        Args:
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        self._observers = []  # type: T.List[Observer[K]]

    async def __asend__(self, value: K) -> None:
        for obv in self._observers:
            # Guard against rare concurrence issue were a stream event can be
            # called after a observer closed, but before it is disposed.
            if not obv.closed:
                await obv.asend(value)

    async def __araise__(self, ex: Exception) -> bool:
        for obv in self._observers:
            # Guard against rare concurrence issue were a stream event can be
            # called after a observer closed, but before it is disposed.
            if not obv.closed:
                await obv.araise(ex)

        # MultiStream doesn't close on raise
        return False

    async def __aclose__(self) -> None:
        for obv in self._observers:
            # Close observers that are open and don't need to outlive stream
            if not (obv.closed or obv.keep_alive):
                await obv.aclose()

        with suppress(InvalidStateError):
            self.future.set_result(None)

    def __observe__(self, observer: Observer[K]) -> Disposable:
        clean_up = None

        async def dispose(_: T.Any = None) -> None:
            clean_up.cancel()

            try:
                self._observers.remove(observer)
            except ValueError:
                warn(
                    f"Dispose for [{type(observer).__qualname__}] was called "
                    f"more than once",
                    RuntimeWarning,
                )

        self._observers.append(observer)

        # Ensure stream closes if observer closes
        clean_up = Promise(observer, loop=self.loop) & dispose

        return AnonymousDisposable(dispose)
