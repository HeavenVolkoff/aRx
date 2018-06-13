__all__ = ("Observer", )

# Internal
import typing as T

from abc import ABCMeta, abstractmethod
from asyncio import InvalidStateError
from warnings import warn

# Project
from ..error import ObserverClosedError
from ..promise import Promise
from ..disposable import Disposable

K = T.TypeVar("K")


class Observer(Promise, Disposable, T.Generic[K], metaclass=ABCMeta):
    """Observer abstract class.

    An observer represents a data sink, where data can be sent to and
    transformed by it.

    Attributes:
        keep_alive: Flag that indicates this observer should not be closed
            externally.

    """
    __slots__ = ("_closed", "keep_alive", "_close_promise")

    def __init__(self, *, keep_alive: bool = False, **kwargs):
        """Observer constructor.

        Arguments:
            keep_alive: :attr:`Observer.keep_alive`
            kwargs: keyword parameters for super.
        """
        super().__init__(**kwargs)
        self.keep_alive = keep_alive

        self._closed = False
        # Ensures that observer closes if it's is resolved externally
        self._close_promise = self.lastly(self.aclose)

    @abstractmethod
    async def __asend__(self, value: K) -> None:
        """Processing of input data.

        Raises:
            NotImplemented

        Arguments:
            value: Received data.

        """
        raise NotImplemented()

    @abstractmethod
    async def __araise__(self, ex: Exception) -> bool:
        """Processing of input exceptions.

        Raises:
            NotImplemented

        Arguments:
            ex: Received exception.

        """
        raise NotImplemented()

    @abstractmethod
    async def __aclose__(self) -> None:
        """Actions to be taken during close.

        Raises:
            NotImplemented
        """
        raise NotImplemented()

    async def __adispose__(self):
        """Close stream when disposed"""
        await self.aclose()

    @property
    def closed(self):
        """Property that indicates if this observer is closed or not."""
        return self.future.done() or self._closed

    async def asend(self, data: K) -> None:
        """Interface thought which data is inputted.

        Raises:
            ObserverClosedError: If observer is closed.

        Arguments:
            data: Data to be inputted.

        """
        if self.closed:
            raise ObserverClosedError(self)
        await self.__asend__(data)

    async def araise(self, ex: Exception) -> bool:
        """Interface thought which exceptions are inputted.

        Arguments:
            ex: Exception to be inputted.

        Raises:
            ObserverClosedError: If observer is closed.

        Returns:
            Boolean indicating if observer will close due to the exception.

        """
        if self.closed:
            raise ObserverClosedError(self)

        should_close = await self.__araise__(ex)

        if should_close:
            try:
                self.future.set_exception(ex)
            except InvalidStateError:
                warn(
                    f"{type(self).__qualname__} was put in a InvalidState"
                    f"during `.araise()`", RuntimeWarning
                )

        return should_close

    async def aclose(self) -> bool:
        """Close observer.

        Returns:
            Boolean indicating if close executed or if it wasn't necessary.

        """
        # Guard against repeated calls
        if self.closed:
            return False

        # Set flag to disable further stream actions
        self._closed = True

        # Cancel close promise
        self._close_promise.cancel()

        # Internal close
        await self.__aclose__()

        # Cancel future in case it wasn't resolved
        self.cancel()

        return True
