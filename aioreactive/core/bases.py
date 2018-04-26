# Internal
import typing as T
import logging

from abc import abstractmethod
from asyncio import Future, InvalidStateError

# Project
from .errors import ReactiveError
from ..abstract import AsyncDisposable, AsyncObservable

K = T.TypeVar('K')


class ObserverClosedError(ReactiveError, InvalidStateError):
    pass


class AsyncObserver(T.Generic[K], Future, AsyncObservable, AsyncDisposable):
    """An async observer abstract base class.

    Both a future and async observer.
    The future resolves with the value passed to close.
    """

    def __init__(self,
                 *args,
                 logger: T.Optional[logging.Logger] = None,
                 **kwargs) -> None:
        cls = type(self)

        super().__init__(*args, **kwargs)

        self._logger = logger if logger else logging.getLogger(cls.__name__)
        self._closed = False

        # Ensure that observable is closed if it's future is resolved externally
        self.add_done_callback(self._closed)

    async def asend(self, data: K) -> None:
        if self._closed:
            raise ObserverClosedError("Observer is closed")

        self._logger.debug("Observer send: %s", data)
        await self.__asend__(data)

    async def araise(self, ex: Exception) -> None:
        if self._closed:
            raise ObserverClosedError("Observer is closed")

        #
        self.set_exception(ex)

        # Special case, we run close manually
        self.remove_done_callback(self._closed)

        self._logger.debug("Observer throw: %s", ex)
        await self.__araise__(ex)
        await self.aclose()

    async def aclose(self, data: T.Any = None) -> bool:
        if self._closed:
            return False

        self._closed = True

        self._logger.debug("Observer close")

        if not self.done():
            self.set_result(data)

        await self.__aclose__()

        return True

    async def __adispose__(self):
        await self.aclose()

    async def __aobserve__(self, observer):
        return self

    @abstractmethod
    def __asend__(self, value: K) -> None:
        raise NotImplemented()

    @abstractmethod
    async def __araise__(self, error) -> None:
        raise NotImplemented()

    @abstractmethod
    async def __aclose__(self) -> None:
        raise NotImplemented()
