__all__ = ("MultiStream", )

# Internal
import typing as T

from asyncio import gather as agather, InvalidStateError
from warnings import warn, catch_warnings, simplefilter as warn_filter
from contextlib import suppress
from weakref import WeakKeyDictionary

# Project
from ..error import (
    ARxWarning, DisposeWarning, MultiStreamError, ObserverClosedError
)
from ..abstract.observer import Observer
from ..abstract.observable import Observable
from ..abstract.disposable import Disposable
from ..disposable.anonymous_disposable import AnonymousDisposable

K = T.TypeVar("K")


async def ensure_action(name, action, dispose):
    """Execute action and treat any exception it may raise.

    Arguments:
        name: Action name
        action: Action to be executed
        dispose: Action disposable, for when action fails
    """
    try:
        await action()
    except Exception as ex:
        if not isinstance(ex, ObserverClosedError):
            warn(
                ARxWarning(
                    "Observer was disposed due to unhandled exception during "
                    f"{name}:", ex
                )
            )
        if dispose is not None:
            with catch_warnings():
                warn_filter("ignore", category=DisposeWarning)
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

        self._observers = []  # type: T.List[Observer[K]]
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
        if observer in self._observers:
            raise MultiStreamError("Duplicate observation")

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
        self._disposable[observer] = dispose

        # Return observation disposable
        return AnonymousDisposable(dispose)
