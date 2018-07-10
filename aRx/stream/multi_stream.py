__all__ = ("MultiStream", )

# Internal
import typing as T

from weakref import WeakKeyDictionary, ReferenceType
from asyncio import gather as agather, InvalidStateError, CancelledError
from warnings import warn
from functools import partial
from contextlib import suppress

# Project
from ..misc.flag import Flag
from ..error import (ARxWarning, MultiStreamError, ObserverClosedError)
from ..promise import Promise
from ..abstract.observer import Observer
from ..abstract.observable import Observable
from ..abstract.disposable import Disposable
from ..disposable.anonymous_disposable import AnonymousDisposable

K = T.TypeVar("K")


# Allow List to be weak referenced
class List(list):
    pass


# Observation dispose
async def dispose_observation(
    disposed: Flag,
    promises: T.List[Promise[None]],
    *,
    _observer: ReferenceType,
    _observers: ReferenceType,
) -> None:
    # Guard against repeated calls
    if disposed:
        return

    disposed.set_true()

    # Cancel dispose promises to ensure no retention
    for promise in promises:
        promise.cancel()

    # Clear cancelled promises
    promises.clear()

    # Remove observer from internal list and close it
    observer = _observer()
    if observer is not None:
        observers = _observers()
        if observers is not None:
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
                        "Failed to exec aclose on "
                        f"{type(observer).__qualname__}", ex
                    )
                )


async def ensure_action(
    name: str, action: T.Awaitable, dispose: T.Callable[[], None]
):
    """Execute action and treat any exception it may raise.

    Arguments:
        name: Action name
        action: Action to be executed
        dispose: Action disposable, for when action fails
    """
    try:
        await action
    except Exception as ex:
        if not isinstance(ex, (ObserverClosedError, CancelledError)):
            warn(
                ARxWarning(
                    "Observer was disposed due to unhandled exception during "
                    f"{name}:", ex
                )
            )
        if dispose is not None:
            await dispose()


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

        self._observers = List()  # type: T.List[Observer[K]]
        self._disposable = WeakKeyDictionary()

    async def __asend__(self, value: K) -> None:
        awaitables = tuple(
            ensure_action(
                "asend", obv.asend(value), self._disposable.get(obv, None)
            ) for obv in self._observers if not obv.closed
        )

        # Remove reference early to avoid keeping large objects in memory
        del value

        await agather(*awaitables)

    async def __araise__(self, ex: Exception) -> bool:
        await agather(
            *(
                ensure_action(
                    "araise", obv.araise(ex), self._disposable.get(obv, None)
                ) for obv in self._observers
            )
        )

        return False

    async def __aclose__(self) -> None:
        # MultiStream should resolve to None when no error is registered
        with suppress(InvalidStateError):
            self.resolve(None)

    def __observe__(self, observer: Observer[K]) -> Disposable:
        # Guard against repeated observation
        if observer in self._observers:
            raise MultiStreamError("Duplicate observation")

        # Add observer to internal observation list
        self._observers.append(observer)

        promises = []
        dispose = partial(
            dispose_observation,
            Flag(),
            promises,
            _observer=ReferenceType(observer),
            _observers=ReferenceType(self._observers),
        )

        # Save weakref to dispose
        self._disposable[observer] = dispose

        # Ensure that observable is disposed when it or the stream closes
        promises.extend((observer.lastly(dispose), self.lastly(dispose)))

        # Return observation disposable
        return AnonymousDisposable(dispose)
