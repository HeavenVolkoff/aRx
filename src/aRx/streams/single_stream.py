# Internal
import typing as T
from asyncio import InvalidStateError
from contextlib import suppress

# External
from async_tools.abstract import AsyncABCMeta

# Project
from ..error import SingleStreamError, ObserverClosedError
from ..observers import Observer
from ..operations import observe
from ..observables import Observable

if T.TYPE_CHECKING:
    # Internal
    from asyncio import Future

    # Project
    from ..namespace import Namespace
    from ..protocols import ObserverProtocol


# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")


class SingleStreamBase(Observable[K], Observer[L], metaclass=AsyncABCMeta):
    """Cold streams tightly coupled with a single observers.

    .. Note::

        The SingleStream is cold in the sense that it is tightly connected to it's only observers.
        So that it will await until it is observed before redirecting any event, and all redirection
        wait for the observers action to execute.
    """

    __slots__ = ("_lock", "_observer")

    def __init__(self, **kwargs: T.Any) -> None:
        """SingleStream constructor.

        Arguments:
            kwargs: Super classes named parameters.

        """
        super().__init__(**kwargs)

        # Internal
        self._lock: "Future[None]" = self._loop.create_future()
        self._observer: T.Optional["ObserverProtocol[K]"] = None

    async def _asend(self, value: L, namespace: "Namespace") -> None:
        # Wait for observers
        await self._lock

        # _observer must be available at this point
        assert self._observer

        awaitable = self._observer.asend(await self._asend_impl(value), namespace)

        # Remove reference early to avoid keeping large objects in memory
        del value

        await awaitable

    async def _asend_impl(self, value: L) -> K:
        raise NotImplementedError

    async def _athrow(self, exc: Exception, namespace: "Namespace") -> bool:

        # Wait for observers
        await self._lock

        # _observer must be available at this point
        assert self._observer

        if self._observer.closed:
            # close stream
            return True

        await self._observer.athrow(exc, namespace)

        # SingleStream doesn't close on raise
        return False

    async def _aclose(self) -> None:
        # Cancel all awaiting event in the case we weren't subscribed
        with suppress(InvalidStateError):
            self._lock.set_exception(ObserverClosedError(self))

        if self._observer:
            # Dispose observer
            await observe(self, self._observer).dispose()

    async def __observe__(self, observer: "ObserverProtocol[K]") -> None:
        """Start streaming.

        Raises:
            SingleStreamMultipleError

        """
        if self._observer:
            if self._observer is observer:
                return

            raise SingleStreamError("Can't assign multiple observers to a SingleStream")

        # Set streams observers
        self._observer = observer

        # Release any awaiting event
        self._lock.set_result(None)

    async def __dispose__(self, observer: "ObserverProtocol[K]") -> None:
        if observer is not self._observer:
            return

        self._observer = None
        await self.aclose()


class SingleStream(SingleStreamBase[K, K]):
    async def _asend_impl(self, value: K) -> K:
        return value


__all__ = ("SingleStreamBase", "SingleStream")
