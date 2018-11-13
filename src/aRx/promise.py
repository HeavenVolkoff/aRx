__all__ = ("Promise",)

# Internal
import typing as T
from abc import ABCMeta, abstractmethod
from asyncio import CancelledError, AbstractEventLoop, InvalidStateError, shield, ensure_future
from contextlib import contextmanager

# Project
from .abstract.promise import Promise as AbstractPromise

K = T.TypeVar("K")
L = T.TypeVar("L")


async def resolve_awaitable(awaitable: T.Union[K, T.Awaitable[K]], loop: AbstractEventLoop) -> K:
    try:
        result_fut = ensure_future(T.cast(T.Awaitable[K], awaitable), loop=loop)
    except TypeError:
        return T.cast(K, awaitable)  # Not an awaitable
    else:
        return await result_fut


class Promise(AbstractPromise[K]):
    """Promise implementation that maintains the callback queue using :class:`~typing.Coroutine`.
    
    See: :class:`~.abstract.promise.Promise` for more information on the Promise abstract interface.
    """

    def then(self, on_fulfilled: T.Callable[[K], L]) -> "Promise[L]":
        """Concrete implementation that wraps the received callback on a :class:`~typing.Coroutine`.
        The :class:`~typing.Coroutine` will await the promise resolution and,
        if no exception is raised, it will call the callback with the promise 
        result.

        See: :meth:`~.abstract.promise.Promise.then` for more information.

        """
        return FulfillmentPromise(self, on_fulfilled, loop=self._loop)

    def catch(self, on_reject: T.Callable[[Exception], L]) -> "Promise[L]":
        """Concrete implementation that wraps the received callback on a :class:`~typing.Coroutine`.
        The :class:`~typing.Coroutine` will await the promise resolution and,
        if a exception is raised, it will call the callback with the promise 
        exception.

        See: :meth:`~.abstract.promise.Promise.catch` for more information.
        
        """
        return RejectionPromise(self, on_reject, loop=self._loop)

    def lastly(self, on_resolved: T.Callable[[], L]) -> "Promise[K]":
        """Concrete implementation that wraps the received callback on a :class:`~typing.Coroutine`.
        The :class:`~typing.Coroutine` will await the promise resolution and
        call the callback.

        See: :meth:`~.abstract.promise.Promise.lastly` for more information.

        """
        return ResolutionPromise(self, on_resolved, loop=self._loop)


class ChainPromise(Promise[K], metaclass=ABCMeta):
    """A special promise implementation used by the chained callback Promises."""

    def __init__(self, promise: AbstractPromise, callback: T.Callable, **kwargs) -> None:
        super().__init__(self._wrapper(promise, callback), **kwargs)

        # Disable the "destroy pending task" warning
        self._fut._log_destroy_pending = False  # type: ignore

    @abstractmethod
    def _wrapper(self, promise: AbstractPromise, callback: T.Callable):
        raise NotImplementedError

    @contextmanager
    def _cancel_parent_on_external_cancellation(self, promise):
        try:
            yield
        except CancelledError:
            # CancellationError must be propagated through stream
            if not self._directly_cancelled:
                promise.cancel()

            raise

    def resolve(self, _: K):
        """See: :meth:`~aRx.abstract.promise.Promise.resolve` for more information.
        
        Raises:
            InvalidStateError: Chained promises aren't allowed to be resolved externally.

        """
        raise InvalidStateError("Chain promise can't be resolved externally")

    def reject(self, _: Exception):
        """See: :meth:`~aRx.abstract.promise.Promise.reject` for more information.
        
        Raises:
            InvalidStateError: Chained promises aren't allowed to be resolved externally.

        """
        raise InvalidStateError("Chain promise can't be rejected externally")


class FulfillmentPromise(ChainPromise[L]):
    def __init__(
        self, promise: AbstractPromise, on_fulfilled: T.Callable[[K], L], **kwargs
    ) -> None:
        super().__init__(promise, on_fulfilled, **kwargs)

    async def _wrapper(self, promise: AbstractPromise, on_fulfilled: T.Callable[[K], L]) -> L:
        """Coroutine that wraps a promise and manages a fulfillment callback.

        Arguments:
            promise: Promise to be awaited for chain action
            on_fulfilled: Fulfillment callback.

        Returns:
            Callback result.

        """
        with self._cancel_parent_on_external_cancellation(promise):
            result = await shield(promise, loop=self.loop)

        return await resolve_awaitable(on_fulfilled(result), self.loop)


class RejectionPromise(ChainPromise[L]):
    def __init__(
        self, promise: AbstractPromise, on_reject: T.Callable[[Exception], L], **kwargs
    ) -> None:
        super().__init__(promise, on_reject, **kwargs)

    async def _wrapper(
        self,
        promise: AbstractPromise,
        on_reject: T.Callable[[Exception], T.Union[L, T.Awaitable[L]]],
    ) -> L:
        """Coroutine that wraps a promise and manages a rejection callback.

        Arguments:
            promise: Promise to be awaited for chain action
            on_reject: Rejection callback.

        Returns:
            Callback result.

        """
        try:
            with self._cancel_parent_on_external_cancellation(promise):
                return await shield(promise, loop=self.loop)
        except CancelledError:
            raise  # CancelledError must be propagated
        except Exception as exc:
            return await resolve_awaitable(on_reject(exc), self.loop)


class ResolutionPromise(ChainPromise[K]):
    def __init__(
        self, promise: AbstractPromise, on_resolution: T.Callable[[], L], **kwargs
    ) -> None:
        super().__init__(promise, on_resolution, **kwargs)

    async def _wrapper(self, promise: AbstractPromise, on_resolution: T.Callable[[], L]) -> K:
        """Coroutine that wraps a promise and manages a resolution callback.

        Arguments:
            promise: Promise to be awaited for chain action
            on_resolution: Resolution callback.

        Returns:
            Callback result.

        """
        try:
            with self._cancel_parent_on_external_cancellation(promise):
                return await shield(promise, loop=self.loop)
        finally:
            # Finally executes always, but in the case itself was directly cancelled.
            if not self._directly_cancelled:
                await resolve_awaitable(on_resolution(), self.loop)
