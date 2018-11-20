__all__ = ("MultiStream",)

# Internal
import typing as T
from asyncio import ALL_COMPLETED, Event, Future, InvalidStateError, wait
from contextlib import suppress

# Project
from ..error import MultiStreamError, ObserverClosedError
from ..abstract.observer import Observer
from ..abstract.observable import Observable
from ..disposable.anonymous_disposable import AnonymousDisposable

# Generic Types
J = T.TypeVar("J")
K = T.TypeVar("K")


# Observation dispose
async def dispose_observation(
    dispose_event: Event, observers: T.List[Observer[K, T.Any]], observer: Observer[K, T.Any]
) -> None:
    # Wait external signal
    await dispose_event.wait()

    try:
        observers.remove(observer)
    except ValueError:
        pass  # Already removed ignore

    if not (observer.closed or observer.keep_alive):
        await observer.aclose()


class MultiStream(Observer[K, None], Observable[K]):
    """Hot stream that can be observed by multiple observers.

    .. Note::

        The AsyncMultiStream is hot in the sense that it will drop events if
        there are currently no observer running.
    """

    def __init__(self, **kwargs: T.Any) -> None:
        """MultiStream constructor.

        Arguments:
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        # Internal
        self._observers: T.List[Observer[K, T.Any]] = []

    async def __asend__(self, value: K) -> None:
        awaitable = wait(
            tuple(obv.asend(value) for obv in self._observers if not obv.closed),
            return_when=ALL_COMPLETED,
        )

        # Remove reference early to avoid keeping large objects in memory
        del value

        done, pending = await awaitable  # type: T.Set[Future[None]], T.Set[Future[None]]

        assert not pending
        for fut in done:
            exc = fut.exception()
            if exc and not isinstance(exc, ObserverClosedError):
                raise exc

    async def __araise__(self, ex: Exception) -> bool:
        done, pending = await wait(
            tuple(obv.araise(ex) for obv in self._observers if not obv.closed),
            return_when=ALL_COMPLETED,
        )  # type: T.Set[Future[None]], T.Set[Future[None]]

        assert not pending
        for fut in done:
            exc = fut.exception()
            if exc and not isinstance(exc, ObserverClosedError):
                raise exc

        return False

    async def __aclose__(self) -> None:
        # MultiStream should resolve to None when no error is registered
        with suppress(InvalidStateError):
            self.resolve(None)

    def __observe__(self, observer: Observer[K, T.Any]) -> AnonymousDisposable:
        # Guard against duplicated observers
        if observer in self._observers:
            raise MultiStreamError(f"{observer} is already observing this stream")

        # Add observer to internal observation list
        self._observers.append(observer)

        # Set-up dispose execution
        dispose_event = Event()
        self.loop.create_task(dispose_observation(dispose_event, self._observers, observer))

        # When either this stream or observer closes sets dispose_event
        self.lastly(dispose_event.set)
        observer.lastly(dispose_event.set)

        # Sets dispose_event if this observation is disposed
        return AnonymousDisposable(dispose_event.set)
