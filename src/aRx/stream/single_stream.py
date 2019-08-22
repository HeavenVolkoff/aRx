# Internal
import typing as T
from abc import abstractmethod
from asyncio import Future

# Project
from ..error import SingleStreamError, ObserverClosedError
from ..abstract import Observer, Namespace, Transformer

# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")


class SingleStreamBase(Transformer[K, L]):
    """Cold stream tightly coupled with a single observer.

    .. Note::

        The SingleStream is cold in the sense that it is tightly connected to it's only observer.
        So that it will await until it is observed before redirecting any event, and all redirection
        wait for the observer action to execute.
    """

    def __init__(self, **kwargs: T.Any) -> None:
        """SingleStream constructor.

        Arguments:
            kwargs: Super classes named parameters.

        """
        super().__init__(**kwargs)

        # Internal
        self._lock: "Future[None]" = self._loop.create_future()
        self._observer: T.Optional[Observer[L]] = None
        self._observer_keep_alive = False

    @abstractmethod
    async def __asend__(self, value: K, namespace: Namespace) -> None:
        raise NotImplemented()

    async def __asend_impl__(self, value: L, namespace: Namespace) -> None:
        # Wait for observer
        await self._lock

        # _observer must be available at this point
        assert self._observer

        try:
            awaitable: T.Awaitable[T.Any] = self._observer.asend(value, namespace)
        except ObserverClosedError:
            awaitable = self.aclose()

        # Remove reference early to avoid keeping large objects in memory
        del value

        await awaitable

    @abstractmethod
    async def __araise__(self, exc: Exception, namespace: Namespace) -> bool:
        raise NotImplemented()

    async def __araise_impl__(self, exc: Exception, namespace: Namespace) -> bool:

        # Wait for observer
        await self._lock

        # _observer must be available at this point
        assert self._observer

        try:
            await self._observer.araise(exc, namespace)
        except ObserverClosedError:
            await self.aclose()

        # SingleStream doesn't close on raise
        return False

    async def __aclose__(self) -> None:
        # Cancel all awaiting event in the case we weren't subscribed
        self._lock.cancel()

        observer = self._observer
        self._observer = None

        # Close observer if necessary
        if observer and not (observer.closed or self._observer_keep_alive):
            await observer.aclose()

    def __observe__(
        self, observer: Observer[L], *, keep_alive: bool = False
    ) -> "SingleStreamBase[K, L]":
        """Start streaming.

        Raises:
            SingleStreamMultipleError

        """
        if self._observer:
            raise SingleStreamError("Can't assign multiple observers to a SingleStream")

        # Set stream observer
        self._observer = observer
        self._observer_keep_alive = keep_alive

        # Release any awaiting event
        self._lock.set_result(None)

        return self


class SingleStream(SingleStreamBase[K, K]):
    async def __asend__(self, value: K, namespace: Namespace) -> None:
        return await self.__asend_impl__(value, namespace)

    async def __araise__(self, exc: Exception, namespace: Namespace) -> bool:
        return await self.__araise_impl__(exc, namespace)


__all__ = ("SingleStreamBase", "SingleStream")
