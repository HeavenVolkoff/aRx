# Internal
import typing as T

from abc import ABCMeta
from asyncio import Future, InvalidStateError

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

        # Internal
        self._ctrl_index = 0
        self._ctrl_future = self.loop.create_future()  # type: Future

        # Ensure that observable closes if it's future is resolved externally
        self.add_done_callback(self.aclose)

    async def __adispose__(self):
        """Implements the disposable interface, enables context management"""
        await self.aclose()

    async def asend(self, data: K, **kwargs) -> None:
        """Public method to send data through this observer

        Args:
            data: Data to be sent through
            kwargs: Arguments to the internal close implementation
        """
        if self.done() or self.closed:
            raise ObserverClosedError(self)

        self._logger.debug("Observer send: %s", data)
        await self.__asend__(data, **kwargs)

    async def araise(self, ex: Exception, **kwargs) -> bool:
        """Public method to raise a exception through this observer

        Args:
            ex: Exception to be raised
            kwargs: Arguments to the internal close implementation


        Returns:
            Boolean indicating if observer was set to close due to the exception
        """
        if self.done() or self.closed:
            raise ObserverClosedError(self)

        self._logger.debug("Observer throw: %s", ex)

        should_close = await self.__araise__(ex, **kwargs)

        if should_close:
            try:
                self.set_exception(ex)
            except InvalidStateError:
                self._logger.warning(
                    "Observer was put in a InvalidState during `.araise()`"
                )

        return should_close

    async def aclose(self, **kwargs) -> bool:
        """Close observer and underlining future with received data as result.

        Args:
            kwargs: Arguments to the internal close implementation

        Returns:
            Boolean indicating if close executed
        """
        # Guard against repeated closes
        if self.closed:
            return False

        self._logger.warning("Closing %s", type(self).__name__)

        # Set flag to disable further stream actions
        self.closed = True

        # Remove callback from internal future
        self.remove_done_callback(self.aclose)

        # Internal close
        await self.__aclose__(**kwargs)

        # Cancel future in case it wasn't resolved
        self.cancel()

        return True
