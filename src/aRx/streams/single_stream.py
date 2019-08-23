# Internal
import typing as T
from abc import ABCMeta
from asyncio import Future

# Project
from ..error import SingleStreamError, ObserverClosedError
from ..namespace import Namespace
from ..observers import Observer
from ..protocols import ObserverProtocol
from ..observables import Observable

# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")


class SingleStreamBase(Observable[K], Observer[L], metaclass=ABCMeta):
    """Cold streams tightly coupled with a single observers.

    .. Note::

        The SingleStream is cold in the sense that it is tightly connected to it's only observers.
        So that it will await until it is observed before redirecting any event, and all redirection
        wait for the observers action to execute.
    """

    def __init__(self, **kwargs: T.Any) -> None:
        """SingleStream constructor.

        Arguments:
            kwargs: Super classes named parameters.

        """
        super().__init__(**kwargs)

        # Internal
        self._lock: "Future[None]" = self._loop.create_future()
        self._observer: T.Optional[ObserverProtocol[K]] = None

    async def _asend(self, value: L, namespace: Namespace) -> None:
        # Wait for observers
        await self._lock

        # _observer must be available at this point
        assert self._observer

        try:
            awaitable: T.Awaitable[T.Any] = self._observer.asend(
                await self._asend_impl(value), namespace
            )
        except ObserverClosedError:
            awaitable = self.aclose()

        # Remove reference early to avoid keeping large objects in memory
        del value

        await awaitable

    async def _asend_impl(self, value: L) -> K:
        raise NotImplementedError()

    async def _athrow(self, exc: Exception, namespace: Namespace) -> bool:

        # Wait for observers
        await self._lock

        # _observer must be available at this point
        assert self._observer

        try:
            await self._observer.athrow(exc, namespace)
        except ObserverClosedError:
            await self.aclose()

        # SingleStream doesn't close on raise
        return False

    async def _aclose(self) -> None:
        # Cancel all awaiting event in the case we weren't subscribed
        self._lock.cancel()
        self._observer = None

    async def __observe__(self, observer: ObserverProtocol[K]) -> None:
        """Start streaming.

        Raises:
            SingleStreamMultipleError

        """
        if self._observer:
            raise SingleStreamError("Can't assign multiple observers to a SingleStream")

        # Set streams observers
        self._observer = observer

        # Release any awaiting event
        self._lock.set_result(None)

    async def __dispose__(self, observer: ObserverProtocol[K]) -> None:
        await self.aclose()


class SingleStream(SingleStreamBase[K, K]):
    async def _asend_impl(self, value: K) -> K:
        return value


__all__ = ("SingleStreamBase", "SingleStream")
