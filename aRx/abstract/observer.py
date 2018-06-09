__all__ = ("Observer", )

# Internal
import typing as T

from abc import ABCMeta, abstractmethod
from asyncio import InvalidStateError

# Project
from .loggable import Loggable
from ..error import ObserverClosedError
from ..promise import Promise

K = T.TypeVar("K")


class Observer(Promise, Loggable, T.Generic[K], metaclass=ABCMeta):
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

        Args:
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
        """Method where data processing must take place.

        Args:
            value: Received data.

        """
        raise NotImplemented()

    @abstractmethod
    async def __araise__(self, ex: Exception) -> bool:
        """Method where processing of exception must take place.

        Args:
            ex: Received exception.

        """
        raise NotImplemented()

    @abstractmethod
    async def __aclose__(self) -> None:
        """Actions necessary to be taken during observer close."""
        raise NotImplemented()

    @property
    def closed(self):
        """Property that indicates if this observer is closed or not."""
        return self.future.done() or self._closed

    async def asend(self, data: K) -> None:
        """Send data through this observer.

        Args:
            data: Data to be sent.

        """
        if self.closed:
            raise ObserverClosedError(self)

        self.logger.debug("%s sends: %s", type(self).__qualname__, data)
        await self.__asend__(data)

    async def araise(self, ex: Exception) -> bool:
        """Raise an exception through this observer.

        Args:
            ex: Exception to be raised.


        Returns:
            Boolean indicating if observer must be closed due to the exception.

        """
        if self.closed:
            raise ObserverClosedError(self)

        self.logger.debug("%s raises: %s", type(self).__qualname__, ex)

        should_close = await self.__araise__(ex)

        if should_close:
            try:
                self.future.set_exception(ex)
            except InvalidStateError:
                self.logger.warning(
                    "%s was put in a InvalidState during `.araise()`",
                    type(self).__qualname__
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

        self.logger.warning("Closing %s", type(self).__qualname__)

        # Set flag to disable further stream actions
        self._closed = True

        # Cancel close promise
        self._close_promise.cancel()

        # Internal close
        await self.__aclose__()

        # Cancel future in case it wasn't resolved
        self.cancel()

        return True
