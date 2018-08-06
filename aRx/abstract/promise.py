__all__ = ("Promise",)

import typing as T
from abc import ABCMeta, abstractmethod
from asyncio import Future, ensure_future

from .loopable import Loopable

K = T.TypeVar("K")
L = T.TypeVar("L")


class Promise(T.Awaitable[K], Loopable, metaclass=ABCMeta):
    """A abstract Promise implementation that encapsulate an awaitable.

    .. Warning::

        No implementation is made as to how the callback queue is generated or
        maintained.
    """

    __slots__ = ("_fut", "_awaited", "_cancelled")

    def __init__(self, awaitable: T.Optional[T.Awaitable[K]] = None, **kwargs) -> None:
        """Promise constructor.

        Arguments:
            awaitable: The awaitable object to be encapsulated.
            kwargs: Keyword parameters for super.
        """
        super().__init__(**kwargs)

        self._fut = (
            self.loop.create_future()
            if awaitable is None
            else ensure_future(awaitable, loop=self.loop)
        )  # type: Future
        self._awaited = False
        self._cancelled = False

    def __await__(self) -> T.Generator[T.Any, None, K]:
        self._awaited = True
        return self._fut.__await__()

    def done(self) -> bool:
        """Check if promise is done.

        Returns:
            Boolean indicating if promise is done or not.

        """
        return self._fut.done()

    def cancel(self) -> bool:
        """Cancel the promise and the underlining future.

        Returns:
            Boolean indicating if the cancellation occurred or not.

        """
        self._cancelled = True
        return self._fut.cancel()

    def cancelled(self) -> bool:
        """Indicates whether promise is cancelled or not.

        Returns:
            Boolean indicating if promise is cancelled or not.

        """
        return self._fut.cancelled()

    def resolve(self, result: K) -> None:
        """Resolve Promise with given value.

        Arguments:
            result: Result to resolve Promise with.

        Raises:
            InvalidStateError: Raised when promise was already resolved

        """
        self._fut.set_result(result)

    def reject(self, error: Exception) -> None:
        """Reject promise with given value.

        Arguments:
            error: Error to reject Promise with.

        Raises:
            InvalidStateError: Raised when promise was already resolved

        """
        self._fut.set_exception(error)

    @abstractmethod
    def then(self, on_fulfilled: T.Callable[[K], L]) -> "Promise":
        """Chain a callback to be executed when the Promise resolves.

        Arguments:
            on_fulfilled: The callback, it must receive a single argument that
                is the result of the Promise.

        Raises:
            NotImplemented

        Returns:
            Promise that will be resolved when the callback finishes executing.

        """
        raise NotImplemented()

    @abstractmethod
    def catch(self, on_reject: T.Callable[[Exception], L]) -> "Promise":
        """Chain a callback to be executed when the Promise fails to resolve.

        Arguments:
            on_reject: The callback, it must receive a single argument that
                is the reason of the Promise resolution failure.

        Raises:
            NotImplemented

        Returns:
            Promise that will be resolved when the callback finishes executing.

        """
        raise NotImplemented()

    @abstractmethod
    def lastly(self, on_fulfilled: T.Callable[[], L]) -> "Promise":
        """Chain a callback to be executed when the Promise concludes.

        Arguments:
            on_fulfilled: The callback. No argument is passed to it.

        Raises:
            NotImplemented

        Returns:
            Promise that will be resolved when the callback finishes executing.
        """
        raise NotImplemented()
