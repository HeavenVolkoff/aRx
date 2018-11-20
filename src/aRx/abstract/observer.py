__all__ = ("Observer",)


# Internal
import typing as T
from abc import ABCMeta, abstractmethod
from asyncio import ALL_COMPLETED, Task, CancelledError, InvalidStateError, wait
from weakref import ReferenceType
from contextlib import suppress, contextmanager

# Project
from ..error import ObserverClosedError
from ..promise import Promise
from ..disposable import Disposable
from ..misc.current_task import current_task

# Generic Types
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

    def __init__(self, *, keep_alive: bool = False, **kwargs: T.Any) -> None:
        """Observer constructor.
        Arguments:
            keep_alive: :attr:`Observer.keep_alive`
            kwargs: keyword parameters for super.
        """
        super().__init__(**kwargs)

        self.keep_alive = keep_alive

        # Internal
        self._close_guard = False
        self._propagation: T.Set[ReferenceType[Task[T.Any]]] = set()
        self._close_promise = self.lastly(self.aclose)

    @abstractmethod
    async def __asend__(self, value: K) -> None:
        """Processing of input data.

        Arguments:
            value: Received data.

        Raises:
            NotImplemented

        """
        raise NotImplemented()

    @abstractmethod
    async def __araise__(self, ex: Exception) -> bool:
        """Processing of input exceptions.

        Arguments:
            ex: Received exception.

        Raises:
            NotImplemented

        """
        raise NotImplemented()

    @abstractmethod
    async def __aclose__(self) -> None:
        """Actions to be taken during close.

        Raises:
            NotImplemented

        """
        raise NotImplemented()

    async def __adispose__(self) -> None:
        """Close stream when disposed"""
        await self.aclose()

    @contextmanager
    def _propagating(self) -> T.Generator[None, None, None]:
        task = ReferenceType(current_task(loop=self.loop))
        self._propagation.add(task)
        try:
            yield
        finally:
            self._propagation.remove(task)

    @property
    def closed(self) -> bool:
        """Property that indicates if this observer is closed or not."""
        return self.done() or self._close_promise.done() or self._close_guard

    async def asend(self, data: K) -> None:
        """Interface thought which data is inputted.

        Arguments:
            data: Data to be inputted.

        Raises:
            ObserverClosedError: If observer is closed.

        """
        if self.closed:
            raise ObserverClosedError(self)

        with self._propagating():
            awaitable = self.__asend__(data)

            # Remove reference early to avoid keeping large objects in memory
            del data

            try:
                await awaitable
            except CancelledError:
                raise  # Cancelled errors are not redirected
            except Exception as ex:
                if not self.closed:
                    await self.araise(ex)
                else:
                    raise RuntimeError(f"{self} closed with a pending Exception") from ex

    async def araise(self, main_exc: Exception) -> None:
        """Interface thought which exceptions are inputted.

        Arguments:
            main_exc: Exception to be inputted.

        Raises:
            ObserverClosedError: If observer is closed.

        Returns:
            Boolean indicating if observer will close due to the exception.

        """
        if self.closed:
            raise ObserverClosedError(self)

        with self._propagating():
            try:
                should_close = await self.__araise__(main_exc)
            except Exception as exc:
                should_close = True

                # Added received exceptions to chain
                exc.__cause__ = main_exc
                main_exc = exc

            # Closes stream on irrecoverable exceptions
            if should_close:
                try:
                    self.reject(main_exc)
                except InvalidStateError as exc:
                    raise RuntimeError(f"{self} closed with a pending Exception") from exc
                else:
                    # Wait till aclose starts executing
                    with suppress(CancelledError):
                        await self._close_promise

    async def aclose(self) -> bool:
        """Close observer.

        Returns:
            Boolean indicating if close executed or if it wasn't necessary.

        """
        # Guard against repeated calls
        if self._close_guard:
            return False

        # This is necessary due to the uncertain timing of promise cancellation
        self._close_guard = True

        # Cancel close promise
        self._close_promise.cancel()

        # Wait pending propagation before closing stream
        await wait(
            tuple(filter(bool, (propagation() for propagation in self._propagation))),
            return_when=ALL_COMPLETED,
        )

        # Internal close
        try:
            await self.__aclose__()
        finally:
            # Cancel in case we didn't get resolved
            if self.cancel():
                self.loop.call_exception_handler(
                    {"message": f"{self}: Failed to finalized correctly and had to be cancelled"}
                )

        return True
