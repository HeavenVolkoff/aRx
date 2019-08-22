# Internal
import typing as T
from abc import abstractmethod
from asyncio import Future, CancelledError
from warnings import warn
from contextlib import contextmanager

# External
from async_tools import Loopable
from async_tools.abstract import BasicRepr, AsyncABCMeta

# Project
from ..error import ObserverClosedError, ObserverClosedWarning
from .namespace import Namespace, get_namespace

__all__ = ("Observer",)


# Generic Types
K = T.TypeVar("K")


class Observer(T.Generic[K], BasicRepr, Loopable, metaclass=AsyncABCMeta):
    """Observer abstract class.

    An observer represents a data sink, where data can flow into and be
    transformed by it.

    Attributes:
        keep_alive: Flag that indicates the default behaviour on whether or not the observer should
                    be closed on observation disposition.
    """

    __slots__ = ("keep_alive", "_closed", "_propagation_count", "_propagation_guard")

    def __init__(self, *, keep_alive: bool = False, **kwargs: T.Any) -> None:
        """Observer constructor.

        Arguments:
            kwargs: keyword parameters for super.

        """
        super().__init__(**kwargs)

        self.keep_alive = keep_alive

        # Internal
        self._closed = False
        self._close_guard = False
        self._propagation_count = 0
        self._propagation_guard: T.Optional["Future[None]"] = None

    @abstractmethod
    async def __asend__(self, value: K, namespace: Namespace) -> None:
        """Method responsible for handling the input data.

        Arguments:
            value: Input data.
            namespace: Namespace to identify propagation origin.

        """
        raise NotImplemented()

    @abstractmethod
    async def __araise__(self, exc: Exception, namespace: Namespace) -> bool:
        """Method responsible for handling any exceptions.

        Arguments:
            exc: Exception.
            namespace: Namespace to identify propagation origin.

        """
        raise NotImplemented()

    @abstractmethod
    async def __aclose__(self) -> None:
        """Method responsible for handling the logic necessary to close the observer."""
        raise NotImplemented()

    async def __aenter__(self) -> "Observer[K]":
        """Async context manager entrypoint.

        Returns:
            The observer object.

        """
        return self

    async def __aexit__(self, _: T.Any, __: T.Any, ___: T.Any) -> bool:
        """Async context manager exit.

        Close observer when the context is disposed.

        Returns:
            False because there is no reason to capture any exception raise inside the context.

        """
        await self.aclose()
        return False

    @contextmanager
    def _propagating(self) -> T.Generator[None, None, None]:
        """Context manager to keep track of any ongoing asend or araise operation."""
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
        return self._closed

    async def asend(self, data: K, namespace: T.Optional[Namespace] = None) -> None:
        """Interface through which data is inputted.

        Arguments:
            data: Data to be inputted.
            namespace: Namespace to identify propagation origin.

        Raises:
            ObserverClosedError: If observer is closed.

        """
        if self.closed or self._close_guard:
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
                # Any exception raised during the handling of the input data will be inputted to
                # the observer for it to handle.
                await self.araise(ex, namespace)

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
        if self.closed or self._close_guard:
            if namespace and namespace.ref is self:
                # Allow calls to araise event when observer is closed if it's originated from the
                # observer's own asend.
                warn(
                    ObserverClosedWarning(
                        f"{self}: Observer is closed but an exception was propagated from asend",
                        main_exc,
                    )
                )
            else:
                raise ObserverClosedError(self)

        with self._propagating():
            awaitable = self.__araise__(main_exc, get_namespace(self, "araise", namespace))

            try:
                should_close = await awaitable
            except CancelledError:
                raise  # Cancelled errors are irreversible
            except Exception:
                # Closes stream on irrecoverable exceptions
                should_close = True
                raise
            finally:
                # Close stream if araise requires
                if should_close:
                    self._close_guard = True
                    self.loop.create_task(self.aclose())

    async def aclose(self) -> bool:
        """Close observer.

        Returns:
            Boolean indicating if close executed or if it wasn't necessary.

        """
        # Guard against repeated calls
        if self.closed:
            return False

        # This is necessary due to the uncertain timing of promise cancellation
        self._closed = True

        # Wait remaining propagations
        if self._propagation_count > 0:
            self._propagation_guard = self.loop.create_future()
            await self._propagation_guard

        # Call internal close
        await self.__aclose__()

        return True
