__all__ = ("Observer",)


# Internal
import typing as T
from abc import abstractmethod
from asyncio import Future, CancelledError, InvalidStateError
from contextlib import contextmanager

# External
from prop import ChainPromise
from async_tools.abstract import AsyncABCMeta

# Project
from ..error import ObserverClosedError
from ..misc.namespace import Namespace, get_namespace

# Generic Types
K = T.TypeVar("K")
J = T.TypeVar("J")


class Observer(
    T.Generic[K, J],
    ChainPromise[J],
    T.AsyncContextManager["Observer[K, J]"],
    metaclass=AsyncABCMeta,
):
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
        self._close_promise = self.lastly(self.aclose)
        self._propagation_count = 0
        self._propagation_guard: T.Optional["Future[None]"] = None

    @abstractmethod
    async def __asend__(self, value: K, namespace: Namespace) -> None:
        """Processing of input data.

        Arguments:
            value: Received data.
            namespace: Namespace to identify propagation origin.

        Raises:
            NotImplemented

        """
        raise NotImplemented()

    @abstractmethod
    async def __araise__(self, exc: Exception, namespace: Namespace) -> bool:
        """Processing of input exceptions.

        Arguments:
            exc: Received exception.
            namespace: Namespace to identify propagation origin.

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

    async def __aexit__(self, _: T.Any, __: T.Any, ___: T.Any) -> bool:
        """Close stream when disposed"""
        await self.aclose()
        return False

    @contextmanager
    def _propagating(self) -> T.Generator[None, None, None]:
        self._propagation_count += 1

        try:
            yield
        finally:
            self._propagation_count -= 1
            if self._propagation_guard and self._propagation_count == 0:
                self._propagation_guard.set_result(None)

    @property
    def closed(self) -> bool:
        """Property that indicates if this observer is closed or not."""
        return self.done() or self._close_promise.done() or self._close_guard

    async def asend(self, data: K, namespace: T.Optional[Namespace] = None) -> None:
        """Interface through which data is inputted.

        Arguments:
            data: Data to be inputted.
            namespace: Namespace to identify propagation origin.

        Raises:
            ObserverClosedError: If observer is closed.

        """
        if self.closed:
            raise ObserverClosedError(self)

        with self._propagating():
            namespace = get_namespace(self, "asend", namespace)
            awaitable = self.__asend__(data, namespace)

            # Remove reference early to avoid keeping large objects in memory
            del data

            try:
                await awaitable
            except CancelledError:
                raise  # Cancelled errors are not redirected
            except Exception as ex:
                if not self.closed:
                    await self.araise(ex, namespace)
                else:
                    raise RuntimeError(f"{self} closed with a pending Exception") from ex

    async def araise(self, main_exc: Exception, namespace: T.Optional[Namespace] = None) -> None:
        """Interface through which exceptions are inputted.

        Arguments:
            main_exc: Exception to be inputted.
            namespace: Namespace to identify propagation origin.

        Raises:
            ObserverClosedError: If observer is closed.

        Returns:
            Boolean indicating if observer will close due to the exception.

        """
        if self.closed:
            raise ObserverClosedError(self)

        with self._propagating():
            awaitable = self.__araise__(main_exc, get_namespace(self, "araise", namespace))

            try:
                should_close = await awaitable
            except CancelledError:
                raise  # Cancelled errors are not redirected
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
        self._close_promise.cancel(task=False)

        # Wait remaining propagations
        if self._propagation_count > 0:
            self._propagation_guard = self.loop.create_future()
            await self._propagation_guard

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
