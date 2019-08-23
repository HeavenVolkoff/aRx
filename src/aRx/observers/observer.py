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
from ..namespace import Namespace, get_namespace
from ..protocols.observer_protocol import ObserverProtocol

__all__ = ("Observer",)


# Generic Types
K = T.TypeVar("K")


class Observer(
    BasicRepr, Loopable, ObserverProtocol[K], T.AsyncContextManager[None], metaclass=AsyncABCMeta
):
    """Observer abstract class.

    An abstract implementation of the ObserverProtocol that defines some basis for the data flow,
    exception handling. Custom behaviour must be implemented in _asend, _athrow, _aclose.
    """

    __slots__ = (
        "keep_alive",
        "_closed",
        "_close_guard",
        "_propagation_count",
        "_propagation_guard",
    )

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

    async def __aenter__(self) -> None:
        """Async context manager entrypoint.

        Returns:
            The observers object.

        """
        return None

    async def __aexit__(self, _: T.Any, __: T.Any, ___: T.Any) -> bool:
        """Async context manager exit.

        Close observers when the context is disposed.

        Returns:
            False because there is no reason to capture any exception raise inside the context.

        """
        await self.aclose()
        return False

    @abstractmethod
    async def _asend(self, value: K, namespace: Namespace) -> None:
        """Method responsible for handling the input data.

        Arguments:
            value: Input data.
            namespace: Namespace to identify propagation origin.

        """
        raise NotImplemented()

    @abstractmethod
    async def _athrow(self, exc: Exception, namespace: Namespace) -> bool:
        """Method responsible for handling any exceptions.

        Arguments:
            exc: Exception.
            namespace: Namespace to identify propagation origin.

        """
        raise NotImplemented()

    @abstractmethod
    async def _aclose(self) -> None:
        """Method responsible for handling the logic necessary to close the observers."""
        raise NotImplemented()

    @contextmanager
    def _propagating(self) -> T.Generator[None, None, None]:
        """Context manager to keep track of any ongoing asend or araise operations."""
        self._propagation_count += 1

        try:
            yield
        finally:
            self._propagation_count -= 1
            if self._propagation_guard and self._propagation_count == 0:
                self._propagation_guard.set_result(None)

    @property
    def closed(self) -> bool:  # type: ignore
        """Property that indicates if this observers is closed or not."""
        return self._closed

    async def asend(self, data: K, namespace: T.Optional[Namespace] = None) -> None:
        """Interface through which data is inputted.

        Arguments:
            data: Data to be inputted.
            namespace: Namespace to identify propagation origin.

        Raises:
            ObserverClosedError: If observers is closed.

        """
        if self.closed or self._close_guard:
            raise ObserverClosedError(self)

        with self._propagating():
            namespace = get_namespace(self, "asend", namespace)
            awaitable = self._asend(data, namespace)

            # Remove reference early to avoid keeping large objects in memory
            del data

            try:
                await awaitable
            except CancelledError:
                raise  # Cancelled errors are not redirected
            except Exception as ex:
                # Any exception raised during the handling of the input data will be inputted to
                # the observers for it to handle.
                await self.athrow(ex, namespace)

    async def athrow(self, main_exc: Exception, namespace: T.Optional[Namespace] = None) -> None:
        """Interface through which exceptions are inputted.

        Arguments:
            main_exc: Exception to be inputted.
            namespace: Namespace to identify propagation origin.

        Raises:
            ObserverClosedError: If observers is closed.

        Returns:
            Boolean indicating if observers will close due to the exception.

        """
        if self.closed or self._close_guard:
            if namespace and namespace.ref is self:
                # Allow calls to araise event when observers is closed if it's originated from the
                # observers's own asend.
                warn(
                    ObserverClosedWarning(
                        f"{self}: Observer is closed but an exception was propagated from asend",
                        main_exc,
                    )
                )
            else:
                raise ObserverClosedError(self)

        with self._propagating():
            awaitable = self._athrow(main_exc, get_namespace(self, "araise", namespace))

            try:
                should_close = await awaitable
            except CancelledError:
                raise  # Cancelled errors are irreversible
            except Exception:
                # Closes streams on irrecoverable exceptions
                should_close = True
                raise
            finally:
                # Close streams if araise requires
                if should_close:
                    self._close_guard = True
                    self.loop.create_task(self.aclose())

    async def aclose(self) -> bool:
        """Close observers.

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
        await self._aclose()

        return True
