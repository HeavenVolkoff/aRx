# Internal
import typing as T

from asyncio import gather as agather, InvalidStateError
from warnings import warn
from contextlib import suppress

# Project
from ..error import DisposeWarning, ARxWarning
from ..abstract.observer import Observer
from ..abstract.observable import Observable
from ..abstract.disposable import Disposable
from ..disposable.anonymous_disposable import AnonymousDisposable

K = T.TypeVar("K")


class MultiStream(Observable, Observer[K]):
    """Hot stream that can be observed by multiple observers.

    .. Note::

        The AsyncMultiStream is hot in the sense that it will drop events if
        there are currently no observer running.
    """

    def __init__(self, **kwargs) -> None:
        """MultiStream constructor

        Arguments:
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        self._observers = []  # type: T.List[Observer[K]]

    async def __asend__(self, value: K) -> None:
        # Filter only open observers to prevent errors due to sending data to
        # closed observers that didn't have their disposed called yet
        awaitables = [
            obv.asend(value) for obv in self._observers if not obv.closed
        ]

        # Remove reference early to avoid keeping large objects in memory
        del value

        await agather(*awaitables)

    async def __araise__(self, main_ex: Exception) -> bool:
        await agather(
            *(obv.araise(main_ex) for obv in self._observers if not obv.closed)
        )

        return False

    async def __aclose__(self) -> None:
        # MultiStream should resolve to None when no error is registered
        with suppress(InvalidStateError):
            self.future.set_result(None)

    def __observe__(self, observer: Observer[K]) -> Disposable:
        stream_name = type(self).__qualname__

        async def dispose() -> None:
            # Cancel dispose promises to ensure no retention
            dispose_promise.cancel()
            stream_close_promise.cancel()

            try:
                self._observers.remove(observer)
            except ValueError:
                warn(
                    DisposeWarning(
                        "Dispose for observation "
                        f"`[{stream_name}] > [{type(observer).__qualname__}]` "
                        "was called more than once",
                    )
                )

            if not (observer.closed or observer.keep_alive):
                try:
                    await observer.aclose()
                except Exception as ex:
                    warn(
                        ARxWarning(
                            "Failed to exec aclose on "
                            f"{type(observer).__qualname__}", ex
                        )
                    )

        # Ensure that observable is disposed when it closes
        dispose_promise = observer.lastly(dispose)
        # Ensure that observable is disposed when stream closes
        stream_close_promise = self.lastly(dispose)

        # Add observer to internal list
        self._observers.append(observer)

        # Return observation disposable
        return AnonymousDisposable(dispose)
