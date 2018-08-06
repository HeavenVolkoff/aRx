__all__ = ("MultiStream",)

import typing as T
from asyncio import Event, InvalidStateError, gather as agather
from warnings import warn
from contextlib import suppress

from ..error import ARxWarning, MultiStreamError
from ..promise import Promise
from ..abstract.observer import Observer
from ..abstract.disposable import Disposable
from ..abstract.observable import Observable
from ..disposable.anonymous_disposable import AnonymousDisposable

K = T.TypeVar("K")


# Observation dispose
async def dispose_observation(
    observer: Observer, observers: T.List[Observer], dispose_event: Event
) -> None:
    # Wait external signal
    await dispose_event.wait()

    try:
        observers.remove(observer)
    except ValueError:
        pass  # Already removed ignore

    if not (observer.closed or observer.keep_alive):
        try:
            await observer.aclose()
        except Exception as ex:
            warn(
                ARxWarning(
                    "Failed to exec aclose on " f"{type(observer).__qualname__}", ex
                )
            )


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
        awaitables = tuple(
            obv.asend(value) for obv in self._observers if not obv.closed
        )

        # Remove reference early to avoid keeping large objects in memory
        del value

        await agather(*awaitables)

    async def __araise__(self, ex: Exception) -> bool:
        await agather(*(obv.araise(ex) for obv in self._observers if not obv.closed))

        return False

    async def __aclose__(self) -> None:
        # MultiStream should resolve to None when no error is registered
        with suppress(InvalidStateError):
            self.resolve(None)

    def __observe__(self, observer) -> Disposable:
        # Guard against repeated observation
        if observer in self._observers:
            raise MultiStreamError("Duplicate observation")

        # Add observer to internal observation list
        self._observers.append(observer)

        dispose_event = Event()
        dispose_stream = self.lastly(dispose_event.set)
        dispose_observer = observer.lastly(dispose_event.set)

        # Set-up dispose execution
        dispose_promise = Promise(
            dispose_observation(observer, self._observers, dispose_event)
        )
        dispose_promise.lastly(dispose_stream.cancel)
        dispose_promise.lastly(dispose_observer.cancel)

        # Return observation disposable
        return AnonymousDisposable(dispose_event.set)
