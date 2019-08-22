# Internal
import typing as T
from asyncio import ALL_COMPLETED, Future, wait
from contextlib import suppress

# Project
from ..error import MultiStreamError
from ..abstract import Observer, Namespace, Transformer
from ..disposable import AnonymousDisposable

__all__ = ("MultiStream",)


# Generic Types
K = T.TypeVar("K")


class MultiStream(Transformer[K, K]):
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
        self._observers: T.List[Observer[K]] = []

    async def __asend__(self, value: K, namespace: Namespace) -> None:
        self._observers = [obv for obv in self._observers if not obv.closed]
        if self._observers:
            awaitable = wait(
                tuple(obv.asend(value, namespace) for obv in self._observers),
                return_when=ALL_COMPLETED,
            )

            # Remove reference early to avoid keeping large objects in memory
            del value

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
        self._observers = [obv for obv in self._observers if not obv.closed]
        if self._observers:
            awaitable = wait(
                tuple(obv.araise(main_exc, namespace) for obv in self._observers),
                return_when=ALL_COMPLETED,
            )

            # Remove reference early to avoid keeping large objects in memory
            del main_exc

            done, pending = await awaitable

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
        pass

    def __observe__(self, observer: Observer[K], *, keep_alive: bool) -> AnonymousDisposable:
        # Guard against duplicated observers
        if observer in self._observers:
            raise MultiStreamError(f"{observer} is already observing this stream")

        # Add observer to internal observation list
        self._observers.append(observer)

        # Set-up dispose execution
        async def dispose_observation() -> None:
            dispose_context.clear()

            with suppress(ValueError):
                self._observers.remove(observer)

            if not (observer.closed or keep_alive):
                await observer.aclose()

        # When either this stream or observer closes or this observation is disposed
        # call dispose_observation
        dispose_context = AnonymousDisposable(dispose_observation)

        # Dispose context
        return dispose_context
