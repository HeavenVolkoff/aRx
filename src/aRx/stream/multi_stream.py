__all__ = ("MultiStream",)


# Internal
import typing as T
from asyncio import ALL_COMPLETED, Future, InvalidStateError, wait
from contextlib import suppress

# Project
from ..error import MultiStreamError
from ..misc.namespace import Namespace, get_namespace
from ..abstract.observer import Observer
from ..abstract.observable import Observable
from ..disposable.anonymous_disposable import AnonymousDisposable

# Generic Types
K = T.TypeVar("K")


class MultiStream(Observer[K, None], Observable[K]):
    """Hot stream that can be observed by multiple observers.

    .. Note::

        The AsyncMultiStream is hot in the sense that it will drop events if there are currently no
        observer running, and all redirection only enqueue the observer action, not waiting for it's
        execution.
    """

    def __init__(self, **kwargs: T.Any) -> None:
        """MultiStream constructor.

        Arguments:
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        # Internal
        self._observers: T.List[Observer[K, T.Any]] = []

    async def __asend__(self, value: K, namespace: Namespace) -> None:
        send_event = tuple(
            obv.asend(value, get_namespace(self, namespace))
            for obv in self._observers
            if not obv.closed
        )
        if send_event:
            awaitable = wait(send_event, return_when=ALL_COMPLETED)

            # Remove reference early to avoid keeping large objects in memory
            del value
            del send_event

            done, pending = await awaitable  # type: T.Set[Future[None]], T.Set[Future[None]]

            assert not pending

            for fut in done:
                exc = fut.exception()
                if exc:
                    self.loop.call_exception_handler(
                        {
                            "message": (
                                "Unhandled exception while attempt "
                                "to propagate data through observer"
                            ),
                            "exception": exc,
                        }
                    )

    async def __araise__(self, main_exc: Exception, namespace: Namespace) -> bool:
        raise_event = tuple(
            obv.araise(main_exc, get_namespace(self, namespace))
            for obv in self._observers
            if not obv.closed
        )
        if raise_event:
            awaitable = wait(raise_event, return_when=ALL_COMPLETED)

            # Remove reference early to avoid keeping large objects in memory
            del main_exc
            del raise_event

            done, pending = await awaitable  # type: T.Set[Future[None]], T.Set[Future[None]]

            assert not pending

            for fut in done:
                exc = fut.exception()
                if exc:
                    self.loop.call_exception_handler(
                        {
                            "message": (
                                "Unhandled exception while attempt "
                                "to propagate exception through observer"
                            ),
                            "exception": exc,
                        }
                    )

        # A MultiStream never closes on araise
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
        async def dispose_observation() -> None:
            dispose_context.clear()
            stream_dispose_promise.cancel(task=False)
            observer_dispose_promise.cancel(task=False)

            with suppress(ValueError):
                self._observers.remove(observer)

            if not (observer.closed or observer.keep_alive):
                await observer.aclose()

        # When either this stream or observer closes or this observation is disposed
        # call dispose_observation
        dispose_context = AnonymousDisposable(dispose_observation)
        stream_dispose_promise = self.lastly(dispose_observation)
        observer_dispose_promise = observer.lastly(dispose_observation)

        # Dispose context
        return dispose_context
