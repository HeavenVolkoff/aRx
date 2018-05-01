# Internal
import typing as T
import logging

from abc import ABCMeta
from enum import Enum, auto
from asyncio import Future, InvalidStateError

# Project
from ..error import ReactiveError
from ..abstract import Disposable, Observer

K = T.TypeVar('K')


class ObserverState(Enum):
    OPEN = auto()
    CLOSED = auto()
    EXCEPTION = auto()


class ObserverClosedError(ReactiveError, InvalidStateError):
    def __init__(self, instance):
        super().__init__(f"{type(instance).__name__} is closed")

    pass


class BaseObserver(Observer[K], Disposable, metaclass=ABCMeta):
    """An async observer abstract base class.

    Both a future and async observer.
    The future resolves with the value passed to close.
    """

    def __init__(
        self, *args, logger: T.Optional[logging.Logger] = None, **kwargs
    ) -> None:
        cls = type(self)

        super(Observer, self).__init__(*args, **kwargs)

        self._state = ObserverState.OPEN
        self._logger = logger if logger else logging.getLogger(cls.__name__)

        # Ensure that observable is closed if it's future is resolved externally
        self.add_done_callback(self.aclose)

    async def __adispose__(self):
        await self.aclose()

    def clear_exception(self) -> None:
        if self._state is not ObserverState.EXCEPTION:
            raise InvalidStateError('Stream is not in a exception state')

        self._state = ObserverState.OPEN

    async def asend(self, data: K) -> None:
        if self._state is ObserverState.CLOSED:
            raise ObserverClosedError(self)

        self._logger.debug("Observer send: %s", data)
        await self.__asend__(data)

    async def araise(self, ex: Exception) -> None:
        if self._state is ObserverState.CLOSED:
            raise ObserverClosedError(self)

        self._logger.debug("Observer throw: %s", ex)

        await self.__araise__(ex, clear=self._clear_exception)

        if self._state is ObserverState.EXCEPTION:
            try:
                self.set_exception(ex)
            except InvalidStateError:
                self._logger.warning(
                    "Observer was put in a InvalidState during `.araise()`"
                )

    async def aclose(self, data: T.Any = None) -> bool:
        if self._state is ObserverState.CLOSED:
            return False

        self._state = ObserverState.CLOSED

        self._logger.debug("Closing observer")

        try:
            self.set_result(data)
        except InvalidStateError:
            pass

        await self.__aclose__()

        return True
