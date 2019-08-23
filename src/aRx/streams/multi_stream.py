# Internal
import typing as T
from asyncio import ALL_COMPLETED, Future, wait
from contextlib import suppress

# Project
from ..error import MultiStreamError
from ..namespace import Namespace
from ..observers import Observer
from ..protocols import ObserverProtocol, TransformerProtocol
from ..observables import Observable

__all__ = ("MultiStream",)


# Generic Types
K = T.TypeVar("K")


class MultiStream(Observer[K], Observable[K]):
    """Hot streams that can be observed by multiple observers.

    .. Note::

        The AsyncMultiStream is hot in the sense that it will drop events if there are currently no
        observers running, and all redirection only enqueue the observers action, not waiting for
        it's execution.
    """

    def __init__(self, **kwargs: T.Any) -> None:
        """MultiStream constructor.

        Arguments:
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        # Internal
        self._observers: T.List[ObserverProtocol[K]] = []

    async def _asend(self, value: K, namespace: Namespace) -> None:
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
                                "to propagate data through observers"
                            ),
                            "exception": exc,
                        }
                    )

    async def _athrow(self, main_exc: Exception, namespace: Namespace) -> bool:
        self._observers = [obv for obv in self._observers if not obv.closed]
        if self._observers:
            awaitable = wait(
                tuple(obv.athrow(main_exc, namespace) for obv in self._observers),
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
                                "to propagate exception through observers"
                            ),
                            "exception": exc,
                        }
                    )

        # A MultiStream never closes on araise
        return False

    async def _aclose(self) -> None:
        pass

    async def __observe__(self, observer: ObserverProtocol[K]) -> None:
        # Guard against duplicated observers
        if observer in self._observers:
            raise MultiStreamError(f"{observer} is already observing this streams")

        # Add observers to internal observation list
        self._observers.append(observer)

    async def __dispose__(self, observer: ObserverProtocol[K]) -> None:
        with suppress(ValueError):
            self._observers.remove(observer)