# Internal
import typing as T

from abc import ABCMeta
from asyncio import InvalidStateError

# Project
from ..error import ReactiveError
from ..abstract import Disposable, Observer, Loggable

K = T.TypeVar('K')


class ObserverClosedError(ReactiveError, InvalidStateError):
    def __init__(self, instance):
        super().__init__(f"{type(instance).__name__} is closed")

    pass


class BaseObserver(Disposable, Loggable, Observer[K], metaclass=ABCMeta):
    """The base class for all Observers.

    Implements all the common behaviour of a Observer
    """

    def __init__(self, **kwargs) -> None:
        """BaseObserver constructor.

        Args
            kwargs: Super classes named parameters
        """
        super().__init__(**kwargs)

        # Public
        self.closed = False

        # Ensure that observable closes if it's future is resolved externally
        self.add_done_callback(self.aclose)

    async def __adispose__(self):
        """Implements the disposable interface, enables context management"""
        await self.aclose()

    async def asend(self, data: K) -> None:
        """Public method to send data through this observer

        Args:
            data: Data to be sent through
        """
        if self.done() or self.closed:
            raise ObserverClosedError(self)

        self._logger.debug("Observer send: %s", data)
        await self.__asend__(data)

    async def araise(self, ex: Exception) -> bool:
        """Public method to raise a exception through this observer

        Args:
            ex: Exception to be raised

        Returns:
            Boolean indicating if observer was set to close due to the exception
        """
        if self.done() or self.closed:
            raise ObserverClosedError(self)

        self._logger.debug("Observer throw: %s", ex)

        should_close = await self.__araise__(ex)

        if should_close:
            try:
                self.set_exception(ex)
            except InvalidStateError:
                self._logger.warning(
                    "Observer was put in a InvalidState during `.araise()`"
                )

        return should_close

    async def aclose(self, data: T.Any = None) -> bool:
        """Close observer and underlining future with received data as result.

        Args:
            data: Data to be used as result to underling future

        Returns:
            Boolean indicating if close executed
        """
        if self.closed:
            return False

        self._logger.debug("Closing observer")

        self.closed = True

        await self.__aclose__()

        try:
            self.set_result(data)
        except InvalidStateError as error:
            if data is not None:
                self._logger.warning(
                    "Observer couldn't be resolved with data passed to "
                    "`.aclosed()`, due to: [%s] %s",
                    type(error).__name__, error
                )

        return True
