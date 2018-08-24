__all__ = ("Observer",)

import typing as T
from abc import ABCMeta, abstractmethod
from asyncio import InvalidStateError
from warnings import warn

from ..error import ARxWarning, ObserverClosedError
from ..promise import Promise
from ..disposable import Disposable

K = T.TypeVar("K")
J = T.TypeVar("J")


class Observer(T.Generic[K, J], Promise[J], Disposable, metaclass=ABCMeta):
    """Observer abstract class.

    An observer represents a data sink, where data can be sent to and
    transformed by it.

    Attributes:
        keep_alive: Flag that indicates this observer should not be closed
            externally.

    """

    __slots__ = ("keep_alive", "_close_guard", "_close_promise")

    def __init__(self, *, keep_alive: bool = False, **kwargs) -> None:
        """Observer constructor.

        Arguments:
            keep_alive: :attr:`Observer.keep_alive`
            kwargs: keyword parameters for super.
        """
        super().__init__(**kwargs)
        self.keep_alive = keep_alive

        # Ensures that observer closes if it's is resolved externally
        self._close_guard = False
        self._close_promise = self.lastly(self.aclose)

    @abstractmethod
    async def __asend__(self, value):
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
    async def __aclose__(self):
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
        return self.done()

    async def asend(self, data: K):
        """Interface thought which data is inputted.

        Raises:
            ObserverClosedError: If observer is closed.

        Arguments:
            data: Data to be inputted.

        """
        if self.closed:
            raise ObserverClosedError(self)

        awaitable = self.__asend__(data)

        # Remove reference early to avoid keeping large objects in memory
        del data

        try:
            await awaitable
        except Exception as ex:
            await self.araise(ex)

    async def araise(self, main_ex: Exception) -> bool:
        """Interface thought which exceptions are inputted.

        Arguments:
            main_ex: Exception to be inputted.

        Raises:
            ObserverClosedError: If observer is closed.

        Returns:
            Boolean indicating if observer will close due to the exception.

        """
        if self.closed:
            raise ObserverClosedError(self)

        try:
            should_close = await self.__araise__(main_ex)
        except Exception as ex:
            should_close = True
            ex.__cause__ = main_ex
            main_ex = ex

        if should_close:
            try:
                self.reject(main_ex)
                # TODO: Should we await aclose?
            except InvalidStateError:
                warn(
                    ARxWarning(
                        f"{type(self).__qualname__} was already resolved"
                        " during `.araise()` call to treat:",
                        main_ex,
                    )
                )

        return should_close

    async def aclose(self) -> bool:
        """Close observer.

        Returns:
            Boolean indicating if close executed or if it wasn't necessary.

        """
        # Guard against repeated calls
        if self._close_guard:
            return False
        self._close_guard = True

        # Cancel close promise
        self._close_promise.cancel()

        # Internal close
        try:
            await self.__aclose__()
        finally:
            # Cancel in case we didn't get resolved
            self.cancel()

        return True
